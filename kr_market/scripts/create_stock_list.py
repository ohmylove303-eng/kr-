#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
한국 주식 종목 리스트 생성
pykrx를 사용하여 KOSPI/KOSDAQ 전체 종목 수집
"""
import pandas as pd
import FinanceDataReader as fdr
import os

def create_stock_list():
    print("📊 Fetching stock list via FinanceDataReader...")
    
    try:
        # KOSPI, KOSDAQ 리스트 가져오기
        df_kospi = fdr.StockListing('KOSPI')
        df_kosdaq = fdr.StockListing('KOSDAQ')
        
        # 시가총액(Marcap) 기준 정렬 후 상위 추출 (속도 및 우량주 위주 분석을 위해)
        # 2026년 가정: fdr은 최신 데이터를 가져옴.
        # Marcap 컬럼이 있으면 정렬, 없으면 그냥 앞부분 자름
        
        if 'Marcap' in df_kospi.columns:
            df_kospi = df_kospi.sort_values('Marcap', ascending=False)
        
        if 'Marcap' in df_kosdaq.columns:
            df_kosdaq = df_kosdaq.sort_values('Marcap', ascending=False)
            
        # KOSPI 상위 150개, KOSDAQ 상위 150개 = 총 300개
        df_kospi_top = df_kospi.head(150)
        df_kosdaq_top = df_kosdaq.head(150)
        
        print(f"   Selected top {len(df_kospi_top)} KOSPI and {len(df_kosdaq_top)} KOSDAQ stocks.")

        # 필요한 컬럼만 선택 및 표준화
        # FDR returns: Code, Name, Market, Sector, ...
        # We need: ticker, name, market, sector
        
        cols_map = {'Code': 'ticker', 'Name': 'name', 'Market': 'market', 'Sector': 'sector'}
        
        # 없으면 빈 컬럼 추가
        for df in [df_kospi_top, df_kosdaq_top]:
            if 'Sector' not in df.columns:
                df['Sector'] = 'Unknown'
            if 'Market' not in df.columns:
                # KOSPI df엔 Market 컬럼이 없을 수도 있음 (StockListing('KOSPI')니까)
                if df is df_kospi_top: df['Market'] = 'KOSPI'
                if df is df_kosdaq_top: df['Market'] = 'KOSDAQ'

        df_kospi_top = df_kospi_top.rename(columns=cols_map)[['ticker', 'name', 'market', 'sector']]
        df_kosdaq_top = df_kosdaq_top.rename(columns=cols_map)[['ticker', 'name', 'market', 'sector']]
        
        all_stocks = pd.concat([df_kospi_top, df_kosdaq_top])
        
        # 저장
        save_path = 'kr_market/data/stock_list.csv'
        os.makedirs(os.path.dirname(save_path), exist_ok=True)
        all_stocks.to_csv(save_path, index=False, encoding='utf-8-sig')
        
        print(f"✅ Saved {len(all_stocks)} stocks to {save_path}")
        
    except Exception as e:
        print(f"❌ Error fetching stock list: {e}")
        # 만약 에러나면 샘플이라도 다시 생성...은 하지 않고 에러 출력


if __name__ == "__main__":
    create_stock_list()
