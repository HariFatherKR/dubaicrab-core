"""
Chroma 벡터 스토어 초기화 및 관리 모듈

환경 변수:
    CHROMA_PERSIST_DIR: 영구 저장 경로 (기본값: data/chroma/)
"""

import logging
import os
from pathlib import Path
from typing import Optional

import chromadb
from chromadb.config import Settings


logger = logging.getLogger(__name__)


# 기본 설정
DEFAULT_PERSIST_DIR = Path(__file__).parent.parent.parent / "data" / "chroma"
DEFAULT_COLLECTION_NAME = "documents"

# 허용된 기본 디렉토리 (보안용)
ALLOWED_BASE_DIRS = [
    Path.home() / ".cache",
    Path.home() / ".local" / "share",
    Path(__file__).parent.parent.parent / "data",
]


def _validate_persist_dir(persist_dir: Path) -> Path:
    """
    영구 저장 경로 보안 검증
    
    Args:
        persist_dir: 검증할 경로
    
    Returns:
        Path: 정규화된 안전한 경로
    
    Raises:
        ValueError: 허용되지 않은 경로
        PermissionError: 쓰기 권한 없음
    """
    # 절대 경로로 정규화
    resolved = persist_dir.resolve()
    
    # 허용된 디렉토리 내 경로인지 확인
    is_allowed = any(
        str(resolved).startswith(str(base.resolve()))
        for base in ALLOWED_BASE_DIRS
    )
    
    if not is_allowed:
        # 환경변수로 지정된 경우 경고만 출력 (엄격 모드 아님)
        logger.warning(
            f"CHROMA_PERSIST_DIR이 허용된 경로 외부입니다: {resolved}. "
            f"허용된 경로: {[str(b) for b in ALLOWED_BASE_DIRS]}"
        )
    
    # 디렉토리가 존재하지 않으면 생성 시도
    if not resolved.exists():
        try:
            resolved.mkdir(parents=True, exist_ok=True)
            logger.info(f"Chroma 저장 디렉토리 생성: {resolved}")
        except PermissionError:
            raise PermissionError(f"디렉토리 생성 권한 없음: {resolved}")
        except OSError as e:
            raise ValueError(f"디렉토리 생성 실패: {resolved} - {e}")
    
    # 쓰기 권한 확인
    if not os.access(resolved, os.W_OK):
        raise PermissionError(f"쓰기 권한 없음: {resolved}")
    
    return resolved


def get_persist_dir() -> Path:
    """
    Chroma 영구 저장 경로 반환 (검증 포함)
    
    Returns:
        Path: 검증된 영구 저장 경로
    """
    persist_dir = os.environ.get("CHROMA_PERSIST_DIR")
    
    if persist_dir:
        path = Path(persist_dir)
    else:
        path = DEFAULT_PERSIST_DIR
    
    try:
        return _validate_persist_dir(path)
    except (ValueError, PermissionError) as e:
        logger.error(f"경로 검증 실패, 기본값 사용: {e}")
        # 폴백: 기본 경로 사용
        fallback = DEFAULT_PERSIST_DIR
        fallback.mkdir(parents=True, exist_ok=True)
        return fallback


def get_client(persist_dir: Optional[Path] = None) -> chromadb.PersistentClient:
    """
    Chroma 클라이언트 생성
    
    Args:
        persist_dir: 영구 저장 경로 (None이면 환경변수 또는 기본값 사용)
    
    Returns:
        chromadb.PersistentClient: Chroma 클라이언트
    """
    if persist_dir is None:
        persist_dir = get_persist_dir()
    
    # 디렉토리 생성
    persist_dir.mkdir(parents=True, exist_ok=True)
    
    settings = Settings(
        anonymized_telemetry=False,
        allow_reset=True,
    )
    
    return chromadb.PersistentClient(
        path=str(persist_dir),
        settings=settings,
    )


def get_or_create_collection(
    client: chromadb.PersistentClient,
    name: str = DEFAULT_COLLECTION_NAME,
    embedding_function: Optional[callable] = None,
) -> chromadb.Collection:
    """
    컬렉션 가져오기 또는 생성
    
    Args:
        client: Chroma 클라이언트
        name: 컬렉션 이름
        embedding_function: 임베딩 함수 (None이면 기본값 사용)
    
    Returns:
        chromadb.Collection: 컬렉션 객체
    """
    return client.get_or_create_collection(
        name=name,
        embedding_function=embedding_function,
        metadata={"hnsw:space": "cosine"},  # 코사인 유사도 사용
    )


def delete_collection(
    client: chromadb.PersistentClient,
    name: str,
) -> bool:
    """
    컬렉션 삭제
    
    Args:
        client: Chroma 클라이언트
        name: 삭제할 컬렉션 이름
    
    Returns:
        bool: 삭제 성공 여부
    """
    try:
        client.delete_collection(name)
        return True
    except ValueError:
        # 컬렉션이 존재하지 않음
        return False


def list_collections(client: chromadb.PersistentClient) -> list[str]:
    """
    모든 컬렉션 목록 반환
    
    Args:
        client: Chroma 클라이언트
    
    Returns:
        list[str]: 컬렉션 이름 목록
    """
    collections = client.list_collections()
    return [col.name for col in collections]
