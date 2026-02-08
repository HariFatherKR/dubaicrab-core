# 🔍 Sprint 3.2 RAG P0 코드 리뷰

> **리뷰어:** CTO  
> **일자:** 2026-02-09  
> **대상:** packages/rag/src/rag/  
> **총점:** 7.2 / 10점

---

## 📊 종합 평가

| 카테고리    | 점수       | 평가                                         |
| ----------- | ---------- | -------------------------------------------- |
| 코드 품질   | 1.6/2.0    | 양호 - 타입 힌트 good, 일부 중복             |
| 아키텍처    | 1.5/2.0    | 양호 - 모듈 분리 good, DI 부족               |
| 에러 핸들링 | 1.3/2.0    | 개선 필요 - 로깅 불충분, 복구 전략 부족      |
| 보안        | 1.4/2.0    | 개선 필요 - 경로 검증 미흡, 리소스 제한 없음 |
| 성능        | 1.4/2.0    | 개선 필요 - 비동기 미지원, 메모리 관리 부족  |
| **총점**    | **7.2/10** | **Pass (조건부)**                            |

---

## 📁 파일별 상세 리뷰

### 1. `__init__.py`

**점수:** 9/10

```python
# 현재
from . import vector_store
from . import embeddings
from . import chunker
from . import indexer
```

**✅ 장점:**

- 깔끔한 모듈 익스포트
- `__version__`, `__all__` 정의 good

**⚠️ 개선 사항:**

- 주요 클래스/함수 직접 익스포트 고려

**💡 개선안:**

```python
from .embeddings import BGEEmbedder, get_embeddings
from .chunker import DocumentChunker, chunk_document
from .indexer import index_document, index_directory
from .vector_store import get_client, get_or_create_collection

__all__ = [
    "BGEEmbedder", "get_embeddings",
    "DocumentChunker", "chunk_document",
    "index_document", "index_directory",
    "get_client", "get_or_create_collection",
]
```

---

### 2. `vector_store.py`

**점수:** 7.5/10

**✅ 장점:**

- 환경변수 기반 설정 분리
- 타입 힌트 완비
- telemetry 비활성화 good

**🔴 P0 문제점:**

#### 2.1 경로 탐색 취약점

```python
# 문제: 환경변수 경로 검증 없음
def get_persist_dir() -> Path:
    persist_dir = os.environ.get("CHROMA_PERSIST_DIR")
    if persist_dir:
        return Path(persist_dir)  # 위험: ../../../ 공격 가능
```

**💡 개선안:**

```python
import os
from pathlib import Path

ALLOWED_BASE_DIRS = [
    Path.home() / ".cache",
    Path(__file__).parent.parent.parent / "data",
]

def get_persist_dir() -> Path:
    persist_dir = os.environ.get("CHROMA_PERSIST_DIR")
    if persist_dir:
        path = Path(persist_dir).resolve()
        # 허용된 경로 내인지 확인
        if not any(str(path).startswith(str(base.resolve())) for base in ALLOWED_BASE_DIRS):
            raise ValueError(f"허용되지 않은 경로: {path}")
        return path
    return DEFAULT_PERSIST_DIR
```

#### 2.2 리소스 정리 누락

```python
# 문제: 클라이언트 종료 메서드 없음
def get_client(...) -> chromadb.PersistentClient:
    ...
    return chromadb.PersistentClient(...)
```

**💡 개선안:**

```python
from contextlib import contextmanager

@contextmanager
def client_context(persist_dir: Optional[Path] = None):
    """컨텍스트 매니저로 클라이언트 생명주기 관리"""
    client = get_client(persist_dir)
    try:
        yield client
    finally:
        # Chroma는 명시적 close 불필요하지만 향후 확장성
        pass
```

**🟡 P1 문제점:**

#### 2.3 에러 핸들링 부족

```python
# 문제: get_or_create_collection의 에러 처리 없음
def get_or_create_collection(...):
    return client.get_or_create_collection(...)  # 예외 전파만
```

**💡 개선안:**

```python
import logging

logger = logging.getLogger(__name__)

def get_or_create_collection(...) -> chromadb.Collection:
    try:
        collection = client.get_or_create_collection(
            name=name,
            embedding_function=embedding_function,
            metadata={"hnsw:space": "cosine"},
        )
        logger.info(f"컬렉션 준비됨: {name}")
        return collection
    except Exception as e:
        logger.error(f"컬렉션 생성 실패: {name}, 에러: {e}")
        raise
```

