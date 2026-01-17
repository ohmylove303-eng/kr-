#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
일별 가격 데이터 수집 (2년치)
pykrx를 사용하여 전체 종목의 OHLCV 데이터 수집
"""
import pandas as pd
from pykrx import stock
from datetime import datetime, timedelta
import time
import os


def create_daily_prices(lookback_days=730):
    """
    일별 가격 데이터 생성
    
    Args:
        lookback_days: 과거 몇 일치 데이터를 수집할지 (기본: 730일 = 2년)
    """
    print(f"📊 일별 가격 데이터 수집 중 (과거 {lookback_days}일)...")
    
    # 날짜 범위
    end_date = datetime.now()
    start_date = end_date - timedelta(days=lookback_days)
    
    start_str = start_date.strftime("%Y%m%d")
    end_str = end_date.strftime("%Y%m%d")
    
    print(f"   기간: {start_str} ~ {end_str}")
    
    # 종목 리스트 로드
    stocks_path = 'kr_market/data/stock_list.csv'
    if not os.path.exists(stocks_path):
        print("❌ 종목 리스트가 없습니다. create_stock_list.py를 먼저 실행하세요.")
        return
    
    stocks_df = pd.read_csv(stocks_path, encoding='utf-8-sig')
    tickers = stocks_df['ticker'].tolist()
    
    print(f"   대상 종목: {len(tickers):,}개")
    
    # 데이터 수집
    all_data = []
    success_count = 0
    
    for i, ticker in enumerate(tickers):
        try:
            # OHLCV 데이터 조회
            df = stock.get_market_ohlcv(start_str, end_str, ticker)
            
            if not df.empty:
                df['ticker'] = ticker
                df['date'] = df.index
                df.reset_index(drop=True, inplace=True)
                
                # 컬럼 이름 영문으로 변경
                df.rename(columns={
                    '시가': 'open',
                    '고가': 'high',
                    '저가': 'low',
                    '종가': 'close',
                    '거래량': 'volume'
                }, inplace=True)
                
                # 'current_price' 컬럼 추가 (종가와 동일)
                df['current_price'] = df['close']
                
                all_data.append(df)
                success_count += 1
            
            # Progress
            if (i + 1) % 100 == 0:
                print(f"   진행률: {i+1}/{len(tickers)} ({success_count}개 성공)")
            
            # Rate limiting
            time.sleep(0.1)
            
        except Exception as e:
            if (i + 1) % 100 == 0:
                print(f"   ⚠️ {ticker} 오류: {e}")
            continue
    
    # 결합 및 저장
    if all_data:
        final_df = pd.concat(all_data, ignore_index=True)
        final_df = final_df[['ticker', 'date', 'open', 'high', 'low', 'close', 'current_price', 'volume']]
        
        output_path = 'kr_market/daily_prices.csv'
        final_df.to_csv(output_path, index=False, encoding='utf-8-sig')
        
        print(f"\n✅ 일별 가격 데이터 생성 완료")
        print(f"   성공: {success_count}/{len(tickers)}개 종목")
        print(f"   총 레코드: {len(final_df):,}개")
        print(f"   저장 위치: {output_path}")
        print(f"   파일 크기: {os.path.getsize(output_path) / 1024 / 1024:.1f} MB")
    else:
        print("❌ 데이터 수집 실패")


if __name__ == "__main__":
    # 2년치 데이터 수집 (약 5-10분 소요)
    create_daily_prices(lookback_days=730)
