"""
Strategy Ranking Utility

This module provides functionality to rank trading strategies based on their performance
with given market data. Ranks strategies from best to worst based on various metrics.
"""

from typing import Dict, List, Tuple, Any, Optional
import pandas as pd
import numpy as np
from dataclasses import dataclass
import sys
import os

# Handle both direct execution and package import
try:
    # Try relative imports first (when imported as part of package)
    from .manager import StrategyManager
    from .signals import StockSignal, OptionSignal, Action
except ImportError:
    # Add parent directory to path for direct execution
    sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    try:
        from trading_signals.manager import StrategyManager
        from trading_signals.signals import StockSignal, OptionSignal, Action
    except ImportError:
        # Fallback to local imports
        from manager import StrategyManager
        from signals import StockSignal, OptionSignal, Action


@dataclass
class StrategyScore:
    """Data class to hold strategy performance metrics"""
    strategy_name: str
    total_signals: int
    buy_signals: int
    sell_signals: int
    signal_frequency: float  # signals per period
    profit_potential: float  # estimated profit score
    risk_score: float       # risk assessment score
    market_fit: float       # how well strategy fits current market
    overall_score: float    # composite score
    rank: int = 0


class StrategyRanker:
    """
    Utility class to rank trading strategies based on performance with given data
    """
    
    def __init__(self, manager: Optional[StrategyManager] = None):
        """
        Initialize the strategy ranker
        
        Args:
            manager: Optional StrategyManager instance. If None, creates a new one.
        """
        self.manager = manager or StrategyManager()
        self.market_conditions = {}
    
    def analyze_market_conditions(self, df: pd.DataFrame) -> Dict[str, float]:
        """
        Analyze market conditions from the given DataFrame
        
        Args:
            df: DataFrame with price data
            
        Returns:
            Dict containing market condition metrics
        """
        if 'close' not in df.columns:
            raise ValueError("DataFrame must contain 'close' column")
        
        conditions = {}
        
        # Volatility analysis
        returns = df['close'].pct_change().dropna()
        conditions['volatility'] = returns.std() * np.sqrt(252) * 100
        conditions['volatility_percentile'] = self._calculate_percentile(
            returns.rolling(20).std() * np.sqrt(252) * 100
        )
        
        # Trend analysis
        short_ma = df['close'].rolling(20).mean()
        long_ma = df['close'].rolling(50).mean()
        conditions['trend_strength'] = (short_ma.iloc[-1] - long_ma.iloc[-1]) / long_ma.iloc[-1]
        conditions['trend_direction'] = 1 if conditions['trend_strength'] > 0 else -1
        
        # Range analysis
        if 'high' in df.columns and 'low' in df.columns:
            range_width = (df['high'].rolling(20).max() - df['low'].rolling(20).min()) / df['close']
            conditions['range_bound'] = 1 - range_width.iloc[-1]  # Higher = more range-bound
        else:
            conditions['range_bound'] = 0.5
        
        # RSI for momentum
        conditions['rsi'] = self._calculate_rsi(df['close']).iloc[-1]
        
        # Market regime classification
        if conditions['volatility_percentile'] > 70:
            conditions['regime'] = 'high_vol'
        elif conditions['volatility_percentile'] < 30:
            conditions['regime'] = 'low_vol'
        elif abs(conditions['trend_strength']) > 0.1:
            conditions['regime'] = 'trending'
        else:
            conditions['regime'] = 'neutral'
        
        self.market_conditions = conditions
        return conditions
    
    def _calculate_rsi(self, prices: pd.Series, window: int = 14) -> pd.Series:
        """Calculate RSI indicator"""
        delta = prices.diff()
        gain = (delta.where(delta > 0, 0)).rolling(window=window).mean()
        loss = (-delta.where(delta < 0, 0)).rolling(window=window).mean()
        rs = gain / loss
        return 100 - (100 / (1 + rs))
    
    def _calculate_percentile(self, series: pd.Series, window: int = 252) -> float:
        """Calculate percentile of current value vs historical"""
        if len(series) < window:
            window = len(series)
        if window < 2:
            return 50.0
        return (series.iloc[-1] > series.tail(window)).sum() / window * 100
    
    def score_strategy(self, strategy_name: str, df: pd.DataFrame) -> StrategyScore:
        """
        Score a single strategy based on its performance with the given data
        
        Args:
            strategy_name: Name of the strategy to score
            df: DataFrame with market data
            
        Returns:
            StrategyScore object with performance metrics
        """
        try:
            # Generate signals
            signals = self.manager.generate_signals(strategy_name, df)
            strategy_info = self.manager.get_strategy_parameters(strategy_name)
            
            # Basic signal metrics
            total_signals = len(signals)
            buy_signals = len([s for s in signals if s.action == Action.BUY])
            sell_signals = len([s for s in signals if s.action == Action.SELL])
            signal_frequency = total_signals / len(df) if len(df) > 0 else 0
            
            # Calculate scores
            profit_potential = self._calculate_profit_potential(signals, strategy_info)
            risk_score = self._calculate_risk_score(signals, strategy_info)
            market_fit = self._calculate_market_fit(strategy_name, strategy_info)
            
            # Composite score (0-100)
            overall_score = self._calculate_overall_score(
                signal_frequency, profit_potential, risk_score, market_fit
            )
            
            return StrategyScore(
                strategy_name=strategy_name,
                total_signals=total_signals,
                buy_signals=buy_signals,
                sell_signals=sell_signals,
                signal_frequency=signal_frequency,
                profit_potential=profit_potential,
                risk_score=risk_score,
                market_fit=market_fit,
                overall_score=overall_score
            )
            
        except Exception as e:
            # Return low score for strategies that fail
            return StrategyScore(
                strategy_name=strategy_name,
                total_signals=0,
                buy_signals=0,
                sell_signals=0,
                signal_frequency=0,
                profit_potential=0,
                risk_score=0,
                market_fit=0,
                overall_score=0
            )
    
    def _calculate_profit_potential(self, signals: List, strategy_info: Dict) -> float:
        """Calculate profit potential score (0-100)"""
        if not signals:
            return 0
        
        score = 50  # Base score
        
        # More signals generally better (but not too many)
        signal_factor = min(len(signals) / 10, 1.0) * 20
        score += signal_factor
        
        # Credit strategies get bonus
        if strategy_info['is_option_trade']:
            credit_signals = [s for s in signals if hasattr(s, 'credit_debit') and 
                            s.credit_debit.value == 'CREDIT']
            if credit_signals:
                score += 15  # Credit strategies collect premium upfront
        
        # Frequency bonus/penalty
        frequency = len(signals)
        if 3 <= frequency <= 15:
            score += 10  # Sweet spot
        elif frequency > 20:
            score -= 5   # Too many signals might be overtrading
        
        return min(max(score, 0), 100)
    
    def _calculate_risk_score(self, signals: List, strategy_info: Dict) -> float:
        """Calculate risk score (0-100, higher = lower risk)"""
        if not signals:
            return 50
        
        score = 50  # Base score
        
        # Option strategies generally have defined risk
        if strategy_info['is_option_trade']:
            score += 20
            
            # Credit spreads and covered calls are safer
            strategy_name = strategy_info['strategy_name'].lower()
            safe_strategies = ['covered_call', 'cash_secured_put', 'bull_put_spread', 
                             'bear_call_spread', 'iron_condor', 'protective_put']
            if any(safe in strategy_name for safe in safe_strategies):
                score += 15
            
            # Undefined risk strategies
            risky_strategies = ['short_straddle', 'short_strangle']
            if any(risky in strategy_name for risky in risky_strategies):
                score -= 20
        
        # Signal frequency risk
        if len(signals) > 25:
            score -= 10  # High frequency can be risky
        
        return min(max(score, 0), 100)
    
    def _calculate_market_fit(self, strategy_name: str, strategy_info: Dict) -> float:
        """Calculate how well strategy fits current market conditions (0-100)"""
        if not self.market_conditions:
            return 50
        
        score = 50
        conditions = self.market_conditions
        regime = conditions.get('regime', 'neutral')
        vol_percentile = conditions.get('volatility_percentile', 50)
        trend_strength = conditions.get('trend_strength', 0)
        rsi = conditions.get('rsi', 50)
        
        strategy_lower = strategy_name.lower()
        
        # Volatility-based scoring
        if 'iron_condor' in strategy_lower or 'iron_butterfly' in strategy_lower:
            # These prefer high vol for entry but low vol for profit
            if vol_percentile > 60:
                score += 20
        elif 'straddle' in strategy_lower or 'strangle' in strategy_lower:
            if 'long' in strategy_lower and vol_percentile < 40:
                score += 20  # Long vol when vol is low
            elif 'short' in strategy_lower and vol_percentile > 60:
                score += 20  # Short vol when vol is high
        
        # Trend-based scoring
        if 'bull' in strategy_lower and trend_strength > 0.05:
            score += 20
        elif 'bear' in strategy_lower and trend_strength < -0.05:
            score += 20
        elif 'covered_call' in strategy_lower and trend_strength > 0:
            score += 15
        
        # RSI-based scoring
        if 'put' in strategy_lower and rsi < 35:
            score += 15  # Put strategies when oversold
        elif 'call' in strategy_lower and rsi > 65:
            score += 10  # Call strategies when overbought
        
        # Range-bound scoring
        range_bound = conditions.get('range_bound', 0.5)
        if range_bound > 0.7:  # Range-bound market
            neutral_strategies = ['iron_condor', 'iron_butterfly', 'short_straddle', 
                                'short_strangle', 'butterfly']
            if any(neutral in strategy_lower for neutral in neutral_strategies):
                score += 15
        
        return min(max(score, 0), 100)
    
    def _calculate_overall_score(self, frequency: float, profit: float, 
                               risk: float, fit: float) -> float:
        """Calculate weighted overall score"""
        # Weights for different components
        weights = {
            'frequency': 0.15,  # Signal frequency
            'profit': 0.35,     # Profit potential
            'risk': 0.25,       # Risk score
            'fit': 0.25         # Market fit
        }
        
        # Frequency score (0-100)
        frequency_score = min(frequency * 200, 100)  # Scale frequency to 0-100
        
        overall = (
            frequency_score * weights['frequency'] +
            profit * weights['profit'] +
            risk * weights['risk'] +
            fit * weights['fit']
        )
        
        return min(max(overall, 0), 100)
    
    def rank_strategies(self, df: pd.DataFrame, 
                       include_strategies: Optional[List[str]] = None) -> List[StrategyScore]:
        """
        Rank all available strategies based on performance with given data
        
        Args:
            df: DataFrame with market data
            include_strategies: Optional list of strategy names to include. 
                              If None, includes all strategies.
            
        Returns:
            List of StrategyScore objects ranked from best to worst
        """
        # Analyze market conditions first
        self.analyze_market_conditions(df)
        
        # Get strategies to evaluate
        if include_strategies:
            strategies_to_test = include_strategies
        else:
            strategies_to_test = [s['name'] for s in self.manager.list_strategies()]
        
        # Score all strategies
        scores = []
        for strategy_name in strategies_to_test:
            score = self.score_strategy(strategy_name, df)
            scores.append(score)
        
        # Sort by overall score (descending)
        scores.sort(key=lambda x: x.overall_score, reverse=True)
        
        # Assign ranks
        for i, score in enumerate(scores, 1):
            score.rank = i
        
        return scores
    
    def get_top_strategies(self, df: pd.DataFrame, top_n: int = 5) -> List[StrategyScore]:
        """
        Get top N strategies for the given market data
        
        Args:
            df: DataFrame with market data
            top_n: Number of top strategies to return
            
        Returns:
            List of top N StrategyScore objects
        """
        all_scores = self.rank_strategies(df)
        return all_scores[:top_n]
    
    def print_ranking_report(self, df: pd.DataFrame, top_n: int = 10):
        """
        Print a comprehensive ranking report
        
        Args:
            df: DataFrame with market data
            top_n: Number of strategies to show in report
        """
        scores = self.rank_strategies(df)[:top_n]
        
        print("=" * 80)
        print("STRATEGY RANKING REPORT")
        print("=" * 80)
        
        # Market conditions summary
        print(f"\nMarket Conditions Analysis:")
        print(f"  Volatility: {self.market_conditions.get('volatility', 0):.1f}%")
        print(f"  Trend Strength: {self.market_conditions.get('trend_strength', 0):.3f}")
        print(f"  RSI: {self.market_conditions.get('rsi', 50):.1f}")
        print(f"  Market Regime: {self.market_conditions.get('regime', 'unknown')}")
        print(f"  Range Bound: {self.market_conditions.get('range_bound', 0):.2f}")
        
        print(f"\nTop {len(scores)} Strategies (Ranked Best to Worst):")
        print("-" * 80)
        
        # Header
        print(f"{'Rank':<4} {'Strategy':<25} {'Score':<6} {'Signals':<8} {'Profit':<7} {'Risk':<6} {'Fit':<6}")
        print("-" * 80)
        
        # Strategy details
        for score in scores:
            print(f"{score.rank:<4} {score.strategy_name:<25} {score.overall_score:<6.1f} "
                  f"{score.total_signals:<8} {score.profit_potential:<7.1f} "
                  f"{score.risk_score:<6.1f} {score.market_fit:<6.1f}")
        
        print("-" * 80)
        print(f"Analysis based on {len(df)} data points")
        print("Score components: Overall (0-100), Profit Potential (0-100), Risk Score (0-100), Market Fit (0-100)")


