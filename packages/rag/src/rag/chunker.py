"""
문서 청킹 모듈

공문서 특화 청킹 전략:
- 조항별 분리 (제1조, 제2조...)
- 항목 리스트 분리 (1., 2., 가., 나.)
- 표는 별도 청크로 분리

hwpparser 패키지와 통합하여 HWP 파일 직접 청킹도 지원합니다.
"""

import re
from dataclasses import dataclass, field
from pathlib import Path
from typing import List, Optional, Union

import hwpparser
from hwpparser import TextChunk as HWPTextChunk


# 기본 설정
DEFAULT_CHUNK_SIZE = 512
DEFAULT_OVERLAP = 50
MIN_CHUNK_SIZE = 50
MAX_CHUNK_SIZE = 2000


@dataclass
class ChunkMetadata:
    """청크 메타데이터"""
    source_file: str                    # 원본 파일명
    chunk_index: int                    # 청크 순서 (0-indexed)
    page_number: Optional[int] = None   # 페이지 번호 (가능시)
    section_title: Optional[str] = None # 섹션 제목
    has_table: bool = False             # 표 포함 여부
    chunk_type: str = "text"            # 청크 유형 (text, table, article)


@dataclass
class Chunk:
    """청크 데이터"""
    content: str
    metadata: ChunkMetadata
    
    def __len__(self) -> int:
        return len(self.content)


