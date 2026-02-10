import type { IncomingMessage, ServerResponse } from "node:http";
import type { ResolvedKakaoAccount, DubaiCrabConfig } from "./accounts.js";

export type KakaoRuntimeEnv = {
  log?: (message: string) => void;
  error?: (message: string) => void;
};

export type KakaoMonitorOptions = {
  account: ResolvedKakaoAccount;
  config: DubaiCrabConfig;
  runtime: KakaoRuntimeEnv;
  abortSignal: AbortSignal;
  webhookPath?: string;
  webhookUrl?: string;
  statusSink?: (patch: { lastInboundAt?: number; lastOutboundAt?: number }) => void;
  // Dubai Crab 에이전트 핸들러
  handleMessage?: (params: {
    senderId: string;
    message: string;
    botId?: string;
  }) => Promise<string>;
};

// 카카오 요청/응답 타입
type KakaoBot = {
  id?: string;
  name?: string;
};

type KakaoUser = {
  id?: string;
  type?: string;
  properties?: Record<string, unknown>;
};

type KakaoUserRequest = {
  utterance?: string;
  user?: KakaoUser;
  params?: Record<string, unknown>;
  callbackUrl?: string;
  lang?: string;
  timezone?: string;
  block?: { id?: string; name?: string };
};

type KakaoRequest = {
  bot?: KakaoBot;
  userRequest?: KakaoUserRequest;
  intent?: { id?: string; name?: string };
  action?: { id?: string; name?: string };
};

type KakaoResponse = {
  version: "2.0";
  useCallback?: boolean;
  template: {
    outputs: Array<{ simpleText: { text: string } }>;
  };
  data?: { text?: string };
};

type WebhookTarget = {
  account: ResolvedKakaoAccount;
  config: DubaiCrabConfig;
  runtime: KakaoRuntimeEnv;
  path: string;
  botId?: string;
  statusSink?: (patch: { lastInboundAt?: number; lastOutboundAt?: number }) => void;
  handleMessage?: (params: {
    senderId: string;
    message: string;
    botId?: string;
  }) => Promise<string>;
};

const webhookTargets = new Map<string, WebhookTarget[]>();

function normalizeWebhookPath(raw: string): string {
  const trimmed = raw.trim();
  if (!trimmed) {
    return "/";
  }
  const withSlash = trimmed.startsWith("/") ? trimmed : `/${trimmed}`;
  if (withSlash.length > 1 && withSlash.endsWith("/")) {
    return withSlash.slice(0, -1);
  }
  return withSlash;
}

function resolveWebhookPath(webhookPath?: string, webhookUrl?: string): string | null {
  const trimmedPath = webhookPath?.trim();
  if (trimmedPath) {
    return normalizeWebhookPath(trimmedPath);
  }
  if (webhookUrl?.trim()) {
    try {
      const parsed = new URL(webhookUrl);
      return normalizeWebhookPath(parsed.pathname || "/");
    } catch {
      return null;
    }
  }
  return "/kakao/webhook";
}

async function readJsonBody(req: IncomingMessage, maxBytes: number) {
  const chunks: Buffer[] = [];
  let total = 0;
  return await new Promise<{ ok: boolean; value?: unknown; error?: string }>((resolve) => {
    req.on("data", (chunk: Buffer) => {
      total += chunk.length;
      if (total > maxBytes) {
        resolve({ ok: false, error: "payload too large" });
        req.destroy();
        return;
      }
      chunks.push(chunk);
    });
    req.on("end", () => {
      try {
        const raw = Buffer.concat(chunks).toString("utf8");
        if (!raw.trim()) {
          resolve({ ok: false, error: "empty payload" });
          return;
        }
        resolve({ ok: true, value: JSON.parse(raw) as unknown });
      } catch (err) {
        resolve({ ok: false, error: err instanceof Error ? err.message : String(err) });
      }
    });
    req.on("error", (err) => {
      resolve({ ok: false, error: err instanceof Error ? err.message : String(err) });
    });
  });
}