---

### 3. `embeddings.py`

**점수:** 7.0/10

**✅ 장점:**

- Lazy loading으로 초기화 비용 최소화
- 싱글톤 패턴으로 모델 재사용
- 배치 처리 지원

**🔴 P0 문제점:**

#### 3.1 trust_remote_code 보안 위험

```python
# 위험: 원격 코드 신뢰 - 공급망 공격 가능
self._model = SentenceTransformer(
    self.model_name,
    trust_remote_code=True,  # ⚠️ 보안 위험
)
```

**💡 개선안:**

```python
import os

TRUSTED_MODELS = {"BAAI/bge-m3", "sentence-transformers/all-MiniLM-L6-v2"}

def __init__(self, model_name: Optional[str] = None, ...):
    self.model_name = model_name or get_model_name()

    # 신뢰할 수 있는 모델만 remote code 허용
    self._trust_remote = self.model_name in TRUSTED_MODELS

    if not self._trust_remote:
        import warnings
        warnings.warn(f"모델 {self.model_name}은(는) 신뢰 목록에 없습니다")

@property
def model(self) -> SentenceTransformer:
    if self._model is None:
        self._model = SentenceTransformer(
            self.model_name,
            device=self.device,
            trust_remote_code=self._trust_remote,
        )
    return self._model
```

#### 3.2 메모리 관리 부재

```python
# 문제: GPU 메모리 해제 불가
_embedder: Optional[BGEEmbedder] = None

def get_embedder() -> BGEEmbedder:
    global _embedder
    if _embedder is None:
        _embedder = BGEEmbedder()
    return _embedder
```

**💡 개선안:**

```python
import gc
import torch

class BGEEmbedder:
    def unload(self):
        """메모리 해제"""
        if self._model is not None:
            del self._model
            self._model = None
            if torch.cuda.is_available():
                torch.cuda.empty_cache()
            gc.collect()

def reset_embedder():
    """싱글톤 인스턴스 해제"""
    global _embedder
    if _embedder is not None:
        _embedder.unload()
        _embedder = None
```

**🟡 P1 문제점:**

#### 3.3 빈 텍스트 검증 없음

```python
# 문제: 빈 리스트 처리 시 에러 발생 가능
def embed_documents(self, texts: List[str]) -> List[List[float]]:
    result = self.get_embeddings(texts, return_dense=True)
    return [emb.tolist() for emb in result["dense"]]
```

**💡 개선안:**

```python
def embed_documents(self, texts: List[str]) -> List[List[float]]:
    if not texts:
        return []

    # 빈 문자열 필터링
    valid_texts = [(i, t) for i, t in enumerate(texts) if t.strip()]
    if not valid_texts:
        raise ValueError("모든 텍스트가 비어있습니다")

    indices, valid_only = zip(*valid_texts)
    result = self.get_embeddings(list(valid_only), return_dense=True)

    # 원래 순서로 복원 (빈 텍스트는 zero vector)
    dim = result["dense"].shape[1]
    output = [[0.0] * dim] * len(texts)
    for idx, emb in zip(indices, result["dense"]):
        output[idx] = emb.tolist()

    return output
```

---

### 4. `chunker.py`

**점수:** 8.0/10

**✅ 장점:**

- 한국어 공문서 특화 패턴 good
- 조항/항목 패턴 정규식 well-designed
- dataclass 활용 깔끔함
- 오버랩 처리 구현 완료

**🟡 P1 문제점:**

#### 4.1 DRY 원칙 위반 - 패턴 중복

```python
# LIST_PATTERNS가 클래스 변수로만 존재, 사용되지 않음
LIST_PATTERNS = [
    re.compile(r"^\s*(\d+)\.\s+", re.MULTILINE),
    ...
]
```

**💡 개선안:**

```python
class DocumentChunker:
    # 사용되지 않는 패턴은 제거하거나 실제 활용
    def _detect_list_boundaries(self, text: str) -> List[int]:
        """리스트 항목 경계 감지"""
        boundaries = []
        for pattern in self.LIST_PATTERNS:
            for match in pattern.finditer(text):
                boundaries.append(match.start())
        return sorted(set(boundaries))
```

