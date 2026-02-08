# Sprint 3.2 RAG 파이프라인 리서치

**작성일**: 2026-02-09  
**프로젝트**: Dubai Crab - 공무원 AI 문서 도우미  
**목적**: RAG(Retrieval Augmented Generation) 기초 구현을 위한 기술 스택 선정

---

## 1. 벡터 데이터베이스 비교

### 1.1 비교 대상

| 항목             | Chroma     | Qdrant     | Milvus     | Weaviate |
| ---------------- | ---------- | ---------- | ---------- | -------- |
| **언어**         | Python     | Rust       | Go/C++     | Go       |
| **라이선스**     | Apache 2.0 | Apache 2.0 | Apache 2.0 | BSD-3    |
| **GitHub Stars** | 16k+       | 21k+       | 32k+       | 13k+     |

### 1.2 로컬 설치 용이성

#### Chroma ⭐⭐⭐⭐⭐ (추천)

```bash
pip install chromadb
```

- **설치 난이도**: 최하 (pip 한 줄)
- **인메모리/영구 저장 모두 지원**
- Docker 불필요, 바로 사용 가능
- 프로토타이핑에 최적

#### Qdrant ⭐⭐⭐⭐

```bash
pip install qdrant-client
# 또는 Docker
docker run -p 6333:6333 qdrant/qdrant
```

- **설치 난이도**: 낮음
- Python 클라이언트로 인메모리/로컬 파일 저장 가능
- 프로덕션 시 Docker 권장

#### Milvus ⭐⭐⭐

```bash
pip install pymilvus
# Milvus Lite (경량 버전)
pip install pymilvus[milvus-lite]
```

- **설치 난이도**: 중간
- Milvus Lite로 로컬 개발 가능
- 풀 버전은 K8s/Docker 환경 필요

#### Weaviate ⭐⭐⭐

```bash
pip install weaviate-client
docker compose up -d
```

- **설치 난이도**: 중간
- 로컬 실행 시 Docker 필수
- 모듈 기반 아키텍처

### 1.3 Python/Node.js 호환성

| DB       | Python SDK | Node.js SDK | TypeScript 지원 |
| -------- | ---------- | ----------- | --------------- |
| Chroma   | ✅ 공식    | ✅ 공식     | ✅              |
| Qdrant   | ✅ 공식    | ✅ 공식     | ✅              |
| Milvus   | ✅ 공식    | ✅ 공식     | ✅              |
| Weaviate | ✅ 공식    | ✅ 공식     | ✅              |

### 1.4 성능 벤치마크 (일반적 순위)

1. **Qdrant** - Rust 기반, 가장 빠른 검색 속도
2. **Milvus** - 대규모 데이터에 최적화 (10억+ 벡터)
3. **Chroma** - 소규모~중규모에서 충분히 빠름
4. **Weaviate** - 모듈화로 유연하지만 약간 느림

### 1.5 🏆 Dubai Crab 권장

**1순위: Chroma**

- 이유:
  - 가장 간단한 설치 및 설정
  - LangChain/LlamaIndex 네이티브 지원
  - 공무원 문서 규모(수천~수만 건)에 충분
  - 개발 속도 최우선일 때 적합

**2순위: Qdrant**

- 이유:
  - 성능이 중요해질 때 전환 고려
  - 필터링/페이로드 기능 우수
  - 인메모리 모드로 쉽게 시작 가능

---

## 2. 임베딩 모델 비교

### 2.1 한글 최적화 모델

#### (1) BGE-M3 (BAAI) ⭐⭐⭐⭐⭐ (최강 추천)

```python
pip install FlagEmbedding
```

- **다국어**: 100+ 언어 지원 (한국어 포함)
- **기능**: Dense + Sparse + ColBERT 동시 지원
- **시퀀스 길이**: 8192 토큰 (긴 문서에 유리)
- **차원**: 1024
- **특징**: 하이브리드 검색 가능 (dense + BM25 스타일)

#### (2) Multilingual-E5-Large (intfloat) ⭐⭐⭐⭐⭐

