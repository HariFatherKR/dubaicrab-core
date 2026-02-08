/**
 * @dubaicrab/shared-types
 * Dubai Crab 프로젝트 공유 타입 정의
 */

// Chat types
export type {
  MessageRole,
  ChatMessage,
  ChatAttachment,
  ChatSession,
  StreamChunk,
  ChatRequest,
  ChatResponse,
} from "./chat";

// Gateway types
export type {
  GatewayConfig,
  ConnectionState,
  ResponseType,
  GatewayResponse,
  GatewayStatus,
  WsMessageType,
  WsIncomingMessage,
  WsOutgoingMessage,
  OllamaModel,
  OllamaStatus,
} from "./gateway";

// File types
export type {
  SupportedExtension,
  FileMetadata,
  ParseResult,
  ParseProgressStage,
  ParseProgress,
  FileValidation,
  ParseConfig,
  UploadedFile,
} from "./file";
