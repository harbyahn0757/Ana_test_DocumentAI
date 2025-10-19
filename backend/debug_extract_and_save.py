#!/usr/bin/env python3
"""
디버깅용 추출 및 저장 스크립트

샘플 PDF 파일들에서 테이블을 추출하고 결과를 JSON/Pickle로 저장하여
시뮬레이션 및 디버깅에 활용할 수 있도록 합니다.
"""

import asyncio
import json
import pickle
import hashlib
from pathlib import Path
from datetime import datetime
from typing import Dict, Any, List

# 현재 스크립트 위치 기준으로 백엔드 모듈 import
import sys
sys.path.append(str(Path(__file__).parent))

from services.extraction_service import ExtractionService
from storage.cache_manager import CacheManager
from models.table_models import ExtractionResult
from models.analysis_models import ExtractionLibrary
import logging

# 로깅 설정
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class DebugExtractor:
    """디버깅용 추출기"""
    
    def __init__(self):
        self.extraction_service = ExtractionService()
        self.cache_manager = CacheManager(
            cache_dir=Path("debug_cache"),
            max_age_hours=24*7  # 일주일 보관
        )
        self.output_dir = Path("debug_output")
        self.output_dir.mkdir(exist_ok=True)
        
    def _generate_file_key(self, file_path: str, library: str) -> str:
        """파일과 라이브러리를 기반으로 고유 키 생성"""
        content = f"{file_path}_{library}_{datetime.now().strftime('%Y%m%d')}"
        return hashlib.md5(content.encode()).hexdigest()[:12]
    
    async def extract_and_save_sample(self, sample_name: str, library: str = "pdfplumber"):
        """샘플 파일 추출 및 저장"""
        try:
            # 샘플 파일 경로 설정
            sample_paths = {
                "sample1": "uploads/0001_250123162148(배치전 1차_1차_8장짜리)_차트넘버 유_송유진_4.pdf",
                "sample2": "uploads/합본_1.pdf",
                "original1": "../samples/0001_250123162148(배치전 1차_1차_8장짜리)_차트넘버 유_송유진.pdf",
                "original2": "../samples/합본.pdf"
            }
            
            if sample_name not in sample_paths:
                raise ValueError(f"사용 가능한 샘플: {list(sample_paths.keys())}")
            
            file_path = sample_paths[sample_name]
            logger.info(f"🔍 샘플 추출 시작: {sample_name} ({library})")
            
            # 파일 존재 확인
            full_path = Path(file_path)
            if not full_path.exists():
                logger.error(f"❌ 파일이 존재하지 않습니다: {full_path}")
                return False
            
            # 추출 실행
            start_time = datetime.now()
            tables = await self.extraction_service.extract_tables(
                file_path=str(full_path),
                library=library
            )
            end_time = datetime.now()
            
            # ExtractionResult 생성
            extraction_result = ExtractionResult(
                file_path=str(full_path),
                file_name=full_path.name,
                file_id=sample_name,
                success=True,
                total_pages=max(table.page_number for table in tables) if tables else 0,
                total_tables=len(tables),
                tables=tables,
                extraction_library=ExtractionLibrary(library),
                processing_time=(end_time - start_time).total_seconds(),
                extracted_at=end_time
            )
            
            # 결과 저장
            await self._save_results(sample_name, library, extraction_result, tables)
            
            logger.info(f"✅ 추출 완료: {len(tables)}개 테이블, {extraction_result.processing_time:.2f}초")
            return True
            
        except Exception as e:
            logger.error(f"❌ 추출 실패: {e}")
            import traceback
            traceback.print_exc()
            return False
    
    async def _save_results(
        self, 
        sample_name: str, 
        library: str, 
        extraction_result: ExtractionResult,
        tables: List
    ):
        """결과를 다양한 형태로 저장"""
        
        file_key = self._generate_file_key(sample_name, library)
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        
        # 1. 캐시 매니저에 저장
        cache_key = f"{sample_name}_{library}_{file_key}"
        success = await self.cache_manager.save_extraction_result(cache_key, extraction_result)
        if success:
            logger.info(f"📦 캐시 저장 완료: {cache_key}")
        
        # 2. JSON 형태로 저장 (읽기 쉬운 형태)
        json_file = self.output_dir / f"{sample_name}_{library}_{timestamp}.json"
        json_data = {
            "metadata": {
                "sample_name": sample_name,
                "library": library,
                "file_key": file_key,
                "extracted_at": extraction_result.extracted_at.isoformat(),
                "processing_time": extraction_result.processing_time,
                "total_tables": extraction_result.total_tables,
                "total_pages": extraction_result.total_pages
            },
            "extraction_result": extraction_result.model_dump(),
            "tables_summary": [
                {
                    "page": table.page_number,
                    "rows": len(table.rows),
                    "cols": len(table.rows[0]) if table.rows else 0,
                    "data_preview": table.rows[:3] if table.rows else []  # 처음 3줄만
                }
                for table in tables
            ]
        }
        
        with open(json_file, 'w', encoding='utf-8') as f:
            json.dump(json_data, f, ensure_ascii=False, indent=2, default=str)
        logger.info(f"📝 JSON 저장 완료: {json_file}")
        
        # 3. Pickle 형태로 저장 (완전한 객체)
        pickle_file = self.output_dir / f"{sample_name}_{library}_{timestamp}.pkl"
        pickle_data = {
            "extraction_result": extraction_result,
            "tables": tables,
            "metadata": {
                "sample_name": sample_name,
                "library": library,
                "file_key": file_key,
                "saved_at": datetime.now()
            }
        }
        
        with open(pickle_file, 'wb') as f:
            pickle.dump(pickle_data, f)
        logger.info(f"🥒 Pickle 저장 완료: {pickle_file}")
        
        # 4. 간단한 통계 요약 저장
        summary_file = self.output_dir / f"summary_{sample_name}_{library}.txt"
        summary_content = f"""
=== 추출 결과 요약 ===
샘플명: {sample_name}
라이브러리: {library}
파일 키: {file_key}
추출 일시: {extraction_result.extracted_at}
처리 시간: {extraction_result.processing_time:.2f}초
총 페이지: {extraction_result.total_pages}
총 테이블: {extraction_result.total_tables}

=== 테이블별 상세 ===
"""
        
        for i, table in enumerate(tables):
            summary_content += f"""
테이블 {i+1}:
  - 페이지: {table.page_number}
  - 크기: {len(table.rows)}행 x {len(table.rows[0]) if table.rows else 0}열
  - 첫 번째 행: {table.rows[0] if table.rows else 'N/A'}
"""
        
        with open(summary_file, 'w', encoding='utf-8') as f:
            f.write(summary_content)
        logger.info(f"📊 요약 저장 완료: {summary_file}")

