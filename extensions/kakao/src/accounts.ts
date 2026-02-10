import type { KakaoAccountConfig } from "./config-schema.js";

export interface DubaiCrabConfig {
  channels?: {
    kakao?: KakaoAccountConfig & {
      accounts?: Record<string, KakaoAccountConfig>;
      defaultAccount?: string;
    };
  };
}

export interface ResolvedKakaoAccount {
  accountId: string;
  name: string;
  enabled: boolean;
  botId?: string;
  config: {
    webhookPath?: string;
    webhookUrl?: string;
    dmPolicy?: "pairing" | "allowlist" | "open" | "disabled";
    allowFrom?: (string | number)[];
    responsePrefix?: string;
  };
}

const DEFAULT_ACCOUNT_ID = "default";

export function listKakaoAccountIds(cfg: DubaiCrabConfig): string[] {
  const kakaoConfig = cfg.channels?.kakao;
  if (!kakaoConfig) {
    return [];
  }

  const accountIds = new Set<string>();

  // 기본 계정
  if (kakaoConfig.webhookPath || kakaoConfig.webhookUrl || kakaoConfig.botId) {
    accountIds.add(DEFAULT_ACCOUNT_ID);
  }

  // 추가 계정들
  if (kakaoConfig.accounts) {
    for (const id of Object.keys(kakaoConfig.accounts)) {
      accountIds.add(id);
    }
  }

  return Array.from(accountIds);
}

export function resolveDefaultKakaoAccountId(cfg: DubaiCrabConfig): string | undefined {
  const kakaoConfig = cfg.channels?.kakao;
  if (!kakaoConfig) {
    return undefined;
  }

  // 명시적 기본 계정
  if (kakaoConfig.defaultAccount) {
    return kakaoConfig.defaultAccount;
  }

  const ids = listKakaoAccountIds(cfg);
  if (ids.length === 1) {
    return ids[0];
  }

  if (ids.includes(DEFAULT_ACCOUNT_ID)) {
    return DEFAULT_ACCOUNT_ID;
  }

  return ids[0];
}

export function resolveKakaoAccount(params: {
  cfg: DubaiCrabConfig;
  accountId?: string;
}): ResolvedKakaoAccount {
  const { cfg, accountId } = params;
  const kakaoConfig = cfg.channels?.kakao;
  const resolvedAccountId = accountId ?? DEFAULT_ACCOUNT_ID;

  // 계정별 설정 또는 기본 설정
  const accountConfig = kakaoConfig?.accounts?.[resolvedAccountId] ?? kakaoConfig;

  if (!accountConfig) {
    return {
      accountId: resolvedAccountId,
      name: resolvedAccountId,
      enabled: false,
      config: {},
    };
  }

  return {
    accountId: resolvedAccountId,
    name: accountConfig.name ?? resolvedAccountId,
    enabled: accountConfig.enabled !== false,
    botId: accountConfig.botId,
    config: {
      webhookPath: accountConfig.webhookPath,
      webhookUrl: accountConfig.webhookUrl,
      dmPolicy: accountConfig.dmPolicy ?? "pairing",
      allowFrom: accountConfig.allowFrom,
      responsePrefix: accountConfig.responsePrefix,
    },
  };
}