#### 4.2 MAX_CHUNK_SIZE 하드코딩

```python
MAX_CHUNK_SIZE = 2000  # 매직 넘버
```

**💡 개선안:**

```python
from dataclasses import dataclass

@dataclass
class ChunkingConfig:
    chunk_size: int = 512
    overlap: int = 50
    min_chunk_size: int = 50
    max_chunk_size: int = 2000

    def __post_init__(self):
        if self.overlap >= self.chunk_size:
            raise ValueError("overlap은 chunk_size보다 작아야 합니다")
        if self.min_chunk_size >= self.chunk_size:
            raise ValueError("min_chunk_size는 chunk_size보다 작아야 합니다")
```

**🟢 P2 개선 제안:**

#### 4.3 타입 힌트 현대화

```python
# 현재
from typing import List, Optional

# 권장 (Python 3.9+)
def chunk_document(
    self,
    text: str,
    source_file: str,
    tables: list[str] | None = None,
) -> list[Chunk]:
```

---

### 5. `indexer.py`

**점수:** 6.5/10

**✅ 장점:**

- 재시도 로직 구현
- 문서 해시로 중복 관리
- 진행률 콜백 지원

**🔴 P0 문제점:**

#### 5.1 경로 검증 취약점

```python
# 문제: 경로 순회 공격에 취약
def index_document(file_path: str | Path, ...):
    file_path = Path(file_path)
    # ../../etc/passwd 같은 경로 허용됨
```

**💡 개선안:**

```python
from pathlib import Path

ALLOWED_EXTENSIONS = {".hwp", ".hwpx", ".txt", ".pdf"}
MAX_FILE_SIZE = 100 * 1024 * 1024  # 100MB

def validate_file_path(file_path: Path, base_dir: Path | None = None) -> Path:
    """파일 경로 보안 검증"""
    resolved = file_path.resolve()

    # 기본 디렉토리 제한 (설정된 경우)
    if base_dir:
        if not str(resolved).startswith(str(base_dir.resolve())):
            raise ValueError(f"허용되지 않은 경로: {resolved}")

    # 확장자 검증
    if resolved.suffix.lower() not in ALLOWED_EXTENSIONS:
        raise ValueError(f"지원하지 않는 파일 형식: {resolved.suffix}")

    # 파일 크기 검증
    if resolved.exists() and resolved.stat().st_size > MAX_FILE_SIZE:
        raise ValueError(f"파일 크기 초과: {resolved.stat().st_size} > {MAX_FILE_SIZE}")

    return resolved

def index_document(file_path: str | Path, ...):
    file_path = validate_file_path(Path(file_path))
    ...
```

#### 5.2 로깅 불충분

```python
# 문제: logger.exception만 사용, 성공 케이스 로깅 없음
except Exception as e:
    logger.exception(f"인덱싱 실패: {file_path}")
```

**💡 개선안:**

```python
import logging
import time

logger = logging.getLogger(__name__)

def index_document(...) -> dict:
    start_time = time.time()
    logger.info(f"인덱싱 시작: {file_path.name}")

    try:
        # ... 파싱, 청킹, 임베딩 ...

        elapsed = time.time() - start_time
        logger.info(
            f"인덱싱 완료: {file_path.name}, "
            f"청크={len(chunks)}, 시간={elapsed:.2f}s"
        )

        return {"success": True, ...}

    except Exception as e:
        elapsed = time.time() - start_time
        logger.error(
            f"인덱싱 실패: {file_path.name}, "
            f"에러={type(e).__name__}: {e}, 시간={elapsed:.2f}s",
            exc_info=True,
        )
        return {"success": False, ...}
```

**🟡 P1 문제점:**

#### 5.3 비동기 처리 미지원

```python
# 문제: 대량 파일 처리 시 블로킹
for i, file_path in enumerate(files):
    result = index_document(file_path, ...)  # 동기 처리
```

**💡 개선안:**

