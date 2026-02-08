# Dubai Crab P3 - 태스크 리스트

> 자동 업데이트됨. 각 에이전트가 완료 시 체크.

---

## 🔄 현재 Phase: Sprint 3.1 - 한글 OCR

---

## Sprint 3.1: 한글 OCR (RICE 110)

### 목표

PaddleOCR 통합으로 스캔 문서/이미지에서 한글 텍스트 추출

### 🔴 P0 - 필수 작업

- [x] **3.1.1 PaddleOCR 환경 설정**
  - [x] Python venv 확인/생성 (.venv-ocr with Python 3.11)
  - [x] PaddleOCR 및 의존성 설치
  - [x] 한글 모델 다운로드 (korean_PP-OCRv3)

- [x] **3.1.2 OCR 서버 스크립트**
  - [x] scripts/ocr_server.py 작성
  - [x] stdin/stdout JSON 통신
  - [x] 에러 핸들링 (Base64 및 파일 경로 지원)

- [x] **3.1.3 이미지 입력 UI**
  - [x] 이미지 드래그앤드롭 지원
  - [x] 파일 다이얼로그 (Tauri)
  - [x] 지원 포맷: PNG, JPG, GIF, WebP, BMP

- [x] **3.1.4 OCR 호출 로직**
  - [x] Tauri Command 작성 (ocr_from_file, ocr_from_base64)
  - [x] Python 프로세스 호출
  - [x] 결과 파싱 및 반환

- [x] **3.1.5 결과 표시 UI**
  - [x] OCR 결과 채팅에 표시
  - [x] 로딩 상태 표시 (OCR 프로그레스 오버레이)
  - [x] 에러 메시지 표시

### 🟡 P1 - 중요 작업

- [x] **3.1.6 클립보드 이미지**
  - [x] Ctrl+V 붙여넣기 지원
  - [x] 이미지 데이터 처리 (Base64 변환)

- [ ] **3.1.7 이미지 프리뷰**
  - [ ] 업로드 전 미리보기
  - [ ] 이미지 정보 표시 (크기, 포맷)

- [x] **3.1.8 AI 분석 연동**
  - [x] OCR 결과 → AI 요약 (analyzeOcrResult)
  - [x] 자동 분석 파이프라인

### 🟢 P2 - 개선 작업

- [ ] **3.1.9 배치 OCR**
  - [ ] 여러 이미지 동시 처리
  - [ ] 진행률 표시

- [ ] **3.1.10 OCR 영역 선택**
  - [ ] 이미지 내 영역 지정
  - [ ] 부분 OCR

- [ ] **3.1.11 결과 내보내기**
  - [ ] TXT 저장
  - [ ] HWP 변환 (옵션)

### 🧪 테스트

- [ ] OCR 정확도 테스트 (한글 문서)
- [ ] 다양한 이미지 포맷 테스트
- [ ] 저품질 이미지 테스트
- [ ] pnpm run check/build 통과
- [ ] git commit

---

## ✅ 완료 항목

(완료된 태스크는 여기로 이동)

---

## 🐛 버그/이슈

(발견된 버그 기록)

---

## 📝 메모

- PaddleOCR 한글 모델: korean_PP-OCRv3
- 권장 Python 버전: 3.9+
- M1/M2 Mac: conda 환경 권장
