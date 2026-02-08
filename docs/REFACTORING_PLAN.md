# Dubai Crab 리팩토링 계획

**작성일**: 2026-02-08  
**참조**: [CODE_REVIEW.md](./CODE_REVIEW.md)

---

## 목차

1. [우선순위 매트릭스](#1-우선순위-매트릭스)
2. [Phase 1: 즉시 조치 (P0)](#2-phase-1-즉시-조치-p0)
3. [Phase 2: 단기 개선 (P1)](#3-phase-2-단기-개선-p1)
4. [Phase 3: 중기 개선 (P2)](#4-phase-3-중기-개선-p2)
5. [도구 및 린터 권장](#5-도구-및-린터-권장)
6. [마이그레이션 체크리스트](#6-마이그레이션-체크리스트)

---

## 1. 우선순위 매트릭스

| 항목                 | 영향도 | 난이도 | 우선순위 | 예상 시간 |
| -------------------- | :----: | :----: | :------: | :-------: |
| 테스트 커버리지 확대 |  높음  |  중간  |  **P0**  |   3-5일   |
| 에러 핸들링 표준화   |  높음  |  낮음  |  **P0**  |    1일    |
| 공유 타입 패키지     |  높음  |  중간  |  **P0**  |    2일    |
| 설정값 외부화        |  중간  |  낮음  |    P1    |    1일    |
| 구조화된 로깅        |  중간  |  낮음  |    P1    |    1일    |
| 파일 파서 리팩토링   |  중간  |  중간  |    P1    |    2일    |
| 파일 업로드 보안     |  중간  |  낮음  |    P1    |    1일    |
| 모노레포 통합        |  높음  |  높음  |    P2    |    1주    |
| API 스키마 문서화    |  중간  |  중간  |    P2    |    3일    |
| 성능 모니터링        |  낮음  |  중간  |    P2    |    2일    |

---

## 2. Phase 1: 즉시 조치 (P0)

### 2.1 테스트 커버리지 확대

#### 목표

- OpenKlaw 테스트 커버리지: 13% → 50%
- dubaicrab-web 테스트 추가: 0% → 기본 E2E

#### 태스크

**OpenKlaw 단위 테스트 추가**

```bash
# 테스트 구조
tests/
├── lib/
│   ├── gateway-client.test.ts   # WebSocket 클라이언트
│   ├── file-parser.test.ts      # 파일 파싱 (확장)
│   ├── stores/
│   │   ├── chat-store.test.ts   # 채팅 저장소
│   │   └── settings-store.test.ts
│   └── skills/
│       ├── report.test.ts       # 보고서 생성
│       └── email.test.ts        # 이메일 작성
└── e2e/
    └── onboarding.test.ts       # Playwright E2E
```

**예시: gateway-client.test.ts**

```typescript
// tests/lib/gateway-client.test.ts
import { describe, it, expect, vi, beforeEach } from "vitest";
import { GatewayClient } from "$lib/gateway-client";

describe("GatewayClient", () => {
  let client: GatewayClient;
  let mockWebSocket: any;

  beforeEach(() => {
    mockWebSocket = {
      send: vi.fn(),
      close: vi.fn(),
      readyState: WebSocket.OPEN,
    };
    vi.stubGlobal(
      "WebSocket",
      vi.fn(() => mockWebSocket),
    );
    client = new GatewayClient({ url: "ws://localhost:18789" });
  });

  describe("connect", () => {
    it("WebSocket 연결 성공 시 connected 이벤트 발생", async () => {
      const handler = vi.fn();
      client.onMessage(handler);

      const connectPromise = client.connect();
      mockWebSocket.onopen();

      await connectPromise;
      expect(handler).toHaveBeenCalledWith({ type: "connected" });
    });

    it("토큰이 있으면 인증 메시지 전송", async () => {
      client = new GatewayClient({
        url: "ws://localhost:18789",
        token: "test-token",
      });

      const connectPromise = client.connect();
      mockWebSocket.onopen();
      await connectPromise;

      expect(mockWebSocket.send).toHaveBeenCalledWith(
        JSON.stringify({ type: "auth", token: "test-token" }),
      );
    });
  });

  describe("sendMessage", () => {
    it("연결되지 않으면 에러 이벤트 발생", () => {
      mockWebSocket.readyState = WebSocket.CLOSED;
      const handler = vi.fn();
      client.onMessage(handler);

      client.sendMessage("test");

      expect(handler).toHaveBeenCalledWith({
        type: "error",
        error: "연결되지 않음",
      });
    });
  });

  describe("reconnect", () => {
    it("연결 끊김 시 재연결 시도", async () => {
      vi.useFakeTimers();
      await client.connect();
      mockWebSocket.onopen();

      mockWebSocket.onclose();

      vi.advanceTimersByTime(1000);
      expect(WebSocket).toHaveBeenCalledTimes(2);
      vi.useRealTimers();
    });
  });
});
```

**dubaicrab-web E2E 테스트**

```typescript
// tests/e2e/landing.spec.ts (Playwright)
import { test, expect } from "@playwright/test";

test.describe("랜딩 페이지", () => {
  test("메인 헤딩 표시", async ({ page }) => {
    await page.goto("/");
    await expect(page.getByRole("heading", { name: /AI 쓰는 방법/ })).toBeVisible();
  });

  test("이메일 폼 제출", async ({ page }) => {
    await page.goto("/");
    await page.getByPlaceholder("이메일 주소").fill("test@example.com");
    await page.getByRole("button", { name: "알림 받기" }).click();
    await expect(page.getByText("등록 완료")).toBeVisible();
  });

  test("다운로드 링크 유효", async ({ page }) => {
    await page.goto("/");
    const downloadLink = page.getByRole("link", { name: /Mac OS Download/ });
    await expect(downloadLink).toHaveAttribute("href", /\.dmg$/);
  });
});
```

---

### 2.2 에러 핸들링 표준화

#### 목표

- 모든 catch 블록에서 타입 안전한 에러 처리
- 공통 에러 유틸리티 함수 제공

#### 구현

**공통 에러 유틸리티 생성**

```typescript
// src/lib/utils/error.ts (OpenKlaw)
export class AppError extends Error {
  constructor(
    message: string,
    public readonly code: string,
    public readonly cause?: unknown,
  ) {
    super(message);
    this.name = "AppError";
  }
}

export function formatError(error: unknown): string {
  if (error instanceof AppError) {
    return `[${error.code}] ${error.message}`;
  }
  if (error instanceof Error) {
    return error.message;
  }
  return String(error);
}

export function isNetworkError(error: unknown): boolean {
  if (error instanceof Error) {
    return (
      error.message.includes("network") ||
      error.message.includes("fetch") ||
      error.name === "TypeError"
    );
  }
  return false;
}

// Result 타입 (에러를 값으로 처리)
export type Result<T, E = AppError> = { ok: true; value: T } | { ok: false; error: E };

export function ok<T>(value: T): Result<T> {
  return { ok: true, value };
}

export function err<E>(error: E): Result<never, E> {
  return { ok: false, error };
}
```

**리팩토링 예시**

```typescript
// Before (file-parser.ts)
} catch (error) {
  return {
    success: false,
    error: `텍스트 파일 읽기 실패: ${error}`
  };
}

// After
import { formatError, AppError } from '$lib/utils/error';

} catch (error) {
  return {
    success: false,
    content: '',
    metadata: { fileName: file.name, fileType: ext, fileSize: file.size },
    error: new AppError(
      `텍스트 파일 읽기 실패: ${formatError(error)}`,
      'FILE_READ_ERROR',
      error
    ).message
  };
}
```

---

### 2.3 공유 타입 패키지

#### 목표

- 프로젝트 간 중복 타입 제거
- 단일 진실 공급원(Single Source of Truth)

#### 구조

```
packages/
└── shared-types/
    ├── package.json
    ├── tsconfig.json
    └── src/
        ├── index.ts
        ├── chat.ts        # ChatMessage, ChatSession
        ├── gateway.ts     # GatewayConfig, GatewayResponse
        ├── file.ts        # ParseResult, SupportedExtension
        └── report.ts      # ReportTemplate, ReportResult
```

**package.json**

```json
{
  "name": "@dubaicrab/shared-types",
  "version": "0.1.0",
  "main": "dist/index.js",
  "types": "dist/index.d.ts",
  "scripts": {
    "build": "tsc",
    "watch": "tsc --watch"
  },
  "devDependencies": {
    "typescript": "^5.0.0"
  }
}
```

**src/chat.ts**

```typescript
export interface ChatMessage {
  id: string;
  role: "user" | "assistant" | "system";
  content: string;
  timestamp: Date;
  metadata?: {
    model?: string;
    tokens?: number;
    attachments?: string[];
  };
}

export interface ChatSession {
  id: string;
  title: string;
  messages: ChatMessage[];
  createdAt: Date;
  updatedAt: Date;
  tags?: string[];
}

export type MessageRole = ChatMessage["role"];
```

---

## 3. Phase 2: 단기 개선 (P1)

### 3.1 설정값 외부화

#### 구현

```typescript
// src/lib/config/index.ts
export const CONFIG = {
  gateway: {
    url: import.meta.env.VITE_GATEWAY_URL || "ws://127.0.0.1:18789",
    httpUrl: import.meta.env.VITE_GATEWAY_HTTP_URL || "http://127.0.0.1:18789",
    reconnect: {
      maxAttempts: Number(import.meta.env.VITE_RECONNECT_MAX) || 5,
      delayMs: Number(import.meta.env.VITE_RECONNECT_DELAY) || 1000,
    },
  },
  storage: {
    maxSessions: 100,
    maxMessagesPerSession: 1000,
  },
  fileParser: {
    maxFileSizeMb: 50,
    maxExcelRows: 50,
    maxExcelSheets: 5,
    maxPptSlides: 20,
  },
} as const;

export type Config = typeof CONFIG;
```

---

### 3.2 구조화된 로깅

#### 구현

```typescript
// src/lib/logger.ts
type LogLevel = "debug" | "info" | "warn" | "error";

interface LogEntry {
  level: LogLevel;
  message: string;
  timestamp: string;
  context?: Record<string, unknown>;
}

class Logger {
  private isDev = import.meta.env.DEV;

  private log(level: LogLevel, message: string, context?: Record<string, unknown>) {
    const entry: LogEntry = {
      level,
      message,
      timestamp: new Date().toISOString(),
      context,
    };

    if (this.isDev) {
      const prefix = `[${level.toUpperCase()}]`;
      const contextStr = context ? ` ${JSON.stringify(context)}` : "";
      console[level === "debug" ? "log" : level](`${prefix} ${message}${contextStr}`);
    }

    // Production: 구조화된 로그 (추후 외부 서비스 연동)
    // this.sendToExternalService(entry);
  }

  debug(message: string, context?: Record<string, unknown>) {
    this.log("debug", message, context);
  }

  info(message: string, context?: Record<string, unknown>) {
    this.log("info", message, context);
  }

  warn(message: string, context?: Record<string, unknown>) {
    this.log("warn", message, context);
  }

  error(message: string, context?: Record<string, unknown>) {
    this.log("error", message, context);
  }
}

export const logger = new Logger();
```

**사용 예**

```typescript
// Before
console.log("[게이트웨이] 연결됨");

// After
import { logger } from "$lib/logger";
logger.info("gateway.connected", { url: this.config.url });
```

---

### 3.3 파일 파서 리팩토링 (전략 패턴)

#### 구현

```typescript
// src/lib/tools/parsers/types.ts
export interface FileParser {
  readonly extensions: readonly string[];
  parse(file: File): Promise<ParseResult>;
}

// src/lib/tools/parsers/text-parser.ts
export class TextFileParser implements FileParser {
  readonly extensions = ["txt", "md", "json"] as const;

  async parse(file: File): Promise<ParseResult> {
    try {
      const content = await file.text();
      return {
        success: true,
        content,
        metadata: {
          fileName: file.name,
          fileType: getFileExtension(file.name),
          fileSize: file.size,
        },
      };
    } catch (error) {
      return this.createError(file, error);
    }
  }

  private createError(file: File, error: unknown): ParseResult {
    return {
      success: false,
      content: "",
      metadata: {
        fileName: file.name,
        fileType: getFileExtension(file.name),
        fileSize: file.size,
      },
      error: `텍스트 파일 읽기 실패: ${formatError(error)}`,
    };
  }
}

// src/lib/tools/parsers/index.ts
import { TextFileParser } from "./text-parser";
import { CsvFileParser } from "./csv-parser";
import { ExcelFileParser } from "./excel-parser";
import { PdfFileParser } from "./pdf-parser";
import { HwpFileParser } from "./hwp-parser";
import { PptFileParser } from "./ppt-parser";

const parsers: FileParser[] = [
  new TextFileParser(),
  new CsvFileParser(),
  new ExcelFileParser(),
  new PdfFileParser(),
  new HwpFileParser(),
  new PptFileParser(),
];

const parserMap = new Map<string, FileParser>();
for (const parser of parsers) {
  for (const ext of parser.extensions) {
    parserMap.set(ext, parser);
  }
}

export async function parseFile(file: File): Promise<ParseResult> {
  const ext = getFileExtension(file.name);
  const parser = parserMap.get(ext);

  if (!parser) {
    return {
      success: false,
      content: "",
      metadata: { fileName: file.name, fileType: ext, fileSize: file.size },
      error: `지원하지 않는 파일 형식: .${ext}`,
    };
  }

  return parser.parse(file);
}
```

---

### 3.4 파일 업로드 보안 강화

```typescript
// src/lib/utils/file-validator.ts
export const FILE_LIMITS = {
  maxSizeMb: 50,
  maxSizeBytes: 50 * 1024 * 1024,
} as const;

export const ALLOWED_TYPES: Record<string, string[]> = {
  document: ["application/pdf", "application/x-hwp", "application/haansofthwp"],
  spreadsheet: [
    "application/vnd.ms-excel",
    "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
  ],
  presentation: [
    "application/vnd.ms-powerpoint",
    "application/vnd.openxmlformats-officedocument.presentationml.presentation",
  ],
  text: ["text/plain", "text/csv", "text/markdown", "application/json"],
};

export interface ValidationResult {
  valid: boolean;
  error?: string;
}

export function validateFile(file: File): ValidationResult {
  // 1. 크기 검사
  if (file.size > FILE_LIMITS.maxSizeBytes) {
    return {
      valid: false,
      error: `파일 크기가 ${FILE_LIMITS.maxSizeMb}MB를 초과합니다.`,
    };
  }

  // 2. 확장자 검사
  const ext = file.name.split(".").pop()?.toLowerCase();
  if (!ext || !SUPPORTED_EXTENSIONS.includes(ext)) {
    return {
      valid: false,
      error: `지원하지 않는 파일 형식입니다: .${ext}`,
    };
  }

  // 3. MIME 타입 검사 (확장자와 일치 여부)
  const allMimes = Object.values(ALLOWED_TYPES).flat();
  if (file.type && !allMimes.includes(file.type)) {
    // 빈 문자열 MIME은 허용 (일부 브라우저에서 발생)
    if (file.type !== "") {
      return {
        valid: false,
        error: `허용되지 않는 파일 타입입니다: ${file.type}`,
      };
    }
  }

  return { valid: true };
}
```

---

## 4. Phase 3: 중기 개선 (P2)

### 4.1 모노레포 구조 통합

#### 권장 구조

```
dubai-crab/
├── apps/
│   ├── core/          # dubaicrab-core (기존)
│   ├── desktop/       # OpenKlaw (기존)
│   └── web/           # dubaicrab-web (기존)
├── packages/
│   ├── shared-types/  # 공통 타입
│   ├── ui-kit/        # 공통 UI 컴포넌트
│   └── utils/         # 공통 유틸리티
├── pnpm-workspace.yaml
├── turbo.json         # Turborepo 설정
└── package.json
```

**pnpm-workspace.yaml**

```yaml
packages:
  - "apps/*"
  - "packages/*"
```

**turbo.json**

```json
{
  "$schema": "https://turbo.build/schema.json",
  "pipeline": {
    "build": {
      "dependsOn": ["^build"],
      "outputs": ["dist/**", "build/**", ".next/**"]
    },
    "test": {
      "dependsOn": ["build"]
    },
    "lint": {},
    "dev": {
      "cache": false,
      "persistent": true
    }
  }
}
```

---

### 4.2 API 스키마 문서화

#### TypeSpec 사용 권장

```typespec
// api/gateway.tsp
import "@typespec/http";
import "@typespec/rest";

@service({
  title: "Dubai Crab Gateway API",
  version: "0.1.0",
})
namespace DubaiCrab;

@route("/api")
namespace Api {
  @route("/status")
  @get
  op getStatus(): {
    @statusCode statusCode: 200;
    @body body: StatusResponse;
  };

  @route("/chat")
  @post
  op sendMessage(@body message: ChatRequest): {
    @statusCode statusCode: 200;
    @body body: ChatResponse;
  };
}

model StatusResponse {
  status: "running" | "stopped";
  version: string;
  uptime: int64;
}

model ChatRequest {
  content: string;
  sessionId?: string;
  attachments?: Attachment[];
}

model ChatResponse {
  messageId: string;
  content: string;
  role: "assistant";
  timestamp: utcDateTime;
}

model Attachment {
  name: string;
  content: string;
  mimeType: string;
}
```

---

## 5. 도구 및 린터 권장

### 현재 사용 중

- ✅ oxlint (TypeScript 린터)
- ✅ prettier (포매터)
- ✅ Vitest (테스트)
- ✅ pre-commit hooks

### 추가 권장

| 도구                 | 용도                  | 설치                                                |
| -------------------- | --------------------- | --------------------------------------------------- |
| **@biomejs/biome**   | oxlint 대체 (더 빠름) | `pnpm add -D @biomejs/biome`                        |
| **knip**             | 미사용 코드 감지      | `pnpm add -D knip`                                  |
| **depcheck**         | 미사용 의존성         | `pnpm add -D depcheck`                              |
| **@playwright/test** | E2E 테스트            | `pnpm add -D @playwright/test`                      |
| **typecov**          | 타입 커버리지         | `pnpm add -D typecov`                               |
| **commitlint**       | 커밋 메시지 검증      | `pnpm add -D @commitlint/{cli,config-conventional}` |

**commitlint 설정**

```js
// commitlint.config.js
export default {
  extends: ["@commitlint/config-conventional"],
  rules: {
    "type-enum": [
      2,
      "always",
      ["feat", "fix", "docs", "style", "refactor", "test", "chore", "perf"],
    ],
    "subject-case": [2, "always", "sentence-case"],
  },
};
```

---

## 6. 마이그레이션 체크리스트

### Phase 1 (P0) - 1주

- [ ] 에러 유틸리티 (`src/lib/utils/error.ts`) 생성
- [ ] 기존 catch 블록 리팩토링 (OpenKlaw)
- [ ] `@dubaicrab/shared-types` 패키지 생성
- [ ] OpenKlaw 테스트 추가
  - [ ] gateway-client.test.ts
  - [ ] file-parser.test.ts (확장)
  - [ ] chat-store.test.ts
  - [ ] settings-store.test.ts
- [ ] dubaicrab-web Playwright 설정
- [ ] 기본 E2E 테스트 작성

### Phase 2 (P1) - 2주

- [ ] 설정 상수 파일 생성 (`src/lib/config/index.ts`)
- [ ] 환경변수 마이그레이션
- [ ] 구조화된 로거 구현
- [ ] console.log → logger 마이그레이션
- [ ] FileParser 인터페이스 정의
- [ ] 각 파서 클래스 분리
- [ ] 파일 검증 유틸리티 추가
- [ ] 업로드 컴포넌트에 검증 적용

### Phase 3 (P2) - 1개월

- [ ] 모노레포 구조 설계
- [ ] Turborepo 설정
- [ ] 패키지 마이그레이션
- [ ] TypeSpec/OpenAPI 스키마 작성
- [ ] API 문서 자동 생성 파이프라인
- [ ] 성능 모니터링 도구 선정
- [ ] 메트릭 수집 구현

---

## 변경 이력

| 날짜       | 버전 | 변경 내용 |
| ---------- | ---- | --------- |
| 2026-02-08 | 1.0  | 초기 작성 |

---

_이 문서는 코드베이스 변경에 따라 지속적으로 업데이트됩니다._
