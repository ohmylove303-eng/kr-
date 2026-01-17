#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
KR VCP AI Analyzer
GPT + Gemini를 활용한 VCP 종목 AI 분석
Based on BLUEPRINT_04_BACKEND_AI_ANALYSIS.md
"""
# FinanceDataReader (Optional)
try:
    import FinanceDataReader as fdr
    FDR_AVAILABLE = True
except ImportError:
    fdr = None
    FDR_AVAILABLE = False

import pandas as pd
import os
import json
from datetime import datetime, timedelta
from typing import Dict, List
from dotenv import load_dotenv
import yfinance as yf

load_dotenv()

OPENAI_API_KEY = os.getenv('OPENAI_API_KEY')
# Validates both GOOGLE_API_KEY and GEMINI_API_KEY for user convenience
GOOGLE_API_KEY = os.getenv('GOOGLE_API_KEY') or os.getenv('GEMINI_API_KEY')


def fetch_market_indices() -> Dict:
    """KOSPI, KOSDAQ 지수 조회 (FDR)"""
    indices = {
        'kospi': {'value': 0, 'change_pct': 0},
        'kosdaq': {'value': 0, 'change_pct': 0}
    }
    
    end = datetime.now()
    start = end - timedelta(days=5)

    # 1. Try FDR first
    if FDR_AVAILABLE:
        try:
            for code, key in [('KS11', 'kospi'), ('KQ11', 'kosdaq')]:
                df = fdr.DataReader(code, start, end)
                if not df.empty and len(df) >= 2:
                    today = df.iloc[-1]['Close']
                    prev = df.iloc[-2]['Close']
                    change_pct = ((today - prev) / prev) * 100
                    indices[key] = {
                        'value': round(float(today), 2),
                        'change_pct': round(change_pct, 2)
                    }
            return indices
        except Exception as e:
            print(f"FDR Market indices fetch error: {e}")
    
    # 2. Fallback to yfinance
    try:
        # KOSPI: ^KS11, KOSDAQ: ^KQ11
        for code, key in [('^KS11', 'kospi'), ('^KQ11', 'kosdaq')]:
            ticker = yf.Ticker(code)
            hist = ticker.history(period="5d")
            if not hist.empty and len(hist) >= 2:
                today = hist.iloc[-1]['Close']
                prev = hist.iloc[-2]['Close']
                change_pct = ((today - prev) / prev) * 100
                indices[key] = {
                    'value': round(float(today), 2),
                    'change_pct': round(change_pct, 2)
                }
    except Exception as e:
        print(f"YFinance Market indices fetch error: {e}")
    
    return indices


def fetch_current_price(ticker: str) -> int:
    """FDR/YF를 통한 실시간 현재가 조회"""
    end = datetime.now()
    start = end - timedelta(days=5)

    # 1. Try FDR
    if FDR_AVAILABLE:
        try:
            df = fdr.DataReader(ticker, start, end)
            if not df.empty:
                return int(df.iloc[-1]['Close'])
        except Exception as e:
            print(f"FDR Current price fetch error for {ticker}: {e}")

    # 2. Fallback to YF
    try:
        # Try .KS then .KQ
        for suffix in ['.KS', '.KQ']:
            t = yf.Ticker(f"{ticker}{suffix}")
            hist = t.history(period='1d')
            if not hist.empty:
                return int(hist.iloc[-1]['Close'])
    except Exception as e:
        print(f"YF Current price fetch error for {ticker}: {e}")
        
    return 0


def fetch_fundamentals(ticker: str, name: str) -> Dict:
    """FDR(Marcap) + yfinance(PER/PBR) 하이브리드 재무지표 조회"""
    fundamentals = {
        'per': 'N/A', 'pbr': 'N/A', 'roe': 'N/A',
        'eps': 'N/A', 'bps': 'N/A', 'div_yield': 'N/A', 'marcap': 'N/A'
    }
    
    try:
        # 1. FDR로 시가총액 우선 확보 (가장 정확함)
        # Performance Note: Listing 전체 로드는 무거우므로 생략하거나 캐시된 데이터 권장.
        # 여기서는 yfinance fallback을 주로 사용하되, yf가 실패하면 N/A
        pass 
        
        # 2. yfinance로 주요 지표 조회 (PER, PBR 등은 yf가 유일한 무료 소스)
        # Try .KS then .KQ
        info = {}
        for suffix in ['.KS', '.KQ']:
            try:
                t = yf.Ticker(f"{ticker}{suffix}")
                i = t.info
                if i and 'regularMarketPrice' in i:
                    info = i
                    break
            except: continue
            
        if not info:
             # Fallback
             t = yf.Ticker(f"{ticker}.KS")
             try: info = t.info
             except: pass

        if info:
            # Market Cap
            cap = info.get('marketCap')
            if cap:
                fundamentals['marcap'] = f"{int(cap // 100000000):,}억원"

            # PER/PBR
            per = info.get('trailingPE')
            if per: fundamentals['per'] = f"{per:.2f}"
            
            pbr = info.get('priceToBook')
            if pbr: fundamentals['pbr'] = f"{pbr:.2f}"
            
            # EPS/BPS
            eps = info.get('trailingEps')
            if eps: fundamentals['eps'] = f"{int(eps):,}원"
            
            bps = info.get('bookValue')
            if bps: fundamentals['bps'] = f"{int(bps):,}원"
            
            # Div Yield
            div = info.get('dividendYield')
            if div: fundamentals['div_yield'] = f"{div*100:.2f}%"
            
            # ROE
            roe = info.get('returnOnEquity')
            if roe: fundamentals['roe'] = f"{roe*100:.2f}%"

    except Exception as e:
        print(f"Fundamentals fetch error for {ticker}: {e}")
    
    return fundamentals


def analyze_with_gemini(signal_data: Dict, market_indices: Dict, news: List[Dict]) -> Dict:
    """Google Gemini 3.0 Flash Preview with Google Search grounding"""
    if not GOOGLE_API_KEY:
        return {'recommendation': {'action': 'N/A', 'confidence': 0, 'reason': 'API 키 없음'}, 'grounding_news': []}
    
    try:
        import sys
        print(f"DEBUG: Gemini API 호출 시작 - {signal_data.get('name')}", file=sys.stderr)
        
        from google import genai
        client = genai.Client(api_key=GOOGLE_API_KEY)
        model_id = 'gemini-2.5-pro'
        
        prompt = f"""당신은 한국 주식시장 전문 애널리스트입니다. 최신 정보를 바탕으로 매수/관망/매도 추천을 해주세요.
        
