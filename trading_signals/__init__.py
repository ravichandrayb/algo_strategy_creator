from .manager import StrategyManager
from .base_strategy import BaseStrategy
from .signals import StockSignal, OptionSignal, Action, OptionType, CreditDebit
from .strategies import SimpleMovingAverageStrategy, SimplePutCreditSpreadStrategy
from .utils import get_all_strategy_info, validate_dataframe, print_package_help
from .strategy_ranker import StrategyRanker, StrategyScore, rank_strategies_simple
from .parameter_discovery import (
    ParameterDiscovery, get_parameter_info, validate_strategy_params,
    print_all_parameters, print_strategy_parameters, get_parameter_cheatsheet,
    find_strategies_by_indicator
)
from .config import config, ensure_config_valid

# Import Kite integration functions (gracefully handle missing kite_utils)
try:
    from .data_fetcher import (
        DataFetcher, fetch_data_for_ranking, 
        rank_strategies_with_kite_data, analyze_symbol_with_kite
    )
    _kite_functions = [
        "DataFetcher", "fetch_data_for_ranking", 
        "rank_strategies_with_kite_data", "analyze_symbol_with_kite"
    ]
except ImportError:
    _kite_functions = []

__version__ = "0.1.0"
__all__ = [
    "StrategyManager",
    "BaseStrategy", 
    "StockSignal",
    "OptionSignal",
    "Action",
    "OptionType", 
    "CreditDebit",
    "SimpleMovingAverageStrategy",
    "SimplePutCreditSpreadStrategy",
    "get_all_strategy_info",
    "validate_dataframe",
    "print_package_help",
    "StrategyRanker",
    "StrategyScore", 
    "rank_strategies_simple",
    "ParameterDiscovery",
    "get_parameter_info",
    "validate_strategy_params", 
    "print_all_parameters",
    "print_strategy_parameters",
    "get_parameter_cheatsheet",
    "find_strategies_by_indicator",
    "config",
    "ensure_config_valid"
] + _kite_functions

# Convenience function for quick help
def help():
    """Print comprehensive package help"""
    print_package_help()

def params():
    """Print comprehensive parameter guide for all strategies"""
    print_all_parameters()