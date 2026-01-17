#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
KR execution Logic (Order Plan)
Handles Tick Rounding and Trade Plan Construction.
"""
import math
from dataclasses import dataclass
from typing import Optional
from datetime import datetime, timedelta
from .config import DEFAULT_TRADE_RULE, DEFAULT_BACKTEST_CONFIG

@dataclass
class OrderPlan:
    ticker: str
    action: str # BUY, SELL, HOLD
    entry_price: int
    stop_loss: int # -7%
    tp1: int # +10-15%
    tp2: int # +20-30%
    quantity: int
    time_stop_date: str
    risk_reward_ratio: float

def get_tick_size(price: int, market: str = "KOSPI") -> int:
    """
    Calculate KRX tick size based on price range.
    Simplified unified rules for KOSPI/KOSDAQ for stability.
    """
    if price < 1000:
        return 1
    elif price < 5000:
        return 5
    elif price < 10000:
        return 10
    elif price < 50000:
        return 50
    elif price < 100000:
        return 100
    elif price < 500000:
        # KOSPI 500, KOSDAQ 100 (if >100k) usually but let's stick to standard KOSPI steps for safety
        return 500
    else:
        return 1000

def round_to_tick(price: float, market: str = "KOSPI") -> int:
    """Round price to nearest valid tick"""
    price_i = int(price)
    tick = get_tick_size(price_i, market)
    return round(price_i / tick) * tick

class PlanBuilder:
    """Builds execution plan based on SSOT config"""
    
    @staticmethod
    def create_buy_plan(ticker: str, current_price: int, market: str = "KOSPI", risk_pivot: Optional[int] = None) -> OrderPlan:
        rule = DEFAULT_TRADE_RULE
        
        # 1. Entry is Current Price (or Breakout level if specified)
        entry = round_to_tick(current_price, market)
        
        # 2. Stop Loss Calculation
        # If pivot is provided and strictly lower, use pivot. Else use fixed %.
        sl_price_fixed = entry * (1 - rule.stop_loss_pct / 100)
        
        final_sl = sl_price_fixed
        if risk_pivot and risk_pivot < entry:
             # If pivot is too deep (>10%), clamp it to fixed SL
             pivot_drop_pct = (entry - risk_pivot) / entry * 100
             if pivot_drop_pct < 10:
                 final_sl = risk_pivot
        
        sl_price = round_to_tick(final_sl, market)
        
        # 3. Take Profit Targets
        tp1_price = round_to_tick(entry * (1 + rule.tp1_pct / 100), market)
        tp2_price = round_to_tick(entry * (1 + rule.tp2_pct / 100), market)
        
        # 4. Time Stop
        ts_date = (datetime.now() + timedelta(days=rule.time_stop_days)).strftime("%Y-%m-%d")
        
        # 5. Position Sizing (Fixed Capital Model)
        # Based on config initial_capital * 10% usually
        capital_per_trade = DEFAULT_BACKTEST_CONFIG.initial_capital * (DEFAULT_BACKTEST_CONFIG.position_size_pct / 100)
        quantity = int(capital_per_trade // entry)
        
        # 6. Risk/Reward
        risk = entry - sl_price
        reward = tp1_price - entry
        rr = round(reward / risk, 2) if risk > 0 else 0
        
        return OrderPlan(
            ticker=ticker,
            action="BUY",
            entry_price=entry,
            stop_loss=sl_price,
            tp1=tp1_price,
            tp2=tp2_price,
            quantity=quantity,
            time_stop_date=ts_date,
            risk_reward_ratio=rr
        )
