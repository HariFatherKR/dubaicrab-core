/**
 * 채팅 관련 타입 정의
 */

/**
 * 메시지 역할
 */
export type MessageRole = "user" | "assistant" | "system";

/**
 * 채팅 메시지
 */
export interface ChatMessage {
  /** 고유 ID */
  id: string;
  /** 역할 (user/assistant/system) */
  role: MessageRole;
  /** 메시지 내용 */
  content: string;
  /** 타임스탬프 (ISO 8601 또는 Unix ms) */
  timestamp: number | string | Date;
  /** 첨부 파일 정보 (선택) */
  attachments?: ChatAttachment[];
  /** 메타데이터 (선택) */
  metadata?: Record<string, unknown>;
}

/**
 * 첨부 파일
 */
export interface ChatAttachment {
  /** 파일명 */
  name: string;
  /** MIME 타입 */
  type: string;
  /** 파일 크기 (bytes) */
  size: number;
  /** 파일 내용 (텍스트/base64) */
  content?: string;
  /** 파일 URL (외부 저장 시) */
  url?: string;
}

/**
 * 채팅 세션
 */
export interface ChatSession {
  /** 세션 ID */
  id: string;
  /** 세션 제목 */
  title: string;
  /** 메시지 목록 */
  messages: ChatMessage[];
  /** 생성 시각 */
  createdAt: Date | string;
  /** 마지막 수정 시각 */
  updatedAt: Date | string;
  /** 사용된 모델 (선택) */
  model?: string;
  /** 시스템 프롬프트 (선택) */
  systemPrompt?: string;
}

/**
 * 스트리밍 응답 청크
 */
export interface StreamChunk {
  /** 청크 타입 */
  type: "start" | "delta" | "done" | "error";
  /** 텍스트 내용 (delta 시) */
  content?: string;
  /** 에러 메시지 (error 시) */
  error?: string;
  /** 완료 시 총 토큰 수 */
  totalTokens?: number;
}

/**
 * 채팅 요청
 */
export interface ChatRequest {
  /** 메시지 목록 */
  messages: ChatMessage[];
  /** 사용할 모델 */
  model: string;
  /** 스트리밍 여부 */
  stream?: boolean;
  /** 온도 (0.0 ~ 2.0) */
  temperature?: number;
  /** 최대 토큰 수 */
  maxTokens?: number;
  /** 시스템 프롬프트 */
  systemPrompt?: string;
}

/**
 * 채팅 응답
 */
export interface ChatResponse {
  /** 응답 메시지 */
  message: ChatMessage;
  /** 사용된 토큰 수 */
  usage?: {
    promptTokens: number;
    completionTokens: number;
    totalTokens: number;
  };
  /** 모델 정보 */
  model?: string;
  /** 응답 시간 (ms) */
  latencyMs?: number;
}