```python
import asyncio
from concurrent.futures import ThreadPoolExecutor

async def index_directory_async(
    dir_path: str | Path,
    max_workers: int = 4,
    ...
) -> dict:
    """비동기 디렉토리 인덱싱"""
    files = list_files(dir_path, recursive)

    loop = asyncio.get_event_loop()
    with ThreadPoolExecutor(max_workers=max_workers) as executor:
        tasks = [
            loop.run_in_executor(
                executor,
                index_document,
                file_path,
                collection_name,
                chunk_size,
                overlap,
            )
            for file_path in files
        ]
        results = await asyncio.gather(*tasks, return_exceptions=True)

    return aggregate_results(results)
```

#### 5.4 기존 문서 삭제 에러 무시

```python
# 문제: 모든 예외 무시는 위험
try:
    existing = collection.get(where={"doc_hash": doc_hash})
    if existing and existing["ids"]:
        collection.delete(ids=existing["ids"])
except Exception:
    pass  # 💀 무시
```

**💡 개선안:**

```python
try:
    existing = collection.get(where={"doc_hash": doc_hash})
    if existing and existing["ids"]:
        collection.delete(ids=existing["ids"])
        logger.debug(f"기존 문서 삭제: {len(existing['ids'])}개 청크")
except ValueError:
    # 문서가 없는 경우 - 정상
    pass
except Exception as e:
    logger.warning(f"기존 문서 삭제 실패 (계속 진행): {e}")
```

---

### 6. `cli.py`

**점수:** 7.0/10

**✅ 장점:**

- argparse 구조 깔끔
- 진행률 표시 구현
- 에러 개수 제한 출력

**🟡 P1 문제점:**

#### 6.1 에러 시 스택트레이스 노출

```python
# 문제: 사용자에게 내부 에러 노출
except Exception as e:
    print(f"❌ 상태 조회 실패: {e}")  # 전체 에러 출력
```

**💡 개선안:**

```python
import logging
import traceback

logger = logging.getLogger(__name__)

def cmd_status(args):
    try:
        ...
    except ConnectionError:
        print("❌ Chroma DB 연결 실패. 서버 상태를 확인하세요.")
        return 1
    except PermissionError:
        print("❌ 저장소 접근 권한이 없습니다.")
        return 1
    except Exception as e:
        logger.exception("상태 조회 실패")
        print("❌ 예상치 못한 오류 발생. 로그를 확인하세요.")
        if args.verbose:
            traceback.print_exc()
        return 1
```

#### 6.2 입력 검증 부족

```python
# 문제: 경로 검증 없이 바로 사용
path = Path(args.path)
if not path.exists():
    ...
```

**💡 개선안:**

```python
def validate_input_path(path_str: str) -> Path:
    """CLI 입력 경로 검증"""
    path = Path(path_str)

    # 절대 경로 변환
    resolved = path.resolve()

    # 홈 디렉토리 외부 제한 (선택적)
    # if not str(resolved).startswith(str(Path.home())):
    #     raise ValueError("홈 디렉토리 외부는 접근할 수 없습니다")

    return resolved

def cmd_index(args):
    try:
        path = validate_input_path(args.path)
    except ValueError as e:
        print(f"❌ 잘못된 경로: {e}")
        return 1
```

**🟢 P2 개선 제안:**

#### 6.3 로깅 설정 추가

```python
def main():
    # 로깅 초기화 추가
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    )

    parser = argparse.ArgumentParser(...)
    parser.add_argument(
        "-v", "--verbose",
        action="store_true",
        help="상세 로그 출력",
    )
```

---

### 7. `parsers/__init__.py`

**점수:** 8.0/10

**✅ 장점:**

- 명확한 `__all__` 정의
- 필요한 것만 익스포트

**🟢 P2 개선 제안:**

```python
# 파서 자동 등록 패턴 고려
from typing import Dict, Type

PARSERS: Dict[str, Type] = {
    ".hwp": HWPParser,
    ".hwpx": HWPXParser,
}

def get_parser(extension: str):
    """확장자별 파서 반환"""
    return PARSERS.get(extension.lower())
```

---

### 8. `parsers/hwp_parser.py`

**점수:** 6.5/10

**✅ 장점:**

- 다양한 환경(macOS, Linux) 지원
- 암호화 파일 감지 시도
- 마크다운 테이블 변환

**🔴 P0 문제점:**

#### 8.1 Command Injection 취약점

