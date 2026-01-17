#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
한국주식 데이터 수집 - 전체 실행 스크립트
모든 필수 데이터 파일을 순차적으로 생성합니다.
"""
import sys
import os

# 현재 디렉토리를 Python 경로에 추가
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from scripts.create_stock_list import create_stock_list
from scripts.create_daily_prices import create_daily_prices
from scripts.create_institutional_data import create_institutional_data


def main():
    """전체 데이터 수집 프로세스 실행"""
    print("=" * 60)
    print("🚀 한국주식 AI 분석 시스템 - 데이터 수집 시작")
    print("=" * 60)
    print()
    
    # 1단계: 종목 리스트
    print("[ 1/3 ] 종목 리스트 생성")
    print("-" * 60)
    try:
        create_stock_list()
        print()
    except Exception as e:
        print(f"❌ 오류: {e}")
        return
    
    # 2단계: 일별 가격 데이터
    print("[ 2/3 ] 일별 가격 데이터 수집 (2년치)")
    print("-" * 60)
    print("⏳ 약 5-10분 소요됩니다...")
    try:
        create_daily_prices(lookback_days=730)
        print()
    except Exception as e:
        print(f"❌ 오류: {e}")
        return
    
    # 3단계: 수급 데이터
    print("[ 3/3 ] 외인/기관 순매매 데이터 수집")
    print("-" * 60)
    print("⏳ 약 10-15분 소요됩니다...")
    try:
        create_institutional_data()
        print()
    except Exception as e:
        print(f"❌ 오류: {e}")
        return
    
    # 완료
    print("=" * 60)
    print("✅ 모든 데이터 수집 완료!")
    print("=" * 60)
    print()
    print("📁 생성된 파일:")
    print("  - kr_market/data/stock_list.csv")
    print("  - kr_market/daily_prices.csv")
    print("  - kr_market/all_institutional_trend_data.csv")
    print()
    print("🚀 이제 Flask 서버를 실행할 수 있습니다:")
    print("  python3 flask_app.py")
    print()


if __name__ == "__main__":
    main()
