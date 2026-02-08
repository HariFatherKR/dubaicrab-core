# 🦀 Dubai Crab Core

**한국 사무직을 위한 로컬 AI 게이트웨이** - OpenClaw 경량 포크

> ChatGPT 차단된 회사를 위한 프라이빗 AI 어시스턴트

## 특징

- 🔒 **완전 로컬** - 데이터 외부 전송 없음
- 📝 **한글 문서 지원** - HWP/HWPX 파싱
- 💬 **멀티 채널** - Telegram, Discord, Slack
- 🖥️ **데스크톱 UI** - Tauri 앱 연동

## 지원 채널

| 채널 | 상태 |
|------|------|
| Telegram | ✅ 지원 |
| Discord | ✅ 지원 |
| Slack | ✅ 지원 |
| KakaoTalk | 🔜 개발 예정 |

## 설치

```bash
# npm
npm install -g dubaicrab-core

# 또는 소스에서
git clone https://github.com/HariFatherKR/dubaicrab-core
cd dubaicrab-core
pnpm install
pnpm build
```

## 사용법

```bash
# 게이트웨이 시작
dubaicrab gateway start

# 설정
dubaicrab config

# 상태 확인
dubaicrab status
```

## 설정

```yaml
# config.yaml
channels:
  telegram:
    enabled: true
    token: "YOUR_BOT_TOKEN"
  discord:
    enabled: true
    token: "YOUR_BOT_TOKEN"
  slack:
    enabled: true
    token: "YOUR_BOT_TOKEN"

model:
  provider: ollama  # 로컬 LLM
  model: llama3.2

skills:
  - hwp-parsing
  - document-drafting
  - email-writing
```

## 한국 오피스 스킬

| 스킬 | 설명 |
|------|------|
| hwp-parsing | HWP/HWPX 문서 파싱 |
| document-drafting | 공문/보고서/기안서 작성 |
| email-writing | 비즈니스 이메일 |
| meeting-notes | 회의록 작성 |
| excel-analysis | 엑셀 데이터 분석 |

## 아키텍처

```
┌─────────────────────────────────────────┐
│           Dubai Crab Core               │
├─────────────────────────────────────────┤
│  Gateway (Node.js)                      │
│  ├── Telegram Channel                   │
│  ├── Discord Channel                    │
│  ├── Slack Channel                      │
│  └── Local UI Channel (WebSocket)       │
├─────────────────────────────────────────┤
│  Skills Engine                          │
│  ├── hwp-parsing                        │
│  ├── document-drafting                  │
│  └── ...                                │
├─────────────────────────────────────────┤
│  LLM Provider                           │
│  ├── Ollama (로컬)                       │
│  ├── OpenAI                             │
│  └── Anthropic                          │
└─────────────────────────────────────────┘
```

## 크레딧

- 기반: [OpenClaw](https://github.com/openclaw/openclaw) (MIT License)
- HWP 파싱: [pyhwp](https://github.com/mete0r/pyhwp) (AGPL v3)

## 라이선스

MIT License

---

**Dubai Crab** 🦀 - 직장에서도 AI를 자유롭게
