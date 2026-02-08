"""hwp_parser 모듈 테스트"""

import tempfile
from pathlib import Path

import pytest

from rag.parsers.hwp_parser import (
    DocumentMetadata,
    ParseResult,
    hwp_to_text,
    get_file_hash,
    check_libreoffice,
)


class TestDocumentMetadata:
    """DocumentMetadata 데이터클래스 테스트"""
    
    def test_create_minimal(self):
        """최소 필수 필드로 생성"""
        meta = DocumentMetadata(
            filename="test.hwp",
            file_hash="abc123",
        )
        
        assert meta.filename == "test.hwp"
        assert meta.file_hash == "abc123"
        assert meta.author is None
        assert meta.title is None
    
    def test_create_full(self):
        """모든 필드 지정"""
        from datetime import datetime
        
        now = datetime.now()
        meta = DocumentMetadata(
            filename="test.hwp",
            file_hash="abc123",
            created_at=now,
            modified_at=now,
            author="작성자",
            title="문서 제목",
            file_size=1024,
        )
        
        assert meta.author == "작성자"
        assert meta.title == "문서 제목"
        assert meta.file_size == 1024


class TestParseResult:
    """ParseResult 데이터클래스 테스트"""
    
    def test_successful_result(self):
        """성공 결과"""
        result = ParseResult(
            text="추출된 텍스트",
            metadata=DocumentMetadata(
                filename="test.hwp",
                file_hash="abc123",
            ),
            success=True,
        )
        
        assert result.success is True
        assert result.text == "추출된 텍스트"
        assert result.error is None
    
    def test_failed_result(self):
        """실패 결과"""
        result = ParseResult(
            text="",
            metadata=DocumentMetadata(
                filename="test.hwp",
                file_hash="",
            ),
            success=False,
            error="파일을 찾을 수 없습니다",
        )
        
        assert result.success is False
        assert result.error == "파일을 찾을 수 없습니다"


class TestGetFileHash:
    """get_file_hash 함수 테스트"""
    
    def test_hash_file(self, temp_dir):
        """파일 해시 계산"""
        test_file = temp_dir / "test.txt"
        test_file.write_text("테스트 내용")
        
        hash1 = get_file_hash(test_file)
        
        assert isinstance(hash1, str)
        assert len(hash1) == 64  # SHA256
    
    def test_same_content_same_hash(self, temp_dir):
        """같은 내용은 같은 해시"""
        file1 = temp_dir / "file1.txt"
        file2 = temp_dir / "file2.txt"
        
        file1.write_text("동일한 내용")
        file2.write_text("동일한 내용")
        
        assert get_file_hash(file1) == get_file_hash(file2)
    
    def test_different_content_different_hash(self, temp_dir):
        """다른 내용은 다른 해시"""
        file1 = temp_dir / "file1.txt"
        file2 = temp_dir / "file2.txt"
        
        file1.write_text("내용 A")
        file2.write_text("내용 B")
        
        assert get_file_hash(file1) != get_file_hash(file2)


class TestCheckLibreoffice:
    """check_libreoffice 함수 테스트"""
    
    def test_returns_path_or_none(self):
        """경로 또는 None 반환"""
        result = check_libreoffice()
        
        assert result is None or isinstance(result, str)


class TestHwpToText:
    """hwp_to_text 함수 테스트"""
    
    def test_file_not_found(self):
        """존재하지 않는 파일"""
        result = hwp_to_text("/nonexistent/path/file.hwp")
        
        assert result.success is False
        assert "찾을 수 없습니다" in result.error
    
    def test_returns_parse_result(self, temp_dir):
        """ParseResult 반환"""
        # 실제 HWP 파일이 없어도 타입 검증
        result = hwp_to_text(temp_dir / "nonexistent.hwp")
        
        assert isinstance(result, ParseResult)
        assert isinstance(result.metadata, DocumentMetadata)
    
    @pytest.mark.integration
    def test_parse_real_hwp(self):
        """실제 HWP 파일 파싱 (통합 테스트)
        
        Note: 실제 HWP 파일이 필요하므로 CI에서는 건너뜀
        """
        # 테스트 데이터 디렉토리에 샘플 HWP가 있는 경우
        sample_hwp = Path(__file__).parent.parent / "data" / "sample.hwp"
        
        if not sample_hwp.exists():
            pytest.skip("샘플 HWP 파일이 없습니다")
        
        result = hwp_to_text(sample_hwp)
        
        assert result.success is True
        assert len(result.text) > 0
