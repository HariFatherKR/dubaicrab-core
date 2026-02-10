# Dubai Crab - Kakao Channel Plugin

카카오톡 스킬서버 웹훅을 통해 Dubai Crab AI 에이전트와 연결합니다.

## 🚀 빠른 시작

### 1. 카카오톡 채널 및 봇 생성

1. [카카오 비즈니스](https://business.kakao.com/)에서 채널 생성
2. [카카오 i 오픈빌더](https://i.kakao.com/)에서 봇 생성
3. 스킬 서버 웹훅 URL 설정

### 2. Dubai Crab 설정

`config.yaml`:

```yaml
channels:
  kakao:
    enabled: true
    webhookPath: /kakao/webhook
    botId: your-kakao-bot-id # 카카오 오픈빌더의 봇 ID
    dmPolicy: open # open | pairing | allowlist | disabled
    allowFrom:
      - "*" # 모든 사용자 허용
```

### 3. 웹훅 URL 설정

카카오 오픈빌더 스킬에서 웹훅 URL 설정:

```
https://your-domain.com/kakao/webhook
```

## ⚙️ 설정 옵션

| 옵션             | 타입    | 기본값           | 설명                           |
| ---------------- | ------- | ---------------- | ------------------------------ |
| `enabled`        | boolean | `true`           | 채널 활성화 여부               |
| `webhookPath`    | string  | `/kakao/webhook` | 웹훅 엔드포인트 경로           |
| `webhookUrl`     | string  | -                | 전체 웹훅 URL (경로 자동 추출) |
| `botId`          | string  | -                | 카카오 봇 ID (다중 봇 구분용)  |
| `dmPolicy`       | string  | `"pairing"`      | DM 정책                        |
| `allowFrom`      | array   | `[]`             | 허용된 사용자 ID 목록          |
| `responsePrefix` | string  | -                | 응답 접두사                    |

### DM 정책 (dmPolicy)

- `open`: 모든 사용자의 메시지 허용
- `pairing`: 페어링 요청 후 승인된 사용자만 허용
- `allowlist`: `allowFrom` 목록에 있는 사용자만 허용
- `disabled`: 모든 메시지 차단

## 📝 카카오 스킬서버 연동

### 요청 형식 (카카오 → Dubai Crab)

```json
{
  "bot": {
    "id": "bot-id",
    "name": "봇 이름"
  },
  "userRequest": {
    "utterance": "사용자 메시지",
    "user": {
      "id": "user-id",
      "properties": {
        "botUserKey": "unique-user-key"
      }
    },
    "callbackUrl": "https://callback-url-for-async"
  }
}
```

### 응답 형식 (Dubai Crab → 카카오)

```json
{
  "version": "2.0",
  "template": {
    "outputs": [
      {
        "simpleText": {
          "text": "AI 응답 메시지"
        }
      }
    ]
  }
}
```

### 비동기 응답 (5초 초과 시)

응답 시간이 5초를 초과하면 `callbackUrl`로 비동기 응답:

```json
// 즉시 응답
{
  "version": "2.0",
  "useCallback": true,
  "data": { "text": "처리중입니다..." },
  "template": { "outputs": [] }
}

// callbackUrl로 후속 응답 전송
```

## 🔧 다중 계정 설정

```yaml
channels:
  kakao:
    defaultAccount: main
    accounts:
      main:
        enabled: true
        webhookPath: /kakao/main
        botId: main-bot-id
        dmPolicy: open
      support:
        enabled: true
        webhookPath: /kakao/support
        botId: support-bot-id
        dmPolicy: allowlist
        allowFrom:
          - admin-user-id
```

## 🛡️ 보안

- 프로덕션에서는 `dmPolicy: allowlist` 사용 권장
- 카카오 서버 IP 화이트리스트 설정 권장
- HTTPS 필수

## 📚 참고 자료

- [카카오 i 오픈빌더 가이드](https://i.kakao.com/docs)
- [카카오톡 채널 관리자센터](https://center-pf.kakao.com/)
- [스킬서버 API 문서](https://i.kakao.com/docs/skill-build)
