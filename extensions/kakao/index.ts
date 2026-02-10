/**
 * Dubai Crab - Kakao Channel Plugin
 *
 * 카카오톡 스킬서버 웹훅을 통해 Dubai Crab AI 에이전트와 연결합니다.
 *
 * 설정 예시 (config.yaml):
 * ```yaml
 * channels:
 *   kakao:
 *     enabled: true
 *     webhookPath: /kakao/webhook
 *     botId: your-kakao-bot-id
 *     dmPolicy: open  # open | pairing | allowlist | disabled
 *     allowFrom:
 *       - "*"  # 모든 사용자 허용
 * ```
 */

export {
  KakaoConfigSchema,
  type KakaoConfig,
  type KakaoAccountConfig,
} from "./src/config-schema.js";
export {
  listKakaoAccountIds,
  resolveDefaultKakaoAccountId,
  resolveKakaoAccount,
  type ResolvedKakaoAccount,
  type DubaiCrabConfig,
} from "./src/accounts.js";
export {
  handleKakaoWebhookRequest,
  monitorKakaoProvider,
  registerKakaoWebhookTarget,
  resolveKakaoWebhookPath,
  type KakaoMonitorOptions,
  type KakaoRuntimeEnv,
} from "./src/monitor.js";

// 플러그인 메타데이터
export const pluginMeta = {
  id: "kakao",
  name: "Kakao",
  description: "Dubai Crab Kakao channel plugin",
  version: "2026.2.10",
};
