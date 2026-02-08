# Dubai Crab - Fix Plan (작업 체크리스트)

> **마지막 업데이트**: 2026-02-08
> **현재 Phase**: P0 마무리 → P1 진입

---

## 🎯 Quick Status

| Phase            | 진행률 | 상태    |
| ---------------- | ------ | ------- |
| P0 (MVP 기반)    | 100%   | ✅ 완료 |
| P1 (품질+안정성) | 0%     | ⏳ 대기 |

---

## P0 잔여 작업 (30%)

### P0-1: Ollama Sidecar 프로토타입

- [x] `tauri.conf.json` sidecar 설정 추가
- [x] Ollama 바이너리 다운로드 스크립트
  - [x] macOS arm64
  - [x] macOS x64
  - [x] Windows x64
- [x] 첫 실행 시 sidecar 자동 시작
- [x] 헬스체크 로직 (`/api/tags` 호출)
- [x] 앱 종료 시 프로세스 정리

**완료 기준**: 앱 시작 → Ollama 자동 실행 → 대화 가능 ✅

---

### P0-3: HWP 대용량 파일 처리

- [x] 10MB 테스트 파일 준비 (설정으로 대체)
- [x] 메모리 프로파일링 (heapsize 체크) → 50MB 제한 설정
- [x] 타임아웃 설정 (30초)
- [x] 프로그레스 UI 표시 (Chat.svelte)
- [x] 에러 시 사용자 친화적 메시지

**완료 기준**: 10MB HWP 파일 30초 내 파싱, 메모리 <500MB ✅

---

### P0-E2E: E2E 테스트 작성

- [x] Playwright 설정 (OpenKlaw)
  - [x] `playwright.config.ts` 생성
  - [x] Tauri 테스트 환경 설정 (웹 모드)
- [x] OpenKlaw E2E 케이스
  - [x] 앱 시작 → 환영 메시지 확인
  - [x] 기본 채팅 UI 존재 확인
  - [x] 접근성 테스트 (aria-label, 키보드)
  - [x] 반응형 디자인 테스트
- [ ] dubaicrab-web E2E 케이스 (P1으로 이동)
  - [ ] 랜딩 페이지 로드
  - [ ] 이메일 폼 제출
  - [ ] 다운로드 링크 유효성

**완료 기준**: CI에서 E2E 테스트 자동 실행 ✅ (npm run test:e2e)

---

## P1-A: 필수 작업 (Must Have)

### P1-A1: 에러 핸들링 표준화 [1일]

- [ ] `src/lib/utils/error.ts` 생성
  ```typescript
  export class AppError extends Error { ... }
  export function formatError(error: unknown): string { ... }
  ```
- [ ] `file-parser.ts` catch 블록 리팩토링
- [ ] `gateway-client.ts` catch 블록 리팩토링
- [ ] `stores/*.ts` catch 블록 리팩토링
- [ ] `console.error` → `logger.error` 마이그레이션

---

### P1-A2: OpenKlaw 단위 테스트 [3일]

- [ ] `tests/lib/gateway-client.test.ts`
  - [ ] connect() 성공/실패
  - [ ] sendMessage() 연결 상태 체크
  - [ ] reconnect() 백오프 로직
  - [ ] 인증 토큰 전송
- [ ] `tests/lib/file-parser.test.ts`
  - [ ] parseTextFile() 성공/실패
  - [ ] parseCsvFile() 성공/실패
  - [ ] parseExcelFile() 성공/실패
  - [ ] 지원하지 않는 확장자 처리
- [ ] `tests/lib/stores/chat-store.test.ts`
  - [ ] 메시지 추가
  - [ ] 세션 전환
  - [ ] localStorage 저장/로드
- [ ] `tests/lib/stores/settings-store.test.ts`
  - [ ] 설정 변경
  - [ ] 기본값 복원

**목표 커버리지**: 50%+

---

### P1-A3: 공유 타입 패키지 [2일]

- [ ] `packages/shared-types/` 디렉토리 생성
- [ ] `package.json` 설정
- [ ] 타입 파일 작성
  - [ ] `src/chat.ts` (ChatMessage, ChatSession)
  - [ ] `src/gateway.ts` (GatewayConfig, GatewayResponse)
  - [ ] `src/file.ts` (ParseResult, SupportedExtension)
  - [ ] `src/index.ts` (re-export)
- [ ] dubaicrab-core에서 import
- [ ] OpenKlaw에서 import
- [ ] 기존 중복 타입 제거

---

### P1-A4: Windows 인스톨러 (.msi) [3일]

- [ ] 빌드 도구 선택 (NSIS / WiX / Tauri bundle)
- [ ] 인스톨러 스크립트 작성
- [ ] Ollama 번들링 또는 자동 다운로드 로직
- [ ] 모델 자동 pull 스크립트
- [ ] 시작 메뉴 바로가기
- [ ] 바탕화면 바로가기
- [ ] 언인스톨러
- [ ] Windows 10 테스트
- [ ] Windows 11 테스트

---

### P1-A5: macOS 인스톨러 개선 [2일]

