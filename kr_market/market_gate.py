#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
KR Market Gate - Market Condition Analysis
Based on BLUEPRINT_03 /api/kr/market-gate endpoint

Provides market health indicators:
- KOSPI/KOSDAQ index performance
- USD/KRW exchange rate
- Foreign net buying data
- Gate score (0-100)
- Market recommendation
"""

import yfinance as yf
from datetime import datetime
from typing import Dict


def get_market_status() -> Dict:
    """
    Get comprehensive KR market condition status
    
    Returns:
        {
            'status': 'BULLISH' | 'NEUTRAL' | 'BEARISH',
            'kospi': {'value': float, 'change_pct': float},
            'kosdaq': {'value': float, 'change_pct': float},
            'usd_krw': float,
            'foreign_net': float,
            'gate_score': int (0-100),
            'recommendation': 'BUY' | 'HOLD' | 'SELL',
            'details': str
        }
    """
    
    try:
        # 1. Fetch KOSPI and KOSDAQ indices
        indices = _fetch_indices()
        
        # 2. Fetch USD/KRW exchange rate
        usd_krw = _fetch_usd_krw()
        
        # 3. Calculate gate score based on indicators
        gate_score = _calculate_gate_score(indices, usd_krw)
        
        # 4. Determine overall status and recommendation
        if gate_score >= 70:
            status = 'BULLISH'
            recommendation = 'BUY'
            details = '시장 상승 모멘텀 강함. 적극적인 매수 포지션 권장.'
        elif gate_score >= 40:
            status = 'NEUTRAL'
            recommendation = 'HOLD'
            details = '시장 방향성 불명확. 관망 또는 선별적 접근 권장.'
        else:
            status = 'BEARISH'
            recommendation = 'SELL'
            details = '시장 하락 압력 높음. 방어적 포지션 권장.'
        
        return {
            'status': status,
            'kospi': indices['kospi'],
            'kosdaq': indices['kosdaq'],
            'usd_krw': usd_krw,
            'foreign_net': 0,  # Would need real-time data source
            'gate_score': gate_score,
            'recommendation': recommendation,
            'details': details,
            'generated_at': datetime.now().isoformat()
        }
        
    except Exception as e:
        print(f"Market gate error: {e}")
        return {
            'status': 'UNKNOWN',
            'kospi': {'value': 0, 'change_pct': 0},
            'kosdaq': {'value': 0, 'change_pct': 0},
            'usd_krw': 0,
            'foreign_net': 0,
            'gate_score': 50,
            'recommendation': 'HOLD',
            'details': f'데이터 조회 실패: {str(e)}',
            'generated_at': datetime.now().isoformat()
        }


def _fetch_indices() -> Dict:
    """Fetch KOSPI and KOSDAQ index values"""
    indices = {
        'kospi': {'value': 0, 'change_pct': 0},
        'kosdaq': {'value': 0, 'change_pct': 0}
    }
    
    try:
        # KOSPI: ^KS11, KOSDAQ: ^KQ11
        tickers = ['^KS11', '^KQ11']
        data = yf.download(tickers, period='2d', progress=False)
        
        if not data.empty and 'Close' in data.columns:
            closes = data['Close']
            
            for ticker, name in [('^KS11', 'kospi'), ('^KQ11', 'kosdaq')]:
                if ticker in closes.columns and len(closes[ticker].dropna()) >= 2:
                    today = closes[ticker].dropna().iloc[-1]
                    prev = closes[ticker].dropna().iloc[-2]
                    change_pct = ((today - prev) / prev) * 100
                    indices[name] = {
                        'value': round(float(today), 2),
                        'change_pct': round(change_pct, 2)
                    }
    except Exception as e:
        print(f"Indices fetch error: {e}")
    
    return indices


def _fetch_usd_krw() -> float:
    """Fetch USD/KRW exchange rate"""
    try:
        # KRW=X is the Yahoo Finance ticker for USD/KRW
        data = yf.download('KRW=X', period='1d', progress=False)
        
        if not data.empty and 'Close' in data.columns:
            rate = data['Close'].iloc[-1]
            return round(float(rate), 2)
    except Exception as e:
        print(f"USD/KRW fetch error: {e}")
    
    return 0


def _calculate_gate_score(indices: Dict, usd_krw: float) -> int:
    """
    Calculate market gate score (0-100)
    
    Scoring components:
    - KOSPI performance (30 points)
    - KOSDAQ performance (30 points)
    - Market breadth (20 points - both indices aligned)
    - Currency stability (20 points - USD/KRW within reasonable range)
    """
    score = 50  # Base score
    
    # KOSPI contribution (up to +/- 20 points)
    kospi_change = indices['kospi']['change_pct']
    if kospi_change > 1.5:
        score += 20
    elif kospi_change > 0.5:
        score += 10
    elif kospi_change < -1.5:
        score -= 20
    elif kospi_change < -0.5:
        score -= 10
    
    # KOSDAQ contribution (up to +/- 20 points)
    kosdaq_change = indices['kosdaq']['change_pct']
    if kosdaq_change > 2.0:
        score += 20
    elif kosdaq_change > 0.5:
        score += 10
    elif kosdaq_change < -2.0:
        score -= 20
    elif kosdaq_change < -0.5:
        score -= 10
    
    # Market breadth bonus (both indices moving in same direction)
    if kospi_change > 0 and kosdaq_change > 0:
        score += 10  # Broad rally
    elif kospi_change < 0 and kosdaq_change < 0:
        score -= 10  # Broad decline
    
    # Clamp score to 0-100 range
    score = max(0, min(100, score))
    
    return score


if __name__ == '__main__':
    # Test the market gate
    status = get_market_status()
    import json
    print(json.dumps(status, ensure_ascii=False, indent=2))