async def main():
    """메인 실행 함수"""
    extractor = DebugExtractor()
    
    print("🔧 디버깅용 샘플 추출 도구")
    print("=" * 50)
    
    # 사용 가능한 샘플 목록
    samples = ["sample1", "sample2", "original1", "original2"]
    libraries = ["pdfplumber", "camelot"]
    
    print("📋 사용 가능한 샘플:")
    for sample in samples:
        print(f"  - {sample}")
    
    print("\n📚 사용 가능한 라이브러리:")
    for lib in libraries:
        print(f"  - {lib}")
    
    # 모든 조합 추출 (선택적)
    extract_all = input("\n모든 조합을 추출하시겠습니까? (y/n): ").lower() == 'y'
    
    if extract_all:
        for sample in samples:
            for library in libraries:
                print(f"\n🚀 {sample} + {library} 추출 중...")
                success = await extractor.extract_and_save_sample(sample, library)
                if success:
                    print(f"✅ {sample} + {library} 완료")
                else:
                    print(f"❌ {sample} + {library} 실패")
    else:
        # 개별 선택
        sample = input(f"\n샘플 선택 ({'/'.join(samples)}): ")
        library = input(f"라이브러리 선택 ({'/'.join(libraries)}): ")
        
        if sample in samples and library in libraries:
            print(f"\n🚀 {sample} + {library} 추출 중...")
            success = await extractor.extract_and_save_sample(sample, library)
            if success:
                print(f"✅ 추출 완료!")
            else:
                print(f"❌ 추출 실패")
        else:
            print("❌ 잘못된 선택입니다.")
    
    print(f"\n📁 결과 확인: backend/debug_output/ 폴더")
    print(f"📦 캐시 확인: backend/debug_cache/ 폴더")

if __name__ == "__main__":
    asyncio.run(main())
