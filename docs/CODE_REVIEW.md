# Dubai Crab 코드 리뷰 리포트

**리뷰일**: 2026-02-08  
**리뷰어**: AI CTO  
**대상 프로젝트**:

- dubaicrab-core (백엔드)
- OpenKlaw (Tauri UI)
- dubaicrab-web (웹사이트)

---

## 1. 프로젝트 개요

### dubaicrab-core (백엔드)

- **기술 스택**: Node.js, TypeScript, pnpm 모노레포
- **주요 특징**: OpenClaw 경량 포크, AI 게이트웨이
- **파일 구조**: 1,656개 TypeScript 파일, 946개 테스트 파일
- **테스트 커버리지**: ~36% (테스트 파일 수 기준)

### OpenKlaw (Tauri UI)

- **기술 스택**: Tauri 2.0, Svelte 5, Rust, TypeScript
- **주요 특징**: 데스크톱 앱, HWP 파싱, Ollama 연동
- **UI 프레임워크**: SvelteKit + TailwindCSS

### dubaicrab-web (웹사이트)

- **기술 스택**: Next.js 16, React 19, TypeScript
- **주요 특징**: 랜딩 페이지, 이메일 수집 폼

---

## 2. 코드 품질 분석

### 2.1 강점 ✅

#### dubaicrab-core

- **타입 안전성**: `strict: true` 설정으로 강력한 타입 체크
- **모듈화**: 기능별 디렉토리 분리 (`src/infra/`, `src/cli/`, `src/config/` 등)
- **테스트 인프라**: Vitest 활용, 단위/통합/E2E 테스트 구분
- **에러 핸들링**: `formatErrorMessage`, `extractErrorCode` 등 일관된 에러 처리
- **린팅**: oxlint, prettier, pre-commit 훅 설정
- **CI/CD**: GitHub Actions 워크플로우 구성

```typescript
// 좋은 예: 일관된 에러 처리 (src/infra/errors.ts)
export function formatUncaughtError(err: unknown): string {
  if (extractErrorCode(err) === "INVALID_CONFIG") {
    return formatErrorMessage(err);
  }
  if (err instanceof Error) {
    return err.stack ?? err.message ?? err.name;
  }
  return formatErrorMessage(err);
}
```

#### OpenKlaw

- **클린 아키텍처**: `lib/` 하위에 stores, skills, tools 분리
- **타입 정의**: 인터페이스 명확하게 정의
- **Tauri 통합**: Rust 백엔드와 TypeScript 프론트엔드 분리
- **재사용 컴포넌트**: GlassCard, StatCard 등 UI 컴포넌트 모듈화

```typescript
// 좋은 예: 명확한 인터페이스 정의 (src/lib/gateway-client.ts)
export interface GatewayConfig {
  url: string;
  token?: string;
}

export interface ChatMessage {
  role: "user" | "assistant" | "system";
  content: string;
  timestamp?: number;
}
```

#### dubaicrab-web

- **최신 스택**: Next.js 16 + React 19 활용
- **애니메이션**: Framer Motion 효과적 사용
- **폼 처리**: react-hook-form으로 타입 안전한 폼

---

### 2.2 개선 필요 사항 ⚠️

#### 1. 에러 핸들링 일관성 부족

**문제점**: 일부 함수에서 `any` 타입 에러 사용, catch 블록에서 빈 처리

```typescript
// 개선 필요 (OpenKlaw - file-parser.ts)
} catch (error) {
  return {
    success: false,
    error: `텍스트 파일 읽기 실패: ${error}`  // 타입 불안전
  };
}

// 권장 방식
} catch (error) {
  const message = error instanceof Error ? error.message : String(error);
  return {
    success: false,
    error: `텍스트 파일 읽기 실패: ${message}`
  };
}
```

**영향도**: 중간  
**위치**: `OpenKlaw/src/lib/file-parser.ts`, 다수

---

#### 2. 함수 크기 과대 (Single Responsibility 위반)

**문제점**: 일부 파서 함수가 300줄 이상, 단일 책임 원칙 위반