def rank_strategies_simple(df: pd.DataFrame, top_n: int = 5) -> List[Tuple[str, float]]:
    """
    Simple function to rank strategies and return top N
    
    Args:
        df: DataFrame with market data (must have 'close' column and ticker attribute)
        top_n: Number of top strategies to return
        
    Returns:
        List of tuples (strategy_name, score) for top N strategies
    """
    ranker = StrategyRanker()
    scores = ranker.get_top_strategies(df, top_n)
    return [(score.strategy_name, score.overall_score) for score in scores]


def demo_strategy_ranking():
    """Demo function for strategy ranking"""
    import pandas as pd
    import numpy as np
    
    print("=" * 60)
    print("STRATEGY RANKING DEMO")
    print("=" * 60)
    
    # Create sample data
    np.random.seed(42)
    dates = pd.date_range('2023-01-01', periods=100, freq='D')
    prices = 100 + np.cumsum(np.random.normal(0, 2, 100))
    
    df = pd.DataFrame({
        'close': prices
    })
    df.ticker = 'DEMO'
    
    print(f"Created sample data with {len(df)} data points")
    print(f"Price range: ${df['close'].min():.2f} - ${df['close'].max():.2f}")
    
    # Run ranking
    ranker = StrategyRanker()
    print(f"\nRanking strategies...")
    ranker.print_ranking_report(df, top_n=5)
    
    print(f"\nSimple ranking:")
    simple_ranking = rank_strategies_simple(df, top_n=3)
    for i, (strategy, score) in enumerate(simple_ranking, 1):
        print(f"  {i}. {strategy}: {score:.1f}")


if __name__ == "__main__":
    demo_strategy_ranking()