#!/bin/bash
# Installation script for trading-signals package

echo "🚀 Installing Trading Signals Package..."

# Install the package
echo "📦 Installing core package..."
pip install -e .

# Install kite integration (optional)
echo "🔗 Installing Kite API integration..."
pip install git+https://github.com/ravichandrayb/kite-trading-utils.git

echo "✅ Installation complete!"
echo ""
echo "🧪 Testing installation..."
trading-signals-test

echo ""
echo "📖 Quick start:"
echo "1. Create a .env file with your Kite API credentials (see .env.example)"
echo "2. Run: python -c \"from trading_signals import rank_strategies_simple; print('Package ready!')\""
echo "3. For Kite integration: python -c \"from trading_signals import analyze_symbol_with_kite; print('Kite integration ready!')\""
