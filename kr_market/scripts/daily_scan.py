#!/usr/bin/env python3
"""
한국주식 일일 자동 VCP 스캔 스크립트
장 마감 후 (16:00 KST) 자동 실행
"""

import os
import sys
import logging
from datetime import datetime

# 프로젝트 루트 설정 (scripts 폴더의 상위의 상위)
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
PROJECT_ROOT = os.path.dirname(os.path.dirname(SCRIPT_DIR))
sys.path.insert(0, PROJECT_ROOT)
os.chdir(PROJECT_ROOT)

from kr_market.signal_tracker import SignalTracker

# 로깅 설정
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(f'{PROJECT_ROOT}/kr_market/data/scan_log.txt'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)


def run_daily_scan():
    """전체 KRX 종목 VCP 스캔 실행"""
    logger.info("=" * 50)
    logger.info(f"일일 VCP 스캔 시작: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    logger.info("=" * 50)
    
    try:
        tracker = SignalTracker()
        
        # 전체 종목 스캔
        logger.info("전체 KRX 종목 스캔 시작...")
        signals = tracker.scan_today_signals()
        
        logger.info(f"스캔 완료: {len(signals)}개 신규 VCP 시그널 발견")
        
        # 결과 요약
        if signals:
            logger.info("\n=== 발견된 시그널 요약 ===")
            for sig in signals[:10]:  # 상위 10개만 로깅
                logger.info(f"  - {sig.get('name', '?')} ({sig.get('ticker')}) | Score: {sig.get('score')}")
        
        logger.info(f"\n일일 스캔 완료: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        return True
        
    except Exception as e:
        logger.error(f"스캔 오류: {e}")
        import traceback
        traceback.print_exc()
        return False


if __name__ == "__main__":
    success = run_daily_scan()
    sys.exit(0 if success else 1)