```python
from sentence_transformers import SentenceTransformer
model = SentenceTransformer('intfloat/multilingual-e5-large')
```

- **다국어**: 100개 언어 지원
- **차원**: 1024
- **시퀀스 길이**: 512 토큰
- **특징**: query/passage 프리픽스 필요
- **벤치마크**: Mr. TyDi에서 우수한 성능

#### (3) KoSimCSE (한국어 특화)

```python
from sentence_transformers import SentenceTransformer
model = SentenceTransformer('BM-K/KoSimCSE-roberta-multitask')
```

- **한국어 전용**: 한국어에만 최적화
- **차원**: 768
- **특징**: 한국어 의미 유사도 SOTA

### 2.2 Ollama 로컬 임베딩 vs OpenAI API

| 항목           | Ollama 로컬                         | OpenAI API                   |
| -------------- | ----------------------------------- | ---------------------------- |
| **비용**       | 무료                                | $0.00002/1K 토큰             |
| **속도**       | GPU 의존                            | 매우 빠름                    |
| **프라이버시** | 완전 로컬                           | 클라우드 전송                |
| **모델**       | nomic-embed-text, mxbai-embed-large | text-embedding-3-small/large |
| **한국어**     | mxbai: 양호                         | 우수                         |

#### Ollama 로컬 임베딩 모델

```bash
ollama pull nomic-embed-text  # 274M, 768차원
ollama pull mxbai-embed-large # 335M, 1024차원
```

### 2.3 🏆 Dubai Crab 권장

**개발/프로토타입 단계:**

```python
# 1순위: BGE-M3 (가장 강력)
from FlagEmbedding import BGEM3FlagModel
model = BGEM3FlagModel('BAAI/bge-m3', use_fp16=True)

# 2순위: Multilingual-E5 (간편)
from sentence_transformers import SentenceTransformer
model = SentenceTransformer('intfloat/multilingual-e5-large')
```

**프로덕션 (비용 고려):**

- 문서 수 적음 → OpenAI text-embedding-3-small (품질/속도 균형)
- 프라이버시 중요 → Ollama mxbai-embed-large

---

## 3. RAG 파이프라인 아키텍처

### 3.1 LangChain vs LlamaIndex 비교

| 항목          | LangChain                        | LlamaIndex                    |
| ------------- | -------------------------------- | ----------------------------- |
| **철학**      | 범용 LLM 애플리케이션 프레임워크 | 데이터 인덱싱/검색 특화       |
| **강점**      | 에이전트, 체인, 도구 연동        | 다양한 인덱스 유형, 고급 검색 |
| **RAG**       | 지원 (기본)                      | 지원 (최적화)                 |
| **학습 곡선** | 중간                             | 낮음                          |
| **문서화**    | 우수                             | 우수                          |
| **커뮤니티**  | 매우 활발                        | 활발                          |
| **통합**      | 300+ 통합                        | LangChain과 통합 가능         |

#### LangChain 장점

- 에이전트 기능 강력 (도구 호출, 의사결정)
- 범용적 (RAG 외 다양한 워크플로우)
- LangGraph로 복잡한 워크플로우 구성

#### LlamaIndex 장점

- RAG에 더 최적화
- 다양한 인덱스 유형 (트리, 그래프, 키워드 등)
- 문서 파싱 파이프라인 우수
- 더 간단한 API

### 3.2 🏆 권장: LlamaIndex

**이유:**

1. Dubai Crab은 문서 검색/질의응답이 핵심 → LlamaIndex가 더 적합
2. 더 간단한 API로 빠른 개발
3. HWP 등 다양한 문서 로더 통합 용이
4. 필요시 LangChain과 함께 사용 가능

```python
from llama_index.core import VectorStoreIndex, SimpleDirectoryReader

# 기본 RAG 파이프라인
documents = SimpleDirectoryReader("./documents").load_data()
index = VectorStoreIndex.from_documents(documents)
query_engine = index.as_query_engine()
response = query_engine.query("문서 관련 질문")
```

### 3.3 청크 사이즈/오버랩 Best Practice

#### 권장 설정

