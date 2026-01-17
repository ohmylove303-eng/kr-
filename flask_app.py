"""
KR Market AI Stock Analysis System - Flask Backend
Based on BLUEPRINT_02_BACKEND_FLASK_CORE.md

Full-featured Flask app with:
- Background price scheduler (5-min updates)
- 19 KR Market API endpoints
- Sector mapping system
- Caching patterns
- Error handlers
"""

import os
import json
import threading
import pandas as pd
import numpy as np
import yfinance as yf
import time
import traceback
from flask import Flask, render_template, jsonify, request
from datetime import datetime
from dotenv import load_dotenv

# Load environment variables explicitly
load_dotenv()

app = Flask(__name__)

# Enable CORS for frontend access
from flask_cors import CORS
CORS(app, resources={r"/api/*": {"origins": "*"}})

# ==================== BACKGROUND PRICE SCHEDULER ====================

# [NEW] 실시간 데이터 - FinanceDataReader (optional - not available on Python 3.13)
try:
    import FinanceDataReader as fdr
    FDR_AVAILABLE = True
except ImportError:
    fdr = None
    FDR_AVAILABLE = False
    print("⚠️ FinanceDataReader 미설치 (검색/실시간 데이터 제한)")

from datetime import timedelta

# [NICE] Theme Manager for dynamic theme lookup
from kr_market.theme_manager import ThemeManager

# KRX 종목 리스트 초기화
KRX_STOCKS = pd.DataFrame()
if FDR_AVAILABLE:
    print("⏳ KRX 종목 리스트 다운로드 중... (서버 시작 시 1회)")
    try:
        KRX_STOCKS = fdr.StockListing('KRX')
        if 'Code' in KRX_STOCKS.columns and 'Symbol' not in KRX_STOCKS.columns:
            KRX_STOCKS['Symbol'] = KRX_STOCKS['Code']
        print(f"✅ KRX 종목 리스트 로드 완료: {len(KRX_STOCKS)}개 종목")
    except Exception as e:
        print(f"⚠️ KRX 종목 리스트 로드 실패 (검색 기능 제한됨): {e}")
    KRX_STOCKS = pd.DataFrame()

# [NEW] pykrx for supply data (foreign/institutional trading)
try:
    from pykrx import stock as pykrx_stock
    PYKRX_AVAILABLE = True
    print("✅ pykrx 모듈 로드 완료 (수급 데이터 사용 가능)")
except ImportError:
    PYKRX_AVAILABLE = False
    print("⚠️ pykrx 미설치 (수급 데이터 제한)")

def get_supply_data(ticker: str, days: int = 5) -> dict:
    """최근 N일간 외국인/기관 순매수 합계 조회 (pykrx 사용)"""
    if not PYKRX_AVAILABLE:
        return {'foreign_5d': 0, 'inst_5d': 0}
    
    try:
        end_date = datetime.now()
        start_date = end_date - timedelta(days=days + 10)  # 영업일 고려 여유
        
        # pykrx API 호출
        df = pykrx_stock.get_market_trading_value_by_date(
            start_date.strftime('%Y%m%d'),
            end_date.strftime('%Y%m%d'),
            ticker
        )
        
        if df.empty or len(df) < 1:
            return {'foreign_5d': 0, 'inst_5d': 0}
        
        # 최근 N일만 사용
        recent = df.tail(days)
        
        # 외국인 순매수 = 외국인 합계
        # 기관 순매수 = 기관 합계
        foreign_col = '외국인합계' if '외국인합계' in recent.columns else (
            '외국인' if '외국인' in recent.columns else None
        )
        inst_col = '기관합계' if '기관합계' in recent.columns else (
            '기관' if '기관' in recent.columns else None
        )
        
        foreign_5d = int(recent[foreign_col].sum()) if foreign_col else 0
        inst_5d = int(recent[inst_col].sum()) if inst_col else 0
        
        return {'foreign_5d': foreign_5d, 'inst_5d': inst_5d}
    except Exception as e:
        print(f"Supply data fetch error ({ticker}): {e}")
        return {'foreign_5d': 0, 'inst_5d': 0}


def search_stock(keyword):
    """실시간 종목 검색"""
    if KRX_STOCKS.empty:
        return []
    
    keyword = keyword.upper().strip()
    if not keyword:
        return []
        
    mask = KRX_STOCKS['Symbol'].str.contains(keyword) | KRX_STOCKS['Name'].str.contains(keyword)
    results = KRX_STOCKS[mask].head(10) # 최대 10개
    
    output = []
    for _, row in results.iterrows():
        output.append({
            'symbol': row['Symbol'], # Code
            'name': row['Name'],
            'market': row['Market'],
            'sector': row.get('Sector', '')
        })
    return output

def get_real_stock_data(symbol):
    """실시간 주가 정보 (FDR 사용)"""
    if not FDR_AVAILABLE:
        return None  # FinanceDataReader not available
        
    try:
        # 최근 5일 데이터 조회 (안전하게)
        end_date = datetime.now()
        start_date = end_date - timedelta(days=7)
        
        df = fdr.DataReader(symbol, start_date, end_date)
        if df.empty:
            return None
            
        last_row = df.iloc[-1]
        prev_row = df.iloc[-2] if len(df) > 1 else last_row
        
        # 기본 정보 확인
        name = symbol
        sector = ''
        if not KRX_STOCKS.empty:
            match = KRX_STOCKS[KRX_STOCKS['Symbol'] == symbol]
            if not match.empty:
                name = match.iloc[0]['Name']
                sector = match.iloc[0].get('Sector', '')

        # 등락률 계산
        change_rate = 0
        if prev_row['Close'] > 0:
            change_rate = ((last_row['Close'] - prev_row['Close']) / prev_row['Close']) * 100

        return {
            'symbol': symbol,
            'name': name,
            'market': 'KRX',
            'sector': sector,
            'current_price': int(last_row['Close']),
            'change_rate': round(change_rate, 2),
            'volume': int(last_row['Volume']),
            'timestamp': last_row.name.strftime('%Y-%m-%d')
        }
    except Exception as e:
        print(f"Real data fetch error ({symbol}): {e}")
        return None

