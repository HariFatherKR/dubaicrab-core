# @dubaicrab/shared-types

Dubai Crab 프로젝트 간 공유 타입 정의 패키지

## 버전 동기화 전략

### 현재 버전

```
0.1.0
```

### 사용법

#### dubaicrab-core (Core)

```bash
# 이미 monorepo 내 패키지이므로 workspace 참조
npm install @dubaicrab/shared-types@workspace:*
```

#### OpenKlaw (UI)

```bash
# npm link 또는 file 참조
npm install ../dubaicrab-core/packages/shared-types
# 또는
npm link @dubaicrab/shared-types
```

### 버전 업데이트 절차

1. **shared-types 버전 업데이트**

   ```bash
   cd packages/shared-types
   npm version patch  # 0.1.0 → 0.1.1
   npm run build
   ```

2. **의존 프로젝트 업데이트**
   - dubaicrab-core: 자동 (workspace)
   - OpenKlaw: `npm update @dubaicrab/shared-types`

3. **커밋 메시지 규칙**
   ```
   chore(shared-types): bump version to 0.1.1
   ```

### 타입 구조

```
src/
├── index.ts      # 메인 export
├── chat.ts       # 채팅 관련 타입
├── gateway.ts    # Gateway 통신 타입
└── file.ts       # 파일 처리 타입
```

### Import 예시

```typescript
// 전체 import
import { ChatMessage, GatewayResponse } from "@dubaicrab/shared-types";

// 서브패스 import
import type { ChatMessage } from "@dubaicrab/shared-types/chat";
import type { GatewayConfig } from "@dubaicrab/shared-types/gateway";
```

## 빌드

```bash
npm run build     # ESM + CJS 빌드
npm run clean     # dist 정리
```

## 주의사항

- 타입 변경 시 breaking change 여부 확인
- Major 변경은 양쪽 프로젝트 동시 업데이트 필요
- PR에 `shared-types` 라벨 추가 권장
