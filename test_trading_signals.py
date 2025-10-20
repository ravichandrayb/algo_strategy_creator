#!/usr/bin/env python3
"""
Comprehensive Test Suite for Trading Signals Package

This script demonstrates all package functionality:
- Real-time data fetching from Kite API
- Strategy ranking and analysis
- Multi-symbol comparison
- Parameter discovery
- Signal generation

Requirements:
1. kite_utils package installed
2. .env file with KITE_API_KEY and KITE_API_SECRET
3. Valid access token (auto-generated if needed)
"""

import os
from typing import List, Dict

def setup_environment():
    """Load environment and verify kite_utils availability"""
    try:
        from dotenv import load_dotenv
        load_dotenv(override=True)
        print("✅ Environment loaded")
    except ImportError:
        print("⚠️  python-dotenv not found, using system environment")
    
    try:
        from kite_utils import SimpleTokenManager, generate_access_token_automated
        
        # Check token validity
        tm = SimpleTokenManager()
        if not tm.validate_token():
            print("🔄 Generating new access token...")
            generate_access_token_automated()
            print("✅ Fresh access token generated")
        else:
            print("✅ Valid access token found")
            
        return True
    except ImportError:
        print("❌ kite_utils not found. Install with:")
        print("   pip install git+https://github.com/ravichandrayb/kite-trading-utils.git")
        return False
    except Exception as e:
        print(f"❌ Kite setup failed: {e}")
        return False

def test_single_symbol_analysis(symbol: str = "NIFTY50", days: int = 100):
    """Test comprehensive analysis for a single symbol"""
    print(f"\n{'='*70}")
    print(f"SINGLE SYMBOL ANALYSIS: {symbol}")
    print(f"{'='*70}")
    
    try:
        from trading_signals import analyze_symbol_with_kite
        
        print(f"📊 Running comprehensive analysis for {symbol} (last {days} days)...")
        strategies = analyze_symbol_with_kite(symbol, days=days, top_n=8)
        
        print(f"\n🎯 Top strategies returned: {len(strategies)}")
        if strategies and hasattr(strategies[0], 'strategy_name'):
            # Handle StrategyScore objects
            for i, strategy_score in enumerate(strategies, 1):
                print(f"   {i}. {strategy_score.strategy_name:<25} Score: {strategy_score.overall_score:5.1f}")
        else:
            # Handle tuples
            for i, (strategy, score) in enumerate(strategies, 1):
                print(f"   {i}. {strategy:<25} Score: {score:5.1f}")
            
        return True
        
    except Exception as e:
        print(f"❌ Single symbol analysis failed: {e}")
        return False

def test_multi_symbol_ranking():
    """Test quick ranking across multiple symbols"""
    print(f"\n{'='*70}")
    print("MULTI-SYMBOL QUICK RANKING")
    print(f"{'='*70}")
    
    symbols = ["NIFTY50", "BANKNIFTY", "RELIANCE", "TCS", "INFY"]
    
    try:
        from trading_signals import rank_strategies_with_kite_data
        
        results = {}
        for symbol in symbols:
            try:
                print(f"\n📈 Analyzing {symbol}...")
                top_strategies = rank_strategies_with_kite_data(symbol, days=60, top_n=3)
                results[symbol] = top_strategies
                
                print(f"   Top 3 strategies for {symbol}:")
                for i, (strategy, score) in enumerate(top_strategies, 1):
                    print(f"     {i}. {strategy:<22} Score: {score:5.1f}")
                    
            except Exception as e:
                print(f"   ❌ Error analyzing {symbol}: {e}")
        
        print(f"\n📋 SUMMARY - Best Strategy by Symbol:")
        print("-" * 50)
        for symbol, strategies in results.items():
            if strategies:
                best_strategy, best_score = strategies[0]
                print(f"  {symbol:<12}: {best_strategy:<22} ({best_score:5.1f})")
        
        return len(results) > 0
        
    except Exception as e:
        print(f"❌ Multi-symbol ranking failed: {e}")
        return False

def test_custom_data_analysis():
    """Test custom data fetching and analysis"""
    print(f"\n{'='*70}")
    print("CUSTOM DATA ANALYSIS")
    print(f"{'='*70}")
    
    try:
        from trading_signals.data_fetcher import DataFetcher
        from trading_signals import StrategyRanker, rank_strategies_simple
        
        # Method 1: Custom data fetching
        print("📥 Method 1: Manual data fetching...")
        fetcher = DataFetcher()
        df = fetcher.fetch_and_prepare_data('NIFTY50', days=90)
        
        print(f"   ✅ Fetched {len(df)} records")
        print(f"   📅 Date range: {df.index[0]} to {df.index[-1]}")
        print(f"   💰 Price range: ₹{df['close'].min():.2f} - ₹{df['close'].max():.2f}")
        
        # Method 2: Quick ranking
        print(f"\n📊 Method 2: Quick strategy ranking...")
        simple_ranking = rank_strategies_simple(df, top_n=5)
        for i, (strategy, score) in enumerate(simple_ranking, 1):
            print(f"   {i}. {strategy:<25} Score: {score:5.1f}")
        
        # Method 3: Detailed analysis
        print(f"\n🔍 Method 3: Detailed analysis...")
        ranker = StrategyRanker()
        detailed_results = ranker.rank_strategies(df)
        
        print("   Strategy performance breakdown:")
        for strategy_score in detailed_results:
            print(f"     {strategy_score.strategy_name}:")
            print(f"       Score: {strategy_score.overall_score:.1f}, "
                  f"Signals: {strategy_score.total_signals}, "
                  f"Profit: {strategy_score.profit_potential:.1f}")
        
        return True
        
    except Exception as e:
        print(f"❌ Custom data analysis failed: {e}")
        return False