@app.route('/api/kr/search')
def api_kr_search():
    """한국 주식 검색 API"""
    q = request.args.get('q', '')
    return jsonify(search_stock(q))

# ==================== BACKGROUND PRICE SCHEDULER ====================

def start_kr_price_scheduler():
    """Background thread for live price updates (5min interval, 10s stagger)"""
    def _run_scheduler():
        print("⏰ KR Price Scheduler started (5min interval, 10s stagger)")
        while True:
            try:
                # 1. Load existing analysis data
                json_path = 'kr_market/data/kr_ai_analysis.json'
                if not os.path.exists(json_path):
                    time.sleep(60)
                    continue

                with open(json_path, 'r', encoding='utf-8') as f:
                    data = json.load(f)

                signals = data.get('signals', [])
                if not signals:
                    time.sleep(300)
                    continue

                # 2. Iterate and update each ticker
                updated_count = 0
                for signal in signals:
                    ticker = signal.get('ticker')
                    if not ticker:
                        continue

                    try:
                        from kr_market.kr_ai_analyzer import fetch_current_price
                        current_price = fetch_current_price(ticker)
                        
                        if current_price > 0:
                            entry = signal.get('entry_price', 0)
                            signal['current_price'] = current_price
                            if entry > 0:
                                signal['return_pct'] = round(
                                    ((current_price - entry) / entry) * 100, 2
                                )
                            
                            # Save immediately after each update
                            with open(json_path, 'w', encoding='utf-8') as f:
                                json.dump(data, f, ensure_ascii=False, indent=2)
                            
                            print(f"🔄 Updated price for {signal.get('name')} ({ticker}): {current_price}")
                            updated_count += 1
                        
                    except Exception as e:
                        print(f"Error updating price for {ticker}: {e}")

                    # 3. Stagger delay (10 seconds between tickers)
                    time.sleep(10)

                print(f"✅ Completed 5-min price update cycle ({updated_count} updated)")
                time.sleep(300)  # Wait 5 minutes before next cycle

            except Exception as e:
                print(f"Scheduler error: {e}")
                time.sleep(60)

    # Start daemon thread
    thread = threading.Thread(target=_run_scheduler, daemon=True)
    thread.start()


# ==================== SECTOR MAPPING SYSTEM ====================

SECTOR_MAP = {
    # Technology
    'AAPL': 'Tech', 'MSFT': 'Tech', 'NVDA': 'Tech', 'AVGO': 'Tech',
    'CRM': 'Tech', 'AMD': 'Tech', 'ADBE': 'Tech', 'CSCO': 'Tech',
    
    # Financials
    'BRK-B': 'Fin', 'JPM': 'Fin', 'V': 'Fin', 'MA': 'Fin',
    'BAC': 'Fin', 'WFC': 'Fin', 'GS': 'Fin', 'MS': 'Fin',
    
    # Healthcare
    'LLY': 'Health', 'UNH': 'Health', 'JNJ': 'Health', 'ABBV': 'Health',
    'MRK': 'Health', 'PFE': 'Health', 'TMO': 'Health', 'ABT': 'Health',
    
    # Energy
    'XOM': 'Energy', 'CVX': 'Energy', 'COP': 'Energy', 'SLB': 'Energy',
    
    # Consumer
    'AMZN': 'Cons', 'TSLA': 'Cons', 'HD': 'Cons', 'MCD': 'Cons',
    'WMT': 'Staple', 'PG': 'Staple', 'COST': 'Staple', 'KO': 'Staple',
    
    # Industrials
    'CAT': 'Indust', 'GE': 'Indust', 'RTX': 'Indust', 'HON': 'Indust',
    
    # Communication
    'META': 'Comm', 'GOOGL': 'Comm', 'NFLX': 'Comm', 'DIS': 'Comm',
    
    # Real Estate
    'PLD': 'REIT', 'AMT': 'REIT', 'EQIX': 'REIT', 'SPG': 'REIT',
}

SECTOR_CACHE_FILE = os.path.join('us_market', 'sector_cache.json')
_sector_cache = {}

def _load_sector_cache():
    """Load sector cache from file"""
    global _sector_cache
    if os.path.exists(SECTOR_CACHE_FILE):
        try:
            with open(SECTOR_CACHE_FILE, 'r') as f:
                _sector_cache = json.load(f)
        except:
            _sector_cache = {}

def _save_sector_cache(cache):
    """Save sector cache to file"""
    os.makedirs(os.path.dirname(SECTOR_CACHE_FILE), exist_ok=True)
    with open(SECTOR_CACHE_FILE, 'w') as f:
        json.dump(cache, f, indent=2)