## 분석 대상: {signal_data.get('name')} ({signal_data.get('ticker')})

## 분석 데이터
- VCP Score: {signal_data.get('score')}
- 수축비율: {signal_data.get('contraction_ratio')}
- 외국인/기관 수급: {signal_data.get('foreign_5d', 0):,} / {signal_data.get('inst_5d', 0):,}

## 응답 형식 (JSON만 출력)
{{
  "recommendation": {{
      "action": "BUY/HOLD/SELL",
      "confidence": 0-100,
      "reason": "한줄 핵심 근거"
  }},
  "news_found": []
}}"""

        response = client.models.generate_content(
            model=model_id,
            contents=prompt,
            config={
                'temperature': 0.1,
                # 'response_mime_type': 'application/json'  # 2.5 Pro에서 불안정할 수 있어 제거
            }
        )
        
        print(f"DEBUG: Gemini 응답 수신 완료", file=sys.stderr)
        
        result_text = response.text.strip()
        # 마크다운 코드 블록 제거
        if result_text.startswith('```'):
            lines = result_text.split('\n')
            result_text = '\n'.join(lines[1:-1] if lines[-1] == '```' else lines[1:])
        result_text = result_text.strip()
        
        # JSON 포맷이 아닌 경우 처리
        if not result_text.startswith('{'):
             # 강제로 JSON 찾기
             start = result_text.find('{')
             end = result_text.rfind('}')
             if start != -1 and end != -1:
                 result_text = result_text[start:end+1]
        
        result = json.loads(result_text)
        return {
            'recommendation': result.get('recommendation', {'action': 'HOLD', 'confidence': 50, 'reason': '분석 실패'}),
            'grounding_news': result.get('news_found', [])
        }
    except Exception as e:
        import sys
        print(f"ERROR: Gemini analysis failed: {e}", file=sys.stderr)
        return {'recommendation': {'action': 'HOLD', 'confidence': 50, 'reason': f'분석 오류: {str(e)[:50]}'}, 'grounding_news': []}


def analyze_with_gpt(signal_data: Dict, market_indices: Dict, news: List[Dict]) -> Dict:
    """OpenAI GPT analysis"""
    if not OPENAI_API_KEY:
        return {'action': 'N/A', 'confidence': 0, 'reason': 'API 키 없음'}
    
    try:
        import openai
        client = openai.OpenAI(api_key=OPENAI_API_KEY)
        
        news_text = "\n".join([
            f"- 제목: {n['title']}\n  요약: {n.get('summary', '내용 없음')}" 
            for n in news[:3]
        ]) if news else "최근 뉴스 없음"
        
        prompt = f"""당신은 한국 주식시장 전문 애널리스트입니다. 매수/관망/매도 추천을 해주세요.