class DocumentChunker:
    """
    문서 청킹 클래스
    
    공문서 특화 기능:
    - 조항 패턴 인식
    - 리스트 항목 분리
    - 표 별도 처리
    """
    
    # 조항 패턴 (제1조, 제2조, ...)
    ARTICLE_PATTERN = re.compile(r"^(제\s*\d+\s*조)[^\n]*", re.MULTILINE)
    
    def __init__(
        self,
        chunk_size: int = DEFAULT_CHUNK_SIZE,
        overlap: int = DEFAULT_OVERLAP,
        min_chunk_size: int = MIN_CHUNK_SIZE,
        max_chunk_size: int = MAX_CHUNK_SIZE,
    ):
        """
        Args:
            chunk_size: 기본 청크 크기 (문자 수)
            overlap: 청크 간 오버랩 (문자 수)
            min_chunk_size: 최소 청크 크기
            max_chunk_size: 최대 청크 크기
        """
        self.chunk_size = chunk_size
        self.overlap = overlap
        self.min_chunk_size = min_chunk_size
        self.max_chunk_size = max_chunk_size
    
    def chunk_document(
        self,
        text: str,
        source_file: str,
        tables: Optional[List[str]] = None,
    ) -> List[Chunk]:
        """
        문서를 청크로 분할
        
        Args:
            text: 문서 텍스트
            source_file: 원본 파일명
            tables: 추출된 표 목록 (마크다운 형식)
        
        Returns:
            List[Chunk]: 청크 목록 (빈 텍스트 시 빈 리스트 반환)
        """
        # 빈 텍스트 검증
        if not text or not text.strip():
            return []
        
        chunks: List[Chunk] = []
        
        # 1. 조항별 분리 시도
        articles = self._split_by_articles(text)
        
        if articles:
            # 조항이 있으면 조항별로 처리
            for i, (title, content) in enumerate(articles):
                article_chunks = self._chunk_text(
                    content,
                    source_file,
                    section_title=title,
                    chunk_type="article",
                    start_index=len(chunks),
                )
                chunks.extend(article_chunks)
        else:
            # 조항이 없으면 일반 텍스트 청킹
            text_chunks = self._chunk_text(
                text,
                source_file,
                chunk_type="text",
                start_index=0,
            )
            chunks.extend(text_chunks)
        
        # 2. 표 청크 추가
        if tables:
            for table in tables:
                if len(table) >= self.min_chunk_size:
                    chunks.append(Chunk(
                        content=table,
                        metadata=ChunkMetadata(
                            source_file=source_file,
                            chunk_index=len(chunks),
                            has_table=True,
                            chunk_type="table",
                        ),
                    ))
        
        return chunks
    
    def _split_by_articles(self, text: str) -> List[tuple[str, str]]:
        """
        조항별로 텍스트 분리
        
        Returns:
            List[tuple[str, str]]: [(조항 제목, 내용), ...]
        """
        matches = list(self.ARTICLE_PATTERN.finditer(text))
        
        if len(matches) < 2:
            return []
        
        articles = []
        for i, match in enumerate(matches):
            title = match.group(0).strip()
            start = match.end()
            
            # 다음 조항까지 또는 끝까지
            if i + 1 < len(matches):
                end = matches[i + 1].start()
            else:
                end = len(text)
            
            content = text[start:end].strip()
            if content:
                articles.append((title, content))
        
        return articles
    
    def _chunk_text(
        self,
        text: str,
        source_file: str,
        section_title: Optional[str] = None,
        chunk_type: str = "text",
        start_index: int = 0,
    ) -> List[Chunk]:
        """
        텍스트를 청크로 분할
        
        문장 또는 단락 경계에서 분할을 시도합니다.
        """
        # 빈 텍스트 처리
        text = text.strip()
        if not text:
            return []
        
        # 작은 텍스트는 그대로 반환
        if len(text) <= self.chunk_size:
            if len(text) < self.min_chunk_size:
                return []
            return [Chunk(
                content=text,
                metadata=ChunkMetadata(
                    source_file=source_file,
                    chunk_index=start_index,
                    section_title=section_title,
                    chunk_type=chunk_type,
                ),
            )]
        
        chunks = []
        
        # 단락으로 분리 시도
        paragraphs = self._split_into_paragraphs(text)
        
        current_chunk = ""
        chunk_index = start_index
        
        for para in paragraphs:
            # 현재 청크에 추가 가능한지 확인
            if len(current_chunk) + len(para) + 1 <= self.chunk_size:
                if current_chunk:
                    current_chunk += "\n\n" + para
                else:
                    current_chunk = para
            else:
                # 현재 청크 저장
                if current_chunk and len(current_chunk) >= self.min_chunk_size:
                    chunks.append(Chunk(
                        content=current_chunk,
                        metadata=ChunkMetadata(
                            source_file=source_file,
                            chunk_index=chunk_index,
                            section_title=section_title,
                            chunk_type=chunk_type,
                        ),
                    ))
                    chunk_index += 1
                
                # 새 청크 시작 (오버랩 적용)
                if self.overlap > 0 and current_chunk:
                    overlap_text = current_chunk[-self.overlap:]
                    current_chunk = overlap_text + "\n\n" + para
                else:
                    current_chunk = para
                
                # 단일 단락이 너무 길면 강제 분할
                while len(current_chunk) > self.max_chunk_size:
                    split_point = self._find_split_point(
                        current_chunk, self.chunk_size
                    )
                    
                    chunks.append(Chunk(
                        content=current_chunk[:split_point],
                        metadata=ChunkMetadata(
                            source_file=source_file,
                            chunk_index=chunk_index,
                            section_title=section_title,
                            chunk_type=chunk_type,
                        ),
                    ))
                    chunk_index += 1
                    
                    # 오버랩 적용
                    overlap_start = max(0, split_point - self.overlap)
                    current_chunk = current_chunk[overlap_start:]
        
        # 마지막 청크 저장
        if current_chunk and len(current_chunk) >= self.min_chunk_size:
            chunks.append(Chunk(
                content=current_chunk,
                metadata=ChunkMetadata(
                    source_file=source_file,
                    chunk_index=chunk_index,
                    section_title=section_title,
                    chunk_type=chunk_type,
                ),
            ))
        
        return chunks
    
    def _split_into_paragraphs(self, text: str) -> List[str]:
        """텍스트를 단락으로 분리"""
        # 빈 줄 2개 이상으로 분리
        paragraphs = re.split(r"\n\s*\n", text)
        return [p.strip() for p in paragraphs if p.strip()]
    
    def _find_split_point(self, text: str, target_size: int) -> int:
        """
        문장 경계에서 분할 지점 찾기
        """
        if len(text) <= target_size:
            return len(text)
        
        # 문장 종결 패턴
        sentence_end = re.compile(r"[.!?]\s+")
        
        # target_size 근처에서 문장 끝 찾기
        search_start = max(0, target_size - 100)
        search_end = min(len(text), target_size + 100)
        search_text = text[search_start:search_end]
        
        matches = list(sentence_end.finditer(search_text))
        
        if matches:
            # target_size에 가장 가까운 문장 끝 선택
            best_match = min(
                matches,
                key=lambda m: abs((search_start + m.end()) - target_size)
            )
            return search_start + best_match.end()
        
        # 문장 끝을 찾지 못하면 공백에서 분할
        space_pos = text.rfind(" ", target_size - 50, target_size + 50)
        if space_pos > 0:
            return space_pos + 1
        
        # 최후의 수단: target_size에서 강제 분할
        return target_size