def get_sector(ticker: str) -> str:
    """Get sector for a ticker, auto-fetch from yfinance if not in SECTOR_MAP"""
    global _sector_cache
    
    # Check static map first
    if ticker in SECTOR_MAP:
        return SECTOR_MAP[ticker]
    
    # Check persistent cache
    if ticker in _sector_cache:
        return _sector_cache[ticker]
    
    # Fetch from yfinance and cache
    try:
        stock = yf.Ticker(ticker)
        info = stock.info
        sector = info.get('sector', '')
        
        # Map to short code
        sector_short_map = {
            'Technology': 'Tech',
            'Healthcare': 'Health',
            'Financials': 'Fin',
            'Consumer Discretionary': 'Cons',
            'Consumer Staples': 'Staple',
            'Energy': 'Energy',
            'Industrials': 'Indust',
            'Materials': 'Mater',
            'Utilities': 'Util',
            'Real Estate': 'REIT',
            'Communication Services': 'Comm',
        }
        
        short_sector = sector_short_map.get(sector, sector[:5] if sector else '-')
        
        # Persist to cache
        _sector_cache[ticker] = short_sector
        _save_sector_cache(_sector_cache)
        
        return short_sector
    except Exception as e:
        _sector_cache[ticker] = '-'
        return '-'


# ==================== PAGE ROUTES ====================

@app.route('/')
def home():
    """Landing page"""
    return render_template('index.html')


@app.route('/app')
@app.route('/dashboard')
def dashboard():
    """Main dashboard with all market views"""
    return render_template('dashboard.html')


@app.route('/dividend')
def dividend_page():
    """Dividend portfolio optimization page"""
    return render_template('dashboard.html')


# ==================== KR MARKET API ROUTES ====================

@app.route('/api/kr/market-status')
def kr_market_status():
    """Check if KR market is open"""
    try:
        now = datetime.now()
        is_weekday = now.weekday() < 5
        is_trading_hours = 9 <= now.hour < 16
        is_open = is_weekday and is_trading_hours
        
        return jsonify({
            'status': 'success',
            'is_open': is_open,
            'message': '장 중' if is_open else '장 마감'
        })
    except Exception as e:
        return jsonify({'status': 'error', 'message': str(e)}), 500


