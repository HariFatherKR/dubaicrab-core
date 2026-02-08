"""
BGE-M3 임베딩 래퍼 모듈 (sentence-transformers 기반)

환경 변수:
    EMBEDDING_MODEL: 임베딩 모델 (기본값: BAAI/bge-m3)
    EMBEDDING_DEVICE: 디바이스 (cuda/mps/cpu, 기본값: 자동 감지)
"""

import os
from typing import List, Optional, Union

import torch
from sentence_transformers import SentenceTransformer


# 기본 설정
DEFAULT_MODEL = "BAAI/bge-m3"
DEFAULT_BATCH_SIZE = 32


def get_device() -> str:
    """
    최적 디바이스 자동 감지
    
    Returns:
        str: 'cuda', 'mps', 또는 'cpu'
    """
    device = os.environ.get("EMBEDDING_DEVICE")
    if device:
        return device
    
    if torch.cuda.is_available():
        return "cuda"
    elif torch.backends.mps.is_available():
        return "mps"
    else:
        return "cpu"


def get_model_name() -> str:
    """임베딩 모델 이름 반환"""
    return os.environ.get("EMBEDDING_MODEL", DEFAULT_MODEL)


class BGEEmbedder:
    """
    BGE-M3 임베딩 래퍼 클래스 (sentence-transformers 기반)
    
    특징:
        - 배치 처리 지원
        - Dense 임베딩 지원
        - 자동 디바이스 감지
    """
    
    def __init__(
        self,
        model_name: Optional[str] = None,
        device: Optional[str] = None,
        batch_size: int = DEFAULT_BATCH_SIZE,
    ):
        """
        Args:
            model_name: 모델 이름 (None이면 환경변수 또는 기본값)
            device: 디바이스 (None이면 자동 감지)
            batch_size: 배치 크기
        """
        self.model_name = model_name or get_model_name()
        self.device = device or get_device()
        self.batch_size = batch_size
        self._model: Optional[SentenceTransformer] = None
    
    @property
    def model(self) -> SentenceTransformer:
        """모델 lazy 로딩"""
        if self._model is None:
            self._model = SentenceTransformer(
                self.model_name,
                device=self.device,
                trust_remote_code=True,  # BGE-M3 커스텀 코드 허용
            )
        return self._model
    
    def get_embeddings(
        self,
        texts: Union[str, List[str]],
        return_dense: bool = True,
        return_sparse: bool = False,
        return_colbert: bool = False,
    ) -> dict:
        """
        텍스트 임베딩 생성
        
        Args:
            texts: 텍스트 또는 텍스트 리스트
            return_dense: Dense 임베딩 반환 여부
            return_sparse: Sparse 임베딩 반환 여부 (현재 미지원)
            return_colbert: ColBERT 임베딩 반환 여부 (현재 미지원)
        
        Returns:
            dict: 임베딩 결과
                - 'dense': Dense 임베딩 (numpy array)
        
        Note:
            sentence-transformers 기반이므로 sparse/colbert는 별도 구현 필요
        """
        if isinstance(texts, str):
            texts = [texts]
        
        embeddings = self.model.encode(
            texts,
            batch_size=self.batch_size,
            show_progress_bar=False,
            convert_to_numpy=True,
        )
        
        result = {}
        if return_dense:
            result["dense"] = embeddings
        
        return result
    
    def embed_query(self, text: str) -> List[float]:
        """
        단일 쿼리 임베딩 (검색용)
        
        Args:
            text: 쿼리 텍스트
        
        Returns:
            List[float]: Dense 임베딩 벡터
        """
        result = self.get_embeddings(text, return_dense=True)
        return result["dense"][0].tolist()
    
    def embed_documents(self, texts: List[str]) -> List[List[float]]:
        """
        문서 배치 임베딩
        
        Args:
            texts: 문서 텍스트 리스트
        
        Returns:
            List[List[float]]: Dense 임베딩 벡터 리스트
        """
        result = self.get_embeddings(texts, return_dense=True)
        return [emb.tolist() for emb in result["dense"]]


# 싱글톤 인스턴스
_embedder: Optional[BGEEmbedder] = None


def get_embedder() -> BGEEmbedder:
    """싱글톤 임베더 반환"""
    global _embedder
    if _embedder is None:
        _embedder = BGEEmbedder()
    return _embedder


def get_embeddings(
    texts: Union[str, List[str]],
    return_dense: bool = True,
    return_sparse: bool = False,
    return_colbert: bool = False,
) -> dict:
    """
    편의 함수: 텍스트 임베딩 생성
    
    Args:
        texts: 텍스트 또는 텍스트 리스트
        return_dense: Dense 임베딩 반환
        return_sparse: Sparse 임베딩 반환 (현재 미지원)
        return_colbert: ColBERT 임베딩 반환 (현재 미지원)
    
    Returns:
        dict: 임베딩 결과
    """
    return get_embedder().get_embeddings(
        texts,
        return_dense=return_dense,
        return_sparse=return_sparse,
        return_colbert=return_colbert,
    )
