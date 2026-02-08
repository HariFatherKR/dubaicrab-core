"""
BGE-M3 임베딩 래퍼 모듈 (sentence-transformers 기반)

환경 변수:
    EMBEDDING_MODEL: 임베딩 모델 (기본값: BAAI/bge-m3)
    EMBEDDING_DEVICE: 디바이스 (cuda/mps/cpu, 기본값: 자동 감지)
    EMBEDDING_TRUST_REMOTE_CODE: 원격 코드 신뢰 여부 (기본값: false)
"""

import gc
import logging
import os
from typing import List, Optional, Set, Union

import torch
from sentence_transformers import SentenceTransformer


logger = logging.getLogger(__name__)


# 기본 설정
DEFAULT_MODEL = "BAAI/bge-m3"
DEFAULT_BATCH_SIZE = 32

# 신뢰할 수 있는 모델 목록 (trust_remote_code 자동 허용)
TRUSTED_MODELS: Set[str] = {
    "BAAI/bge-m3",
    "BAAI/bge-large-en-v1.5",
    "BAAI/bge-base-en-v1.5",
    "sentence-transformers/all-MiniLM-L6-v2",
    "sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2",
}


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
        - GPU 메모리 관리
    """
    
    def __init__(
        self,
        model_name: Optional[str] = None,
        device: Optional[str] = None,
        batch_size: int = DEFAULT_BATCH_SIZE,
        trust_remote_code: Optional[bool] = None,
    ):
        """
        Args:
            model_name: 모델 이름 (None이면 환경변수 또는 기본값)
            device: 디바이스 (None이면 자동 감지)
            batch_size: 배치 크기
            trust_remote_code: 원격 코드 신뢰 여부 (None이면 자동 결정)
        """
        self.model_name = model_name or get_model_name()
        self.device = device or get_device()
        self.batch_size = batch_size
        self._model: Optional[SentenceTransformer] = None
        
        # trust_remote_code 설정
        if trust_remote_code is not None:
            self._trust_remote_code = trust_remote_code
        else:
            # 환경변수 확인
            env_trust = os.environ.get("EMBEDDING_TRUST_REMOTE_CODE", "").lower()
            if env_trust in ("true", "1", "yes"):
                self._trust_remote_code = True
            elif env_trust in ("false", "0", "no"):
                self._trust_remote_code = False
            else:
                # 신뢰할 수 있는 모델 목록에서 자동 결정
                self._trust_remote_code = self.model_name in TRUSTED_MODELS
        
        # 보안 경고 로깅
        if self._trust_remote_code and self.model_name not in TRUSTED_MODELS:
            logger.warning(
                f"⚠️ 보안 경고: 모델 '{self.model_name}'에 대해 "
                f"trust_remote_code=True가 설정되었습니다. "
                f"신뢰할 수 있는 모델인지 확인하세요."
            )
        
        if not self._trust_remote_code and self.model_name in TRUSTED_MODELS:
            logger.info(
                f"모델 '{self.model_name}'는 신뢰 목록에 있으므로 "
                f"trust_remote_code=True로 설정합니다."
            )
            self._trust_remote_code = True
    
    @property
    def model(self) -> SentenceTransformer:
        """모델 lazy 로딩"""
        if self._model is None:
            logger.info(
                f"임베딩 모델 로드: {self.model_name} "
                f"(device={self.device}, trust_remote_code={self._trust_remote_code})"
            )
            self._model = SentenceTransformer(
                self.model_name,
                device=self.device,
                trust_remote_code=self._trust_remote_code,
            )
        return self._model
    
    def cleanup(self) -> None:
        """
        GPU 메모리 해제
        
        모델을 언로드하고 CUDA 캐시를 정리합니다.
        """
        if self._model is not None:
            logger.info(f"임베딩 모델 언로드: {self.model_name}")
            del self._model
            self._model = None
            
            # GPU 메모리 해제
            if torch.cuda.is_available():
                torch.cuda.empty_cache()
                logger.debug("CUDA 캐시 정리 완료")
            
            # 가비지 컬렉션 강제 실행
            gc.collect()
    
    def __del__(self):
        """소멸자에서 메모리 정리"""
        try:
            self.cleanup()
        except Exception:
            pass  # 소멸자에서는 예외 무시
    
    def __enter__(self):
        """컨텍스트 매니저 진입"""
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        """컨텍스트 매니저 종료 시 정리"""
        self.cleanup()
        return False
    
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
        
        Raises:
            ValueError: 빈 텍스트 또는 빈 리스트 입력 시
        
        Note:
            sentence-transformers 기반이므로 sparse/colbert는 별도 구현 필요
        """
        if isinstance(texts, str):
            texts = [texts]
        
        # 빈 입력 검증
        if not texts:
            raise ValueError("임베딩할 텍스트가 비어있습니다")
        
        # 빈 문자열 필터링 및 검증
        valid_texts = [t for t in texts if t and t.strip()]
        if not valid_texts:
            raise ValueError("모든 텍스트가 비어있습니다")
        
        embeddings = self.model.encode(
            valid_texts,
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
        
        Raises:
            ValueError: 빈 쿼리 텍스트 입력 시
        """
        if not text or not text.strip():
            raise ValueError("쿼리 텍스트가 비어있습니다")
        
        result = self.get_embeddings(text, return_dense=True)
        return result["dense"][0].tolist()
    
    def embed_documents(self, texts: List[str]) -> List[List[float]]:
        """
        문서 배치 임베딩
        
        Args:
            texts: 문서 텍스트 리스트
        
        Returns:
            List[List[float]]: Dense 임베딩 벡터 리스트
        
        Raises:
            ValueError: 빈 리스트 또는 모든 텍스트가 빈 경우
        """
        if not texts:
            raise ValueError("임베딩할 문서 리스트가 비어있습니다")
        
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


def reset_embedder() -> None:
    """
    싱글톤 임베더 해제 및 메모리 정리
    
    GPU 메모리 해제가 필요할 때 호출합니다.
    """
    global _embedder
    if _embedder is not None:
        _embedder.cleanup()
        _embedder = None
        logger.info("싱글톤 임베더 해제 완료")


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
