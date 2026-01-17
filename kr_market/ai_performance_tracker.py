#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
KR Market - AI Performance Tracker Module
Tracks and analyzes AI recommendation effectiveness.
"""
import pandas as pd
import numpy as np
from datetime import datetime
from typing import Dict, List, Optional, Any
import os
import logging

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)


class AIPerformanceTracker:
    """
    Track AI recommendation performance to validate effectiveness.
    Compares GPT vs Gemini recommendations against actual returns.
    """
    
    def __init__(self, data_dir: str = None):
        self.data_dir = data_dir or os.path.dirname(os.path.abspath(__file__))
        self.signals_log_path = os.path.join(self.data_dir, 'data', 'signals_log.csv')
        
    def load_signals_with_ai(self) -> pd.DataFrame:
        """Load signals that have AI recommendations."""
        if not os.path.exists(self.signals_log_path):
            return pd.DataFrame()
            
        df = pd.read_csv(self.signals_log_path)
        
        # Filter to only signals with AI recommendations
        ai_cols = ['ai_action_gpt', 'ai_action_gemini']
        if any(col in df.columns for col in ai_cols):
            return df
        return pd.DataFrame()
    
    def get_ai_action_stats(self, ai_source: str = "gpt") -> Dict[str, Dict[str, Any]]:
        """
        Analyze performance by AI action (BUY/HOLD/SELL).
        
        Args:
            ai_source: 'gpt' or 'gemini'
            
        Returns:
            Dict with action as key, containing avg_return, win_rate, count
        """
        df = self.load_signals_with_ai()
        
        action_col = f'ai_action_{ai_source}'
        if df.empty or action_col not in df.columns:
            return {"BUY": {}, "HOLD": {}, "SELL": {}}
            
        result = {}
        
        for action in ["BUY", "HOLD", "SELL"]:
            action_df = df[df[action_col] == action]
            
            stats = {
                "count": len(action_df),
                "percentage": len(action_df) / len(df) * 100 if len(df) > 0 else 0
            }
            
            if 'return_pct' in action_df.columns and len(action_df) > 0:
                stats["avg_return"] = float(action_df['return_pct'].mean())
                stats["total_return"] = float(action_df['return_pct'].sum())
                stats["win_rate"] = float((action_df['return_pct'] > 0).mean() * 100)
                stats["max_return"] = float(action_df['return_pct'].max())
                stats["min_return"] = float(action_df['return_pct'].min())
            else:
                stats["avg_return"] = 0.0
                stats["total_return"] = 0.0
                stats["win_rate"] = 0.0
                stats["max_return"] = 0.0
                stats["min_return"] = 0.0
                
            result[action] = stats
            
        return result
    
    def get_confidence_correlation(self, ai_source: str = "gpt") -> Dict[str, Any]:
        """
        Calculate correlation between AI confidence and actual returns.
        
        Args:
            ai_source: 'gpt' or 'gemini'
            
        Returns:
            Dict with correlation coefficient and breakdown by confidence range
        """
        df = self.load_signals_with_ai()
        
        conf_col = f'ai_conf_{ai_source}'
        if df.empty or conf_col not in df.columns or 'return_pct' not in df.columns:
            return {"correlation": 0.0, "confidence_ranges": {}}
            
        # Filter valid data
        valid = df[[conf_col, 'return_pct']].dropna()
        if len(valid) < 5:
            return {"correlation": 0.0, "confidence_ranges": {}}
            
        # Calculate correlation
        correlation = float(valid[conf_col].corr(valid['return_pct']))
        
        # Breakdown by confidence ranges
        confidence_ranges = {}
        ranges = [
            ("high", 80, 100),
            ("medium", 50, 80),
            ("low", 0, 50)
        ]
        
        for label, low, high in ranges:
            range_df = df[(df[conf_col] >= low) & (df[conf_col] < high)]
            if len(range_df) > 0 and 'return_pct' in range_df.columns:
                confidence_ranges[label] = {
                    "range": f"{low}-{high}",
                    "count": len(range_df),
                    "avg_return": float(range_df['return_pct'].mean()),
                    "win_rate": float((range_df['return_pct'] > 0).mean() * 100)
                }
            else:
                confidence_ranges[label] = {
                    "range": f"{low}-{high}",
                    "count": 0,
                    "avg_return": 0.0,
                    "win_rate": 0.0
                }
                
        return {
            "correlation": correlation,
            "confidence_ranges": confidence_ranges,
            "interpretation": self._interpret_correlation(correlation)
        }
    
    def _interpret_correlation(self, corr: float) -> str:
        """Interpret correlation coefficient."""
        if corr > 0.5:
            return "Strong positive - Higher AI confidence leads to better returns"
        elif corr > 0.2:
            return "Moderate positive - AI confidence somewhat predictive"
        elif corr > -0.2:
            return "Weak/No correlation - AI confidence not predictive"
        elif corr > -0.5:
            return "Moderate negative - WARNING: High confidence may indicate worse returns"
        else:
            return "Strong negative - CRITICAL: AI confidence inversely related to returns"
    
    def compare_with_without_ai(self) -> Dict[str, Dict[str, Any]]:
        """
        Compare strategy performance with vs without AI filter.
        
        Returns:
            Dict comparing 'base_strategy', 'ai_buy_only', 'ai_filtered'
        """
        df = self.load_signals_with_ai()
        
        if df.empty:
            return {}
            
        result = {}
        
        # Base strategy (all signals)
        result['base_strategy'] = self._calc_performance(df, "All signals without AI filter")
        
        # AI BUY only (GPT)
        if 'ai_action_gpt' in df.columns:
            buy_only = df[df['ai_action_gpt'] == 'BUY']
            result['gpt_buy_only'] = self._calc_performance(buy_only, "Only GPT BUY recommendations")
            
        # AI BUY only (Gemini)
        if 'ai_action_gemini' in df.columns:
            buy_only = df[df['ai_action_gemini'] == 'BUY']
            result['gemini_buy_only'] = self._calc_performance(buy_only, "Only Gemini BUY recommendations")
            
        # Both AI systems agree on BUY
        if 'ai_action_gpt' in df.columns and 'ai_action_gemini' in df.columns:
            both_buy = df[(df['ai_action_gpt'] == 'BUY') & (df['ai_action_gemini'] == 'BUY')]
            result['dual_ai_buy'] = self._calc_performance(both_buy, "Both GPT and Gemini recommend BUY")
            
        return result
    
    def _calc_performance(self, df: pd.DataFrame, description: str) -> Dict[str, Any]:
        """Calculate performance metrics for a dataframe."""
        perf = {
            "description": description,
            "signal_count": len(df)
        }
        
        if len(df) > 0 and 'return_pct' in df.columns:
            perf["total_return"] = float(df['return_pct'].sum())
            perf["avg_return"] = float(df['return_pct'].mean())
            perf["win_rate"] = float((df['return_pct'] > 0).mean() * 100)
            perf["std_return"] = float(df['return_pct'].std())
            perf["sharpe"] = perf["avg_return"] / perf["std_return"] * np.sqrt(252) if perf["std_return"] > 0 else 0
        else:
            perf["total_return"] = 0.0
            perf["avg_return"] = 0.0
            perf["win_rate"] = 0.0
            perf["std_return"] = 0.0
            perf["sharpe"] = 0.0
            
        return perf
    
    def generate_ai_effectiveness_report(self) -> Dict[str, Any]:
        """
        Generate comprehensive AI effectiveness report.
        
        Returns:
            Complete analysis of AI recommendation performance
        """
        return {
            "generated_at": datetime.now().isoformat(),
            "gpt_action_stats": self.get_ai_action_stats("gpt"),
            "gemini_action_stats": self.get_ai_action_stats("gemini"),
            "gpt_confidence_analysis": self.get_confidence_correlation("gpt"),
            "gemini_confidence_analysis": self.get_confidence_correlation("gemini"),
            "comparison": self.compare_with_without_ai(),
            "recommendation": self._generate_recommendation()
        }
    
    def _generate_recommendation(self) -> str:
        """Generate actionable recommendation based on analysis."""
        comparison = self.compare_with_without_ai()
        
        if not comparison:
            return "Insufficient data for recommendation. Need more signals with AI analysis."
            
        base = comparison.get('base_strategy', {})
        gpt = comparison.get('gpt_buy_only', {})
        gemini = comparison.get('gemini_buy_only', {})
        
        base_return = base.get('avg_return', 0)
        gpt_return = gpt.get('avg_return', 0)
        gemini_return = gemini.get('avg_return', 0)
        
        if gpt_return > base_return and gemini_return > base_return:
            return "POSITIVE: Both AI systems improve base strategy. Continue using AI filter."
        elif gpt_return > base_return:
            return "Consider using GPT recommendations only - performs better than Gemini."
        elif gemini_return > base_return:
            return "Consider using Gemini recommendations only - performs better than GPT."
        else:
            return "WARNING: AI filter may be harming performance. Consider removing or tuning AI."


if __name__ == "__main__":
    tracker = AIPerformanceTracker()
    report = tracker.generate_ai_effectiveness_report()
    print("=== AI Effectiveness Report ===")
    import json
    print(json.dumps(report, indent=2, default=str))