def chunk_document(
    text: str,
    source_file: str,
    tables: Optional[List[str]] = None,
    chunk_size: int = DEFAULT_CHUNK_SIZE,
    overlap: int = DEFAULT_OVERLAP,
) -> List[Chunk]:
    """
    편의 함수: 문서 청킹
    
    Args:
        text: 문서 텍스트
        source_file: 원본 파일명
        tables: 추출된 표 목록
        chunk_size: 청크 크기
        overlap: 오버랩 크기
    
    Returns:
        List[Chunk]: 청크 목록
    """
    chunker = DocumentChunker(chunk_size=chunk_size, overlap=overlap)
    return chunker.chunk_document(text, source_file, tables)


def chunks_to_dict(chunks: List[Chunk]) -> List[dict]:
    """
    청크 목록을 딕셔너리 목록으로 변환 (JSON 출력용)
    """
    return [
        {
            "content": chunk.content,
            "metadata": {
                "source_file": chunk.metadata.source_file,
                "chunk_index": chunk.metadata.chunk_index,
                "page_number": chunk.metadata.page_number,
                "section_title": chunk.metadata.section_title,
                "has_table": chunk.metadata.has_table,
                "chunk_type": chunk.metadata.chunk_type,
            },
        }
        for chunk in chunks
    ]


# =============================================================================
# hwpparser 통합 함수들
# =============================================================================


def chunk_hwp_file(
    file_path: Union[str, Path],
    chunk_size: int = DEFAULT_CHUNK_SIZE,
    overlap: int = DEFAULT_OVERLAP,
    use_hwpparser_chunking: bool = False,
) -> List[Chunk]:
    """
    HWP 파일을 직접 청킹 (hwpparser 사용)
    
    Args:
        file_path: HWP/HWPX 파일 경로
        chunk_size: 청크 크기
        overlap: 오버랩 크기
        use_hwpparser_chunking: True면 hwpparser.hwp_to_chunks 사용,
                                False면 텍스트 추출 후 공문서 특화 청킹 사용
    
    Returns:
        List[Chunk]: 청크 목록
    """
    file_path = Path(file_path)
    
    if use_hwpparser_chunking:
        # hwpparser의 청킹 사용 (빠름, 일반적인 청킹)
        hwp_chunks = hwpparser.hwp_to_chunks(
            file_path,
            chunk_size=chunk_size,
            chunk_overlap=overlap,
        )
        return _convert_hwpparser_chunks(hwp_chunks, file_path.name)
    else:
        # 텍스트 추출 후 공문서 특화 청킹 (조항별 분리 등)
        text = hwpparser.hwp_to_text(file_path)
        return chunk_document(
            text=text,
            source_file=file_path.name,
            chunk_size=chunk_size,
            overlap=overlap,
        )


def _convert_hwpparser_chunks(
    hwp_chunks: List[HWPTextChunk],
    source_file: str,
) -> List[Chunk]:
    """
    hwpparser의 TextChunk를 RAG의 Chunk로 변환
    
    Args:
        hwp_chunks: hwpparser.TextChunk 목록
        source_file: 원본 파일명
    
    Returns:
        List[Chunk]: 변환된 Chunk 목록
    """
    chunks = []
    for hwp_chunk in hwp_chunks:
        chunk = Chunk(
            content=hwp_chunk.text,
            metadata=ChunkMetadata(
                source_file=source_file,
                chunk_index=hwp_chunk.index,
                chunk_type="text",
            ),
        )
        chunks.append(chunk)
    return chunks


def hwp_to_chunks_rag(
    file_path: Union[str, Path],
    chunk_size: int = DEFAULT_CHUNK_SIZE,
    overlap: int = DEFAULT_OVERLAP,
) -> List[Chunk]:
    """
    HWP 파일을 RAG 파이프라인용 청크로 변환 (공문서 특화)
    
    hwpparser로 텍스트를 추출한 후,
    공문서 특화 청킹 전략(조항별 분리)을 적용합니다.
    
    Args:
        file_path: HWP/HWPX 파일 경로
        chunk_size: 청크 크기
        overlap: 오버랩 크기
    
    Returns:
        List[Chunk]: 청크 목록
    """
    return chunk_hwp_file(
        file_path,
        chunk_size=chunk_size,
        overlap=overlap,
        use_hwpparser_chunking=False,  # 공문서 특화 청킹 사용
    )
