"""vector_store 모듈 테스트"""

import os
import tempfile
from pathlib import Path

import pytest

from rag.vector_store import (
    get_client,
    get_or_create_collection,
    delete_collection,
    list_collections,
    get_persist_dir,
    DEFAULT_COLLECTION_NAME,
)


class TestGetClient:
    """get_client 함수 테스트"""
    
    def test_create_client_with_temp_dir(self, temp_dir):
        """임시 디렉토리로 클라이언트 생성"""
        client = get_client(persist_dir=temp_dir)
        
        assert client is not None
        # Chroma 데이터 파일이 생성되었는지 확인
        assert (temp_dir / "chroma.sqlite3").exists()
    
    def test_client_is_persistent(self, temp_dir):
        """영구 저장 클라이언트 확인"""
        client = get_client(persist_dir=temp_dir)
        
        # 컬렉션 생성
        collection = get_or_create_collection(client, "test_persist")
        collection.add(
            ids=["doc1"],
            documents=["테스트 문서"],
        )
        
        # 새 클라이언트로 다시 연결
        client2 = get_client(persist_dir=temp_dir)
        collection2 = client2.get_collection("test_persist")
        
        # 데이터가 유지되어야 함
        result = collection2.get()
        assert len(result["ids"]) == 1
        assert result["documents"][0] == "테스트 문서"


class TestGetOrCreateCollection:
    """get_or_create_collection 함수 테스트"""
    
    def test_create_new_collection(self, temp_dir):
        """새 컬렉션 생성"""
        client = get_client(persist_dir=temp_dir)
        
        collection = get_or_create_collection(client, "new_collection")
        
        assert collection is not None
        assert collection.name == "new_collection"
    
    def test_get_existing_collection(self, temp_dir):
        """기존 컬렉션 가져오기"""
        client = get_client(persist_dir=temp_dir)
        
        # 첫 번째 생성
        collection1 = get_or_create_collection(client, "existing")
        collection1.add(ids=["id1"], documents=["doc1"])
        
        # 두 번째 호출 - 기존 컬렉션 반환
        collection2 = get_or_create_collection(client, "existing")
        
        # 같은 컬렉션이어야 함
        result = collection2.get()
        assert len(result["ids"]) == 1
    
    def test_default_collection_name(self, temp_dir):
        """기본 컬렉션 이름 사용"""
        client = get_client(persist_dir=temp_dir)
        
        collection = get_or_create_collection(client)
        
        assert collection.name == DEFAULT_COLLECTION_NAME


class TestDeleteCollection:
    """delete_collection 함수 테스트"""
    
    def test_delete_existing_collection(self, temp_dir):
        """존재하는 컬렉션 삭제"""
        client = get_client(persist_dir=temp_dir)
        
        # 컬렉션 생성
        get_or_create_collection(client, "to_delete")
        
        # 삭제
        result = delete_collection(client, "to_delete")
        
        assert result is True
        
        # 컬렉션이 더 이상 존재하지 않아야 함
        collections = list_collections(client)
        assert "to_delete" not in collections
    
    def test_delete_nonexistent_collection(self, temp_dir):
        """존재하지 않는 컬렉션 삭제 시도"""
        client = get_client(persist_dir=temp_dir)
        
        result = delete_collection(client, "nonexistent")
        
        assert result is False


class TestListCollections:
    """list_collections 함수 테스트"""
    
    def test_list_empty(self, temp_dir):
        """빈 컬렉션 목록"""
        client = get_client(persist_dir=temp_dir)
        
        result = list_collections(client)
        
        assert isinstance(result, list)
    
    def test_list_multiple_collections(self, temp_dir):
        """여러 컬렉션 목록"""
        client = get_client(persist_dir=temp_dir)
        
        # 여러 컬렉션 생성
        get_or_create_collection(client, "col1")
        get_or_create_collection(client, "col2")
        get_or_create_collection(client, "col3")
        
        result = list_collections(client)
        
        assert "col1" in result
        assert "col2" in result
        assert "col3" in result


class TestGetPersistDir:
    """get_persist_dir 함수 테스트"""
    
    def test_returns_path(self):
        """Path 객체 반환"""
        result = get_persist_dir()
        
        assert isinstance(result, Path)
    
    def test_env_override(self, temp_dir):
        """환경 변수로 경로 지정"""
        custom_path = temp_dir / "custom_chroma"
        os.environ["CHROMA_PERSIST_DIR"] = str(custom_path)
        
        try:
            result = get_persist_dir()
            assert result == custom_path.resolve()
        finally:
            del os.environ["CHROMA_PERSIST_DIR"]
