"""
HWP/HWPX 문서 텍스트 추출 모듈

hwpparser 패키지를 사용한 래퍼 모듈입니다.
기존 인터페이스(ParseResult, DocumentMetadata)를 유지하면서
hwpparser의 기능을 활용합니다.
"""

import hashlib
import logging
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from typing import List, Optional

import hwpparser
from hwpparser import HWPParserError


logger = logging.getLogger(__name__)


@dataclass
class DocumentMetadata:
    """문서 메타데이터"""
    filename: str
    file_hash: str
    created_at: Optional[datetime] = None
    modified_at: Optional[datetime] = None
    author: Optional[str] = None
    title: Optional[str] = None
    file_size: int = 0


@dataclass
class ParseResult:
    """파싱 결과"""
    text: str
    metadata: DocumentMetadata
    tables: List[str] = field(default_factory=list)
    success: bool = True
    error: Optional[str] = None


def get_file_hash(file_path: Path) -> str:
    """파일 해시 계산 (SHA256)"""
    sha256 = hashlib.sha256()
    with open(file_path, "rb") as f:
        for chunk in iter(lambda: f.read(8192), b""):
            sha256.update(chunk)
    return sha256.hexdigest()


def check_libreoffice() -> Optional[str]:
    """
    LibreOffice 실행 경로 확인
    
    hwpparser 내부에서 처리하므로 호환성을 위해 유지.
    Returns:
        str: LibreOffice 실행 경로, 없으면 None
    """
    # hwpparser가 내부적으로 처리하므로 간단히 확인만
    import shutil
    import os
    
    paths = [
        "/Applications/LibreOffice.app/Contents/MacOS/soffice",
        "/usr/bin/soffice",
        "/usr/bin/libreoffice",
    ]
    
    for path in paths:
        if os.path.exists(path):
            return path
    
    return shutil.which("soffice")


def hwpx_to_text(file_path: Path) -> str:
    """
    HWPX 파일에서 텍스트 추출 (hwpparser 사용)
    
    Args:
        file_path: HWPX 파일 경로
    
    Returns:
        str: 추출된 텍스트
    """
    return hwpparser.hwp_to_text(file_path)


def hwp_to_text(
    file_path: str | Path,
    timeout: int = 60,
) -> ParseResult:
    """
    HWP/HWPX 파일에서 텍스트 추출 (메인 함수)
    
    hwpparser 패키지를 사용하여 텍스트를 추출합니다.
    
    Args:
        file_path: HWP 또는 HWPX 파일 경로
        timeout: 변환 타임아웃 (초) - hwpparser에서 내부 처리
    
    Returns:
        ParseResult: 파싱 결과 (텍스트, 메타데이터, 표, 에러)
    """
    file_path = Path(file_path)
    
    if not file_path.exists():
        return ParseResult(
            text="",
            metadata=DocumentMetadata(
                filename=file_path.name,
                file_hash="",
            ),
            success=False,
            error=f"파일을 찾을 수 없습니다: {file_path}",
        )
    
    # 메타데이터 수집
    stat = file_path.stat()
    file_hash = get_file_hash(file_path)
    
    metadata = DocumentMetadata(
        filename=file_path.name,
        file_hash=file_hash,
        modified_at=datetime.fromtimestamp(stat.st_mtime),
        file_size=stat.st_size,
    )
    
    try:
        # hwpparser로 텍스트 추출
        text = hwpparser.hwp_to_text(file_path)
        
        # hwpparser의 메타데이터도 가져오기
        try:
            hwp_meta = hwpparser.extract_metadata(file_path)
            if hwp_meta.get("title"):
                metadata.title = hwp_meta["title"]
            if hwp_meta.get("author"):
                metadata.author = hwp_meta["author"]
        except Exception:
            pass  # 메타데이터 추출 실패해도 계속 진행
        
        return ParseResult(
            text=text,
            metadata=metadata,
            tables=[],  # hwpparser는 표를 별도로 분리하지 않음
            success=True,
        )
    
    except hwpparser.HWPFileNotFoundError as e:
        return ParseResult(
            text="",
            metadata=metadata,
            success=False,
            error=f"파일을 찾을 수 없습니다: {e}",
        )
    except hwpparser.DependencyError as e:
        return ParseResult(
            text="",
            metadata=metadata,
            success=False,
            error=f"의존성 오류 (LibreOffice 또는 pyhwp 필요): {e}",
        )
    except HWPParserError as e:
        return ParseResult(
            text="",
            metadata=metadata,
            success=False,
            error=f"HWP 파싱 오류: {e}",
        )
    except Exception as e:
        logger.exception(f"HWP 파싱 중 예외 발생: {file_path}")
        return ParseResult(
            text="",
            metadata=metadata,
            success=False,
            error=f"HWP 파싱 오류: {str(e)}",
        )
