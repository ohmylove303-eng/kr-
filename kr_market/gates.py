#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
KR Market Gates (NICE Perfect Version)
Implements L0-L5 Gates to filter stocks rigorously.
"""
from dataclasses import dataclass
from typing import Dict, Optional
import pandas as pd
from .config import DEFAULT_TRADE_RULE, DEFAULT_GATE_WEIGHTS
from .market_gate import get_market_status

@dataclass
class GateResult:
    passed: bool
    score: int  # 0-100
    reason: str
    details: Dict

class MarketGate_L0:
    """L0: Market Regime Gate"""
    def evaluate(self) -> GateResult:
        status = get_market_status()
        score = status.get('gate_score', 50)
        
        # Critical Fail Condition: Deep Bear Market
        failed = score < 30
        
        return GateResult(
            passed=not failed,
            score=score,
            reason="Market Regime Check",
            details=status
        )

class LiquidityGuard_L1:
    """L1: Liquidity & Tradability Guard"""
    def evaluate(self, ticker: str, df: pd.DataFrame) -> GateResult:
        if df.empty or len(df) < 20:
            return GateResult(False, 0, "Insufficient Data", {})
            
        # Calculate trailing 20d average turnover
        # Volume * Close approximates turnover
        recent = df.tail(20)
        avg_vol = recent['Volume'].mean()
        curr_price = recent['Close'].iloc[-1]
        
        avg_turnover = avg_vol * curr_price
        min_required = DEFAULT_TRADE_RULE.min_volume_krw
        
        passed = avg_turnover >= min_required
        score = min(100, int((avg_turnover / min_required) * 60)) # Base score
        
        if passed:
            score = 100
            
        return GateResult(
            passed=passed,
            score=score,
            reason=f"Turnover: {avg_turnover/100000000:.1f}억 (Min {min_required/100000000:.1f}억)",
            details={'turnover': avg_turnover}
        )

class TechnicalGate_L2:
    """L2: Technical Analysis (VCP + Palantir + Palantir Mini)"""
    def evaluate(self, vcp_result: dict, df: pd.DataFrame) -> GateResult:
        if df.empty or len(df) < 120:
             # VCP result might exist from signal_tracker (which uses 50 days), but Palantir needs 120
             if not vcp_result:
                 return GateResult(False, 0, "Insufficient Data for Palantir", {})
        
        # 1. Calculate Moving Averages
        ma20 = df['Close'].rolling(window=20).mean().iloc[-1]
        ma60 = df['Close'].rolling(window=60).mean().iloc[-1]
        ma120 = df['Close'].rolling(window=120).mean().iloc[-1]
        
        current_price = df['Close'].iloc[-1]
        
        # 2. Palantir Logic (Perfect Alignment: 20 > 60 > 120)
        is_palantir = (ma20 > ma60) and (ma60 > ma120) and (current_price > ma20)
        
        # 3. Palantir Mini Logic (Price > 20MA & 20MA Slope Up)
        recent_ma20 = df['Close'].rolling(window=20).mean()
        slope_ma20 = recent_ma20.iloc[-1] - recent_ma20.iloc[-5] # 5-day slope
        is_palantir_mini = (current_price > ma20) and (slope_ma20 > 0)
        
        # 4. VCP Scoring (from tracker)
        ratio = vcp_result.get('contraction_ratio', 1.0) if vcp_result else 1.0
        vcp_score = max(0, int(100 - (ratio * 50)))
        
        # Final Verification Score
        final_score = vcp_score
        reason_parts = []
        
        if is_palantir: 
            final_score = max(final_score, 90)
            reason_parts.append("🛡️Palantir")
        elif is_palantir_mini:
            final_score = max(final_score, 70)
            reason_parts.append("⚔️Mini")
            
        if vcp_result:
            reason_parts.append(f"VCP({ratio:.2f})")
            
        return GateResult(
            passed=True, # Technical gate rarely hard fails unless broken structure, handled by L0/L1
            score=final_score,
            reason=" + ".join(reason_parts),
            details={
                'is_palantir': is_palantir,
                'is_palantir_mini': is_palantir_mini,
                'ma20': ma20,
                'ma60': ma60,
                'vcp_ratio': ratio
            }
        )

class FlowGate_L3:
    """L3: Smart Money Flow"""
    def evaluate(self, foreign_5d: int, inst_5d: int) -> GateResult:
        net_sum = foreign_5d + inst_5d
        
        # Fail if both are selling heavily
        if foreign_5d < 0 and inst_5d < 0:
             return GateResult(False, 20, "Double Outflow", {})
             
        score = 50
        if net_sum > 0: score += 10
        if foreign_5d > 0 and inst_5d > 0: score += 20 # Double Inflow
        if foreign_5d > 5_000_000: score += 10 # Strong Foreign
        if inst_5d > 3_000_000: score += 10    # Strong Inst
        
        score = min(100, score)
        
        return GateResult(
            passed=True, # Flow usually doesn't hard block unless massive selloff (handled above)
            score=score,
            reason=f"Net Flow: {net_sum}",
            details={'foreign': foreign_5d, 'inst': inst_5d}
        )

class QualityGate_L4:
    """L4: Fundamental Quality"""
    def evaluate(self, market_cap: float) -> GateResult:
        # Simple Market Cap check for now
        # Future: Add PER/PBR/ROE checks if available
        
        min_cap = 50.0 # 500억 (unit usually billion in data)
        
        # If market_cap is in full KRW, adjust (usually it's in billions or millions depending on source)
        # Assuming billions based on blueprint
        
        if market_cap < min_cap:
            return GateResult(False, 30, "Too Small Cap", {'cap': market_cap})
            
        score = 60
        if market_cap > 2000: score = 90 # Big safe cap
        elif market_cap > 500: score = 80
        
        return GateResult(
            passed=True,
            score=score,
            reason="Market Cap Pass",
            details={'cap': market_cap}
        )
