# Dubai Crab - Sprint 3.2 RAG 기초

> **마지막 업데이트**: 2026-02-09
> **Sprint 기간**: 3주 (2026-02-10 ~ 2026-02-28)
> **목표**: RAG 파이프라인 MVP 구현 - 공무원 문서 벡터 검색

---

## 🎯 Quick Status

| 영역        | 진행률 | 상태       |
| ----------- | ------ | ---------- |
| 환경 설정   | 100%   | ✅ 완료    |
| 문서 처리   | 100%   | ✅ 완료    |
| 벡터 인덱싱 | 100%   | ✅ 완료    |
| 검색 API    | 0%     | ⏳ P1 대기 |
| 리랭킹      | 0%     | 🔮 P2 선택 |

---

## P0: 핵심 인프라 (Must Have)

### P0-1: 환경 설정 및 의존성 [2일] ✅

- [x] Python 의존성 추가 (pyproject.toml)
  - [x] `llama-index>=0.10.0`
  - [x] `chromadb>=0.4.0`
  - [x] `sentence-transformers>=2.2.0`
  - [x] ~~`FlagEmbedding>=1.2.0`~~ (transformers 호환 이슈로 제외)
- [x] Chroma 초기화 모듈
  - [x] `src/rag/vector_store.py` 생성
  - [x] 영구 저장 경로 설정 (`data/chroma/`)
  - [x] 컬렉션 생성 유틸리티
- [x] BGE-M3 임베딩 래퍼
  - [x] `src/rag/embeddings.py` 생성
  - [x] `get_embeddings()` 함수
  - [x] sentence-transformers 기반 구현
  - [x] 배치 처리 지원 (batch_size=32)
- [x] 환경 변수 설정
  - [x] `CHROMA_PERSIST_DIR`
  - [x] `EMBEDDING_MODEL` (기본값: BAAI/bge-m3)
  - [x] `EMBEDDING_DEVICE` (cuda/mps/cpu)

**완료 기준**: `python -c "from src.rag import vector_store, embeddings"` 성공 ✅

---

### P0-2: HWP 텍스트 추출 개선 [3일] ✅

- [x] LibreOffice 기반 변환 파이프라인
  - [x] `src/rag/parsers/hwp_parser.py` 생성
  - [x] `hwp_to_text(file_path) -> ParseResult` 구현
  - [x] LibreOffice headless 모드 호출
  - [x] 임시 파일 정리 로직 (tempfile.TemporaryDirectory)
- [x] hwpx (OOXML) 지원
  - [x] ZIP 압축 해제
  - [x] `Contents/section*.xml` 파싱
  - [x] 텍스트 노드 추출
- [x] 메타데이터 추출
  - [x] 파일명, 수정일, 파일 해시
  - [x] DocumentMetadata dataclass 구현
- [x] 표(Table) 처리
  - [x] 표 감지 로직 (탭/공백 패턴)
  - [x] 마크다운 테이블 변환
- [x] 에러 핸들링
  - [x] 암호화 파일 감지
  - [x] 타임아웃 (기본 60초)
  - [x] ParseResult로 에러 정보 반환

**완료 기준**: 테스트 HWP 10개 파일 100% 텍스트 추출 성공 ✅

---

### P0-3: 청킹 파이프라인 [2일] ✅

- [x] 청킹 모듈 구현
  - [x] `src/rag/chunker.py` 생성
  - [x] DocumentChunker 클래스 구현
  - [x] 기본 설정: chunk_size=512, overlap=50
- [x] 공문서 특화 청킹
  - [x] 조항별 분리 (제1조, 제2조...)
  - [x] 항목 리스트 패턴 인식
  - [x] 표는 별도 청크로 분리
- [x] 청크 메타데이터
  - [x] `source_file`: 원본 파일명
  - [x] `chunk_index`: 청크 순서
  - [x] `page_number`: 페이지 번호 (가능시)
  - [x] `section_title`: 섹션 제목
  - [x] `has_table`: 표 포함 여부
- [x] 청킹 품질 검증
  - [x] 빈 청크 필터링
  - [x] 최소 길이 체크 (50자)
  - [x] 최대 길이 체크 (2000자)

**완료 기준**: 문서 1개 → 청크 N개 + 메타데이터 JSON 출력 ✅

---

### P0-4: 벡터 인덱싱 [2일] ✅

- [x] 인덱싱 파이프라인
  - [x] `src/rag/indexer.py` 생성
  - [x] `index_document(file_path)` 함수
  - [x] `index_directory(dir_path)` 함수
- [x] Chroma 컬렉션 관리
  - [x] 컬렉션 생성/삭제 (vector_store.py)
  - [x] 문서 추가/업데이트
  - [x] 중복 체크 (file_hash 기반)
- [x] 배치 인덱싱
  - [x] 진행률 콜백 지원
  - [x] 실패 문서 로깅
  - [x] 재시도 로직 (3회)
- [x] CLI 도구
  - [x] `python -m src.rag.cli index <path>`
  - [x] `--collection` 옵션
  - [x] `--recursive` 옵션
  - [x] `python -m src.rag.cli status`

**완료 기준**: 100개 문서 인덱싱 < 5분 (M1 Mac 기준) ✅

---

## P1: 검색 API (Should Have)

### P1-1: 검색 엔진 구현 [2일]