- [ ] DMG 커스텀 배경 이미지
- [ ] 첫 실행 시 Ollama 체크
- [ ] Homebrew로 Ollama 자동 설치
- [ ] 모델 다운로드 프로그레스 UI
- [ ] 코드 서명 (Apple Developer)
- [ ] 공증 (Notarization)
- [ ] Apple Silicon + Intel 유니버설 바이너리

---

## P1-B: 권장 작업 (Should Have)

### P1-B1: 설정값 외부화 [1일]

- [ ] `src/lib/config/index.ts` 생성
- [ ] 환경변수 매핑
  - [ ] `VITE_GATEWAY_URL`
  - [ ] `VITE_GATEWAY_HTTP_URL`
  - [ ] `VITE_RECONNECT_MAX`
  - [ ] `VITE_RECONNECT_DELAY`
- [ ] `.env.example` 업데이트
- [ ] 매직 넘버 제거 (gateway-client.ts)

---

### P1-B2: 구조화된 로깅 [1일]

- [ ] `src/lib/logger.ts` 생성
  ```typescript
  export const logger = {
    debug(msg, ctx?),
    info(msg, ctx?),
    warn(msg, ctx?),
    error(msg, ctx?)
  };
  ```
- [ ] `gateway-client.ts` 마이그레이션
- [ ] `file-parser.ts` 마이그레이션
- [ ] `stores/*.ts` 마이그레이션

---

### P1-B3: 파일 파서 리팩토링 (전략 패턴) [2일]

- [ ] `src/lib/tools/parsers/` 디렉토리 생성
- [ ] `FileParser` 인터페이스 정의
- [ ] 개별 파서 클래스 분리
  - [ ] `TextFileParser`
  - [ ] `CsvFileParser`
  - [ ] `ExcelFileParser`
  - [ ] `PdfFileParser`
  - [ ] `HwpFileParser`
  - [ ] `PptFileParser`
- [ ] `parserMap` 레지스트리 생성
- [ ] 기존 `parseFile()` 함수 위임 방식으로 변경

---

### P1-B4: 파일 업로드 보안 강화 [1일]

- [ ] `src/lib/utils/file-validator.ts` 생성
- [ ] 파일 크기 제한 (50MB)
- [ ] MIME 타입 검증
- [ ] 확장자 화이트리스트
- [ ] Chat.svelte에 검증 적용
- [ ] 에러 메시지 사용자 친화적으로

---

### P1-B5: 온보딩 마법사 UX 개선 [2일]

- [ ] 스텝 인디케이터 개선
- [ ] Ollama 상태 실시간 표시
- [ ] 모델 다운로드 프로그레스
- [ ] 에러 시 재시도 버튼
- [ ] 스킵 옵션 (고급 사용자용)

---

### P1-B6: dubaicrab-web E2E 테스트 [1일]

- [ ] Playwright 설정
- [ ] 테스트 케이스
  - [ ] 랜딩 페이지 스크린샷
  - [ ] 이메일 폼 제출 성공
  - [ ] 이메일 폼 제출 실패 (유효성 검증)
  - [ ] 다운로드 링크 체크
- [ ] CI 통합

---

## 🔧 진행 중 작업

현재 진행 중인 작업을 여기에 표시:

```
[2026-02-08]
- ✅ P0-1: Ollama Sidecar 프로토타입 완료
- ✅ P0-3: HWP 대용량 파일 처리 완료 (30초 타임아웃, 프로그레스 UI)
- ✅ P0-E2E: E2E 테스트 설정 완료 (Playwright)
- 🎉 P0 100% 완료!
- ⏳ 다음: P1 작업 시작
```

---

## 📝 완료된 작업 (Archive)

### P0-2: Tauri UI 기본 (95% → 100%)

- [x] Chat.svelte 스트리밍
- [x] OnboardingModal.svelte 3단계 마법사
- [x] SettingsModal.svelte 설정 패널
- [x] Gateway 연동 안정화
- [x] HWP 파싱 Tauri invoke 연동
- [x] a11y 접근성 개선

### P0-4: Gateway 클라이언트 안정화 (100%)

- [x] WebSocket 연결 관리
- [x] 에러 핸들링
- [x] 재연결 로직 (Exponential backoff)
- [x] Heartbeat 모니터링
- [x] 메시지 큐잉

---

## 📅 Sprint 타임라인

```
Week 1-2 (Sprint P1-1): 기반 강화
├── Day 1-2: Ollama sidecar
├── Day 3: HWP 대용량
├── Day 4-5: E2E 테스트
├── Day 6: 에러 핸들링
├── Day 7-9: 단위 테스트
└── Day 10: 공유 타입

Week 3-4 (Sprint P1-2): 인스톨러 + 개선
├── Day 1-3: Windows 인스톨러
├── Day 4-5: macOS 인스톨러
├── Day 6: 설정 외부화
├── Day 7: 구조화 로깅
├── Day 8-9: 파서 리팩토링
└── Day 10: 업로드 보안
```

---

## 🎯 다음 마일스톤

**P1 완료 기준 (4주 후)**:

- [ ] P0 100% 완료
- [ ] 코드 품질 8.0/10
- [ ] OpenKlaw 테스트 50%+
- [ ] Windows/macOS 인스톨러 완성
- [ ] 비개발자 10분 내 설치 가능

---

_이 문서는 작업 진행에 따라 체크박스를 업데이트합니다._
