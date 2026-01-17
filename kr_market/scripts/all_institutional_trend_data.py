#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
KR Market - Institutional Trend Data Analyzer
Based on BLUEPRINT_09_SUPPORTING_MODULES.md

Scrapes and analyzes institutional investor trends from Naver Finance.
Generates supply/demand index (0-100) and accumulation signals.

Output: kr_market/data/all_institutional_trend_data.csv
"""

import os
import time
import requests
import pandas as pd
from bs4 import BeautifulSoup
from dataclasses import dataclass, asdict
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional
import logging
from concurrent.futures import ThreadPoolExecutor, as_completed

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)


@dataclass
class TrendConfig:
    """Trend analysis thresholds"""
    strong_buy_inst: int = 3_000_000          # Institutional strong buy threshold
    buy_inst: int = 1_000_000               
    strong_buy_foreign: int = 5_000_000       # Foreign strong buy threshold
    buy_foreign: int = 2_000_000
    high_ratio_inst: float = 8.0              # High ratio threshold
    high_ratio_foreign: float = 12.0


@dataclass
class InstitutionalData:
    """Complete institutional data structure"""
    ticker: str
    name: str = ''
    scrape_date: str = ''
    data_source: str = 'naver'
    total_days: int = 0
    
    # Net buy amounts by period
    institutional_net_buy_60d: int = 0
    institutional_net_buy_20d: int = 0
    institutional_net_buy_10d: int = 0
    institutional_net_buy_5d: int = 0
    
    foreign_net_buy_60d: int = 0
    foreign_net_buy_20d: int = 0
    foreign_net_buy_10d: int = 0
    foreign_net_buy_5d: int = 0
    
    # Volume ratios
    institutional_ratio_20d: float = 0.0
    foreign_ratio_20d: float = 0.0
    
    # Trend analysis
    institutional_trend: str = 'neutral'
    foreign_trend: str = 'neutral'
    supply_demand_index: float = 50.0
    supply_demand_stage: str = '중립'
    
    # Accumulation signals
    strong_accumulation: int = 0
    accumulation_signal: int = 0
    accumulation_intensity: str = '보통'


class NaverFinanceScraper:
    """Naver Finance institutional data scraper"""
    
    def __init__(self, data_dir: str = None):
        self.data_dir = Path(data_dir or os.getenv('DATA_DIR', '.'))
        self.output_path = self.data_dir / 'all_institutional_trend_data.csv'
        self.base_url = "https://finance.naver.com/item/frgn.naver"
        
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        })
        
        self.request_delay = 0.3
        self.max_retries = 3
        self.config = TrendConfig()
        
        logger.info("✅ Naver Finance Scraper initialized")
    
    def scrape_ticker(self, ticker: str, name: str = '') -> Optional[InstitutionalData]:
        """Scrape 60-day institutional data for single ticker"""
        url = f"{self.base_url}?code={ticker}"
        
        for attempt in range(self.max_retries):
            try:
                time.sleep(self.request_delay)
                response = self.session.get(url, timeout=10)
                response.raise_for_status()
                
                soup = BeautifulSoup(response.content, 'html.parser')
                table = soup.select_one('table.type2')
                
                if not table:
                    logger.warning(f"No data table for {ticker}")
                    return None
                
                # Parse table rows
                rows = table.select('tr')[2:]  # Skip header rows
                data_rows = []
                
                for row in rows:
                    cols = row.select('td')
                    if len(cols) >= 10:
                        try:
                            date_str = cols[0].get_text(strip=True)
                            close_price = self._parse_number(cols[1].get_text(strip=True))
                            volume = self._parse_number(cols[5].get_text(strip=True))
                            foreign_net = self._parse_number(cols[6].get_text(strip=True))
                            inst_net = self._parse_number(cols[9].get_text(strip=True))
                            
                            data_rows.append({
                                'date': date_str,
                                'close': close_price,
                                'volume': volume,
                                'foreign_net': foreign_net,
                                'inst_net': inst_net
                            })
                        except Exception:
                            continue
                
                if not data_rows:
                    return None
                
                # Analyze data
                return self._analyze_data(ticker, name, data_rows)
                
            except Exception as e:
                logger.error(f"Error scraping {ticker} (attempt {attempt + 1}): {e}")
                if attempt < self.max_retries - 1:
                    time.sleep(2)
                    continue
                return None
        
        return None
    
    def _parse_number(self, text: str) -> int:
        """Parse number from Korean formatted string"""
        text = text.replace(',', '').replace('-', '0')
        try:
            return int(float(text))
        except:
            return 0
    
    def _analyze_data(self, ticker: str, name: str, data_rows: List[Dict]) -> InstitutionalData:
        """Analyze institutional data and calculate metrics"""
        df = pd.DataFrame(data_rows)
        
        # Calculate period sums
        inst_60d = int(df['inst_net'].sum()) if len(df) >= 60 else 0
        inst_20d = int(df.head(20)['inst_net'].sum()) if len(df) >= 20 else 0
        inst_10d = int(df.head(10)['inst_net'].sum()) if len(df) >= 10 else 0
        inst_5d = int(df.head(5)['inst_net'].sum()) if len(df) >= 5 else 0
        
        foreign_60d = int(df['foreign_net'].sum()) if len(df) >= 60 else 0
        foreign_20d = int(df.head(20)['foreign_net'].sum()) if len(df) >= 20 else 0
        foreign_10d = int(df.head(10)['foreign_net'].sum()) if len(df) >= 10 else 0
        foreign_5d = int(df.head(5)['foreign_net'].sum()) if len(df) >= 5 else 0
        
        # Calculate volume ratios
        total_vol_20d = df.head(20)['volume'].sum() if len(df) >= 20 else 1
        inst_ratio = abs(df.head(20)['inst_net'].sum()) / total_vol_20d * 100 if total_vol_20d > 0 else 0
        foreign_ratio = abs(df.head(20)['foreign_net'].sum()) / total_vol_20d * 100 if total_vol_20d > 0 else 0
        
        # Determine trends
        inst_trend = self._determine_trend(inst_5d, inst_10d, self.config.buy_inst, self.config.strong_buy_inst)
        foreign_trend = self._determine_trend(foreign_5d, foreign_10d, self.config.buy_foreign, self.config.strong_buy_foreign)
        
        # Calculate supply/demand index
        supply_demand_index = self._calculate_supply_demand_index({
            'inst_60d': inst_60d,
            'inst_20d': inst_20d,
            'inst_5d': inst_5d,
            'foreign_60d': foreign_60d,
            'foreign_20d': foreign_20d,
            'foreign_5d': foreign_5d,
            'inst_ratio': inst_ratio,
            'foreign_ratio': foreign_ratio,
            'total_vol': total_vol_20d
        })
        
        # Determine stage
        supply_demand_stage = self._get_stage_label(supply_demand_index)
        
        # Accumulation signals
        strong_acc = 1 if supply_demand_index >= 85 else 0
        acc_signal = 1 if supply_demand_index >= 70 else 0
        acc_intensity = self._get_accumulation_intensity(supply_demand_index)
        
        return InstitutionalData(
            ticker=ticker,
            name=name,
            scrape_date=datetime.now().strftime('%Y-%m-%d'),
            total_days=len(df),
            institutional_net_buy_60d=inst_60d,
            institutional_net_buy_20d=inst_20d,
            institutional_net_buy_10d=inst_10d,
            institutional_net_buy_5d=inst_5d,
            foreign_net_buy_60d=foreign_60d,
            foreign_net_buy_20d=foreign_20d,
            foreign_net_buy_10d=foreign_10d,
            foreign_net_buy_5d=foreign_5d,
            institutional_ratio_20d=round(inst_ratio, 2),
            foreign_ratio_20d=round(foreign_ratio, 2),
            institutional_trend=inst_trend,
            foreign_trend=foreign_trend,
            supply_demand_index=round(supply_demand_index, 1),
            supply_demand_stage=supply_demand_stage,
            strong_accumulation=strong_acc,
            accumulation_signal=acc_signal,
            accumulation_intensity=acc_intensity
        )
    
    def _determine_trend(self, net_5d: int, net_10d: int, buy_threshold: int, strong_buy_threshold: int) -> str:
        """Determine trend based on net buy amounts"""
        if net_5d >= strong_buy_threshold and net_10d >= buy_threshold:
            return 'strong_buy'
        elif net_5d >= buy_threshold:
            return 'buy'
        elif net_5d <= -strong_buy_threshold and net_10d <= -buy_threshold:
            return 'strong_sell'
        elif net_5d <= -buy_threshold:
            return 'sell'
        else:
            return 'neutral'
    
    def _calculate_supply_demand_index(self, metrics: Dict) -> float:
        """Calculate supply demand index (0-100)"""
        score = 50.0  # Base score
        
        # Institutional score (0-50)
        inst_score = 0
        if metrics['inst_60d'] > 0:
            inst_score += 10
        if metrics['inst_20d'] > 0:
            inst_score += 15
        if metrics['inst_5d'] > self.config.buy_inst:
            inst_score += 15
        elif metrics['inst_5d'] > self.config.buy_inst / 2:
            inst_score += 10
        
        # Foreign score (0-50)
        foreign_score = 0
        if metrics['foreign_60d'] > 0:
            foreign_score += 10
        if metrics['foreign_20d'] > 0:
            foreign_score += 15
        if metrics['foreign_5d'] > self.config.buy_foreign:
            foreign_score += 15
        elif metrics['foreign_5d'] > self.config.buy_foreign / 2:
            foreign_score += 10
        
        # Volume weight
        volume_weight = min(metrics['total_vol'] / 10_000_000, 1.0)
        
        final_score = (inst_score + foreign_score) * (0.8 + 0.2 * volume_weight)
        return min(max(final_score, 0), 100)
    
    def _get_stage_label(self, score: float) -> str:
        """Get Korean stage label"""
        if score >= 85:
            return '강한매집'
        elif score >= 70:
            return '매집'
        elif score >= 60:
            return '약매집'
        elif score >= 40:
            return '중립'
        elif score >= 30:
            return '약분산'
        elif score >= 15:
            return '분산'
        else:
            return '강한분산'
    
    def _get_accumulation_intensity(self, score: float) -> str:
        """Get accumulation intensity"""
        if score >= 85:
            return '매우강함'
        elif score >= 70:
            return '강함'
        elif score >= 60:
            return '보통'
        else:
            return '약함'
    
    def scrape_all_tickers(self, tickers: List[tuple], max_workers: int = 5):
        """Scrape all tickers using multithreading"""
        results = []
        total = len(tickers)
        
        logger.info(f"📡 Starting scrape for {total} tickers...")
        
        with ThreadPoolExecutor(max_workers=max_workers) as executor:
            futures = {
                executor.submit(self.scrape_ticker, ticker, name): (ticker, name)
                for ticker, name in tickers
            }
            
            for i, future in enumerate(as_completed(futures), 1):
                ticker, name = futures[future]
                try:
                    result = future.result()
                    if result:
                        results.append(asdict(result))
                        logger.info(f"✅ [{i}/{total}] {name} ({ticker}) - Index: {result.supply_demand_index}")
                    else:
                        logger.warning(f"⚠️ [{i}/{total}] {name} ({ticker}) - No data")
                except Exception as e:
                    logger.error(f"❌ [{i}/{total}] {name} ({ticker}) - Error: {e}")
        
        # Save to CSV
        if results:
            df = pd.DataFrame(results)
            df.to_csv(self.output_path, index=False, encoding='utf-8-sig')
            logger.info(f"💾 Saved {len(results)} records to {self.output_path}")
        else:
            logger.warning("No data to save")


def load_stock_list(stock_list_path: str) -> List[tuple]:
    """Load stock list from CSV"""
    df = pd.read_csv(stock_list_path, encoding='utf-8-sig')
    return list(zip(df['ticker'], df['name']))


def main(max_stocks: int = None):
    """Main entry point"""
    # Load stock list
    stock_list_path = 'kr_market/data/stock_list.csv'
    
    if not os.path.exists(stock_list_path):
        logger.error(f"Stock list not found: {stock_list_path}")
        return
    
    tickers = load_stock_list(stock_list_path)
    
    if max_stocks:
        tickers = tickers[:max_stocks]
        logger.info(f"Limiting to first {max_stocks} stocks")
    
    scraper = NaverFinanceScraper(data_dir='kr_market/data')
    scraper.scrape_all_tickers(tickers, max_workers=3)
    
    logger.info("✅ Institutional data scraping complete")


if __name__ == '__main__':
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument('--max', type=int, help='Maximum number of stocks to scrape')
    args = parser.parse_args()
    
    main(max_stocks=args.max)
