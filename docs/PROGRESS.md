# Dubai Crab P0 개발 진행 현황

> 마지막 업데이트: 2026-02-08 14:30 KST

## 📊 전체 진행률: 35%

---

## P0-1: 원클릭 인스톨러 프레임워크

### 상태: 🔄 진행중

| 항목                    | 상태      | 비고                         |
| ----------------------- | --------- | ---------------------------- |
| Ollama 번들링 방안 조사 | 🔄 진행중 | Tauri sidecar 활용           |
| macOS 설치 스크립트     | ✅ 완료   | `scripts/install-ollama.sh`  |
| Windows 설치 스크립트   | ✅ 완료   | `scripts/install-ollama.ps1` |
| 의존성 자동 설치        | 🔄 진행중 | postinstall.js 개선 필요     |
| Tauri 빌드 통합         | 📋 예정   | -                            |

### 기술 결정

#### Ollama 번들링 방안

**Option 1: Tauri Sidecar (권장)**

- Ollama 바이너리를 sidecar로 포함
- 장점: 완전 오프라인 설치 가능
- 단점: 앱 크기 증가 (~100MB)

**Option 2: 설치 시 다운로드**

- 현재 구현: 첫 실행 시 Ollama 다운로드
- 장점: 앱 크기 최소화
- 단점: 인터넷 필요

**결정: Phase 1에서는 Option 2 유지, Phase 2에서 Option 1 구현**

---

## P0-2: Tauri UI 기본 완성

### 상태: 🔄 진행중 (70%)

| 컴포넌트                   | 상태      | 비고                   |
| -------------------------- | --------- | ---------------------- |
| Chat.svelte                | ✅ 완료   | 스트리밍, 드래그앤드롭 |
| OnboardingModal.svelte     | ✅ 완료   | 3단계 마법사           |
| SettingsModal.svelte       | ✅ 완료   | 모델, 테마, 단축키     |
| QuickActions.svelte        | ✅ 완료   | 빠른 작업 버튼         |
| ReportTemplateModal.svelte | ✅ 완료   | 5종 템플릿             |
| Sidebar.svelte             | ✅ 완료   | 네비게이션             |
| Header.svelte              | ✅ 완료   | 타이틀, 상태           |
| Gateway 연동               | 🔄 개선중 | OpenClaw Gateway 통합  |
| HWP 파싱 UI                | 🔄 개선중 | Python 연동 필요       |

### 빌드 상태

- ✅ `pnpm build` 성공
- ⚠️ a11y 경고 존재 (label 연결)
- 📋 Tauri 빌드 테스트 필요

---

## P0-3: HWP 파싱 개선

### 상태: 🔄 진행중 (50%)

| 기능             | 상태      | 비고                |
| ---------------- | --------- | ------------------- |
| 기본 텍스트 추출 | ✅ 완료   | hwpparser text      |
| 표 마크다운 변환 | ✅ 완료   | hwpparser rich-text |
| HWPX 지원        | ✅ 완료   | Open XML 형식       |
| 이미지 추출      | 📋 예정   | Phase 2             |
| Tauri 통합       | 🔄 진행중 | Python 서비스 연동  |

### HWP 파서 스킬 위치

- 스킬: `/Users/harifatherkr/.openclaw/workspace/skills/hwp-parser/`
- 프로젝트 내: `~/Documents/snovium/OpenKlaw/scripts/parse_hwp.py`

### 개선 필요 사항

1. Chat.svelte에서 Python 파서 호출 연동
2. 표 추출 결과 마크다운 렌더링
3. 대용량 파일 처리 최적화

---

## 🛠️ 기술 스택 확인

```
프로젝트: ~/Documents/snovium/OpenKlaw/
├── Frontend: SvelteKit 5 + Tailwind
├── Desktop: Tauri 2.0
├── LLM: Ollama (qwen2.5:3b-instruct)
├── HWP 파싱: pyhwp (Python)
└── 빌드: Vite + Rust
```

---

## 📋 다음 작업

### 즉시 (Today)

1. [ ] HWP 파싱 Python 서비스 연동 완성
2. [ ] Gateway 클라이언트 안정화
3. [ ] Tauri 빌드 테스트

### 이번 주

1. [ ] Ollama sidecar 프로토타입
2. [ ] a11y 경고 수정
3. [ ] E2E 테스트 작성

---

## 📝 변경 이력

| 날짜       | 변경 내용                    |
| ---------- | ---------------------------- |
| 2026-02-08 | 초기 문서 작성, P0 작업 분석 |