## 종목 기본 정보
- 티커: {signal_data.get('ticker')}
- 종목명: {signal_data.get('name')}
- VCP Score: {signal_data.get('score')}
- 수축비율: {signal_data.get('contraction_ratio')}
- 외국인 5일 순매수: {signal_data.get('foreign_5d', 0):,}주
- 기관 5일 순매수: {signal_data.get('inst_5d', 0):,}주
- 진입가: ₩{signal_data.get('entry_price', 0):,}
- 현재가: ₩{signal_data.get('current_price', 0):,} (수익률: {signal_data.get('return_pct', 0):+.2f}%)

## 재무지표
- PER: {signal_data.get('fundamentals', {}).get('per', 'N/A')}
- PBR: {signal_data.get('fundamentals', {}).get('pbr', 'N/A')}
- ROE: {signal_data.get('fundamentals', {}).get('roe', 'N/A')}

## 수집된 뉴스 (Gemini Grounding)
{news_text}

## 응답 형식 (JSON)
{{"action": "BUY/HOLD/SELL", "confidence": 0-100, "reason": "한줄 이유"}}

JSON만 응답하세요."""

        response = client.chat.completions.create(
            model="gpt-4o",
            messages=[{"role": "user", "content": prompt}],
            temperature=0.3,
            max_completion_tokens=200,
            response_format={"type": "json_object"}
        )
        
        result_text = response.choices[0].message.content.strip()
        result = json.loads(result_text)
        return {
            'action': result.get('action', 'HOLD'),
            'confidence': result.get('confidence', 50),
            'reason': result.get('reason', '')
        }
    except Exception as e:
        print(f"GPT analysis error: {e}")
        return {'action': 'HOLD', 'confidence': 50, 'reason': '분석 실패'}


def calculate_nice_layers(signal_data: Dict, theme: str) -> Dict:
    """NICE 5-Layer 점수 계산 - 한국주식 맞춤형"""
    vcp_score = signal_data.get('score', 50)
    foreign_5d = signal_data.get('foreign_5d', 0)
    inst_5d = signal_data.get('inst_5d', 0)
    
    # L1: 기술적 분석 (Tracker에서 계산된 점수 사용)
    # 기존 VCP 점수 단순 변환이 아닌, Gates에서 검증된 Technical Score 사용
    # signal_data에 'nice_tech_score'가 있으면 사용, 없으면 legacy fallback
    l1_tech = signal_data.get('nice_tech_score', min(100, int(vcp_score * 1.2)))
    
    # Palantir Bonus (이미 Technical Score에 반영되었을 수 있으나, AI 관점에서 추가 보정 가능)
    is_palantir = signal_data.get('is_palantir', False)
    if is_palantir:
        l1_tech = max(l1_tech, 95) # Palantir 강제 상향
        
    l1_tech = int(l1_tech) # Ensure int

    # L2: 수급 분석 (외국인 + 기관 순매수)
    supply_flow = foreign_5d + inst_5d
    if supply_flow > 500000:
        l2_supply = 30
    elif supply_flow > 100000:
        l2_supply = 25
    elif supply_flow > 0:
        l2_supply = 20
    else:
        l2_supply = 10
    
    # L3: 시장 심리 (AI 합의 기반)
    gpt_action = signal_data.get('gpt_recommendation', {}).get('action', 'HOLD')
    gemini_action = signal_data.get('gemini_recommendation', {}).get('action', 'HOLD')
    if gpt_action == 'BUY' and gemini_action == 'BUY':
        l3_sentiment = 80
    elif gpt_action == 'BUY' or gemini_action == 'BUY':
        l3_sentiment = 60
    elif gpt_action == 'SELL' or gemini_action == 'SELL':
        l3_sentiment = 30
    else:
        l3_sentiment = 50
    
    # L4: 거시경제 (테마 기반 보너스)
    l4_macro = 20
    if theme in ['방산', '조선', '환율수혜']:
        l4_macro = 32  # 현재 강세 테마
    elif theme in ['반도체', 'AI인프라', 'AI전력']:
        l4_macro = 35  # AI 인프라 투자 확대
    
    # L5: 기관/ETF 참여도
    if inst_5d > 100000:
        l5_inst = 28
    elif inst_5d > 50000:
        l5_inst = 22
    elif inst_5d > 0:
        l5_inst = 18
    else:
        l5_inst = 12
    
    total = l1_tech + l2_supply + l3_sentiment + l4_macro + l5_inst
    
    return {
        'L1_technical': l1_tech,
        'L2_supply': l2_supply,
        'L3_sentiment': l3_sentiment,
        'L4_macro': l4_macro,
        'L5_institutional': l5_inst,
        'total': total,
        'max_total': 300
    }


def calculate_valuation_grade(fundamentals: Dict) -> Dict:
    """밸류에이션 등급 계산"""
    per_str = fundamentals.get('per', 'N/A')
    pbr_str = fundamentals.get('pbr', 'N/A')
    
    grade = 'B'  # 기본: 적정
    description = '적정 가치'
    
    try:
        per = float(per_str) if per_str != 'N/A' else None
        pbr = float(pbr_str) if pbr_str != 'N/A' else None
        
        if per and pbr:
            if per < 10 and pbr < 1.0:
                grade = 'A'
                description = '저평가 (매력적)'
            elif per < 15 and pbr < 1.5:
                grade = 'B+'
                description = '적정~저평가'
            elif per > 30 or pbr > 3.0:
                grade = 'C'
                description = '고평가 (주의)'
            elif per > 20 or pbr > 2.0:
                grade = 'B-'
                description = '적정~고평가'
    except:
        pass
    
    return {
        'grade': grade,
        'description': description,
        'per': per_str,
        'pbr': pbr_str
    }


def calculate_final_score(signal: Dict) -> float:
    """종합 추천 점수 = VCP(40%) + NICE(30%) + AI합의(20%) + 밸류에이션(10%)"""
    vcp_score = signal.get('score', 50)
    nice_total = signal.get('nice_layers', {}).get('total', 150)
    
    # AI 합의 점수
    gpt_conf = signal.get('gpt_recommendation', {}).get('confidence', 50)
    gemini_conf = signal.get('gemini_recommendation', {}).get('confidence', 50)
    ai_score = (gpt_conf + gemini_conf) / 2
    
    # 밸류에이션 점수
    val_grade = signal.get('valuation', {}).get('grade', 'B')
    val_score_map = {'A': 100, 'B+': 80, 'B': 60, 'B-': 45, 'C': 30}
    val_score = val_score_map.get(val_grade, 60)
    
    # 종합 점수 계산
    final = (vcp_score * 0.4) + ((nice_total / 300) * 100 * 0.3) + (ai_score * 0.2) + (val_score * 0.1)
    return round(final, 1)


def generate_ai_recommendations(vcp_signals: List[Dict]) -> Dict:
    """VCP 시그널에 대한 AI 추천 생성 (Main Entry Point) - NICE + 밸류에이션 통합"""
    from kr_market.theme_manager import ThemeManager
    
    market_indices = fetch_market_indices()
    analyzed_signals = []
    
    for signal in vcp_signals:  # 모든 시그널 처리 (테마 포함)
        ticker = signal.get('ticker', '')
        name = signal.get('name', '')
        
        # 1. 테마 자동 할당
        theme = ThemeManager.get_theme(ticker)
        
        # 2. 재무지표 조회
        fundamentals = fetch_fundamentals(ticker, name)
        signal_with_fund = {**signal, 'fundamentals': fundamentals, 'theme': theme}
        
        # 3. 현재가 조회 및 수익률 계산
        current_price = fetch_current_price(ticker)
        if current_price > 0 and signal_with_fund.get('entry_price', 0) > 0:
            entry = signal_with_fund['entry_price']
            ret = ((current_price - entry) / entry) * 100
            signal_with_fund['current_price'] = current_price
            signal_with_fund['return_pct'] = round(ret, 2)
        elif current_price > 0:
            signal_with_fund['current_price'] = current_price
        
        # 4. AI 분석 (Gemini + GPT)
        gemini_res = analyze_with_gemini(signal_with_fund, market_indices, [])
        grounding_news = gemini_res.get('grounding_news', [])
        gpt_rec = analyze_with_gpt(signal_with_fund, market_indices, grounding_news)
        
        signal_with_fund['news'] = grounding_news
        signal_with_fund['gpt_recommendation'] = gpt_rec
        signal_with_fund['gemini_recommendation'] = gemini_res.get('recommendation', {})
        
        # 5. NICE 5-Layer 계산
        nice_layers = calculate_nice_layers(signal_with_fund, theme)
        signal_with_fund['nice_layers'] = nice_layers
        
        # 6. 밸류에이션 등급 계산
        valuation = calculate_valuation_grade(fundamentals)
        signal_with_fund['valuation'] = valuation
        
        # 7. 종합 추천 점수 계산
        final_score = calculate_final_score(signal_with_fund)
        signal_with_fund['final_recommendation_score'] = final_score
        
        # 8. 매매 계획 (Target Price & Stop Loss)
        if current_price > 0:
            signal_with_fund['tp1'] = int(current_price * 1.10)  # +10%
            signal_with_fund['tp2'] = int(current_price * 1.20)  # +20%
            signal_with_fund['stop_loss'] = int(current_price * 0.93)  # -7%
        
        analyzed_signals.append(signal_with_fund)
    
    # 종합 점수 기준 정렬
    analyzed_signals.sort(key=lambda x: x.get('final_recommendation_score', 0), reverse=True)
    
    return {
        'market_indices': market_indices,
        'signals': analyzed_signals,
        'generated_at': datetime.now().isoformat(),
        'signal_date': datetime.now().strftime('%Y-%m-%d')
    }


from kr_market.gates import TechnicalGate_L2, FlowGate_L3
# import FinanceDataReader as fdr (Removed, handled globally at top)
from datetime import datetime, timedelta

def analyze_single_stock_realtime(ticker: str, cached_signal: Dict = None) -> Dict:
    """단일 종목 실시간 AI 분석 (On-Demand) w/ Data Preservation"""
    from kr_market.theme_manager import ThemeManager
    
    # 1. 기본 정보 조회
    stock_names = {}
    stocks_file = 'kr_market/data/stock_list.csv'
    if os.path.exists(stocks_file):
        stocks_df = pd.read_csv(stocks_file, encoding='utf-8-sig', dtype={'ticker': str})
        stock_names = dict(zip(stocks_df['ticker'].astype(str).str.zfill(6), stocks_df['name']))
    
    name = stock_names.get(ticker, ticker)
    theme = ThemeManager.get_theme(ticker)
    
    # [Data Preservation] Use cached data for heavy metrics (Foreign/Inst/Tech)
    # yfinance cannot fetch accurate investor breakdown, causing score drops.
    # So we prefer the cached high-quality data if available.
    foreign_5d = 0
    inst_5d = 0
    nice_tech_score = 0
    is_palantir = False
    
    if cached_signal:
        foreign_5d = cached_signal.get('foreign_5d', 0)
        inst_5d = cached_signal.get('inst_5d', 0)
        nice_tech_score = cached_signal.get('nice_tech_score', 0)
        if nice_tech_score == 0:
             # Fallback to L1 if tech score missing
             nice_tech_score = cached_signal.get('nice_layers', {}).get('L1_technical', 0)
        is_palantir = cached_signal.get('is_palantir', False)
        
    
    # 2. 실시간 가격 및 재무 조회
    current_price = fetch_current_price(ticker)
    fundamentals = fetch_fundamentals(ticker, name)
    market_indices = fetch_market_indices()
    
    # 2.1 기술적/수급 데이터 계산 (Radar Chart용)
    # Only recalculate if we don't have cached data OR if FDR is available (full power)
    should_recalc_tech = (nice_tech_score == 0) or FDR_AVAILABLE
    
    is_palantir_mini = False # Always recalc mini? Or preserve?
    
    if should_recalc_tech:
        nice_tech_score = 0 # reset to calc
    else:
        print(f"ℹ️ Preserving existing Tech/Supply Score for {ticker} (Tech: {nice_tech_score})")
    
    try:
        # OHLCV (120일)
        end_dt = datetime.now()
        start_dt = end_dt - timedelta(days=200) # 넉넉하게
        
        df = pd.DataFrame()
        
        # 1. Try FDR
        if FDR_AVAILABLE:
            try:
                df = fdr.DataReader(ticker, start=start_dt.strftime('%Y-%m-%d'))
            except: pass
            
        # 2. Fallback YF
        if df.empty:
             for suffix in ['.KS', '.KQ']:
                 try:
                     df = yf.download(f"{ticker}{suffix}", start=start_dt, progress=False)
                     if not df.empty:
                         # YF returns columns like (Close, Ticker), need to flatten if MultiIndex
                         if isinstance(df.columns, pd.MultiIndex):
                             df.columns = df.columns.get_level_values(0)
                         break
                 except: pass
        
        
        if not df.empty:
            # Technical Gate
            gate_l2 = TechnicalGate_L2()
            # VCP contraction은 약식으로 0.5 가정 (정밀 계산은 복잡하므로)
            l2_res = gate_l2.evaluate({'contraction_ratio': 0.5}, df)
            nice_tech_score = int(l2_res.score)
            is_palantir = bool(l2_res.details.get('is_palantir', False))
            is_palantir_mini = bool(l2_res.details.get('is_palantir_mini', False))
            
            # Flow Gate (Volume proxy)
            # pykrx가 느리므로 거래량 기반 추정 또는 0 처리
            # 여기서는 API 응답 속도를 위해 0으로 두되, 기존 정보가 있다면 유지하도록 프론트엔드가 처리
            pass 
    except Exception as e:
        print(f"Error fetching technical data: {e}")
    
    # 임시 Signal 객체 생성
    signal = {
        'ticker': ticker,
        'name': name,
        'score': 0, # calculate_nice_layers에서 재계산됨
        'contraction_ratio': 0.5,
        'foreign_5d': foreign_5d, 
        'inst_5d': inst_5d,
        'entry_price': current_price,
        'current_price': current_price,
        'return_pct': 0,
        'fundamentals': fundamentals,
        'theme': theme,
        'nice_tech_score': nice_tech_score,
        'is_palantir': is_palantir,
        'is_palantir_mini': is_palantir_mini
    }
    
    # 2.2 NICE Layer 점수 계산
    calculated_layers = calculate_nice_layers(signal, theme)
    signal['nice_layers'] = calculated_layers # Frontend expects this nesting
    signal['score'] = calculated_layers['total'] # score 필드 동기화

    # 3. AI 분석 실행
    # Gemini (뉴스 검색 포함)
    gemini_res = analyze_with_gemini(signal, market_indices, [])
    grounding_news = gemini_res.get('grounding_news', [])
    
    # GPT (최종 판단)
    gpt_rec = analyze_with_gpt(signal, market_indices, grounding_news)
    
    # [Fallback] GPT가 실패('분석 실패' or 'API 키 없음')하면 Gemini 결과 사용
    # 판정 기준: reason이 에러 메시지거나 action이 N/A인 경우
    gpt_reason = gpt_rec.get('reason', '')
    if gpt_reason == '분석 실패' or gpt_reason == 'API 키 없음' or gpt_rec.get('action') == 'N/A':
        print(f"⚠️ GPT Analysis failed ({gpt_reason}). Falling back to Gemini.")
        
        # Gemini 결과 사용
        gpt_rec = gemini_res.get('recommendation', {})
        gpt_rec['source'] = 'Gemini-2.5-Pro'
        
        # Gemini도 실패했는지 확인
        if gpt_rec.get('action') == 'N/A' or '오류' in gpt_rec.get('reason', ''):
             gpt_rec['source'] = 'System (All Failed)'
    else:
        gpt_rec['source'] = 'GPT-4o'
    
    
    # 4. 결과 종합
    signal['gpt_recommendation'] = gpt_rec
    signal['gemini_recommendation'] = gemini_res.get('recommendation', {})
    signal['news'] = grounding_news
    
    return signal


def analyze_market_theme(theme_name: str) -> Dict:
    """Analyze a specific market theme using Gemini"""
    if not GOOGLE_API_KEY:
        return {'analysis': 'API 키 없음', 'outlook': 'N/A'}

    try:
        from google import genai
        client = genai.Client(api_key=GOOGLE_API_KEY)
        model_id = 'gemini-2.5-pro'
        
        prompt = f"""당신은 한국 주식시장 전문 애널리스트입니다.
현재 '{theme_name}' 테마의 시장 상황과 전망을 분석해주세요.

## 요청사항
1. 해당 테마가 주목받는 이유 (Key Driver)
2. 최근 긍정/부정적 요인
3. 단기 전망 (Outlook)

## 응답 형식 (JSON)
{{
  "analysis": "핵심 분석 내용 (3문장 내외 요약)",
  "outlook": "Positive/Neutral/Negative",
  "key_stocks": ["관련 대장주 1", "관련 대장주 2"]
}}"""

        response = client.models.generate_content(
            model=model_id,
            contents=prompt,
            config={'temperature': 0.3}
        )
        
        result_text = response.text.strip()
        if result_text.startswith('```'):
            lines = result_text.split('\n')
            result_text = '\n'.join(lines[1:-1] if lines[-1] == '```' else lines[1:])
            
        # Extract JSON
        start = result_text.find('{')
        end = result_text.rfind('}')
        if start != -1 and end != -1:
            result_text = result_text[start:end+1]
            
        import json
        return json.loads(result_text)
        
    except Exception as e:
        print(f"Theme analysis failed: {e}")
        return {'analysis': '분석 실패', 'outlook': 'Unknown'}
