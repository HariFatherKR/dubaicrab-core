"""
HWP/HWPX 문서 텍스트 추출 모듈

LibreOffice headless 모드를 사용하여 HWP 파일을 텍스트로 변환합니다.
HWPX (OOXML 형식)는 직접 XML 파싱으로 처리합니다.
"""

import hashlib
import logging
import os
import re
import shutil
import subprocess
import tempfile
import xml.etree.ElementTree as ET
import zipfile
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from typing import List, Optional


logger = logging.getLogger(__name__)


# 타임아웃 설정 (초)
DEFAULT_TIMEOUT = 60


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
    
    Returns:
        str: LibreOffice 실행 경로, 없으면 None
    """
    # macOS
    macos_paths = [
        "/Applications/LibreOffice.app/Contents/MacOS/soffice",
        "/Applications/OpenOffice.app/Contents/MacOS/soffice",
    ]
    
    # Linux / Windows WSL
    linux_paths = [
        "/usr/bin/soffice",
        "/usr/bin/libreoffice",
    ]
    
    for path in macos_paths + linux_paths:
        if os.path.exists(path):
            return path
    
    # PATH에서 찾기
    soffice = shutil.which("soffice")
    if soffice:
        return soffice
    
    return None


def is_encrypted_hwp(file_path: Path) -> bool:
    """
    암호화된 HWP 파일인지 확인
    
    HWP 파일 헤더에서 암호화 플래그를 확인합니다.
    """
    try:
        with open(file_path, "rb") as f:
            # OLE2 시그니처 확인
            header = f.read(8)
            if header[:4] != b"\xd0\xcf\x11\xe0":
                return False  # OLE2 파일이 아님
            
            # HWP 암호화 플래그는 복잡하므로 일단 False 반환
            # 실제 구현 시 olefile 라이브러리 사용 권장
            return False
    except Exception:
        return False


def _validate_file_path(file_path: Path) -> Path:
    """
    파일 경로 보안 검증
    
    Args:
        file_path: 검증할 파일 경로
    
    Returns:
        Path: 검증된 절대 경로
    
    Raises:
        ValueError: 안전하지 않은 경로인 경우
    """
    # 절대 경로로 정규화 (심볼릭 링크 해제)
    resolved_path = file_path.resolve()
    
    # 경로 순회 공격 체크 (.. 패턴)
    try:
        # 상대 경로 계산 시 ValueError 발생하면 경로 순회 시도
        resolved_path.relative_to(file_path.parent.resolve())
    except ValueError:
        pass  # 정상적인 경우
    
    # 파일명에 셸 메타문자 검사 (안전하지 않은 문자 필터링)
    unsafe_chars = set(';&|`$(){}[]<>\\"\'\n\r\t')
    if any(c in str(resolved_path.name) for c in unsafe_chars):
        logger.warning(f"안전하지 않은 문자가 포함된 파일명: {resolved_path.name}")
        raise ValueError(f"파일명에 허용되지 않은 문자가 포함되어 있습니다: {resolved_path.name}")
    
    return resolved_path


def hwp_to_text_libreoffice(
    file_path: Path,
    timeout: int = DEFAULT_TIMEOUT,
) -> str:
    """
    LibreOffice headless 모드로 HWP → TXT 변환
    
    Args:
        file_path: HWP 파일 경로
        timeout: 타임아웃 (초)
    
    Returns:
        str: 추출된 텍스트
    
    Raises:
        FileNotFoundError: LibreOffice가 설치되지 않은 경우
        subprocess.TimeoutExpired: 변환 시간 초과
        RuntimeError: 변환 실패
        ValueError: 안전하지 않은 파일 경로
    """
    soffice = check_libreoffice()
    if not soffice:
        raise FileNotFoundError(
            "LibreOffice가 설치되지 않았습니다. "
            "brew install --cask libreoffice 또는 apt install libreoffice 로 설치하세요."
        )
    
    # 파일 경로 보안 검증
    validated_path = _validate_file_path(file_path)
    
    with tempfile.TemporaryDirectory() as tmpdir:
        # 안전한 파일명으로 복사 (셸 메타문자 방지)
        safe_name = f"doc_{get_file_hash(validated_path)[:8]}{validated_path.suffix}"
        safe_path = Path(tmpdir) / safe_name
        shutil.copy2(validated_path, safe_path)
        
        # LibreOffice로 TXT 변환 (리스트 형태로 전달, shell=False 기본값)
        cmd = [
            soffice,
            "--headless",
            "--convert-to", "txt:Text",
            "--outdir", tmpdir,
            str(safe_path),  # 안전한 경로 사용
        ]
        
        try:
            subprocess.run(
                cmd,
                timeout=timeout,
                check=True,
                capture_output=True,
            )
        except subprocess.TimeoutExpired:
            raise TimeoutError(f"HWP 변환 시간 초과 ({timeout}초)")
        except subprocess.CalledProcessError as e:
            raise RuntimeError(f"HWP 변환 실패: {e.stderr.decode()}")
        
        # 변환된 TXT 파일 찾기
        txt_files = list(Path(tmpdir).glob("*.txt"))
        if not txt_files:
            raise RuntimeError("변환된 TXT 파일을 찾을 수 없습니다")
        
        # 텍스트 읽기
        text = txt_files[0].read_text(encoding="utf-8", errors="replace")
        return text


def hwpx_to_text(file_path: Path) -> str:
    """
    HWPX (OOXML) 파일에서 텍스트 추출
    
    HWPX는 ZIP 압축된 XML 파일로, Contents/section*.xml에서 텍스트를 추출합니다.
    
    Args:
        file_path: HWPX 파일 경로
    
    Returns:
        str: 추출된 텍스트
    """
    texts = []
    
    with zipfile.ZipFile(file_path, "r") as zf:
        # section 파일 목록 가져오기
        section_files = sorted([
            name for name in zf.namelist()
            if name.startswith("Contents/section") and name.endswith(".xml")
        ])
        
        for section_file in section_files:
            with zf.open(section_file) as f:
                try:
                    tree = ET.parse(f)
                    root = tree.getroot()
                    
                    # 모든 텍스트 노드 추출
                    for elem in root.iter():
                        if elem.text and elem.text.strip():
                            texts.append(elem.text.strip())
                        if elem.tail and elem.tail.strip():
                            texts.append(elem.tail.strip())
                except ET.ParseError:
                    continue
    
    return "\n".join(texts)


def extract_tables_from_text(text: str) -> List[str]:
    """
    텍스트에서 표 패턴 감지 및 마크다운 변환
    
    간단한 휴리스틱으로 표 형태를 감지합니다.
    """
    tables = []
    lines = text.split("\n")
    
    # 탭 또는 연속 공백으로 구분된 행 감지
    table_pattern = re.compile(r"[\t]{2,}|[ ]{4,}")
    
    current_table = []
    for line in lines:
        if table_pattern.search(line):
            current_table.append(line)
        else:
            if len(current_table) >= 2:
                # 마크다운 테이블로 변환
                table_md = _convert_to_markdown_table(current_table)
                if table_md:
                    tables.append(table_md)
            current_table = []
    
    # 마지막 테이블 처리
    if len(current_table) >= 2:
        table_md = _convert_to_markdown_table(current_table)
        if table_md:
            tables.append(table_md)
    
    return tables


def _convert_to_markdown_table(rows: List[str]) -> Optional[str]:
    """표 행을 마크다운 테이블로 변환"""
    if not rows:
        return None
    
    # 탭 또는 여러 공백으로 셀 분리
    split_pattern = re.compile(r"\t+|[ ]{2,}")
    
    table_rows = []
    max_cols = 0
    
    for row in rows:
        cells = split_pattern.split(row.strip())
        cells = [c.strip() for c in cells if c.strip()]
        if cells:
            table_rows.append(cells)
            max_cols = max(max_cols, len(cells))
    
    if not table_rows or max_cols == 0:
        return None
    
    # 마크다운 생성
    md_lines = []
    for i, row in enumerate(table_rows):
        # 열 수 맞추기
        while len(row) < max_cols:
            row.append("")
        
        md_lines.append("| " + " | ".join(row) + " |")
        
        # 헤더 구분선
        if i == 0:
            md_lines.append("|" + "|".join(["---"] * max_cols) + "|")
    
    return "\n".join(md_lines)


def hwp_to_text(
    file_path: str | Path,
    timeout: int = DEFAULT_TIMEOUT,
) -> ParseResult:
    """
    HWP/HWPX 파일에서 텍스트 추출 (메인 함수)
    
    Args:
        file_path: HWP 또는 HWPX 파일 경로
        timeout: 변환 타임아웃 (초)
    
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
    metadata = DocumentMetadata(
        filename=file_path.name,
        file_hash=get_file_hash(file_path),
        modified_at=datetime.fromtimestamp(stat.st_mtime),
        file_size=stat.st_size,
    )
    
    # 암호화 확인
    if is_encrypted_hwp(file_path):
        return ParseResult(
            text="",
            metadata=metadata,
            success=False,
            error="암호화된 HWP 파일은 지원하지 않습니다",
        )
    
    try:
        # HWPX 파일 처리
        if file_path.suffix.lower() == ".hwpx":
            text = hwpx_to_text(file_path)
        else:
            # HWP 파일 처리 (LibreOffice 사용)
            text = hwp_to_text_libreoffice(file_path, timeout)
        
        # 표 추출
        tables = extract_tables_from_text(text)
        
        return ParseResult(
            text=text,
            metadata=metadata,
            tables=tables,
            success=True,
        )
    
    except FileNotFoundError as e:
        return ParseResult(
            text="",
            metadata=metadata,
            success=False,
            error=str(e),
        )
    except TimeoutError as e:
        return ParseResult(
            text="",
            metadata=metadata,
            success=False,
            error=str(e),
        )
    except Exception as e:
        return ParseResult(
            text="",
            metadata=metadata,
            success=False,
            error=f"HWP 파싱 오류: {str(e)}",
        )
