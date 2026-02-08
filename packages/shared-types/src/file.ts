/**
 * 파일 파서 관련 타입 정의
 */

/**
 * 지원되는 파일 확장자
 */
export type SupportedExtension =
  | "txt"
  | "md"
  | "json"
  | "csv"
  | "xlsx"
  | "xls"
  | "pdf"
  | "hwp"
  | "hwpx"
  | "ppt"
  | "pptx";

/**
 * 파일 메타데이터
 */
export interface FileMetadata {
  /** 파일명 */
  fileName: string;
  /** 파일 확장자 */
  fileType: string;
  /** 파일 크기 (bytes) */
  fileSize: number;
  /** 페이지 수 (PDF/HWP) */
  pages?: number;
  /** 시트 이름 (Excel) */
  sheets?: string[];
  /** 슬라이드 수 (PPT) */
  slides?: number;
  /** MIME 타입 */
  mimeType?: string;
  /** 인코딩 */
  encoding?: string;
}

/**
 * 파일 파싱 결과
 */
export interface ParseResult {
  /** 성공 여부 */
  success: boolean;
  /** 추출된 텍스트 내용 */
  content: string;
  /** 파일 메타데이터 */
  metadata: FileMetadata;
  /** 에러 메시지 (실패 시) */
  error?: string;
}

/**
 * 파싱 진행 상태
 */
export type ParseProgressStage =
  | "preparing"
  | "reading"
  | "writing"
  | "parsing"
  | "complete"
  | "error";

/**
 * 파싱 진행 상황
 */
export interface ParseProgress {
  /** 현재 단계 */
  stage: ParseProgressStage;
  /** 파일명 */
  fileName: string;
  /** 파일 크기 */
  fileSize: number;
  /** 진행 메시지 */
  message: string;
  /** 진행률 (0-100) */
  percentage?: number;
}

/**
 * 파일 유효성 검사 결과
 */
export interface FileValidation {
  /** 유효 여부 */
  valid: boolean;
  /** 에러 코드 */
  errorCode?: "UNSUPPORTED_TYPE" | "FILE_TOO_LARGE" | "INVALID_MIME" | "EMPTY_FILE";
  /** 에러 메시지 */
  errorMessage?: string;
}

/**
 * 파일 파싱 설정
 */
export interface ParseConfig {
  /** 타임아웃 (ms) */
  timeoutMs?: number;
  /** 대용량 파일 기준 (bytes) */
  largeFileThreshold?: number;
  /** 최대 파일 크기 (bytes) */
  maxFileSize?: number;
  /** 최대 행 수 (CSV/Excel) */
  maxRows?: number;
  /** 인코딩 */
  encoding?: string;
}

/**
 * 업로드된 파일 정보
 */
export interface UploadedFile {
  /** 고유 ID */
  id: string;
  /** 원본 파일명 */
  originalName: string;
  /** 저장 경로 */
  storagePath?: string;
  /** 파일 크기 */
  size: number;
  /** MIME 타입 */
  mimeType: string;
  /** 업로드 시각 */
  uploadedAt: Date | string;
  /** 파싱 결과 */
  parseResult?: ParseResult;
}
