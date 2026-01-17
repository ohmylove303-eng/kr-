#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
외인/기관 순매매 데이터 수집
네이버 금융 크롤링을 통한 수급 데이터 수집
Based on BLUEPRINT_09_SUPPORTING_MODULES.md
"""
import pandas as pd
import requests
from bs4 import BeautifulSoup
import time
import os
from datetime import datetime


def scrape_institutional_data(ticker, max_retries=3):
    """
    네이버 금융에서 외인/기관 순매매 데이터 크롤링
    
    Args:
        ticker: 6자리 종목 코드
        max_retries: 최대 재시도 횟수
    
    Returns:
        Dict with 5d/10d/20d/60d net buy data
    """
    url = f"https://finance.naver.com/item/frgn.naver?code={ticker}"
    
    for attempt in range(max_retries):
        try:
            headers = {
                'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36'
            }
            response = requests.get(url, headers=headers, timeout=10)
            response.encoding = 'euc-kr'
            
            if response.status_code != 200:
                return None
            
            soup = BeautifulSoup(response.text, 'html.parser')
            
            # 테이블 파싱
            table = soup.find('table', {'class': 'type2'})
            if not table:
                return None
            
            rows = table.find_all('tr')
            
            # 데이터 추출
            daily_data = []
            for row in rows[2:]:  # 헤더 스킵
                cols = row.find_all('td')
                if len(cols) >= 7:
                    try:
                        # 외국인 순매수, 기관 순매수 (단위: 주)
                        foreign_net = int(cols[5].get_text().strip().replace(',', '') or 0)
                        inst_net = int(cols[6].get_text().strip().replace(',', '') or 0)
                        
                        daily_data.append({
                            'foreign': foreign_net,
                            'inst': inst_net
                        })
                    except:
                        continue
            
            if len(daily_data) < 5:
                return None
            
            # 누적 계산
            foreign_5d = sum([d['foreign'] for d in daily_data[:5]])
            foreign_10d = sum([d['foreign'] for d in daily_data[:10]])
            foreign_20d = sum([d['foreign'] for d in daily_data[:20]])
            foreign_60d = sum([d['foreign'] for d in daily_data[:min(60, len(daily_data))]])
            
            inst_5d = sum([d['inst'] for d in daily_data[:5]])
            inst_10d = sum([d['inst'] for d in daily_data[:10]])
            inst_20d = sum([d['inst'] for d in daily_data[:20]])
            inst_60d = sum([d['inst'] for d in daily_data[:min(60, len(daily_data))]])
            
            # Supply Demand Index 간단 계산 (0-100)
            # 외인 50점 + 기관 50점
            foreign_score = min(max((foreign_60d / 1_000_000) * 10, 0), 50)
            inst_score = min(max((inst_60d / 500_000) * 10, 0), 50)
            supply_demand_index = min(foreign_score + inst_score, 100)
            
            return {
                'ticker': ticker,
                'scrape_date': datetime.now().strftime('%Y-%m-%d'),
                'foreign_net_buy_5d': foreign_5d,
                'foreign_net_buy_10d': foreign_10d,
                'foreign_net_buy_20d': foreign_20d,
                'foreign_net_buy_60d': foreign_60d,
                'institutional_net_buy_5d': inst_5d,
                'institutional_net_buy_10d': inst_10d,
                'institutional_net_buy_20d': inst_20d,
                'institutional_net_buy_60d': inst_60d,
                'supply_demand_index': round(supply_demand_index, 1)
            }
            
        except Exception as e:
            if attempt == max_retries - 1:
                return None
            time.sleep(1)
    
    return None


def create_institutional_data():
    """외인/기관 수급 데이터 전체 수집"""
    print("📊 외인/기관 순매매 데이터 수집 중...")
    
    # 종목 리스트 로드
    stocks_path = 'kr_market/data/stock_list.csv'
    if not os.path.exists(stocks_path):
        print("❌ 종목 리스트가 없습니다. create_stock_list.py를 먼저 실행하세요.")
        return
    
    stocks_df = pd.read_csv(stocks_path, encoding='utf-8-sig')
    tickers = stocks_df['ticker'].tolist()
    
    print(f"   대상 종목: {len(tickers):,}개")
    print("   ⏳ 약 10-15분 소요 예상...")
    
    # 데이터 수집
    results = []
    success_count = 0
    
    for i, ticker in enumerate(tickers):
        data = scrape_institutional_data(ticker)
        
        if data:
            # 종목명 추가
            name = stocks_df[stocks_df['ticker'] == ticker]['name'].values[0]
            data['name'] = name
            results.append(data)
            success_count += 1
        
        # Progress
        if (i + 1) % 50 == 0:
            print(f"   진행률: {i+1}/{len(tickers)} ({success_count}개 성공)")
        
        # Rate limiting (네이버 서버 부하 방지)
        time.sleep(0.3)
    
    # 저장
    if results:
        df = pd.DataFrame(results)
        df = df[['ticker', 'name', 'scrape_date',
                 'foreign_net_buy_5d', 'foreign_net_buy_10d', 'foreign_net_buy_20d', 'foreign_net_buy_60d',
                 'institutional_net_buy_5d', 'institutional_net_buy_10d', 'institutional_net_buy_20d', 'institutional_net_buy_60d',
                 'supply_demand_index']]
        
        output_path = 'kr_market/all_institutional_trend_data.csv'
        df.to_csv(output_path, index=False, encoding='utf-8-sig')
        
        print(f"\n✅ 수급 데이터 생성 완료")
        print(f"   성공: {success_count}/{len(tickers)}개 종목")
        print(f"   저장 위치: {output_path}")
        
        # 통계
        strong_buy = len(df[df['supply_demand_index'] >= 70])
        print(f"   강한 매수세 (SI≥70): {strong_buy}개")
    else:
        print("❌ 데이터 수집 실패")


if __name__ == "__main__":
    create_institutional_data()
