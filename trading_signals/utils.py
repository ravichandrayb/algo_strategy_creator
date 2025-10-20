"""
Utility functions for the trading signals package
"""
from typing import Dict, Any, List
import pandas as pd
from .manager import StrategyManager


def get_all_strategy_info() -> Dict[str, Any]:
    """
    Get comprehensive information about all available strategies.
    
    Returns:
        Dict containing all strategies with their parameters and descriptions
    """
    manager = StrategyManager()
    strategies_info = {}
    
    for strategy_data in manager.list_strategies():
        name = strategy_data["name"]
        info = strategy_data["info"]
        
        strategies_info[name] = {
            "display_name": info["name"],
            "type": "Options" if info["is_option_trade"] else "Stock",
            "parameters": info["params"],
            "parameter_descriptions": info.get("param_descriptions", {}),
            "required_columns": info.get("required_columns", []),
            "is_option_trade": info["is_option_trade"]
        }
    
    return strategies_info


def validate_dataframe(df: pd.DataFrame, required_columns: List[str]) -> bool:
    """
    Validate that a DataFrame has the required columns.
    
    Args:
        df: DataFrame to validate
        required_columns: List of required column names
        
    Returns:
        True if valid, raises ValueError if not
    """
    missing_columns = [col for col in required_columns if col not in df.columns]
    
    if missing_columns:
        raise ValueError(f"DataFrame is missing required columns: {missing_columns}")
    
    return True


def print_package_help():
    """Print comprehensive help for the trading signals package"""
    print("Trading Signals Package Help")
    print("=" * 50)
    print("\nQuick Start:")
    print("```python")
    print("from trading_signals import StrategyManager")
    print("import pandas as pd")
    print("")
    print("# Create manager")
    print("manager = StrategyManager()")
    print("")
    print("# Load your data (must have 'close' column)")
    print("df = pd.read_csv('your_data.csv')")
    print("df.ticker = 'AAPL'  # Set ticker attribute")
    print("")
    print("# Generate signals")
    print("signals = manager.generate_signals('sma_crossover', df)")
    print("```")
    print("\nAvailable Methods:")
    print("- manager.list_strategies()           # List all strategies")
    print("- manager.get_strategy_parameters()   # Get parameter info")
    print("- manager.print_strategy_help()       # Print detailed help")
    print("- manager.generate_signals()          # Generate trading signals")
    print("")
    
    # Show strategy information
    manager = StrategyManager()
    manager.print_strategy_help()