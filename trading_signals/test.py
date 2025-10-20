#!/usr/bin/env python3
"""
Test module for trading_signals package
Can be run as: trading-signals-test
"""

import sys
import os

def main():
    """Main entry point for the test command"""
    # Import the comprehensive test
    try:
        # Add current directory to path if running locally
        current_dir = os.path.dirname(os.path.abspath(__file__))
        parent_dir = os.path.dirname(current_dir)
        if os.path.exists(os.path.join(parent_dir, 'test_trading_signals.py')):
            sys.path.insert(0, parent_dir)
            
        # Try to import and run the test
        try:
            from test_trading_signals import run_comprehensive_test
            success = run_comprehensive_test()
            sys.exit(0 if success else 1)
        except ImportError:
            # Fallback to a simple test
            print("Running basic package test...")
            test_basic_import()
    except Exception as e:
        print(f"Error running tests: {e}")
        sys.exit(1)

def test_basic_import():
    """Basic test to verify package installation"""
    print("🧪 Testing trading_signals package installation...")
    
    try:
        import trading_signals
        print("✅ trading_signals imported successfully")
        
        # Test basic imports
        from trading_signals import StrategyManager
        print("✅ StrategyManager imported")
        
        from trading_signals import rank_strategies_simple
        print("✅ rank_strategies_simple imported")
        
        # Test strategy creation
        manager = StrategyManager()
        print("✅ StrategyManager created")
        
        # Test with sample data
        import pandas as pd
        import numpy as np
        
        # Create sample data
        dates = pd.date_range('2023-01-01', periods=50, freq='D')
        prices = 100 + np.cumsum(np.random.normal(0, 1, 50))
        
        df = pd.DataFrame({
            'close': prices
        }, index=dates)
        df.ticker = 'TEST'
        
        # Test strategy ranking
        results = rank_strategies_simple(df, top_n=2)
        print(f"✅ Strategy ranking successful: {len(results)} strategies")
        
        for i, (strategy, score) in enumerate(results, 1):
            print(f"   {i}. {strategy}: {score:.1f}")
        
        print("\n🎉 Basic package test PASSED!")
        print("\n📖 Usage:")
        print("   from trading_signals import rank_strategies_simple")
        print("   from trading_signals import StrategyManager")
        print("   from trading_signals import analyze_symbol_with_kite  # Requires kite_utils")
        
        return True
        
    except Exception as e:
        print(f"❌ Package test FAILED: {e}")
        return False

if __name__ == "__main__":
    main()
