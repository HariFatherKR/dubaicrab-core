"""
벡터 인덱싱 모듈

문서 → 청크 → 임베딩 → Chroma 저장 파이프라인
"""

import hashlib
import logging
import os
from pathlib import Path
from typing import Callable, List, Optional, Set

from .chunker import Chunk, chunk_document, chunks_to_dict
from .embeddings import get_embedder
from .parsers import hwp_to_text, ParseResult
from .vector_store import get_client, get_or_create_collection, DEFAULT_COLLECTION_NAME


logger = logging.getLogger(__name__)


# 지원 파일 확장자
SUPPORTED_EXTENSIONS = {".hwp", ".hwpx", ".txt"}

# 최대 파일 크기 (100MB)
MAX_FILE_SIZE = 100 * 1024 * 1024


def validate_file_path(
    file_path: Path,
    base_dir: Optional[Path] = None,
) -> Path:
    """
    파일 경로 보안 검증
    
    Args:
        file_path: 검증할 파일 경로
        base_dir: 허용할 기본 디렉토리 (None이면 제한 없음)
    
    Returns:
        Path: 정규화된 안전한 경로
    
    Raises:
        ValueError: 허용되지 않은 경로
        FileNotFoundError: 파일이 존재하지 않음
    """
    # 절대 경로로 정규화 (심볼릭 링크 해제, .. 처리)
    resolved = Path(os.path.realpath(file_path))
    
    # 파일 존재 확인
    if not resolved.exists():
        raise FileNotFoundError(f"파일을 찾을 수 없습니다: {resolved}")
    
    # 경로 순회 공격 방지: base_dir이 지정된 경우 해당 디렉토리 내 파일만 허용
    if base_dir is not None:
        base_resolved = Path(os.path.realpath(base_dir))
        try:
            resolved.relative_to(base_resolved)
        except ValueError:
            raise ValueError(
                f"경로 순회 공격 감지: {file_path} 는 "
                f"허용된 디렉토리({base_resolved}) 외부입니다"
            )
    
    # 확장자 검증
    if resolved.suffix.lower() not in SUPPORTED_EXTENSIONS:
        raise ValueError(f"지원하지 않는 파일 형식: {resolved.suffix}")
    
    # 파일 크기 검증
    if resolved.stat().st_size > MAX_FILE_SIZE:
        raise ValueError(
            f"파일 크기 초과: {resolved.stat().st_size} > {MAX_FILE_SIZE} bytes"
        )
    
    return resolved


def validate_directory_path(dir_path: Path) -> Path:
    """
    디렉토리 경로 보안 검증
    
    Args:
        dir_path: 검증할 디렉토리 경로
    
    Returns:
        Path: 정규화된 안전한 경로
    
    Raises:
        ValueError: 디렉토리가 아닌 경우
    """
    # 절대 경로로 정규화
    resolved = Path(os.path.realpath(dir_path))
    
    if not resolved.is_dir():
        raise ValueError(f"디렉토리가 아닙니다: {resolved}")
    
    return resolved


def get_document_hash(file_path: Path) -> str:
    """파일 해시 계산"""
    sha256 = hashlib.sha256()
    with open(file_path, "rb") as f:
        for chunk in iter(lambda: f.read(8192), b""):
            sha256.update(chunk)
    return sha256.hexdigest()[:16]  # 짧게 잘라서 ID로 사용