```typescript
// 개선 필요 (file-parser.ts - parseFile 함수)
export async function parseFile(file: File): Promise<ParseResult> {
  const ext = getFileExtension(file.name);
  switch (ext) {
    case "txt":
    case "md":
    case "json":
      return parseTextFile(file);
    // ... 많은 케이스
  }
}

// 권장: 전략 패턴 사용
const parsers: Record<string, FileParser> = {
  txt: new TextFileParser(),
  csv: new CsvFileParser(),
  xlsx: new ExcelFileParser(),
  // ...
};

export async function parseFile(file: File): Promise<ParseResult> {
  const ext = getFileExtension(file.name);
  const parser = parsers[ext];
  if (!parser) throw new UnsupportedFileError(ext);
  return parser.parse(file);
}
```

**영향도**: 중간  
**위치**: `OpenKlaw/src/lib/file-parser.ts`

---

#### 3. 하드코딩된 설정값

**문제점**: 매직 넘버, 하드코딩된 URL

```typescript
// 개선 필요
const maxReconnectAttempts = 5;
const reconnectDelay = 1000;
const url = "ws://127.0.0.1:18789";

// 권장: 설정 파일 분리
// config/constants.ts
export const GATEWAY_CONFIG = {
  DEFAULT_URL: process.env.GATEWAY_URL || "ws://127.0.0.1:18789",
  MAX_RECONNECT_ATTEMPTS: 5,
  RECONNECT_DELAY_MS: 1000,
} as const;
```

**영향도**: 낮음  
**위치**: `OpenKlaw/src/lib/gateway-client.ts`, `src/lib/stores/`

---

#### 4. 테스트 커버리지 불균형

**문제점**: core는 테스트 풍부, OpenKlaw/Web은 테스트 부족

| 프로젝트       | 테스트 파일 | 소스 파일 | 비율 |
| -------------- | ----------- | --------- | ---- |
| dubaicrab-core | 946         | 1,656     | ~57% |
| OpenKlaw       | 4           | 31        | ~13% |
| dubaicrab-web  | 0           | 2         | 0%   |

**영향도**: 높음  
**권장**: OpenKlaw에 단위 테스트 추가, Web에 E2E 테스트 도입

---

#### 5. 중복 코드 (DRY 위반)

**문제점**: 채팅 메시지 타입, 파일 파싱 로직 중복

```typescript
// dubaicrab-core
export interface ChatMessage {
  role: "user" | "assistant" | "system";
  content: string;
  // ...
}

// OpenKlaw (동일한 정의 반복)
export interface ChatMessage {
  role: "user" | "assistant" | "system";
  content: string;
  // ...
}
```

**권장**: 공유 패키지 추출 또는 모노레포 구조 개선

---

#### 6. 로깅 불일치

**문제점**: console.log/error 직접 사용, 구조화된 로깅 부재

```typescript
// 현재 (OpenKlaw)
console.log("[게이트웨이] 연결됨");
console.error("[Gateway] Parse error:", e);

// 권장: 구조화된 로거
import { logger } from "$lib/logger";
logger.info("gateway.connected", { url: this.config.url });
logger.error("gateway.parse_error", { error: e });
```

**영향도**: 낮음  
**위치**: 전 프로젝트

---

### 2.3 보안 검토 🔒

#### 양호한 부분

- `.env.example` 제공으로 민감 정보 보호
- `.secrets.baseline` 시크릿 스캔 설정
- SSRF 방어 구현 (`src/infra/net/ssrf.ts`)

#### 개선 필요

1. **입력 검증**: 파일 업로드 시 MIME 타입 검증 미흡
2. **토큰 관리**: WebSocket 인증 토큰 평문 전송
3. **의존성**: 일부 패키지 취약점 검토 필요

```typescript
// 권장: 파일 업로드 검증 강화
function validateFile(file: File): boolean {
  const MAX_SIZE = 50 * 1024 * 1024; // 50MB
  const ALLOWED_MIMES = ['application/pdf', 'application/x-hwp', ...];

  if (file.size > MAX_SIZE) return false;
  if (!ALLOWED_MIMES.includes(file.type)) return false;
  return true;
}
```

---

### 2.4 성능 분석 ⚡

#### 양호한 부분

- 스트리밍 응답 처리
- WebSocket 재연결 백오프 구현
- 세션 데이터 최대 100개 제한

#### 개선 필요

1. **메모리**: localStorage 100개 세션 제한이지만, 메시지 수 무제한
2. **번들 사이즈**: xlsx, jszip 등 대형 라이브러리 lazy loading 미적용
3. **Excel 파싱**: 대용량 파일 시 메모리 이슈 가능

