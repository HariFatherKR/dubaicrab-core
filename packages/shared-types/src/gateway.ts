/**
 * 게이트웨이 관련 타입 정의
 */

/**
 * 게이트웨이 설정
 */
export interface GatewayConfig {
  /** WebSocket URL */
  url: string;
  /** HTTP API URL (선택) */
  httpUrl?: string;
  /** 인증 토큰 */
  token?: string;
  /** 최대 재연결 시도 횟수 */
  reconnectMaxAttempts?: number;
  /** 재연결 기본 딜레이 (ms) */
  reconnectBaseDelayMs?: number;
  /** 하트비트 간격 (ms) */
  heartbeatIntervalMs?: number;
}

/**
 * 연결 상태
 */
export type ConnectionState =
  | "disconnected"
  | "connecting"
  | "connected"
  | "reconnecting"
  | "failed";

/**
 * 게이트웨이 응답 타입
 */
export type ResponseType =
  | "message"
  | "typing"
  | "error"
  | "connected"
  | "disconnected"
  | "reconnecting"
  | "stream";

/**
 * 게이트웨이 응답
 */
export interface GatewayResponse {
  /** 응답 타입 */
  type: ResponseType;
  /** 메시지 내용 */
  content?: string;
  /** 에러 메시지 */
  error?: string;
  /** 재연결 시도 횟수 */
  attempt?: number;
  /** 최대 재연결 시도 횟수 */
  maxAttempts?: number;
}

/**
 * 게이트웨이 상태
 */
export interface GatewayStatus {
  /** 사용 가능 여부 */
  available: boolean;
  /** 게이트웨이 URL */
  url: string;
  /** 에러 메시지 */
  error?: string;
  /** 응답 지연 시간 (ms) */
  latencyMs?: number;
  /** 버전 정보 */
  version?: string;
}

/**
 * WebSocket 메시지 타입
 */
export type WsMessageType =
  | "auth"
  | "chat"
  | "ping"
  | "pong"
  | "response"
  | "stream"
  | "typing"
  | "error";

/**
 * WebSocket 수신 메시지
 */
export interface WsIncomingMessage {
  type: WsMessageType;
  content?: string;
  chunk?: string;
  message?: string;
  timestamp?: number;
}

/**
 * WebSocket 송신 메시지
 */
export interface WsOutgoingMessage {
  type: WsMessageType;
  content?: string;
  token?: string;
  file?: {
    name: string;
    content: string;
  };
  timestamp?: number;
}

/**
 * Ollama 모델 정보
 */
export interface OllamaModel {
  /** 모델 이름 */
  name: string;
  /** 표시 이름 */
  displayName?: string;
  /** 파일 크기 */
  size?: number;
  /** 수정 날짜 */
  modifiedAt?: string;
  /** 다이제스트 */
  digest?: string;
}

/**
 * Ollama 상태
 */
export interface OllamaStatus {
  /** 실행 중 여부 */
  running: boolean;
  /** 버전 */
  version?: string;
  /** 설치된 모델 목록 */
  models?: OllamaModel[];
  /** 에러 메시지 */
  error?: string;
}