def test_parameter_discovery():
    """Test parameter discovery functionality"""
    print(f"\n{'='*70}")
    print("PARAMETER DISCOVERY")
    print(f"{'='*70}")
    
    try:
        from trading_signals import get_all_strategy_info, print_all_parameters
        
        print("📋 Available strategies and parameters:")
        strategy_info = get_all_strategy_info()
        
        for strategy_name, info in strategy_info.items():
            display_name = info.get('display_name', strategy_name.replace('_', ' ').title())
            strategy_type = info.get('type', 'Unknown')
            description = info.get('description', 'No description available')
            
            print(f"\n🎯 {display_name} ({strategy_name})")
            print(f"   Type: {strategy_type}")
            print(f"   Description: {description}")
            
            if 'parameters' in info:
                print("   Parameters:")
                for param_name, param_info in info['parameters'].items():
                    param_desc = param_info.get('description', 'No description') if isinstance(param_info, dict) else 'No description'
                    param_default = param_info.get('default', 'N/A') if isinstance(param_info, dict) else 'N/A'
                    param_min = param_info.get('min', 'N/A') if isinstance(param_info, dict) else 'N/A'
                    param_max = param_info.get('max', 'N/A') if isinstance(param_info, dict) else 'N/A'
                    
                    print(f"     • {param_name}: {param_desc}")
                    print(f"       Default: {param_default}, Range: {param_min}-{param_max}")
        
        return True
        
    except Exception as e:
        print(f"❌ Parameter discovery failed: {e}")
        return False

def test_signal_generation():
    """Test actual signal generation"""
    print(f"\n{'='*70}")
    print("SIGNAL GENERATION")
    print(f"{'='*70}")
    
    try:
        from trading_signals import StrategyManager
        from trading_signals.data_fetcher import fetch_data_for_ranking
        
        # Get real data
        df = fetch_data_for_ranking('NIFTY50', days=30)
        print(f"📊 Using {len(df)} days of NIFTY50 data for signal generation")
        
        # Test different strategies
        manager = StrategyManager()
        
        strategies_to_test = ['sma_crossover', 'put_credit_spread']
        
        for strategy_name in strategies_to_test:
            print(f"\n🎯 Testing {strategy_name} strategy...")
            
            try:
                signals = manager.generate_signals(strategy_name, df)
                print(f"   ✅ Generated {len(signals)} signals")
                
                if signals:
                    print("   📋 Sample signals:")
                    for i, signal in enumerate(signals[:3], 1):  # Show first 3 signals
                        if hasattr(signal, 'action') and hasattr(signal, 'price'):
                            print(f"     {i}. {signal.action} at ₹{signal.price:.2f}")
                        else:
                            print(f"     {i}. {signal}")
                else:
                    print("   ℹ️  No signals generated (normal for current market conditions)")
                    
            except Exception as e:
                print(f"   ❌ Signal generation failed for {strategy_name}: {e}")
        
        return True
        
    except Exception as e:
        print(f"❌ Signal generation test failed: {e}")
        return False

def test_batch_symbol_fetching():
    """Test batch data fetching for multiple symbols"""
    print(f"\n{'='*70}")
    print("BATCH SYMBOL FETCHING")
    print(f"{'='*70}")
    
    try:
        from trading_signals.data_fetcher import DataFetcher
        
        symbols = ["NIFTY50", "RELIANCE", "TCS"]
        fetcher = DataFetcher()
        
        print(f"📥 Fetching data for {len(symbols)} symbols...")
        results = fetcher.fetch_multiple_symbols(symbols, days=30)
        
        print(f"\n📊 Batch fetching results:")
        for symbol, df in results.items():
            print(f"   {symbol}: {len(df)} records, "
                  f"₹{df['close'].min():.2f}-₹{df['close'].max():.2f}")
        
        return len(results) > 0
        
    except Exception as e:
        print(f"❌ Batch symbol fetching failed: {e}")
        return False

def run_comprehensive_test():
    """Run all tests and provide summary"""
    print("🚀 TRADING SIGNALS PACKAGE - COMPREHENSIVE TEST SUITE")
    print("=" * 70)
    
    # Setup
    if not setup_environment():
        print("\n❌ Setup failed. Please configure kite_utils first.")
        return False
    
    # Run all tests
    test_results = {
        "Single Symbol Analysis": test_single_symbol_analysis(),
        "Multi-Symbol Ranking": test_multi_symbol_ranking(), 
        "Custom Data Analysis": test_custom_data_analysis(),
        "Parameter Discovery": test_parameter_discovery(),
        "Signal Generation": test_signal_generation(),
        "Batch Symbol Fetching": test_batch_symbol_fetching()
    }
    
    # Summary
    print(f"\n{'='*70}")
    print("TEST SUMMARY")
    print(f"{'='*70}")
    
    passed = sum(test_results.values())
    total = len(test_results)
    
    for test_name, result in test_results.items():
        status = "✅ PASSED" if result else "❌ FAILED"
        print(f"{test_name:<25}: {status}")
    
    print(f"\nOverall: {passed}/{total} tests passed ({passed/total*100:.1f}%)")
    
    if passed == total:
        print("\n🎉 ALL TESTS PASSED! Package is working perfectly!")
        print("\n📖 Usage Examples:")
        print("   from trading_signals import rank_strategies_with_kite_data")
        print("   strategies = rank_strategies_with_kite_data('NIFTY50', days=180)")
        print("   ")
        print("   from trading_signals import analyze_symbol_with_kite")
        print("   analyze_symbol_with_kite('RELIANCE', days=365)")
    else:
        print(f"\n⚠️  {total-passed} tests failed. Check error messages above.")
    
    return passed == total

if __name__ == "__main__":
    success = run_comprehensive_test()
    exit(0 if success else 1)