def parse_document(file_path: Path) -> ParseResult:
    """
    파일 유형에 따라 적절한 파서 호출
    """
    suffix = file_path.suffix.lower()
    
    if suffix in (".hwp", ".hwpx"):
        return hwp_to_text(file_path)
    elif suffix == ".txt":
        # 텍스트 파일 직접 읽기
        try:
            text = file_path.read_text(encoding="utf-8")
            from .parsers.hwp_parser import DocumentMetadata
            return ParseResult(
                text=text,
                metadata=DocumentMetadata(
                    filename=file_path.name,
                    file_hash=get_document_hash(file_path),
                ),
                success=True,
            )
        except Exception as e:
            from .parsers.hwp_parser import DocumentMetadata
            return ParseResult(
                text="",
                metadata=DocumentMetadata(
                    filename=file_path.name,
                    file_hash="",
                ),
                success=False,
                error=str(e),
            )
    else:
        from .parsers.hwp_parser import DocumentMetadata
        return ParseResult(
            text="",
            metadata=DocumentMetadata(
                filename=file_path.name,
                file_hash="",
            ),
            success=False,
            error=f"지원하지 않는 파일 형식: {suffix}",
        )


def index_document(
    file_path: str | Path,
    collection_name: str = DEFAULT_COLLECTION_NAME,
    chunk_size: int = 512,
    overlap: int = 50,
    base_dir: Optional[Path] = None,
    progress_callback: Optional[Callable[[str, int, int], None]] = None,
) -> dict:
    """
    단일 문서 인덱싱
    
    Args:
        file_path: 문서 파일 경로
        collection_name: Chroma 컬렉션 이름
        chunk_size: 청크 크기
        overlap: 오버랩 크기
        base_dir: 허용할 기본 디렉토리 (보안용, None이면 제한 없음)
        progress_callback: 진행률 콜백 (message, current, total)
    
    Returns:
        dict: 인덱싱 결과
            - success: 성공 여부
            - file: 파일명
            - chunks_indexed: 인덱싱된 청크 수
            - error: 에러 메시지 (실패 시)
    """
    file_path = Path(file_path)
    
    # 경로 보안 검증
    try:
        file_path = validate_file_path(file_path, base_dir)
    except (ValueError, FileNotFoundError) as e:
        logger.warning(f"파일 경로 검증 실패: {file_path} - {e}")
        return {
            "success": False,
            "file": str(file_path),
            "chunks_indexed": 0,
            "error": str(e),
        }
    
    logger.info(f"인덱싱 시작: {file_path.name}")
    
    # 1. 문서 파싱
    if progress_callback:
        progress_callback(f"파싱 중: {file_path.name}", 0, 3)
    
    parse_result = parse_document(file_path)
    
    if not parse_result.success:
        return {
            "success": False,
            "file": file_path.name,
            "chunks_indexed": 0,
            "error": parse_result.error,
        }
    
    if not parse_result.text.strip():
        return {
            "success": False,
            "file": file_path.name,
            "chunks_indexed": 0,
            "error": "추출된 텍스트가 없습니다",
        }
    
    # 2. 청킹
    if progress_callback:
        progress_callback(f"청킹 중: {file_path.name}", 1, 3)
    
    chunks = chunk_document(
        text=parse_result.text,
        source_file=file_path.name,
        tables=parse_result.tables,
        chunk_size=chunk_size,
        overlap=overlap,
    )
    
    if not chunks:
        return {
            "success": False,
            "file": file_path.name,
            "chunks_indexed": 0,
            "error": "생성된 청크가 없습니다",
        }
    
    # 3. 임베딩 및 저장
    if progress_callback:
        progress_callback(f"인덱싱 중: {file_path.name}", 2, 3)
    
    try:
        # Chroma 클라이언트 및 컬렉션 가져오기
        client = get_client()
        collection = get_or_create_collection(client, collection_name)
        
        # 임베딩 생성
        embedder = get_embedder()
        texts = [chunk.content for chunk in chunks]
        embeddings = embedder.embed_documents(texts)
        
        # 문서 해시 (중복 체크용)
        doc_hash = parse_result.metadata.file_hash
        
        # Chroma에 저장
        ids = [f"{doc_hash}_{i}" for i in range(len(chunks))]
        metadatas = [
            {
                "source_file": chunk.metadata.source_file,
                "chunk_index": chunk.metadata.chunk_index,
                "section_title": chunk.metadata.section_title or "",
                "has_table": chunk.metadata.has_table,
                "chunk_type": chunk.metadata.chunk_type,
                "doc_hash": doc_hash,
            }
            for chunk in chunks
        ]
        
        # 기존 문서 삭제 (업데이트 시)
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
        
        # 새 청크 추가
        collection.add(
            ids=ids,
            documents=texts,
            embeddings=embeddings,
            metadatas=metadatas,
        )
        
        if progress_callback:
            progress_callback(f"완료: {file_path.name}", 3, 3)
        
        return {
            "success": True,
            "file": file_path.name,
            "chunks_indexed": len(chunks),
        }
    
    except Exception as e:
        logger.exception(f"인덱싱 실패: {file_path}")
        return {
            "success": False,
            "file": file_path.name,
            "chunks_indexed": 0,
            "error": str(e),
        }


