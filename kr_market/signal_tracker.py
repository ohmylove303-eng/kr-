#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
KR Market - Signal Tracker (Real-Time Edition)
Fetching data directly via yfinance to ensure up-to-date analysis.
Supports multiple strategy modes for A/B testing effectiveness.
"""
import pandas as pd
import numpy as np
import os
import FinanceDataReader as fdr
from datetime import datetime, timedelta
from enum import Enum
import logging
import concurrent.futures

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)


class StrategyMode(Enum):
    """Strategy modes for A/B testing effectiveness"""
    VCP_ONLY = "vcp_only"           # VCP pattern only
    FLOW_ONLY = "flow_only"         # Supply/demand flow only
    VCP_FLOW = "vcp_flow"           # VCP + Flow combined
    VCP_FLOW_MACRO = "vcp_flow_macro"  # VCP + Flow + Macro gate
    FULL_AI = "full_ai"             # Full strategy with AI filter

class SignalTracker:
    def __init__(self, data_dir: str = None):
        self.data_dir = data_dir or os.path.dirname(os.path.abspath(__file__))
        self.signals_log_path = os.path.join(self.data_dir, 'data', 'signals_log.csv')
        self.stock_list_path = os.path.join(self.data_dir, 'data', 'stock_list.csv')
        
        # Strategy Parameters
        self.strategy_params = {
            'contraction_max': 0.85,  # Slightly looser for detection
            'near_high_pct': 0.85,    # Within 15% of high
        }
        
    def get_price_data(self, ticker: str, market: str) -> pd.DataFrame:
        """Fetch ~60 days of history from FinanceDataReader"""
        try:
            symbol = ticker
            end_date = datetime.now()
            start_date = end_date - timedelta(days=90) # 3 months
            return fdr.DataReader(symbol, start_date, end_date)
        except Exception as e:
            logger.error(f"Error for {ticker}: {e}")
            return pd.DataFrame()

    def detect_vcp(self, ticker: str, df: pd.DataFrame) -> dict:
        """Analyze DataFrame for VCP pattern (FDR based)"""
        if df.empty or len(df) < 50:
            return None
            
        recent = df.tail(50)
        
        try:
            current_price = float(recent['Close'].values[-1])
            recent_high = float(recent['High'].max())
        except:
            return None
        
        if recent_high == 0: return None
        
        # 1. Price Location (Near High)
        from_high_pct = (recent_high - current_price) / recent_high
        near_high_check = current_price >= (recent_high * self.strategy_params['near_high_pct'])
        
        # 2. Contraction (Volatillity Contraction)
        # Compare first 25 days range vs last 25 days range
        first_half = recent.iloc[:25]
        last_half = recent.iloc[25:]
        
        try:
            range1 = float(first_half['High'].max()) - float(first_half['Low'].min())
            range2 = float(last_half['High'].max()) - float(last_half['Low'].min())
        except:
            return None
        
        if range1 == 0: return None
        contraction_ratio = range2 / range1
        
        contraction_check = contraction_ratio <= self.strategy_params['contraction_max']
        
        if near_high_check and contraction_check:
            # Estimate institutional flow proxy using Volume * Price
            # This is NOT real net buy, but indicates activity
            try:
                avg_vol = last_half['Volume'].mean()
                if isinstance(avg_vol, pd.Series): avg_vol = avg_vol.iloc[0]
                est_flow = float(avg_vol) * current_price * 0.1 # 10% assumption
            except:
                est_flow = 0
            
            return {
                'ticker': ticker,
                'current_price': current_price,
                'entry_price': current_price, # Breakout point approx
                'score': int(100 - (from_high_pct * 100) - (contraction_ratio * 20)), # Simple scoring
                'contraction_ratio': round(contraction_ratio, 2),
                'foreign_5d': int(est_flow * 0.3), # Proxy
                'inst_5d': int(est_flow * 0.4),    # Proxy
                'signal_date': datetime.now().strftime('%Y-%m-%d')
            }
            
        return None

    def scan_today_signals(self, mode: StrategyMode = StrategyMode.VCP_FLOW):
        """
        Scan for trading signals based on specified strategy mode.
        
        Args:
            mode: Strategy mode for filtering (VCP_ONLY, FLOW_ONLY, VCP_FLOW, etc.)
        """
        logger.info(f"🚀 Starting Real-Time Scan [Mode: {mode.value}]...")
        
        if not os.path.exists(self.stock_list_path):
            logger.error("Stock list not found. Run create_stock_list.py first.")
            return []
            
        stocks_df = pd.read_csv(self.stock_list_path)
        targets = stocks_df.head(300)
        
        signals = []
        
        # Initialize NICE Modules
        from kr_market.gates import LiquidityGuard_L1, TechnicalGate_L2, FlowGate_L3, QualityGate_L4
        from kr_market.order_plan import PlanBuilder
        from kr_market.evidence import EvidenceLedger
        
        liquidity_guard = LiquidityGuard_L1()
        technical_gate = TechnicalGate_L2()
        flow_gate = FlowGate_L3()
        quality_gate = QualityGate_L4()
        evidence_ledger = EvidenceLedger()
        
        def process_stock(row):
            try:
                ticker = str(row['ticker']).zfill(6)
                market = row['market']
                name = row['name']
                
                df = self.get_price_data(ticker, market)
                if df.empty: return None
                
                # --- NICE GATE LAYER ---
                
                # L1: Liquidity Guard (Fail Fast)
                l1_res = liquidity_guard.evaluate(ticker, df)
                if not l1_res.passed:
                    # In FULL_AI / VCP_FLOW mode, strict filtering
                    return None 
                
                # Mode-specific filtering
                vcp_result = None
                
                # VCP detection
                if mode in [StrategyMode.VCP_ONLY, StrategyMode.VCP_FLOW, 
                           StrategyMode.VCP_FLOW_MACRO, StrategyMode.FULL_AI]:
                    vcp_result = self.detect_vcp(ticker, df)
                    if mode == StrategyMode.VCP_ONLY and not vcp_result:
                        return None
                        
                # L2: Technical Gate (VCP + Palantir)
                # Replaces old VCPGate
                l2_res = technical_gate.evaluate(vcp_result, df)
                
                # Hard Fail if neither VCP nor Palantir detected in strict modes
                # If mode is FLOW_ONLY, we might skip this
                if mode != StrategyMode.FLOW_ONLY and not l2_res.passed:
                     return None
                
                # Check Palantir Bonus
                is_palantir = l2_res.details.get('is_palantir', False)
                is_palantir_mini = l2_res.details.get('is_palantir_mini', False)

                # Check Theme
                from kr_market.theme_manager import ThemeManager
                theme = ThemeManager.get_theme(ticker)

                # Prepare Flow Data (Proxy for now, ideally real data)
                # detect_vcp calculates proxies, reuse if available
                if vcp_result:
                     f_flow = vcp_result.get('foreign_5d', 0)
                     i_flow = vcp_result.get('inst_5d', 0)
                else:
                     f_flow = 0; i_flow = 0
                     
                # L3: Flow Gate
                l3_res = flow_gate.evaluate(f_flow, i_flow)
                
                # L4: Quality Gate (Market Cap check)
                marcap = float(row.get('marcap', 100000000000)) 
                l4_res = quality_gate.evaluate(marcap / 100000000) # Convert to billions for gate
                
                # --- SCORING ---
                final_score = int(
                    (l1_res.score * 0.2) + 
                    (l2_res.score * 0.4) +  # increased weight for technical
                    (l3_res.score * 0.2) + 
                    (l4_res.score * 0.2)
                )
                
                if theme: final_score += 10 # Theme Bonus
                
                # Filter by Score
                if final_score < 50: return None
                
                # --- EXECUTION LAYER (L6) ---
                current_price = df['Close'].iloc[-1]
                pivot = None # TODO: Calculate Pivot
                plan = PlanBuilder.create_buy_plan(ticker, int(current_price), market, pivot)
                
                # --- EVIDENCE LAYER (L7) ---
                gate_results = {
                    'L1_Liquidity': l1_res,
                    'L2_Technical': l2_res,
                    'L3_Flow': l3_res,
                    'L4_Quality': l4_res
                }
                evidence_ledger.log_signal(ticker, gate_results, plan, final_score)
                
                # Build Result
                result = vcp_result if vcp_result else {
                    'ticker': ticker,
                    'current_price': float(current_price),
                    'entry_price': float(current_price),
                    'contraction_ratio': 0,
                    'foreign_5d': 0,
                    'inst_5d': 0,
                    'signal_date': datetime.now().strftime('%Y-%m-%d')
                }
                
                # Enrich with Plan & Nice Info
                result.update({
                    'name': name,
                    'market': market,
                    'sector': row.get('sector', ''),
                    'theme': theme if theme else '',
                    'strategy_mode': mode.value,
                    'score': final_score,
                    'nice_tech_score': l2_res.score,
                    'is_palantir': is_palantir,
                    'is_palantir_mini': is_palantir_mini,
                    'stop_loss': plan.stop_loss,
                    'tp1': plan.tp1,
                    'tp2': plan.tp2,
                    'time_stop': plan.time_stop_date,
                    'min_turnover': l1_res.details.get('turnover', 0)
                })
                
                return result
                
            except Exception as e:
                # logger.error(f"Error processing {row.get('ticker')}: {e}")
                return None
            return None

        # Parallel Execution
        with concurrent.futures.ThreadPoolExecutor(max_workers=20) as executor:
            futures = [executor.submit(process_stock, row) for _, row in targets.iterrows()]
            for future in concurrent.futures.as_completed(futures):
                res = future.result()
                if res:
                    signals.append(res)
                    theme_tag = f"[{res['theme']}] " if res['theme'] else ""
                    # Log Evidence Created
                    print(f"🔥 Signal Found: {theme_tag}{res['name']} ({res['ticker']}) | Score: {res['score']}")

        # Save results
        if signals:
            sigs_df = pd.DataFrame(signals)
            # Standardize columns for dashboard compatibility
            sigs_df['close'] = sigs_df['current_price']
            sigs_df['foreign_net_buy_5d'] = sigs_df['foreign_5d']
            sigs_df['inst_net_buy_5d'] = sigs_df['inst_5d']
            sigs_df['supply_demand_score'] = sigs_df['score']
            
            # Ensure theme column exists
            if 'theme' not in sigs_df.columns:
                 sigs_df['theme'] = ''

            # Add AI tracking columns (for Phase 3)
            if 'ai_action_gpt' not in sigs_df.columns:
                sigs_df['ai_action_gpt'] = ''
                sigs_df['ai_conf_gpt'] = 0
                sigs_df['ai_action_gemini'] = ''
                sigs_df['ai_conf_gemini'] = 0
            
            # Ensure strategy_mode is present
            if 'strategy_mode' not in sigs_df.columns:
                sigs_df['strategy_mode'] = mode.value
            
            # Ensure status is present
            if 'status' not in sigs_df.columns:
                sigs_df['status'] = 'OPEN'
            
            sigs_df.to_csv(self.signals_log_path, index=False, encoding='utf-8-sig')
            logger.info(f"✅ Saved {len(signals)} signals [Mode: {mode.value}] to {self.signals_log_path}")
        else:
            logger.info(f"No signals detected today [Mode: {mode.value}].")
            
        return signals

if __name__ == "__main__":
    tracker = SignalTracker()
    tracker.scan_today_signals()