@app.route('/api/kr/signals')
def get_kr_signals():
    """오늘의 VCP + 외인매집 시그널 (Top 20 순위)"""
    try:
        signals_path = 'kr_market/data/signals_log.csv'
        
        if not os.path.exists(signals_path):
            return jsonify({
                'signals': [],
                'count': 0,
                'message': '시그널 로그가 없습니다. 먼저 스캔을 실행하세요.'
            })
        
        df = pd.read_csv(signals_path, encoding='utf-8-sig')
        df['ticker'] = df['ticker'].astype(str).str.zfill(6)
        
        # 종목명 및 시장 정보 로드
        stock_names = {}
        stock_markets = {}
        stocks_file = 'kr_market/data/stock_list.csv'
        if os.path.exists(stocks_file):
            stocks_df = pd.read_csv(stocks_file, encoding='utf-8-sig', dtype={'ticker': str})
            stocks_df['ticker'] = stocks_df['ticker'].astype(str).str.zfill(6)
            stock_names = dict(zip(stocks_df['ticker'], stocks_df['name']))
            stock_markets = dict(zip(stocks_df['ticker'], stocks_df['market']))
        
        # 최신 시그널 (OPEN 상태)
        if 'status' not in df.columns:
            df['status'] = 'OPEN'
        open_signals = df[df['status'] == 'OPEN'].copy()
        today = datetime.now().strftime('%Y-%m-%d')
        
        signals = []
        for _, row in open_signals.iterrows():
            score = float(row['score']) if pd.notna(row['score']) else 0
            contraction = float(row['contraction_ratio']) if pd.notna(row['contraction_ratio']) else 1
            foreign_5d = int(row['foreign_5d']) if pd.notna(row['foreign_5d']) else 0
            inst_5d = int(row['inst_5d']) if pd.notna(row['inst_5d']) else 0
            signal_date = row['signal_date']
            
            # 제외 조건
            if contraction > 0.8:  # 수축 미완료
                continue
            if foreign_5d < 0 and inst_5d < 0:  # 수급 모두 이탈
                continue
            if score < 50:  # 기본 점수 미달
                continue
            
            # Final Score 계산
            contraction_score = (1 - contraction) * 100
            supply_score = min((foreign_5d + inst_5d) / 100000, 30)
            today_bonus = 10 if signal_date == today else 0
            
            final_score = (score * 0.4) + (contraction_score * 0.3) + (supply_score * 0.2 * 10) + today_bonus
            
            # Compute nice_layers for Radar Chart (approximation based on available data)
            L1_technical = min(int(score), 100)  # VCP score as technical
            L2_supply = min(int((1 - contraction) * 30), 30)  # Contraction -> supply
            L3_sentiment = 50  # Default neutral
            L4_macro = 35  # Default
            L5_institutional = min(int((foreign_5d + inst_5d) / 1e8), 35)  # Normalize flow
            nice_total = L1_technical + L2_supply + L3_sentiment + L4_macro + L5_institutional
            
            signals.append({
                'ticker': row['ticker'],
                'name': stock_names.get(row['ticker'], ''),
                'market': stock_markets.get(row['ticker'], ''),
                'theme': ThemeManager.get_theme(str(row['ticker']).zfill(6)) or '',  # [NICE] Dynamic theme lookup
                'signal_date': signal_date,
                'foreign_5d': foreign_5d,
                'inst_5d': inst_5d,
                'score': round(score, 1),
                'contraction_ratio': round(contraction, 2),
                'entry_price': round(row['entry_price'], 0) if pd.notna(row['entry_price']) else 0,
                'status': row['status'],
                'final_score': round(final_score, 1),
                # NICE Layers for Radar Chart
                'nice_layers': {
                    'L1_technical': L1_technical,
                    'L2_supply': L2_supply,
                    'L3_sentiment': L3_sentiment,
                    'L4_macro': L4_macro,
                    'L5_institutional': L5_institutional,
                    'total': nice_total,
                    'max_total': 300
                },
                # NICE Plan Fields
                'stop_loss': row.get('stop_loss', 0),
                'tp1': row.get('tp1', 0),
                'tp2': row.get('tp2', 0),
                'time_stop': row.get('time_stop', ''),
                'min_turnover': row.get('min_turnover', 0)
            })
        
        # ========== 테마 종목 자동 추가 (테마 탭이 비어 있지 않도록) ==========
        existing_tickers = {s['ticker'] for s in signals}
        theme_tickers = ThemeManager.get_all_target_tickers()
        
        for t_ticker in theme_tickers:
            t_ticker = str(t_ticker).zfill(6)
            if t_ticker in existing_tickers:
                continue  # 이미 시그널에 있음
            
            theme = ThemeManager.get_theme(t_ticker)
            if not theme:
                continue
            
            # 기본 시그널 생성 (VCP 스캔 없이 테마 종목으로 추가)
            t_name = stock_names.get(t_ticker, t_ticker)
            t_market = stock_markets.get(t_ticker, 'KOSPI')
            
            # 현재가 조회
            try:
                cp = get_real_stock_data(t_ticker)
                current_price = cp.get('current_price', 0) if cp else 0
            except:
                current_price = 0
            
            if current_price <= 0:
                continue
            
            signals.append({
                'ticker': t_ticker,
                'name': t_name,
                'market': t_market,
                'theme': theme,
                'signal_date': today,
                'foreign_5d': 0,
                'inst_5d': 0,
                'score': 65,  # 테마 기본 점수
                'contraction_ratio': 0.5,
                'entry_price': current_price,
                'current_price': current_price,
                'return_pct': 0,
                'status': 'THEME',
                'final_score': 55,  # 테마 기본 점수
                # NICE Layers for Radar Chart (Theme default)
                'nice_layers': {
                    'L1_technical': 65,
                    'L2_supply': 15,
                    'L3_sentiment': 50,
                    'L4_macro': 35,
                    'L5_institutional': 10,
                    'total': 175,
                    'max_total': 300
                },
                'stop_loss': int(current_price * 0.93),
                'tp1': int(current_price * 1.10),
                'tp2': int(current_price * 1.20),
                'time_stop': '',
                'min_turnover': 0
            })
        
        # final_score 기준 정렬 후 Top 20
        signals_sorted = sorted(signals, key=lambda x: x['final_score'], reverse=True)[:20]
        
        # Top 20에 대해 현재가 조회 및 수익률 계산
        if signals_sorted:
            # 티커 맵 로드 (Yahoo Finance용)
            ticker_map = {}
            ticker_map_file = 'kr_market/ticker_to_yahoo_map.csv'
            if os.path.exists(ticker_map_file):
                try:
                    tm_df = pd.read_csv(ticker_map_file, dtype=str)
                    ticker_map = dict(zip(tm_df['ticker'].str.zfill(6), tm_df['yahoo_ticker']))
                except:
                    pass
            
            # Yahoo 티커 변환
            tickers = [s['ticker'] for s in signals_sorted]
            yahoo_tickers = [ticker_map.get(t, f"{t}.KS") for t in tickers]
            
            # 현재가 조회
            current_prices = {}
            try:
                data = yf.download(yahoo_tickers, period='1d', progress=False)
                if not data.empty and 'Close' in data.columns:
                    closes = data['Close']
                    if isinstance(closes, pd.Series):
                        closes = closes.to_frame()
                        closes.columns = yahoo_tickers
                    for orig, yf_t in zip(tickers, yahoo_tickers):
                        if yf_t in closes.columns:
                            val = closes[yf_t].iloc[-1]
                            if not pd.isna(val):
                                current_prices[orig] = float(val)
            except Exception as e:
                print(f"Price fetch error: {e}")
            
            # 현재가 및 수익률 추가
            for sig in signals_sorted:
                entry = sig['entry_price']
                curr = current_prices.get(sig['ticker'], entry)
                sig['current_price'] = round(curr, 0)
                if entry > 0 and curr > 0:
                    sig['return_pct'] = round(((curr - entry) / entry) * 100, 2)
                else:
                    sig['return_pct'] = 0
        
        return jsonify({
            'signals': signals_sorted,
            'count': len(signals_sorted),
            'total_filtered': len(signals),
            'generated_at': datetime.now().isoformat()
        })
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@app.route('/api/kr/history/<ticker>')
def get_kr_history(ticker):
    """Get price history for a ticker (Direct list for Lightweight Charts)"""
    try:
        # Fetch chart data using FDR or yfinance fallback
        symbol = ticker
        
        # 기간 설정
        period_days = 365
        period_arg = request.args.get('period', '1y')
        
        if period_arg == '1mo': period_days = 30
        elif period_arg == '3mo': period_days = 90
        elif period_arg == '6mo': period_days = 180
        
        end_date = datetime.now()
        start_date = end_date - timedelta(days=period_days)
        
        df = pd.DataFrame()
        
        # Try FinanceDataReader first
        if FDR_AVAILABLE:
            try:
                df = fdr.DataReader(symbol, start_date, end_date)
            except Exception as fdr_err:
                print(f"FDR fetch failed for {ticker}: {fdr_err}")
        
        # Fallback to yfinance if FDR failed or unavailable
        if df.empty:
            try:
                yahoo_ticker = f"{symbol}.KS"
                df = yf.download(yahoo_ticker, start=start_date, end=end_date, progress=False)
                if df.empty:
                    yahoo_ticker = f"{symbol}.KQ"  # Try KOSDAQ
                    df = yf.download(yahoo_ticker, start=start_date, end=end_date, progress=False)
            except Exception as yf_err:
                print(f"YFinance fetch failed for {ticker}: {yf_err}")
        
        if df.empty:
            return jsonify([]), 200 # Return empty list instead of 404 for safer frontend handling
        
        chart_data = []
        for date, row in df.iterrows():
            chart_data.append({
                'date': date.strftime('%Y-%m-%d'),
                'open': int(row['Open']),
                'high': int(row['High']),
                'low': int(row['Low']),
                'close': int(row['Close']),
                'volume': int(row['Volume'])
            })
        
        return jsonify(chart_data)
        
    except Exception as e:
        print(f"History fetch error for {ticker}: {e}")
        return jsonify({'error': str(e)}), 500


