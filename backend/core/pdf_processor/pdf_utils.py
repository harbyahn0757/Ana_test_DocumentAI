"""
PDF 처리 공통 유틸리티 함수들

PDF 처리기들에서 공통으로 사용되는 기능들을 모음
"""

from pathlib import Path
from typing import Optional
import logging

logger = logging.getLogger(__name__)


class PDFUtils:
    """PDF 처리 관련 공통 유틸리티 클래스"""
    
    @staticmethod
    def get_page_count(file_path: Path) -> int:
        """
        PDF 파일의 총 페이지 수 반환
        
        여러 라이브러리를 시도하여 안정적으로 페이지 수를 확인합니다.
        우선순위: PyPDF2 → pdfplumber
        
        Args:
            file_path: PDF 파일 경로
            
        Returns:
            int: 총 페이지 수
            
        Raises:
            FileValidationError: 페이지 수 확인 실패 시
        """
        from .base import FileValidationError
        
        try:
            # 1순위: PyPDF2 사용 (가볍고 빠름)
            try:
                import PyPDF2
                with open(file_path, 'rb') as file:
                    pdf_reader = PyPDF2.PdfReader(file)
                    page_count = len(pdf_reader.pages)
                    logger.debug(f"PyPDF2로 페이지 수 확인: {page_count}페이지")
                    return page_count
            except ImportError:
                logger.debug("PyPDF2가 설치되지 않음, pdfplumber로 대체")
            except Exception as e:
                logger.warning(f"PyPDF2 처리 실패: {e}, pdfplumber로 대체")
            
            # 2순위: pdfplumber 사용 (더 안정적)
            try:
                import pdfplumber
                with pdfplumber.open(file_path) as pdf:
                    page_count = len(pdf.pages)
                    logger.debug(f"pdfplumber로 페이지 수 확인: {page_count}페이지")
                    return page_count
            except ImportError:
                raise FileValidationError(
                    "PyPDF2 또는 pdfplumber가 필요합니다", 
                    "pdf_utils", 
                    str(file_path)
                )
            except Exception as e:
                raise FileValidationError(
                    f"pdfplumber 처리 실패: {e}", 
                    "pdf_utils", 
                    str(file_path)
                )
                
        except Exception as e:
            if isinstance(e, FileValidationError):
                raise
            raise FileValidationError(f"페이지 수 확인 실패: {e}", "pdf_utils", str(file_path))
    
    @staticmethod
    def validate_pdf_file_basic(file_path: Path) -> bool:
        """
        PDF 파일 기본 유효성 검증
        
        각 라이브러리별 validate_file 메서드에서 공통으로 사용할 기본 검증
        
        Args:
            file_path: PDF 파일 경로
            
        Returns:
            bool: 기본 조건을 만족하는 PDF 파일 여부
        """
        try:
            # 파일 존재 여부 확인
            if not file_path.exists():
                logger.debug(f"파일이 존재하지 않음: {file_path}")
                return False
            
            # 파일 형태 확인
            if not file_path.is_file():
                logger.debug(f"디렉토리이거나 파일이 아님: {file_path}")
                return False
            
            # 확장자 확인
            if file_path.suffix.lower() != '.pdf':
                logger.debug(f"PDF 파일이 아님: {file_path}")
                return False
            
            # 파일 크기 확인 (0바이트 파일 제외)
            if file_path.stat().st_size == 0:
                logger.debug(f"빈 파일: {file_path}")
                return False
            
            # 기본적인 PDF 헤더 확인
            with open(file_path, 'rb') as file:
                header = file.read(8)
                if not header.startswith(b'%PDF-'):
                    logger.debug(f"올바른 PDF 헤더가 아님: {file_path}")
                    return False
            
            return True
            
        except Exception as e:
            logger.warning(f"기본 PDF 파일 검증 실패: {e}")
            return False
    
    @staticmethod
    def get_pdf_info(file_path: Path) -> Optional[dict]:
        """
        PDF 파일 기본 정보 추출
        
        Args:
            file_path: PDF 파일 경로
            
        Returns:
            dict: PDF 정보 (title, author, pages 등) 또는 None
        """
        try:
            import PyPDF2
            
            with open(file_path, 'rb') as file:
                pdf_reader = PyPDF2.PdfReader(file)
                
                info = {
                    'pages': len(pdf_reader.pages),
                    'title': pdf_reader.metadata.title if pdf_reader.metadata else None,
                    'author': pdf_reader.metadata.author if pdf_reader.metadata else None,
                    'creator': pdf_reader.metadata.creator if pdf_reader.metadata else None,
                    'producer': pdf_reader.metadata.producer if pdf_reader.metadata else None,
                    'file_size': file_path.stat().st_size
                }
                
                return info
                
        except Exception as e:
            logger.warning(f"PDF 정보 추출 실패: {e}")
            return None
    
    @staticmethod
    def estimate_processing_time(file_path: Path, pages_per_minute: int = 10) -> float:
        """
        PDF 처리 예상 시간 계산
        
        Args:
            file_path: PDF 파일 경로
            pages_per_minute: 분당 처리 가능한 페이지 수
            
        Returns:
            float: 예상 처리 시간 (초)
        """
        try:
            page_count = PDFUtils.get_page_count(file_path)
            estimated_minutes = page_count / pages_per_minute
            return estimated_minutes * 60  # 초 단위로 변환
        except Exception:
            return 60.0  # 기본값: 1분