def index_directory(
    dir_path: str | Path,
    collection_name: str = DEFAULT_COLLECTION_NAME,
    recursive: bool = True,
    chunk_size: int = 512,
    overlap: int = 50,
    max_retries: int = 3,
    progress_callback: Optional[Callable[[str, int, int], None]] = None,
) -> dict:
    """
    디렉토리 내 모든 문서 인덱싱
    
    Args:
        dir_path: 디렉토리 경로
        collection_name: Chroma 컬렉션 이름
        recursive: 하위 디렉토리 포함 여부
        chunk_size: 청크 크기
        overlap: 오버랩 크기
        max_retries: 최대 재시도 횟수
        progress_callback: 진행률 콜백
    
    Returns:
        dict: 인덱싱 결과 요약
    """
    # 디렉토리 경로 검증
    try:
        dir_path = validate_directory_path(Path(dir_path))
    except ValueError as e:
        return {
            "success": False,
            "total_files": 0,
            "indexed_files": 0,
            "failed_files": 0,
            "total_chunks": 0,
            "errors": [str(e)],
        }
    
    # 대상 파일 수집
    if recursive:
        files = [
            f for f in dir_path.rglob("*")
            if f.suffix.lower() in SUPPORTED_EXTENSIONS
        ]
    else:
        files = [
            f for f in dir_path.glob("*")
            if f.suffix.lower() in SUPPORTED_EXTENSIONS
        ]
    
    total = len(files)
    indexed = 0
    failed = 0
    total_chunks = 0
    errors: List[str] = []
    
    for i, file_path in enumerate(files):
        if progress_callback:
            progress_callback(f"인덱싱: {file_path.name}", i, total)
        
        # 재시도 로직
        for attempt in range(max_retries):
            result = index_document(
                file_path,
                collection_name=collection_name,
                chunk_size=chunk_size,
                overlap=overlap,
                base_dir=dir_path,  # 경로 순회 공격 방지
            )
            
            if result["success"]:
                indexed += 1
                total_chunks += result["chunks_indexed"]
                break
            elif attempt < max_retries - 1:
                logger.warning(
                    f"재시도 {attempt + 1}/{max_retries}: {file_path.name}"
                )
            else:
                failed += 1
                errors.append(f"{file_path.name}: {result.get('error', '알 수 없는 오류')}")
    
    if progress_callback:
        progress_callback("완료", total, total)
    
    return {
        "success": failed == 0,
        "total_files": total,
        "indexed_files": indexed,
        "failed_files": failed,
        "total_chunks": total_chunks,
        "errors": errors,
    }


def get_indexed_documents(collection_name: str = DEFAULT_COLLECTION_NAME) -> Set[str]:
    """
    인덱싱된 문서 목록 조회
    
    Returns:
        Set[str]: 인덱싱된 파일명 집합
    """
    client = get_client()
    
    try:
        collection = client.get_collection(collection_name)
        result = collection.get(include=["metadatas"])
        
        files = set()
        for metadata in result.get("metadatas", []):
            if metadata and "source_file" in metadata:
                files.add(metadata["source_file"])
        
        return files
    except Exception:
        return set()