function resolveSenderId(request: KakaoUserRequest): string | null {
  const userId = request.user?.id?.trim();
  if (userId) {
    return userId;
  }
  const props = request.user?.properties ?? {};
  const botUserKey = typeof props.botUserKey === "string" ? props.botUserKey : undefined;
  if (botUserKey?.trim()) {
    return botUserKey.trim();
  }
  const legacyBotUserKey = typeof props.bot_user_key === "string" ? props.bot_user_key : undefined;
  if (legacyBotUserKey?.trim()) {
    return legacyBotUserKey.trim();
  }
  return null;
}

function buildKakaoResponse(text: string): KakaoResponse {
  return {
    version: "2.0",
    template: {
      outputs: [
        {
          simpleText: {
            text,
          },
        },
      ],
    },
  };
}

async function sendKakaoCallbackResponse(
  url: string,
  payload: KakaoResponse,
  runtime: KakaoRuntimeEnv,
): Promise<void> {
  try {
    const res = await fetch(url, {
      method: "POST",
      headers: { "Content-Type": "application/json; charset=utf-8" },
      body: JSON.stringify(payload),
    });
    if (!res.ok) {
      const body = await res.text().catch(() => "");
      runtime.error?.(`[kakao] callback response failed (${res.status})${body ? `: ${body}` : ""}`);
    }
  } catch (err) {
    runtime.error?.(`[kakao] callback response error: ${String(err)}`);
  }
}

function pickTarget(targets: WebhookTarget[], botId?: string): WebhookTarget | null {
  if (targets.length === 0) {
    return null;
  }
  if (botId) {
    const match = targets.find((entry) => entry.botId && entry.botId === botId);
    if (match) {
      return match;
    }
  }
  if (targets.length === 1) {
    return targets[0];
  }
  return null;
}

export function registerKakaoWebhookTarget(target: WebhookTarget): () => void {
  const key = normalizeWebhookPath(target.path);
  const normalizedTarget = { ...target, path: key };
  const existing = webhookTargets.get(key) ?? [];
  const next = [...existing, normalizedTarget];
  webhookTargets.set(key, next);
  return () => {
    const updated = (webhookTargets.get(key) ?? []).filter((entry) => entry !== normalizedTarget);
    if (updated.length > 0) {
      webhookTargets.set(key, updated);
    } else {
      webhookTargets.delete(key);
    }
  };
}

async function processKakaoRequest(params: {
  request: KakaoRequest;
  target: WebhookTarget;
}): Promise<string | null> {
  const { request, target } = params;
  const userRequest = request.userRequest;
  if (!userRequest) {
    return null;
  }

  const rawBody = userRequest.utterance?.trim() || "";
  if (!rawBody) {
    return null;
  }

  const senderId = resolveSenderId(userRequest) ?? "unknown";
  const dmPolicy = target.account.config.dmPolicy ?? "open";
  const configAllowFrom = (target.account.config.allowFrom ?? []).map((v) => String(v));

  // 접근 제어
  if (dmPolicy === "disabled") {
    target.runtime.log?.(`[kakao] blocked sender ${senderId} (disabled)`);
    return "이 봇은 현재 비활성화되어 있습니다.";
  }

  if (dmPolicy !== "open" && configAllowFrom.length > 0) {
    const normalizedSenderId = senderId.toLowerCase();
    const isAllowed = configAllowFrom.some((entry) => {
      const normalized = entry.toLowerCase().replace(/^(kakao|kakaotalk):/i, "");
      return normalized === normalizedSenderId || entry === "*";
    });

    if (!isAllowed) {
      target.runtime.log?.(`[kakao] blocked sender ${senderId}`);
      return "접근이 허용되지 않았습니다. 관리자에게 문의하세요.";
    }
  }

  // Dubai Crab 에이전트로 메시지 전달
  if (target.handleMessage) {
    try {
      const response = await target.handleMessage({
        senderId,
        message: rawBody,
        botId: request.bot?.id,
      });
      return response || "응답을 생성하지 못했어요.";
    } catch (err) {
      target.runtime.error?.(`[kakao] agent error: ${String(err)}`);
      return "처리 중 오류가 발생했습니다.";
    }
  }

  return "Dubai Crab 에이전트가 연결되지 않았습니다.";
}

