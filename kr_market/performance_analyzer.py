#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
KR Market - Performance Analyzer Module
Provides detailed performance decomposition for strategy effectiveness validation.
"""
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any
from enum import Enum
import os
import logging

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)


class PerformanceAnalyzer:
    """
    Comprehensive performance analysis for trading strategies.
    Supports mode-based filtering for A/B testing.
    """
    
    def __init__(self, data_dir: str = None):
        self.data_dir = data_dir or os.path.dirname(os.path.abspath(__file__))
        self.signals_log_path = os.path.join(self.data_dir, 'data', 'signals_log.csv')
        self.trades_log_path = os.path.join(self.data_dir, 'data', 'trades_log.csv')
        
    def load_signals(self, mode: str = None) -> pd.DataFrame:
        """Load signals log, optionally filtered by strategy mode."""
        if not os.path.exists(self.signals_log_path):
            logger.warning(f"Signals log not found: {self.signals_log_path}")
            return pd.DataFrame()
            
        df = pd.read_csv(self.signals_log_path)
        
        if mode and 'strategy_mode' in df.columns:
            df = df[df['strategy_mode'] == mode]
            
        return df
    
    def get_monthly_returns(self, mode: str = None) -> Dict[str, float]:
        """
        Calculate monthly returns breakdown.
        
        Returns:
            Dict with 'YYYY-MM' keys and return percentages as values
        """
        df = self.load_signals(mode)
        if df.empty:
            return {}
            
        if 'signal_date' not in df.columns:
            return {}
            
        df['month'] = pd.to_datetime(df['signal_date']).dt.to_period('M').astype(str)
        
        # If we have return data
        if 'return_pct' in df.columns:
            monthly = df.groupby('month')['return_pct'].mean().to_dict()
        else:
            # Placeholder if no return data yet
            monthly = df.groupby('month').size().to_dict()
            monthly = {k: 0 for k in monthly.keys()}
            
        return monthly
    
    def calculate_mdd(self, returns: List[float] = None) -> float:
        """
        Calculate Maximum Drawdown.
        
        Returns:
            Maximum drawdown as percentage (e.g., -15.5 for -15.5%)
        """
        if returns is None or len(returns) == 0:
            return 0.0
            
        cumulative = np.cumprod(1 + np.array(returns) / 100)
        rolling_max = np.maximum.accumulate(cumulative)
        drawdowns = (cumulative - rolling_max) / rolling_max * 100
        
        return float(np.min(drawdowns))
    
    def get_benchmark_alpha(self, mode: str = None, benchmark: str = "KOSPI") -> Dict[str, float]:
        """
        Calculate alpha vs benchmark index.
        
        Returns:
            Dict with 'strategy_return', 'benchmark_return', 'alpha'
        """
        df = self.load_signals(mode)
        
        result = {
            "strategy_return": 0.0,
            "benchmark_return": 0.0,
            "alpha": 0.0,
            "benchmark": benchmark
        }
        
        if df.empty or 'return_pct' not in df.columns:
            return result
            
        # Calculate strategy return
        result["strategy_return"] = float(df['return_pct'].sum())
        
        # TODO: Fetch actual benchmark return from KOSPI data
        # For now, use placeholder
        result["benchmark_return"] = 5.0  # Placeholder
        result["alpha"] = result["strategy_return"] - result["benchmark_return"]
        
        return result
    
    def get_sector_breakdown(self, mode: str = None) -> Dict[str, Dict[str, Any]]:
        """
        Analyze performance by sector.
        
        Returns:
            Dict with sector names as keys, containing count, avg_return, win_rate
        """
        df = self.load_signals(mode)
        
        if df.empty or 'sector' not in df.columns:
            return {}
            
        result = {}
        for sector in df['sector'].unique():
            sector_df = df[df['sector'] == sector]
            
            sector_result = {
                "count": len(sector_df),
                "avg_score": float(sector_df['score'].mean()) if 'score' in sector_df.columns else 0
            }
            
            if 'return_pct' in sector_df.columns:
                sector_result["avg_return"] = float(sector_df['return_pct'].mean())
                sector_result["win_rate"] = float((sector_df['return_pct'] > 0).mean() * 100)
            else:
                sector_result["avg_return"] = 0.0
                sector_result["win_rate"] = 0.0
                
            result[sector] = sector_result
            
        return result
    
    def get_strategy_comparison(self, modes: List[str]) -> Dict[str, Dict[str, Any]]:
        """
        Compare performance across different strategy modes.
        
        Args:
            modes: List of strategy mode strings to compare
            
        Returns:
            Dict with mode names as keys, containing performance metrics
        """
        result = {}
        
        for mode in modes:
            df = self.load_signals(mode)
            
            mode_result = {
                "signal_count": len(df),
                "avg_score": float(df['score'].mean()) if len(df) > 0 and 'score' in df.columns else 0
            }
            
            if len(df) > 0 and 'return_pct' in df.columns:
                mode_result["total_return"] = float(df['return_pct'].sum())
                mode_result["avg_return"] = float(df['return_pct'].mean())
                mode_result["win_rate"] = float((df['return_pct'] > 0).mean() * 100)
                mode_result["mdd"] = self.calculate_mdd(df['return_pct'].tolist())
            else:
                mode_result["total_return"] = 0.0
                mode_result["avg_return"] = 0.0
                mode_result["win_rate"] = 0.0
                mode_result["mdd"] = 0.0
                
            result[mode] = mode_result
            
        return result
    
    def get_rolling_sharpe(self, window: int = 20, mode: str = None) -> List[float]:
        """
        Calculate rolling Sharpe ratio.
        
        Args:
            window: Rolling window size in days
            mode: Strategy mode filter
            
        Returns:
            List of rolling Sharpe ratios
        """
        df = self.load_signals(mode)
        
        if df.empty or 'return_pct' not in df.columns:
            return []
            
        returns = df['return_pct'].values
        
        if len(returns) < window:
            return []
            
        rolling_sharpe = []
        for i in range(window, len(returns) + 1):
            window_returns = returns[i-window:i]
            mean_return = np.mean(window_returns)
            std_return = np.std(window_returns)
            
            if std_return > 0:
                sharpe = mean_return / std_return * np.sqrt(252)  # Annualized
            else:
                sharpe = 0
                
            rolling_sharpe.append(float(sharpe))
            
        return rolling_sharpe
    
    def generate_comprehensive_report(self, mode: str = None) -> Dict[str, Any]:
        """
        Generate comprehensive performance report.
        
        Returns:
            Complete performance analysis dictionary
        """
        df = self.load_signals(mode)
        
        report = {
            "generated_at": datetime.now().isoformat(),
            "mode": mode or "all",
            "signal_count": len(df),
            "monthly_returns": self.get_monthly_returns(mode),
            "sector_breakdown": self.get_sector_breakdown(mode),
            "benchmark_alpha": self.get_benchmark_alpha(mode)
        }
        
        if 'return_pct' in df.columns and len(df) > 0:
            returns = df['return_pct'].tolist()
            report["mdd"] = self.calculate_mdd(returns)
            report["total_return"] = float(sum(returns))
            report["avg_return"] = float(np.mean(returns))
            report["std_return"] = float(np.std(returns))
            report["win_rate"] = float((df['return_pct'] > 0).mean() * 100)
            report["sharpe_ratio"] = report["avg_return"] / report["std_return"] * np.sqrt(252) if report["std_return"] > 0 else 0
        else:
            report["mdd"] = 0.0
            report["total_return"] = 0.0
            report["avg_return"] = 0.0
            report["std_return"] = 0.0
            report["win_rate"] = 0.0
            report["sharpe_ratio"] = 0.0
            
        return report


if __name__ == "__main__":
    analyzer = PerformanceAnalyzer()
    report = analyzer.generate_comprehensive_report()
    print("=== Performance Report ===")
    for key, value in report.items():
        print(f"{key}: {value}")