```python
from llama_index.core.node_parser import SentenceSplitter

# 일반적인 권장값
parser = SentenceSplitter(
    chunk_size=512,      # 토큰 수
    chunk_overlap=50,    # 10% 정도 오버랩
)

# 긴 공문서용 (BGE-M3 사용 시)
parser = SentenceSplitter(
    chunk_size=1024,
    chunk_overlap=100,
)
```

#### 가이드라인

| 문서 유형    | 청크 사이즈 | 오버랩 | 이유         |
| ------------ | ----------- | ------ | ------------ |
| 짧은 공문서  | 256-512     | 25-50  | 정확한 매칭  |
| 긴 보고서    | 512-1024    | 50-100 | 문맥 유지    |
| 법률/규정    | 256-512     | 50-75  | 조항별 구분  |
| 표 포함 문서 | 512-768     | 0-25   | 표 구조 유지 |

### 3.4 리랭킹 전략

#### (1) Cross-Encoder 리랭커 (권장)

```python
from FlagEmbedding import FlagReranker
reranker = FlagReranker('BAAI/bge-reranker-v2-m3', use_fp16=True)

# 리랭킹
scores = reranker.compute_score([
    ['질문', '문서1'],
    ['질문', '문서2'],
])
```

#### (2) 리랭킹 파이프라인 예시

```
사용자 질문
    ↓
1차 검색 (벡터 유사도) → Top 20개 후보
    ↓
2차 리랭킹 (Cross-Encoder) → Top 5개 선별
    ↓
LLM 컨텍스트로 전달
```

#### 권장 리랭커 모델

- **BAAI/bge-reranker-v2-m3**: 다국어 지원, 한국어 우수
- **Cohere Rerank**: API 기반, 간편

---

## 4. HWP 문서 특화 전략

### 4.1 HWP 텍스트 추출

#### (1) pyhwp (Python) - AGPL 라이선스 주의

```python
pip install pyhwp

from hwp5.hwp5txt import Hwp5Txt
from hwp5.hwp5odt import Hwp5ODT

# 텍스트 추출
hwp = Hwp5Txt()
text = hwp.to_txt('document.hwp')

# ODT 변환 후 처리
hwp = Hwp5ODT()
hwp.convert('document.hwp', 'document.odt')
```

**주의**: AGPL 라이선스 → 상업적 사용 시 코드 공개 의무

#### (2) hwplib (Java) + Python 래퍼

```bash
# Java 라이브러리 사용
pip install jpype1
```

- 한글과컴퓨터 공식 스펙 기반
- 더 안정적인 추출

#### (3) hwpx (OOXML 기반 신규 포맷)

```python
# hwpx는 ZIP + XML 구조
import zipfile
import xml.etree.ElementTree as ET

with zipfile.ZipFile('document.hwpx', 'r') as z:
    with z.open('Contents/section0.xml') as f:
        tree = ET.parse(f)
        # XML 파싱하여 텍스트 추출
```

#### (4) LibreOffice 변환 (안정적)

```bash
libreoffice --headless --convert-to txt document.hwp
```

- 가장 안정적인 방법
- 테이블 구조 일부 보존
- 서버에 LibreOffice 설치 필요

### 4.2 표/이미지 처리 전략

#### 표 처리

```python
# 전략 1: 마크다운 테이블로 변환
def table_to_markdown(table_data):
    """표를 마크다운 형식으로 변환"""
    header = "| " + " | ".join(table_data[0]) + " |"
    separator = "|" + "|".join(["---"] * len(table_data[0])) + "|"
    rows = "\n".join([
        "| " + " | ".join(row) + " |"
        for row in table_data[1:]
    ])
    return f"{header}\n{separator}\n{rows}"

# 전략 2: 표를 별도 청크로 분리
# - 표 제목 + 표 내용을 하나의 청크로
# - 메타데이터에 "type": "table" 추가
```

#### 이미지 처리