- [ ] 검색 모듈
  - [ ] `src/rag/retriever.py` 생성
  - [ ] `search(query, top_k=5) -> List[SearchResult]`
  - [ ] 메타데이터 필터링 지원
- [ ] LlamaIndex 통합
  - [ ] `VectorStoreIndex` 래퍼
  - [ ] `QueryEngine` 설정
  - [ ] 하이브리드 검색 모드 (dense + sparse)
- [ ] 검색 결과 포맷
  ```python
  @dataclass
  class SearchResult:
      content: str          # 청크 텍스트
      score: float          # 유사도 점수
      source: str           # 원본 파일명
      metadata: dict        # 추가 메타데이터
  ```

**완료 기준**: 검색 쿼리 → 관련 문서 Top 5 반환

---

### P1-2: FastAPI 검색 엔드포인트 [2일]

- [ ] API 라우터 추가
  - [ ] `POST /api/rag/search`
  - [ ] `POST /api/rag/index`
  - [ ] `GET /api/rag/status`
  - [ ] `DELETE /api/rag/collection/{name}`
- [ ] 요청/응답 스키마

  ```python
  class SearchRequest(BaseModel):
      query: str
      top_k: int = 5
      filters: Optional[dict] = None

  class SearchResponse(BaseModel):
      results: List[SearchResult]
      query_time_ms: float
  ```

- [ ] 인덱싱 API
  - [ ] 파일 업로드 → 인덱싱
  - [ ] 진행률 SSE 스트림
  - [ ] 백그라운드 작업 지원
- [ ] 에러 핸들링
  - [ ] 컬렉션 없음 404
  - [ ] 쿼리 길이 제한
  - [ ] Rate limiting (선택)

**완료 기준**: Swagger UI에서 검색 API 테스트 성공

---

### P1-3: 채팅 통합 [1일]

- [ ] RAG 컨텍스트 주입
  - [ ] 채팅 쿼리 → RAG 검색
  - [ ] 검색 결과 → LLM 프롬프트
  - [ ] 출처 표시 ("참고: xxx.hwp")
- [ ] 프롬프트 템플릿

  ```python
  RAG_PROMPT = """
  다음 문서를 참고하여 질문에 답변하세요:

  {context}

  질문: {question}

  답변:
  """
  ```

- [ ] 설정 옵션
  - [ ] RAG 활성화/비활성화
  - [ ] 검색 결과 수 조절
  - [ ] 최소 유사도 임계값

**완료 기준**: 채팅 → RAG 검색 → 컨텍스트 기반 답변 생성

---

## P2: 고급 기능 (Nice to Have)

### P2-1: 리랭킹 [2일]

- [ ] BGE Reranker 통합
  - [ ] `src/rag/reranker.py` 생성
  - [ ] `BAAI/bge-reranker-v2-m3` 로드
  - [ ] FP16 모드 지원
- [ ] 리랭킹 파이프라인
  - [ ] 1차 검색: Top 20 후보
  - [ ] 2차 리랭킹: Top 5 선별
- [ ] 성능 비교 테스트
  - [ ] 리랭킹 전/후 정확도 비교
  - [ ] 응답 시간 측정

---

### P2-2: 다중 파일 형식 [2일]

- [ ] PDF 파서 개선
  - [ ] PyMuPDF 기반
  - [ ] 표 추출 지원
- [ ] DOCX 파서
  - [ ] python-docx 기반
  - [ ] 스타일 메타데이터
- [ ] 통합 파서 인터페이스
  - [ ] `BaseParser` 추상 클래스
  - [ ] 파일 확장자 → 파서 매핑

---

### P2-3: 인덱스 관리 UI [3일]

- [ ] 컬렉션 목록 조회
- [ ] 문서 추가/삭제
- [ ] 인덱싱 상태 모니터링
- [ ] 검색 테스트 UI

---

## 🔧 진행 중 작업

```
[2026-02-09]
- ⏳ Sprint 3.2 계획 수립 완료
- 다음: P0-1 환경 설정 시작
```

---

## 📅 Sprint 타임라인

```
Week 1 (2/10 ~ 2/14): 기반 구축
├── Day 1-2: P0-1 환경 설정
├── Day 3-5: P0-2 HWP 텍스트 추출

Week 2 (2/17 ~ 2/21): 파이프라인 완성
├── Day 1-2: P0-3 청킹 파이프라인
├── Day 3-4: P0-4 벡터 인덱싱
├── Day 5: 통합 테스트

Week 3 (2/24 ~ 2/28): API & 통합
├── Day 1-2: P1-1 검색 엔진
├── Day 3-4: P1-2 FastAPI 엔드포인트
├── Day 5: P1-3 채팅 통합
```

---

## 📝 기술 선택 요약

| 항목       | 선택               | 이유                          |
| ---------- | ------------------ | ----------------------------- |
| 벡터 DB    | Chroma             | pip 설치, LlamaIndex 네이티브 |
| 임베딩     | BGE-M3             | 한국어 우수, 8192 토큰        |
| 프레임워크 | LlamaIndex         | RAG 특화, 간단한 API          |
| HWP 파서   | LibreOffice        | 가장 안정적                   |
| 리랭킹     | bge-reranker-v2-m3 | 다국어, 고성능                |

---

_이 문서는 작업 진행에 따라 체크박스를 업데이트합니다._
