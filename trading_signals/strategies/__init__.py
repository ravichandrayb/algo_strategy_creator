import sys
import os

try:
    from .example_stock import SimpleMovingAverageStrategy
    from .example_option import SimplePutCreditSpreadStrategy
except ImportError:
    # Add parent directory to path for direct execution
    sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
    try:
        from trading_signals.strategies.example_stock import SimpleMovingAverageStrategy
        from trading_signals.strategies.example_option import SimplePutCreditSpreadStrategy
    except ImportError:
        from example_stock import SimpleMovingAverageStrategy
        from example_option import SimplePutCreditSpreadStrategy

__all__ = ['SimpleMovingAverageStrategy', 'SimplePutCreditSpreadStrategy']