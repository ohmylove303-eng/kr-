"""
KR Market Configuration Classes
Extracted from BLUEPRINT_09_SUPPORTING_MODULES.md
"""

from dataclasses import dataclass
from typing import Optional


@dataclass
class VCPConfig:
    """VCP Scoring Configuration"""
    
    # Scoring weights (must sum to 1.0)
    weight_foreign: float = 0.40    # Foreign investor flow (40%)
    weight_inst: float = 0.30       # Institutional flow (30%)
    weight_technical: float = 0.20  # Technical analysis (20%)
    weight_fundamental: float = 0.10 # Fundamentals (10%)
    
    # Thresholds for strong signals
    foreign_strong_buy: int = 5_000_000  # 5M shares
    inst_strong_buy: int = 3_000_000     # 3M shares
    
    # VCP pattern requirements
    min_score: int = 60                  # Minimum VCP score to trigger signal
    max_contraction_ratio: float = 0.8   # Maximum volatility contraction
    min_contraction_days: int = 10       # Minimum consolidation period
    
    # Volume requirements
    min_avg_volume: int = 100_000        # Minimum average daily volume
    volume_surge_threshold: float = 1.5  # Breakout volume surge
    
    # Price requirements
    min_price: int = 1000                # Minimum stock price (KRW)
    max_price: int = 500_000             # Maximum stock price
    
    # Market cap requirements (billion KRW)
    min_market_cap: float = 50.0         # 50 billion KRW minimum
    max_market_cap: Optional[float] = None


@dataclass
class BacktestConfig:
    """Backtest Configuration"""
    
    # Exit strategies
    stop_loss_pct: float = 5.0           # Stop loss at -5%
    take_profit_pct: float = 15.0        # Take profit at +15%
    trailing_stop_pct: float = 5.0       # Trailing stop from peak
    max_hold_days: int = 15              # Maximum holding period
    
    # Position sizing
    position_size_pct: float = 10.0      # 10% of capital per position
    max_positions: int = 10              # Maximum concurrent positions
    initial_capital: float = 10_000_000  # 10 million KRW
    
    # Slippage and fees
    slippage_pct: float = 0.1            # 0.1% slippage
    commission_pct: float = 0.015        # 0.015% commission (each side)
    
    # Risk management
    max_sector_exposure: float = 0.3     # Max 30% in one sector
    max_daily_loss_pct: float = 2.0      # Stop trading if -2% daily loss
    
    # Validation period
    lookback_days: int = 365             # Historical test period


@dataclass
class TrendConfig:
    """Trend Analysis Thresholds"""
    
    strong_buy_inst: int = 3_000_000      # Institutional strong buy threshold
    buy_inst: int = 1_000_000             
    strong_buy_foreign: int = 5_000_000   # Foreign strong buy threshold
    buy_foreign: int = 2_000_000
    high_ratio_inst: float = 8.0          # High ratio threshold
    high_ratio_foreign: float = 12.0


@dataclass
class TradeRuleConfig:
    """NICE Execution Rules (SSOT)"""
    stop_loss_pct: float = 7.0         # Fixed 7% SL or Pivot based
    tp1_pct: float = 15.0              # Target Profit 1
    tp2_pct: float = 30.0              # Target Profit 2
    time_stop_days: int = 15           # Time cut
    min_volume_krw: int = 10_000_000_000 # Min 10B/day turnover (Liquidity Gate)


@dataclass
class GateWeights:
    """NICE Gate Scoring Weights"""
    market: float = 0.10      # Market regime
    liquidity: float = 0.20   # Liquidity guard
    vcp: float = 0.30         # Core VCP pattern
    flow: float = 0.25        # Foreign/Inst flow
    quality: float = 0.15     # Fundamentals


# Default configurations
DEFAULT_VCP_CONFIG = VCPConfig()
DEFAULT_BACKTEST_CONFIG = BacktestConfig()
DEFAULT_TREND_CONFIG = TrendConfig()
DEFAULT_TRADE_RULE = TradeRuleConfig()
DEFAULT_GATE_WEIGHTS = GateWeights()


# Parameter Validation Records (for transparency and reproducibility)
PARAM_VALIDATION = {
    "foreign_min": {
        "value": 5_000_000,
        "optimized_period": "2023-01 to 2024-12",
        "in_sample_sharpe": 1.23,
        "out_sample_validated": True,
        "notes": "Threshold for strong foreign buying pressure"
    },
    "contraction_max": {
        "value": 0.8,
        "optimized_period": "2023-01 to 2024-12",
        "in_sample_win_rate": 0.62,
        "out_sample_validated": True,
        "notes": "Maximum volatility contraction ratio for VCP pattern"
    },
    "hold_days": {
        "value": 15,
        "optimized_period": "2023-01 to 2024-12",
        "optimal_range": (10, 20),
        "notes": "Maximum holding period based on historical performance"
    },
    "stop_loss_pct": {
        "value": 5.0,
        "optimized_period": "2023-01 to 2024-12",
        "risk_adjusted": True,
        "notes": "Stop loss percentage to limit downside"
    },
    "near_high_pct": {
        "value": 0.85,
        "optimized_period": "2023-01 to 2024-12",
        "notes": "Price must be within 15% of 52-week high"
    }
}