```python
# 전략 1: 이미지 설명 텍스트만 추출
# HWP 이미지의 alt text나 캡션 활용

# 전략 2: Vision LLM으로 이미지 설명 생성 (비용 발생)
# GPT-4 Vision 또는 LLaVA 활용

# 전략 3: OCR 적용 (이미지 내 텍스트)
import pytesseract
from PIL import Image

text = pytesseract.image_to_string(Image.open('chart.png'), lang='kor')
```

### 4.3 메타데이터 활용

#### 추출할 메타데이터

```python
metadata_schema = {
    "file_name": str,          # 파일명
    "created_date": datetime,   # 작성일
    "modified_date": datetime,  # 수정일
    "author": str,             # 작성자
    "department": str,         # 부서 (파싱 필요)
    "document_type": str,      # 공문, 보고서, 규정 등
    "keywords": List[str],     # 키워드
    "page_number": int,        # 페이지 번호
    "section_title": str,      # 섹션 제목
    "has_table": bool,         # 표 포함 여부
    "has_image": bool,         # 이미지 포함 여부
}
```

#### 메타데이터 기반 필터링 예시

```python
# Chroma 예시
results = collection.query(
    query_texts=["출장 규정"],
    n_results=10,
    where={
        "document_type": "규정",
        "department": "총무과"
    }
)
```

---

## 5. 최종 권장 기술 스택

### Sprint 3.2 MVP

```
┌─────────────────────────────────────────────────────────┐
│                     Dubai Crab RAG                       │
├─────────────────────────────────────────────────────────┤
│  문서 로더                                               │
│  ├── HWP: LibreOffice 변환 → 텍스트 추출                │
│  ├── PDF: PyMuPDF                                       │
│  └── DOCX: python-docx                                  │
├─────────────────────────────────────────────────────────┤
│  임베딩                                                  │
│  └── BAAI/bge-m3 (로컬) 또는 OpenAI text-embedding-3    │
├─────────────────────────────────────────────────────────┤
│  벡터 DB                                                │
│  └── Chroma (개발) → Qdrant (프로덕션 고려)             │
├─────────────────────────────────────────────────────────┤
│  프레임워크                                              │
│  └── LlamaIndex                                         │
├─────────────────────────────────────────────────────────┤
│  리랭킹 (선택)                                           │
│  └── BAAI/bge-reranker-v2-m3                            │
├─────────────────────────────────────────────────────────┤
│  LLM                                                    │
│  └── OpenAI GPT-4 또는 Ollama 로컬 모델                 │
└─────────────────────────────────────────────────────────┘
```

### 구현 순서 (Sprint 3.2)

1. **Week 1**: 문서 로더 구현 (HWP → 텍스트)
2. **Week 1**: Chroma + BGE-M3 기본 인덱싱
3. **Week 2**: LlamaIndex 기반 검색 파이프라인
4. **Week 2**: 메타데이터 추출 및 필터링
5. **Week 3**: 리랭킹 추가 및 성능 튜닝
6. **Week 3**: API 엔드포인트 구현

### 설치 명령어 (Core)

```bash
# 필수 패키지
pip install llama-index
pip install chromadb
pip install sentence-transformers
pip install FlagEmbedding

# HWP 처리
pip install pyhwp  # 또는 LibreOffice 설치
pip install python-docx  # DOCX
pip install PyMuPDF  # PDF

# 선택 (리랭킹)
pip install FlagEmbedding[reranker]
```

---

## 6. 참고 자료

### 공식 문서

- [LlamaIndex 문서](https://docs.llamaindex.ai/)
- [Chroma 문서](https://docs.trychroma.com/)
- [BGE-M3 GitHub](https://github.com/FlagOpen/FlagEmbedding)
- [pyhwp 문서](https://pyhwp.readthedocs.io/)

### 벤치마크/비교

- [MTEB Leaderboard](https://huggingface.co/spaces/mteb/leaderboard) - 임베딩 모델 비교
- [Qdrant 벤치마크](https://qdrant.tech/benchmarks/) - 벡터 DB 성능

### 한국어 특화

- [KorQuAD](https://korquad.github.io/) - 한국어 QA 데이터셋
- [KoSimCSE](https://github.com/BM-K/KoSimCSE-SKT) - 한국어 임베딩
