"""embeddings 모듈 테스트

Note: 실제 모델 로드는 시간이 오래 걸리므로,
일부 테스트는 모델 로드 없이 검증 로직만 테스트합니다.
"""

import pytest

from rag.embeddings import (
    BGEEmbedder,
    get_device,
    get_model_name,
    get_embedder,
    reset_embedder,
    TRUSTED_MODELS,
    DEFAULT_MODEL,
)


class TestGetDevice:
    """get_device 함수 테스트"""
    
    def test_returns_valid_device(self):
        """유효한 디바이스 반환"""
        device = get_device()
        
        assert device in ("cuda", "mps", "cpu")


class TestGetModelName:
    """get_model_name 함수 테스트"""
    
    def test_default_model(self):
        """기본 모델 이름"""
        model = get_model_name()
        
        assert model == DEFAULT_MODEL


class TestBGEEmbedderInit:
    """BGEEmbedder 초기화 테스트 (모델 로드 없이)"""
    
    def test_init_default(self):
        """기본값 초기화"""
        embedder = BGEEmbedder()
        
        assert embedder.model_name == DEFAULT_MODEL
        assert embedder.device in ("cuda", "mps", "cpu")
        assert embedder._model is None  # lazy load
    
    def test_init_custom_model(self):
        """커스텀 모델 지정"""
        embedder = BGEEmbedder(model_name="test-model")
        
        assert embedder.model_name == "test-model"
    
    def test_trusted_model_auto_trust(self):
        """신뢰 목록 모델은 자동으로 trust_remote_code=True"""
        embedder = BGEEmbedder(model_name="BAAI/bge-m3")
        
        assert embedder._trust_remote_code is True
    
    def test_untrusted_model_default_false(self):
        """신뢰 목록에 없는 모델은 기본 False"""
        embedder = BGEEmbedder(model_name="unknown/model")
        
        assert embedder._trust_remote_code is False


class TestBGEEmbedderValidation:
    """BGEEmbedder 입력 검증 테스트"""
    
    @pytest.fixture
    def mock_embedder(self, mocker):
        """모델 로드를 모킹한 embedder"""
        embedder = BGEEmbedder()
        
        # mock encode 메서드
        import numpy as np
        mock_model = mocker.MagicMock()
        mock_model.encode.return_value = np.array([[0.1, 0.2, 0.3]])
        embedder._model = mock_model
        
        return embedder
    
    def test_embed_query_empty_raises(self):
        """빈 쿼리는 ValueError 발생"""
        embedder = BGEEmbedder()
        embedder._model = object()  # 임시 모델 설정
        
        with pytest.raises(ValueError, match="쿼리 텍스트가 비어있습니다"):
            embedder.embed_query("")
        
        with pytest.raises(ValueError, match="쿼리 텍스트가 비어있습니다"):
            embedder.embed_query("   ")
    
    def test_embed_documents_empty_list_raises(self):
        """빈 리스트는 ValueError 발생"""
        embedder = BGEEmbedder()
        embedder._model = object()
        
        with pytest.raises(ValueError, match="비어있습니다"):
            embedder.embed_documents([])
    
    def test_get_embeddings_empty_texts_raises(self):
        """모든 텍스트가 빈 경우 ValueError 발생"""
        embedder = BGEEmbedder()
        embedder._model = object()
        
        with pytest.raises(ValueError, match="비어있습니다"):
            embedder.get_embeddings([])
        
        with pytest.raises(ValueError, match="모든 텍스트가 비어있습니다"):
            embedder.get_embeddings(["", "   ", "\n"])


class TestEmbedderCleanup:
    """임베더 정리 테스트"""
    
    def test_cleanup_resets_model(self):
        """cleanup 호출 시 모델 해제"""
        embedder = BGEEmbedder()
        embedder._model = object()  # 가짜 모델
        
        embedder.cleanup()
        
        assert embedder._model is None
    
    def test_context_manager(self):
        """컨텍스트 매니저 사용"""
        with BGEEmbedder() as embedder:
            embedder._model = object()
        
        # 컨텍스트 종료 후 정리됨
        assert embedder._model is None


class TestSingletonEmbedder:
    """싱글톤 임베더 테스트"""
    
    def test_get_embedder_returns_same_instance(self):
        """get_embedder는 같은 인스턴스 반환"""
        reset_embedder()  # 초기화
        
        e1 = get_embedder()
        e2 = get_embedder()
        
        assert e1 is e2
        
        reset_embedder()  # 정리
    
    def test_reset_embedder(self):
        """reset_embedder로 인스턴스 해제"""
        e1 = get_embedder()
        reset_embedder()
        e2 = get_embedder()
        
        # 다른 인스턴스여야 함
        assert e1 is not e2
        
        reset_embedder()  # 정리


# 실제 모델 로드가 필요한 통합 테스트
# CI에서는 건너뛰도록 마킹
@pytest.mark.slow
@pytest.mark.integration
class TestBGEEmbedderIntegration:
    """실제 모델 로드 통합 테스트"""
    
    @pytest.fixture(scope="class")
    def embedder(self):
        """클래스 단위로 임베더 공유 (로드 시간 절약)"""
        e = BGEEmbedder()
        yield e
        e.cleanup()
    
    def test_embed_query(self, embedder):
        """단일 쿼리 임베딩"""
        result = embedder.embed_query("테스트 쿼리입니다")
        
        assert isinstance(result, list)
        assert len(result) > 0
        assert all(isinstance(v, float) for v in result)
    
    def test_embed_documents(self, embedder):
        """문서 배치 임베딩"""
        docs = ["첫 번째 문서", "두 번째 문서", "세 번째 문서"]
        
        result = embedder.embed_documents(docs)
        
        assert len(result) == 3
        assert all(isinstance(emb, list) for emb in result)
    
    def test_get_embeddings(self, embedder):
        """get_embeddings 테스트"""
        result = embedder.get_embeddings(["테스트"], return_dense=True)
        
        assert "dense" in result
        assert result["dense"].shape[0] == 1