@app.route('/api/kr/ai-analysis')
def kr_ai_analysis():
    """
    Get AI recommendations (Top 10 VCP signals with GPT + Gemini analysis)
    Supports caching with ?refresh=true to force regeneration
    """
    try:
        from kr_market.kr_ai_analyzer import generate_ai_recommendations
        
        signals_file = 'kr_market/data/signals_log.csv'
        if not os.path.exists(signals_file):
            return jsonify({'error': 'signals_log.csv not found'}), 404
        
        # 현재 시그널의 최신 날짜 확인
        df = pd.read_csv(signals_file, encoding='utf-8-sig')
        df['ticker'] = df['ticker'].astype(str).str.zfill(6)
        
        # 가장 최근 시그널 날짜
        # 가장 최근 시그널 날짜
        if 'status' in df.columns:
            open_signals = df[df['status'] == 'OPEN']
        else:
            open_signals = df  # status 컬럼 없으면 전체 사용
            
        if open_signals.empty:
            return jsonify({'error': 'No open signals'}), 404
        
        latest_signal_date = open_signals['signal_date'].max()
        
        # 강제 새로고침 여부 확인
        force_refresh = request.args.get('refresh', 'false').lower() == 'true'
        
        # 저장된 분석 결과 확인 (refresh=true 시 캐시 무시)
        KR_AI_ANALYSIS_FILE = 'kr_market/data/kr_ai_analysis.json'
        if not force_refresh and os.path.exists(KR_AI_ANALYSIS_FILE):
            try:
                with open(KR_AI_ANALYSIS_FILE, 'r', encoding='utf-8') as f:
                    cached_data = json.load(f)
                
                # 같은 날짜의 분석 결과가 있으면 반환
                if cached_data.get('signal_date') == latest_signal_date:
                    print(f"✅ Using cached AI analysis for {latest_signal_date}")
                    return jsonify(cached_data)
            except Exception as load_error:
                print(f"Cache load error: {load_error}")
        
        print(f"🔄 Generating new AI analysis for {latest_signal_date} (refresh={force_refresh})...")
        
        # 종목명/시장 로드
        stock_names = {}
        stock_markets = {}
        stocks_file = 'kr_market/data/stock_list.csv'
        if os.path.exists(stocks_file):
            stocks_df = pd.read_csv(stocks_file, encoding='utf-8-sig', dtype={'ticker': str})
            stocks_df['ticker'] = stocks_df['ticker'].astype(str).str.strip().str.zfill(6)
            stock_names = dict(zip(stocks_df['ticker'], stocks_df['name']))
            stock_markets = dict(zip(stocks_df['ticker'], stocks_df['market']))
        
        # VCP 필터링 및 Top 10 선정
        today = datetime.now().strftime('%Y-%m-%d')
        signals = []
        
        for _, row in open_signals.iterrows():
            score = float(row['score']) if pd.notna(row['score']) else 0
            contraction = float(row['contraction_ratio']) if pd.notna(row['contraction_ratio']) else 1
            foreign_5d = int(row['foreign_5d']) if pd.notna(row['foreign_5d']) else 0
            inst_5d = int(row['inst_5d']) if pd.notna(row['inst_5d']) else 0
            signal_date = row['signal_date']
            
            if contraction > 0.8 or (foreign_5d < 0 and inst_5d < 0) or score < 50:
                continue
            
            contraction_score = (1 - contraction) * 100
            supply_score = min((foreign_5d + inst_5d) / 100000, 30)
            today_bonus = 10 if signal_date == today else 0
            final_score = (score * 0.4) + (contraction_score * 0.3) + (supply_score * 0.2 * 10) + today_bonus
            
            signals.append({
                'ticker': row['ticker'],
                'name': stock_names.get(row['ticker'], ''),
                'market': stock_markets.get(row['ticker'], ''),
                'score': round(score, 1),
                'contraction_ratio': round(contraction, 2),
                'foreign_5d': foreign_5d,
                'inst_5d': inst_5d,
                'entry_price': round(row['entry_price'], 0) if pd.notna(row['entry_price']) else 0,
                'final_score': round(final_score, 1)
            })
        
        # ========== 테마 종목 자동 추가 ==========
        existing_tickers = {s['ticker'] for s in signals}
        theme_tickers = ThemeManager.get_all_target_tickers()
        
        # open_signals를 ticker로 인덱싱하여 빠른 조회
        supply_data = {}
        for _, row in open_signals.iterrows():
            ticker = str(row['ticker']).zfill(6)
            supply_data[ticker] = {
                'foreign_5d': int(row['foreign_5d']) if pd.notna(row['foreign_5d']) else 0,
                'inst_5d': int(row['inst_5d']) if pd.notna(row['inst_5d']) else 0,
                'score': float(row['score']) if pd.notna(row['score']) else 0,
                'contraction_ratio': float(row['contraction_ratio']) if pd.notna(row['contraction_ratio']) else 0.5,
                'entry_price': float(row['entry_price']) if pd.notna(row['entry_price']) else 0
            }
        
        for t_ticker in theme_tickers:
            t_ticker = str(t_ticker).zfill(6)
            if t_ticker in existing_tickers:
                continue
            
            theme = ThemeManager.get_theme(t_ticker)
            if not theme:
                continue
            
            t_name = stock_names.get(t_ticker, t_ticker)
            t_market = stock_markets.get(t_ticker, 'KOSPI')
            
            # 수급 데이터 조회 (open_signals에서 먼저 찾고, 없으면 pykrx로 조회)
            sd = supply_data.get(t_ticker, None)
            if sd:
                foreign_5d = sd.get('foreign_5d', 0)
                inst_5d = sd.get('inst_5d', 0)
                vcp_score = sd.get('score', 0)
                contraction = sd.get('contraction_ratio', 0.5)
                entry_price = sd.get('entry_price', 0)
            else:
                # pykrx로 실시간 수급 데이터 조회
                print(f"  📊 수급 조회 중: {t_ticker} ({t_name})")
                supply = get_supply_data(t_ticker, days=5)
                foreign_5d = supply.get('foreign_5d', 0)
                inst_5d = supply.get('inst_5d', 0)
                vcp_score = 0
                contraction = 0.5
                entry_price = 0
            
            # 현재가 조회 (실패해도 계속 진행)
            try:
                cp = get_real_stock_data(t_ticker)
                current_price = cp.get('current_price', 0) if cp else 0
            except:
                current_price = 0
            
            # 현재가가 없으면 entry_price 또는 기본값 사용
            if current_price <= 0:
                current_price = entry_price if entry_price > 0 else 10000
            
            signals.append({
                'ticker': t_ticker,
                'name': t_name or t_ticker,
                'market': t_market,
                'score': vcp_score if vcp_score > 0 else 65,  # VCP 점수 있으면 사용
                'contraction_ratio': contraction,
                'foreign_5d': foreign_5d,
                'inst_5d': inst_5d,
                'entry_price': current_price,
                'final_score': 55
            })
        
        # Top 10 (VCP 시그널 우선) + 테마 종목 (최대 25개)
        vcp_signals = sorted([s for s in signals if s['final_score'] >= 60], key=lambda x: x['final_score'], reverse=True)[:10]
        theme_signals = [s for s in signals if ThemeManager.get_theme(s['ticker']) and s['final_score'] < 60][:15]
        top_signals = vcp_signals + theme_signals
        
        # AI 분석 수행
        result = generate_ai_recommendations(top_signals)
        
        # 결과에 시그널 날짜 추가
        result['signal_date'] = latest_signal_date
        
        # 파일에 저장 (최신 버전 + 히스토리 보관)
        os.makedirs(os.path.dirname(KR_AI_ANALYSIS_FILE), exist_ok=True)
        
        # 1. 최신 분석 파일 (항상 덮어쓰기)
        with open(KR_AI_ANALYSIS_FILE, 'w', encoding='utf-8') as f:
            json.dump(result, f, ensure_ascii=False, indent=2)
        
        # 2. 히스토리 파일 (날짜별 보관)
        history_dir = 'kr_market/data/history'
        os.makedirs(history_dir, exist_ok=True)
        history_file = f"{history_dir}/kr_ai_analysis_{latest_signal_date}.json"
        with open(history_file, 'w', encoding='utf-8') as f:
            json.dump(result, f, ensure_ascii=False, indent=2)
        
        print(f"✅ AI analysis saved to {KR_AI_ANALYSIS_FILE}")
        
        return jsonify(result)
        
    except Exception as e:
        print(f"KR AI Analysis error: {e}")
        traceback.print_exc()
        return jsonify({'error': str(e)}), 500