```python
# 위험: file_path가 검증되지 않으면 명령 주입 가능
cmd = [
    soffice,
    "--headless",
    "--convert-to", "txt:Text",
    "--outdir", tmpdir,
    str(file_path),  # ⚠️ 셸 메타문자 포함 가능
]
subprocess.run(cmd, ...)
```

**💡 개선안:**

```python
import shlex

def hwp_to_text_libreoffice(file_path: Path, timeout: int = DEFAULT_TIMEOUT) -> str:
    # 1. 파일명 검증
    if not file_path.name.replace(".", "").replace("_", "").replace("-", "").isalnum():
        # 안전한 임시 파일로 복사
        safe_name = f"doc_{get_file_hash(file_path)[:8]}{file_path.suffix}"
        safe_path = Path(tmpdir) / safe_name
        shutil.copy2(file_path, safe_path)
        file_path = safe_path

    # 2. subprocess.run은 shell=False가 기본이므로
    #    리스트로 전달하면 안전하지만 추가 검증 권장
    cmd = [
        soffice,
        "--headless",
        "--convert-to", "txt:Text",
        "--outdir", tmpdir,
        str(file_path.resolve()),  # 절대 경로 사용
    ]
```

#### 8.2 임시 파일 정리 미흡

```python
# 문제: 예외 발생 시 임시 디렉토리 정리 보장 불확실
with tempfile.TemporaryDirectory() as tmpdir:
    subprocess.run(cmd, timeout=timeout, ...)
    # 여기서 예외 발생하면?
```

**💡 개선안:**

```python
import atexit
import signal

def hwp_to_text_libreoffice(file_path: Path, timeout: int = DEFAULT_TIMEOUT) -> str:
    tmpdir = tempfile.mkdtemp(prefix="hwp_convert_")

    def cleanup():
        shutil.rmtree(tmpdir, ignore_errors=True)

    atexit.register(cleanup)

    try:
        # ... 변환 로직 ...
        return text
    finally:
        cleanup()
        atexit.unregister(cleanup)
```

**🟡 P1 문제점:**

#### 8.3 인코딩 처리 불완전

```python
# 문제: 다양한 HWP 인코딩 미고려 (EUC-KR 등)
text = txt_files[0].read_text(encoding="utf-8", errors="replace")
```

**💡 개선안:**

```python
import chardet

def read_text_with_fallback(file_path: Path) -> str:
    """다양한 인코딩 시도"""
    encodings = ["utf-8", "cp949", "euc-kr", "utf-16"]

    # chardet으로 자동 감지 시도
    with open(file_path, "rb") as f:
        raw = f.read()
        detected = chardet.detect(raw)
        if detected["confidence"] > 0.7:
            encodings.insert(0, detected["encoding"])

    for encoding in encodings:
        try:
            return raw.decode(encoding)
        except (UnicodeDecodeError, LookupError):
            continue

    # 최후의 수단
    return raw.decode("utf-8", errors="replace")
```

#### 8.4 is_encrypted_hwp 미완성

```python
# 문제: 실제 암호화 감지 미구현
def is_encrypted_hwp(file_path: Path) -> bool:
    ...
    # 실제 구현 시 olefile 라이브러리 사용 권장
    return False  # 항상 False
```

**💡 개선안:**

```python
try:
    import olefile
    HAS_OLEFILE = True
except ImportError:
    HAS_OLEFILE = False

def is_encrypted_hwp(file_path: Path) -> bool:
    """HWP 암호화 여부 확인"""
    if not HAS_OLEFILE:
        logger.warning("olefile 미설치 - 암호화 감지 불가")
        return False

    try:
        with olefile.OleFileIO(file_path) as ole:
            # HwpSummaryInformation 스트림에서 암호화 플래그 확인
            if ole.exists("HwpSummaryInformation"):
                # 암호화 플래그 파싱 로직
                pass

            # FileHeader 스트림에서 암호화 확인
            if ole.exists("FileHeader"):
                header = ole.openstream("FileHeader").read()
                # 바이트 오프셋 36에 암호화 플래그
                if len(header) > 36:
                    return (header[36] & 0x02) != 0
        return False
    except Exception:
        return False
```

---

## 📋 우선순위별 수정 사항

### 🔴 P0 (즉시 수정 필요) - 보안/안정성