```typescript
// 권장: 청크 기반 Excel 처리
async function* parseExcelChunks(file: File, chunkSize = 1000) {
  const workbook = XLSX.read(await file.arrayBuffer());
  for (const sheetName of workbook.SheetNames) {
    const sheet = workbook.Sheets[sheetName];
    const range = XLSX.utils.decode_range(sheet["!ref"] || "A1");
    for (let r = 0; r <= range.e.r; r += chunkSize) {
      yield extractRows(sheet, r, Math.min(r + chunkSize, range.e.r));
    }
  }
}
```

---

## 3. 아키텍처 평가

### 3.1 전체 구조 (점수: 8/10)

```
┌─────────────────────────────────────────────────────────────┐
│                    Dubai Crab 아키텍처                       │
├─────────────────────────────────────────────────────────────┤
│                                                              │
│  ┌──────────────┐    ┌──────────────┐    ┌──────────────┐  │
│  │ dubaicrab-web│    │  OpenKlaw    │    │dubaicrab-core│  │
│  │ (Next.js)    │    │ (Tauri+Svelte)│    │ (Node.js)   │  │
│  │              │    │              │    │              │  │
│  │ 랜딩 페이지   │    │ 데스크톱 앱   │    │ AI 게이트웨이 │  │
│  └──────────────┘    └───────┬──────┘    └───────┬──────┘  │
│                              │                    │         │
│                              │ WebSocket          │ API     │
│                              │                    │         │
│                              ▼                    ▼         │
│                       ┌──────────────────────────────┐      │
│                       │         Ollama               │      │
│                       │     (로컬 LLM 서버)          │      │
│                       └──────────────────────────────┘      │
│                                                              │
└─────────────────────────────────────────────────────────────┘
```

### 3.2 장점

- 명확한 역할 분리 (Web=마케팅, App=클라이언트, Core=백엔드)
- 로컬 우선 설계 (Ollama 기반)
- 플랫폼 독립적 (Tauri로 크로스 플랫폼)

### 3.3 개선점

- **공유 타입 부재**: 프로젝트 간 타입 정의 중복
- **모노레포 미활용**: 세 프로젝트가 별도 저장소로 분리됨
- **API 계약 미정의**: Gateway-Client 간 스키마 문서화 필요

---

## 4. SOLID 원칙 적용도

| 원칙                  | Core | OpenKlaw | Web | 비고                     |
| --------------------- | :--: | :------: | :-: | ------------------------ |
| Single Responsibility |  ✅  |    ⚠️    | ✅  | file-parser.ts 개선 필요 |
| Open/Closed           |  ✅  |    ✅    | ✅  | 플러그인 아키텍처 양호   |
| Liskov Substitution   |  ✅  |    ✅    | ✅  | 인터페이스 준수          |
| Interface Segregation |  ✅  |    ⚠️    | ✅  | 일부 과도한 인터페이스   |
| Dependency Inversion  |  ✅  |    ⚠️    | ✅  | 하드코딩된 의존성        |

---

## 5. 종합 점수

| 카테고리   |  Core   | OpenKlaw |   Web   |    전체    |
| ---------- | :-----: | :------: | :-----: | :--------: |
| 코드 품질  |  9/10   |   7/10   |  8/10   |  **8/10**  |
| 아키텍처   |  9/10   |   8/10   |  7/10   |  **8/10**  |
| 테스트     |  8/10   |   4/10   |  2/10   |  **5/10**  |
| 보안       |  8/10   |   6/10   |  7/10   |  **7/10**  |
| 성능       |  8/10   |   7/10   |  8/10   | **7.5/10** |
| 유지보수성 |  8/10   |   7/10   |  8/10   | **7.5/10** |
| **종합**   | **8.3** | **6.5**  | **6.7** | **7.2/10** |

---

## 6. 핵심 권장 사항

### 즉시 조치 (P0)

1. OpenKlaw 테스트 커버리지 확대
2. 에러 핸들링 표준화
3. 공유 타입 패키지 생성

### 단기 (P1, 1-2주)

4. 설정값 외부화 (환경변수, 설정 파일)
5. 구조화된 로깅 도입
6. 파일 업로드 보안 강화

### 중기 (P2, 1-2개월)

7. 모노레포 구조 통합 검토
8. API 스키마 문서화 (OpenAPI/TypeSpec)
9. 성능 모니터링 도입

---

_다음 문서: [REFACTORING_PLAN.md](./REFACTORING_PLAN.md)_
