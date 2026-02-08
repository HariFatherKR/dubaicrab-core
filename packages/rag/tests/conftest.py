"""pytest 공통 설정 및 픽스처"""

import tempfile
from pathlib import Path

import pytest


@pytest.fixture
def temp_dir():
    """임시 디렉토리 픽스처"""
    with tempfile.TemporaryDirectory() as tmpdir:
        yield Path(tmpdir)


@pytest.fixture
def sample_text():
    """샘플 텍스트 픽스처"""
    return """
    제1조 (목적)
    이 규정은 문서 관리에 관한 사항을 정함을 목적으로 한다.
    
    제2조 (정의)
    이 규정에서 사용하는 용어의 정의는 다음과 같다.
    1. "문서"란 업무상 작성 또는 취득한 문서를 말한다.
    2. "기록물"이란 공공기관이 업무와 관련하여 생산한 기록을 말한다.
    
    제3조 (적용범위)
    이 규정은 모든 부서에 적용된다.
    """


@pytest.fixture
def sample_hwp_content():
    """샘플 HWP 추출 텍스트 픽스처"""
    return """
    두바이 관광 안내서
    
    1. 개요
    두바이는 아랍에미리트의 대표적인 관광도시입니다.
    
    2. 주요 관광지
    가. 부르즈 칼리파
    나. 팜 주메이라
    다. 두바이 몰
    
    3. 여행 시 주의사항
    현지 법규를 준수해야 합니다.
    """