export async function handleKakaoWebhookRequest(
  req: IncomingMessage,
  res: ServerResponse,
): Promise<boolean> {
  const url = new URL(req.url ?? "/", "http://localhost");
  const path = normalizeWebhookPath(url.pathname);
  const targets = webhookTargets.get(path);
  if (!targets || targets.length === 0) {
    return false;
  }

  if (req.method !== "POST") {
    res.statusCode = 405;
    res.setHeader("Allow", "POST");
    res.end("Method Not Allowed");
    return true;
  }

  const body = await readJsonBody(req, 1024 * 1024);
  if (!body.ok) {
    res.statusCode = body.error === "payload too large" ? 413 : 400;
    res.end(body.error ?? "invalid payload");
    return true;
  }

  const raw = body.value;
  if (!raw || typeof raw !== "object" || Array.isArray(raw)) {
    res.statusCode = 400;
    res.end("invalid payload");
    return true;
  }

  const request = raw as KakaoRequest;
  const botId = request.bot?.id?.trim();
  if (!request.userRequest || typeof request.userRequest.utterance !== "string") {
    res.statusCode = 400;
    res.end("invalid payload");
    return true;
  }

  const target = pickTarget(targets, botId);
  if (!target) {
    res.statusCode = 409;
    res.end("ambiguous kakao webhook target");
    return true;
  }

  target.statusSink?.({ lastInboundAt: Date.now() });

  const callbackUrl = request.userRequest.callbackUrl?.trim() || "";

  // 비동기 콜백 응답 (5초 이상 걸리는 경우)
  if (callbackUrl) {
    res.statusCode = 200;
    res.setHeader("Content-Type", "application/json; charset=utf-8");
    res.end(
      JSON.stringify({
        version: "2.0",
        useCallback: true,
        data: { text: "처리중입니다..." },
        template: { outputs: [] },
      }),
    );

    void (async () => {
      let text: string | null = null;
      try {
        text = await processKakaoRequest({ request, target });
      } catch (err) {
        target.runtime.error?.(`[kakao] webhook failed: ${String(err)}`);
      }
      const responseText = text ?? "응답을 생성하지 못했어요.";
      await sendKakaoCallbackResponse(
        callbackUrl,
        buildKakaoResponse(responseText),
        target.runtime,
      );
      target.statusSink?.({ lastOutboundAt: Date.now() });
    })();
    return true;
  }

  // 동기 응답 (5초 이내)
  let text: string | null = null;
  try {
    text = await processKakaoRequest({ request, target });
  } catch (err) {
    target.runtime.error?.(`[kakao] webhook failed: ${String(err)}`);
  }

  const responseText = text ?? "응답을 생성하지 못했어요.";
  const payload = buildKakaoResponse(responseText);
  res.statusCode = 200;
  res.setHeader("Content-Type", "application/json; charset=utf-8");
  res.end(JSON.stringify(payload));
  target.statusSink?.({ lastOutboundAt: Date.now() });
  return true;
}

export function monitorKakaoProvider(options: KakaoMonitorOptions): () => void {
  const webhookPath = resolveWebhookPath(options.webhookPath, options.webhookUrl);
  if (!webhookPath) {
    options.runtime.error?.(`[${options.account.accountId}] invalid webhook path`);
    return () => {};
  }

  const unregister = registerKakaoWebhookTarget({
    account: options.account,
    config: options.config,
    runtime: options.runtime,
    path: webhookPath,
    botId: options.account.botId,
    statusSink: options.statusSink,
    handleMessage: options.handleMessage,
  });

  options.runtime.log?.(`[kakao] registered webhook handler at ${webhookPath}`);

  const stop = () => {
    options.abortSignal.removeEventListener("abort", stop);
    unregister();
  };
  options.abortSignal.addEventListener("abort", stop);
  return stop;
}

export function resolveKakaoWebhookPath(params: { account: ResolvedKakaoAccount }): string {
  return (
    resolveWebhookPath(params.account.config.webhookPath, params.account.config.webhookUrl) ??
    "/kakao/webhook"
  );
}
