"""
Chroma 벡터 스토어 초기화 및 관리 모듈

환경 변수:
    CHROMA_PERSIST_DIR: 영구 저장 경로 (기본값: data/chroma/)
"""

import os
from pathlib import Path
from typing import Optional

import chromadb
from chromadb.config import Settings


# 기본 설정
DEFAULT_PERSIST_DIR = Path(__file__).parent.parent.parent / "data" / "chroma"
DEFAULT_COLLECTION_NAME = "documents"


def get_persist_dir() -> Path:
    """Chroma 영구 저장 경로 반환"""
    persist_dir = os.environ.get("CHROMA_PERSIST_DIR")
    if persist_dir:
        return Path(persist_dir)
    return DEFAULT_PERSIST_DIR


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
