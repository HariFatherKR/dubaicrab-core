"""chunker 모듈 테스트"""

import pytest

from rag.chunker import (
    Chunk,
    ChunkMetadata,
    DocumentChunker,
    chunk_document,
    chunks_to_dict,
    DEFAULT_CHUNK_SIZE,
    DEFAULT_OVERLAP,
)


class TestDocumentChunker:
    """DocumentChunker 클래스 테스트"""
    
    def test_init_default_values(self):
        """기본값으로 초기화"""
        chunker = DocumentChunker()
        assert chunker.chunk_size == DEFAULT_CHUNK_SIZE
        assert chunker.overlap == DEFAULT_OVERLAP
    
    def test_init_custom_values(self):
        """커스텀 값으로 초기화"""
        chunker = DocumentChunker(chunk_size=256, overlap=25)
        assert chunker.chunk_size == 256
        assert chunker.overlap == 25
    
    def test_chunk_empty_text(self):
        """빈 텍스트 청킹 - 빈 리스트 반환"""
        chunker = DocumentChunker()
        
        # 빈 문자열
        result = chunker.chunk_document("", "test.txt")
        assert result == []
        
        # 공백만 있는 문자열
        result = chunker.chunk_document("   \n\t  ", "test.txt")
        assert result == []
        
        # None은 TypeError 발생 (의도적)
    
    def test_chunk_short_text(self):
        """짧은 텍스트 청킹"""
        chunker = DocumentChunker(chunk_size=512, min_chunk_size=10)
        text = "이것은 충분히 긴 테스트 문서입니다."  # min_chunk_size 이상
        
        result = chunker.chunk_document(text, "test.txt")
        
        assert len(result) == 1
        assert result[0].content == text
        assert result[0].metadata.source_file == "test.txt"
        assert result[0].metadata.chunk_index == 0
    
    def test_chunk_too_short_text(self):
        """min_chunk_size 미만 텍스트는 빈 리스트 반환"""
        chunker = DocumentChunker(chunk_size=512, min_chunk_size=50)
        text = "짧음"  # 2자 < 50
        
        result = chunker.chunk_document(text, "test.txt")
        
        assert result == []
    
    def test_chunk_with_articles(self, sample_text):
        """조항 패턴이 있는 문서 청킹"""
        chunker = DocumentChunker(chunk_size=512)
        
        result = chunker.chunk_document(sample_text, "규정.hwp")
        
        # 청크가 생성되어야 함 (짧은 텍스트는 하나로 합쳐질 수 있음)
        assert len(result) >= 1
        
        # 메타데이터 확인
        for chunk in result:
            assert chunk.metadata.source_file == "규정.hwp"
            assert chunk.metadata.chunk_type in ("article", "text")
    
    def test_chunk_long_articles_separately(self):
        """긴 조항은 별도 청크로 분리"""
        # 각 조항이 충분히 긴 텍스트
        long_text = """
        제1조 (목적)
        이 규정은 문서 관리에 관한 사항을 정함을 목적으로 한다.
        본 규정의 목적은 다음과 같은 세부 사항을 포함한다.
        첫째, 모든 문서의 체계적인 관리를 위한 기준을 수립한다.
        둘째, 문서의 작성, 보관, 폐기에 관한 절차를 정한다.
        셋째, 관련 담당자의 역할과 책임을 명확히 한다.
        
        제2조 (정의)
        이 규정에서 사용하는 용어의 정의는 다음과 같다.
        문서란 업무상 작성 또는 취득한 모든 형태의 기록물을 말한다.
        기록물이란 공공기관이 업무와 관련하여 생산한 기록을 말한다.
        전자문서란 정보처리시스템에 의해 전자적 형태로 작성된 문서를 말한다.
        """
        chunker = DocumentChunker(chunk_size=200, min_chunk_size=50)
        
        result = chunker.chunk_document(long_text, "규정.hwp")
        
        # 여러 청크로 분리되어야 함
        assert len(result) >= 2
    
    def test_chunk_with_tables(self):
        """표 포함 문서 청킹"""
        chunker = DocumentChunker(min_chunk_size=20)
        text = "본문 내용입니다." * 20  # min_chunk_size 이상
        # 표도 min_chunk_size 이상이어야 함
        tables = ["| 항목 | 값 | 설명 |\n|------|----|---------|\n| A | 1 | 첫번째 항목 |\n| B | 2 | 두번째 항목 |"]
        
        result = chunker.chunk_document(text, "test.txt", tables=tables)
        
        # 표 청크가 포함되어야 함
        table_chunks = [c for c in result if c.metadata.has_table]
        assert len(table_chunks) >= 1
    
    def test_split_by_articles(self):
        """조항별 분리 테스트"""
        chunker = DocumentChunker()
        
        # 조항 패턴이 명확한 텍스트
        text_with_articles = """
제1조 (목적)
이 규정은 문서 관리에 관한 사항을 정한다.

제2조 (정의)
이 규정에서 사용하는 용어의 정의는 다음과 같다.

제3조 (적용범위)
이 규정은 모든 부서에 적용된다.
"""
        articles = chunker._split_by_articles(text_with_articles)
        
        # 최소 2개 조항이 분리되어야 함
        assert len(articles) >= 2
        
        # 조항 제목 확인
        titles = [title for title, _ in articles]
        assert any("제1조" in t for t in titles)
        assert any("제2조" in t for t in titles)
    
    def test_split_into_paragraphs(self):
        """단락 분리 테스트"""
        chunker = DocumentChunker()
        text = "첫 번째 단락\n\n두 번째 단락\n\n세 번째 단락"
        
        result = chunker._split_into_paragraphs(text)
        
        assert len(result) == 3
        assert result[0] == "첫 번째 단락"
        assert result[1] == "두 번째 단락"
        assert result[2] == "세 번째 단락"


class TestChunkDocument:
    """chunk_document 편의 함수 테스트"""
    
    def test_basic_chunking(self):
        """기본 청킹 테스트"""
        text = "테스트 문서입니다. " * 100
        
        result = chunk_document(text, "test.txt")
        
        assert len(result) >= 1
        assert all(isinstance(c, Chunk) for c in result)
    
    def test_empty_text_returns_empty_list(self):
        """빈 텍스트는 빈 리스트 반환"""
        result = chunk_document("", "test.txt")
        assert result == []
        
        result = chunk_document("   ", "test.txt")
        assert result == []


class TestChunksToDict:
    """chunks_to_dict 함수 테스트"""
    
    def test_conversion(self):
        """청크를 딕셔너리로 변환"""
        chunks = [
            Chunk(
                content="테스트 내용",
                metadata=ChunkMetadata(
                    source_file="test.txt",
                    chunk_index=0,
                    chunk_type="text",
                ),
            )
        ]
        
        result = chunks_to_dict(chunks)
        
        assert len(result) == 1
        assert result[0]["content"] == "테스트 내용"
        assert result[0]["metadata"]["source_file"] == "test.txt"
        assert result[0]["metadata"]["chunk_index"] == 0
    
    def test_empty_list(self):
        """빈 리스트 변환"""
        result = chunks_to_dict([])
        assert result == []