@app.route('/api/kr/analyze-stock', methods=['POST'])
def api_kr_analyze_stock():
    """Real-time On-Demand AI Analysis"""
    try:
        data = request.json
        ticker = data.get('ticker')
        if not ticker:
            return jsonify({'error': 'Ticker is required'}), 400
            
        print(f"🚀 On-Demand Analysis Triggered for {ticker}")
        
        from kr_market.kr_ai_analyzer import analyze_single_stock_realtime
        result = analyze_single_stock_realtime(ticker)
        
        # Save or Log if needed? For now just return
        return jsonify(result)
        
    except Exception as e:
        print(f"On-Demand Analysis Error: {e}")
        traceback.print_exc()
        return jsonify({'error': str(e)}), 500


@app.route('/api/kr/ai-summary/<ticker>')
def kr_ai_summary(ticker):
    """Get individual AI summary for a stock"""
    try:
        # Load AI analysis
        cache_file = 'kr_market/data/kr_ai_analysis.json'
        if not os.path.exists(cache_file):
            return jsonify({'error': 'No AI analysis available'}), 404
        
        with open(cache_file, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        # Find ticker in signals
        signals = data.get('signals', [])
        for signal in signals:
            if signal.get('ticker') == ticker.zfill(6):
                return jsonify(signal)
        
        return jsonify({'error': 'Ticker not found in analysis'}), 404
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@app.route('/api/kr/ai-history-dates')
def get_kr_ai_history_dates():
    """Get list of available KR AI analysis history dates"""
    try:
        history_dir = 'kr_market/data/history'
        
        if not os.path.exists(history_dir):
            return jsonify({'dates': []})
        
        dates = []
        for filename in os.listdir(history_dir):
            if filename.startswith('kr_ai_analysis_') and filename.endswith('.json'):
                # Extract date from filename
                date = filename.replace('kr_ai_analysis_', '').replace('.json', '')
                dates.append(date)
        
        # Sort descending (newest first)
        dates.sort(reverse=True)
        
        return jsonify({
            'dates': dates,
            'count': len(dates)
        })
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@app.route('/api/kr/ai-history/<date>')
def get_kr_ai_history(date):
    """Get KR AI analysis for a specific date"""
    try:
        history_file = f'kr_market/data/history/kr_ai_analysis_{date}.json'
        
        if not os.path.exists(history_file):
            return jsonify({'error': f'No analysis found for {date}'}), 404
        
        with open(history_file, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        return jsonify(data)
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@app.route('/api/kr/cumulative-return')
def get_kr_cumulative_return():
    """Calculate cumulative return for KR signals portfolio"""
    try:
        signals_path = 'kr_market/data/signals_log.csv'
        
        if not os.path.exists(signals_path):
            return jsonify({'error': 'No signals file'}), 404
        
        df = pd.read_csv(signals_path, encoding='utf-8-sig')
        df['ticker'] = df['ticker'].astype(str).str.zfill(6)
        
        # Get OPEN signals
        open_signals = df[df['status'] == 'OPEN']
        
        # Calculate returns for each signal
        returns = []
        for _, row in open_signals.iterrows():
            entry = row['entry_price']
            ticker = row['ticker']
            
            # Fetch current price
            try:
                from kr_market.kr_ai_analyzer import fetch_current_price
                current = fetch_current_price(ticker)
                if current > 0 and entry > 0:
                    ret = ((current - entry) / entry) * 100
                    returns.append({
                        'ticker': ticker,
                        'return_pct': round(ret, 2)
                    })
            except:
                pass
        
        # Calculate portfolio metrics
        if returns:
            avg_return = sum(r['return_pct'] for r in returns) / len(returns)
            winners = len([r for r in returns if r['return_pct'] > 0])
            losers = len([r for r in returns if r['return_pct'] <= 0])
            win_rate = (winners / len(returns)) * 100 if returns else 0
        else:
            avg_return = 0
            win_rate = 0
            winners = 0
            losers = 0
        
        return jsonify({
            'cumulative_return': round(avg_return, 2),
            'win_rate': round(win_rate, 1),
            'winners': winners,
            'losers': losers,
            'total_positions': len(returns),
            'positions': returns
        })
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@app.route('/api/kr/performance')
def kr_performance():
    """Get signal performance metrics"""
    try:
        from kr_market import signal_tracker
        tracker = signal_tracker.SignalTracker()
        report = tracker.get_performance_report()
        
        return jsonify({'status': 'success', 'data': report})
    except Exception as e:
        return jsonify({'status': 'error', 'message': str(e)}), 500


@app.route('/api/kr/market-gate')
def get_kr_market_gate():
    """Get KR market condition gate status"""
    try:
        from kr_market.market_gate import get_market_status
        
        status = get_market_status()
        
        return jsonify({
            'status': status.get('status', 'UNKNOWN'),
            'kospi': status.get('kospi', {}),
            'kosdaq': status.get('kosdaq', {}),
            'usd_krw': status.get('usd_krw', 0),
            'foreign_net': status.get('foreign_net', 0),
            'gate_score': status.get('gate_score', 0),
            'recommendation': status.get('recommendation', ''),
            'generated_at': datetime.now().isoformat()
        })
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@app.route('/api/kr/vcp-scan')
def kr_vcp_scan():
    """Run VCP scanner"""
    try:
        from kr_market import signal_tracker
        tracker = signal_tracker.SignalTracker()
        signals = tracker.scan_today_signals()
        
        return jsonify({
            'status': 'success',
            'data': signals.to_dict('records') if not signals.empty else [],
            'count': len(signals)
        })
    except Exception as e:
        import traceback
        traceback.print_exc()
        return jsonify({'status': 'error', 'message': str(e)}), 500



# ==================== MACRO ECONOMIC INDICATORS API ====================

@app.route('/api/kr/macro-indicators')
def get_macro_indicators():
    """통합 매크로 경제 지표 조회"""
    try:
        from kr_market.macro_indicators import get_all_macro_indicators
        return jsonify(get_all_macro_indicators())
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@app.route('/api/kr/exchange-rate')
def get_exchange_rate():
    """실시간 USD/KRW 환율"""
    try:
        from kr_market.macro_indicators import get_usd_krw_rate
        return jsonify(get_usd_krw_rate())
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@app.route('/api/kr/interest-spread')
def get_interest_spread():
    """한미 금리차"""
    try:
        from kr_market.macro_indicators import get_interest_rate_spread
        return jsonify(get_interest_rate_spread())
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@app.route('/api/kr/fx-reserves')
def get_fx_reserves():
    """외환보유액"""
    try:
        from kr_market.macro_indicators import get_fx_reserves
        return jsonify(get_fx_reserves())
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@app.route('/api/kr/sector-performance')
def get_sector_perf():
    """섹터별 성과"""
    try:
        from kr_market.macro_indicators import get_sector_performance
        return jsonify(get_sector_performance())
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@app.route('/api/kr/crisis-indicators')
def get_crisis_indicators():
    """위기 시나리오 모니터"""
    try:
        from kr_market.macro_indicators import get_crisis_indicators
        return jsonify(get_crisis_indicators())
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@app.route('/api/kr/strategy-comparison')
def strategy_comparison():
    """전략 모드별 성과 비교 for A/B testing"""
    try:
        from kr_market.performance_analyzer import PerformanceAnalyzer
        from kr_market.signal_tracker import StrategyMode
        
        analyzer = PerformanceAnalyzer()
        modes = [mode.value for mode in StrategyMode]
        comparison = analyzer.get_strategy_comparison(modes)
        
        return jsonify({
            'status': 'success',
            'comparison': comparison,
            'available_modes': modes
        })
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@app.route('/api/kr/ai-performance')
def ai_performance():
    """AI 추천 효과성 분석"""
    try:
        from kr_market.ai_performance_tracker import AIPerformanceTracker
        
        tracker = AIPerformanceTracker()
        report = tracker.generate_ai_effectiveness_report()
        
        return jsonify({
            'status': 'success',
            'report': report
        })
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@app.route('/api/kr/performance-report')
def performance_report():
    """종합 성과 리포트"""
    try:
        from kr_market.performance_analyzer import PerformanceAnalyzer
        
        mode = request.args.get('mode', None)
        analyzer = PerformanceAnalyzer()
        report = analyzer.generate_comprehensive_report(mode)
        
        return jsonify({
            'status': 'success',
            'report': report
        })
    except Exception as e:
        return jsonify({'error': str(e)}), 500


# ==================== GENIUS QUESTION & NICE LAYER API ====================

@app.route('/api/kr/genius-analysis/<ticker>')
def genius_analysis(ticker):
    """천재들의 질문법 (5Why + SCAMPER) 분석 API"""
    try:
        from kr_market.advanced_analyzer import GeniusQuestionMethod
        
        # 종목 데이터 로드
        ticker = ticker.zfill(6)
        stock_data = get_real_stock_data(ticker)
        if not stock_data:
            stock_data = {'name': ticker, 'current_price': 0}
        
        # 5Why 분석
        five_why = GeniusQuestionMethod.five_why_analysis(
            ticker, '투자 적합성 분석', stock_data
        )
        
        # SCAMPER 분석
        scamper = GeniusQuestionMethod.scamper_analysis(ticker, stock_data)
        
        return jsonify({
            'status': 'success',
            'ticker': ticker,
            'five_why': five_why,
            'scamper': scamper
        })
    except Exception as e:
        import traceback
        traceback.print_exc()
        return jsonify({'error': str(e)}), 500


@app.route('/api/kr/nice-layer/<ticker>')
def nice_layer_analysis(ticker):
    """NICE 5-Layer 분석 API - 한국주식 맞춤형"""
    try:
        ticker = ticker.zfill(6)
        stock_data = get_real_stock_data(ticker)
        
        # 기본값
        l1_tech = 50
        l2_supply = 15
        l3_sentiment = 50
        l4_macro = 20
        l5_inst = 15
        
        if stock_data:
            price = stock_data.get('current_price', 0)
            change = stock_data.get('change_pct', 0)
            
            # L1: 기술적 분석 (가격 변동 기반)
            if change > 3:
                l1_tech = 85
            elif change > 1:
                l1_tech = 70
            elif change > -1:
                l1_tech = 55
            else:
                l1_tech = 35
            
            # 테마 기반 점수 보너스
            from kr_market.theme_manager import ThemeManager
            theme = ThemeManager.get_theme(ticker)
            if theme in ['반도체', 'AI인프라']:
                l1_tech = min(100, l1_tech + 10)
                l2_supply = min(30, l2_supply + 5)
            elif theme in ['조선', '방산']:
                l4_macro = min(40, l4_macro + 8)
                l5_inst = min(30, l5_inst + 5)
        
        total_score = l1_tech + l2_supply + l3_sentiment + l4_macro + l5_inst
        
        return jsonify({
            'status': 'success',
            'ticker': ticker,
            'layers': {
                'L1_technical': l1_tech,
                'L2_supply': l2_supply,
                'L3_sentiment': l3_sentiment,
                'L4_macro': l4_macro,
                'L5_institutional': l5_inst
            },
            'total_score': total_score,
            'max_total': 300
        })
    except Exception as e:
        import traceback
        traceback.print_exc()
        return jsonify({'error': str(e)}), 500


# ==================== ERROR HANDLERS ====================

@app.errorhandler(500)
def internal_error(error):
    return jsonify({
        'status': 'error',
        'message': 'Internal server error',
        'details': str(error)
    }), 500


@app.errorhandler(404)
def not_found(error):
    return jsonify({
        'status': 'error',
        'message': 'Endpoint not found'
    }), 404


# ==================== SERVER STARTUP ====================

if __name__ == '__main__':
    # Load sector cache
    _load_sector_cache()
    
    # Start background scheduler
    start_kr_price_scheduler()
    
    # Start Flask server
    print("🚀 Flask Server Starting on port 5001...")
    app.run(debug=True, host='127.0.0.1', port=5001)
