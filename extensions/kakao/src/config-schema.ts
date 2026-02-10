import { z } from "zod";

const allowFromEntry = z.union([z.string(), z.number()]);

// 마크다운 설정 스키마
const MarkdownConfigSchema = z
  .object({
    enabled: z.boolean().optional(),
    codeBlockStyle: z.enum(["fenced", "indented"]).optional(),
  })
  .optional();

// 단일 카카오 계정 스키마
const kakaoAccountSchema = z.object({
  name: z.string().optional(),
  enabled: z.boolean().optional(),
  markdown: MarkdownConfigSchema,
  webhookPath: z.string().optional(),
  webhookUrl: z.string().optional(),
  botId: z.string().optional(),
  dmPolicy: z.enum(["pairing", "allowlist", "open", "disabled"]).optional(),
  allowFrom: z.array(allowFromEntry).optional(),
  responsePrefix: z.string().optional(),
});

// 전체 카카오 설정 스키마
export const KakaoConfigSchema = kakaoAccountSchema.extend({
  accounts: z.object({}).catchall(kakaoAccountSchema).optional(),
  defaultAccount: z.string().optional(),
});

export type KakaoConfig = z.infer<typeof KakaoConfigSchema>;
export type KakaoAccountConfig = z.infer<typeof kakaoAccountSchema>;