| #   | 파일              | 문제                            | 위험도   |
| --- | ----------------- | ------------------------------- | -------- |
| 1   | `hwp_parser.py`   | Command Injection 가능성        | Critical |
| 2   | `indexer.py`      | 경로 순회 공격 취약점           | High     |
| 3   | `vector_store.py` | 환경변수 경로 검증 없음         | High     |
| 4   | `embeddings.py`   | trust_remote_code 무조건 활성화 | High     |
| 5   | `embeddings.py`   | GPU 메모리 해제 불가            | High     |

### 🟡 P1 (Sprint 내 수정) - 품질/유지보수

| #   | 파일            | 문제                      | 영향           |
| --- | --------------- | ------------------------- | -------------- |
| 1   | `indexer.py`    | 로깅 불충분               | 디버깅 어려움  |
| 2   | `indexer.py`    | 비동기 처리 미지원        | 대량 처리 성능 |
| 3   | `indexer.py`    | 모든 예외 무시 패턴       | 버그 은폐      |
| 4   | `cli.py`        | 에러 시 스택트레이스 노출 | 보안/UX        |
| 5   | `hwp_parser.py` | 다양한 인코딩 미지원      | 일부 파일 실패 |
| 6   | `hwp_parser.py` | 암호화 감지 미구현        | 기능 불완전    |
| 7   | `embeddings.py` | 빈 텍스트 처리 없음       | 런타임 에러    |
| 8   | `chunker.py`    | LIST_PATTERNS 미사용      | 데드 코드      |

### 🟢 P2 (다음 Sprint) - 개선/최적화

| #   | 파일                  | 개선사항                    |
| --- | --------------------- | --------------------------- |
| 1   | `__init__.py`         | 주요 클래스 직접 익스포트   |
| 2   | `chunker.py`          | Python 3.9+ 타입 힌트       |
| 3   | `chunker.py`          | ChunkingConfig 설정 클래스  |
| 4   | `cli.py`              | 로깅 초기화 및 verbose 옵션 |
| 5   | `parsers/__init__.py` | 파서 자동 등록 패턴         |
| 6   | 전체                  | 유닛 테스트 추가            |

---

## 🏗️ 아키텍처 권장 사항

### 1. 의존성 주입 (DI) 도입

```python
# 현재: 하드코딩된 의존성
def index_document(...):
    client = get_client()  # 전역 함수 호출
    embedder = get_embedder()  # 싱글톤

# 권장: 의존성 주입
@dataclass
class IndexingService:
    vector_store: VectorStoreProtocol
    embedder: EmbedderProtocol
    chunker: ChunkerProtocol

    def index_document(self, file_path: Path, ...) -> dict:
        ...
```

### 2. 설정 중앙화

```python
# config.py
from pydantic import BaseSettings

class RAGSettings(BaseSettings):
    chroma_persist_dir: str = "data/chroma"
    embedding_model: str = "BAAI/bge-m3"
    embedding_device: str = "auto"
    chunk_size: int = 512
    chunk_overlap: int = 50
    max_file_size: int = 100 * 1024 * 1024

    class Config:
        env_prefix = "RAG_"
```

### 3. 프로토콜 기반 추상화

```python
from typing import Protocol

class EmbedderProtocol(Protocol):
    def embed_query(self, text: str) -> list[float]: ...
    def embed_documents(self, texts: list[str]) -> list[list[float]]: ...
```

---

## ✅ 결론

**총점: 7.2/10 (Pass - 조건부)**

전반적으로 한국어 공문서 처리에 특화된 좋은 기반 코드입니다. 청킹 로직과 HWP 파싱 구조는 잘 설계되었습니다.

그러나 **보안 취약점(P0)**이 5개 발견되어 프로덕션 배포 전 반드시 수정이 필요합니다:

1. Command Injection 가능성
2. 경로 순회 공격
3. 환경변수 경로 검증 부재
4. 원격 코드 무조건 신뢰
5. 메모리 누수 가능성

**권장 액션:**

1. P0 항목 5개 즉시 수정 (예상 1-2일)
2. P1 항목 Sprint 내 해결
3. 보안 테스트 추가 (pytest + 경로 인젝션 테스트)

---

_리뷰 완료: 2026-02-09_  
_다음 리뷰 예정: P0 수정 완료 후_
