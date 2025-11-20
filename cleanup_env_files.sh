#!/bin/bash
# Cleanup script to remove duplicate .env files
# Run this after verifying the centralized config works

set -e

echo "🧹 Cleaning up duplicate .env files..."
echo ""

PROJECT_ROOT="/Users/ravi/Documents/personal/Algo Startegy Signals"
BACKEND_ENV="$PROJECT_ROOT/strategy_ui/backend/.env"

# Check if backend .env exists
if [ -f "$BACKEND_ENV" ]; then
    echo "📋 Found duplicate .env file at: $BACKEND_ENV"
    echo ""
    
    # Create backup
    BACKUP_FILE="$BACKEND_ENV.backup.$(date +%Y%m%d_%H%M%S)"
    cp "$BACKEND_ENV" "$BACKUP_FILE"
    echo "✅ Created backup: $BACKUP_FILE"
    
    # Show differences with root .env if it exists
    ROOT_ENV="$PROJECT_ROOT/.env"
    if [ -f "$ROOT_ENV" ]; then
        echo ""
        echo "🔍 Comparing with root .env file..."
        if diff -q "$ROOT_ENV" "$BACKEND_ENV" > /dev/null 2>&1; then
            echo "✅ Files are identical - safe to remove"
        else
            echo "⚠️  Files differ! Check the differences:"
            echo ""
            diff "$ROOT_ENV" "$BACKEND_ENV" || true
            echo ""
            echo "Please manually review the differences before proceeding."
            echo "Backup saved at: $BACKUP_FILE"
            exit 1
        fi
    fi
    
    # Ask for confirmation
    echo ""
    read -p "Remove duplicate .env file? (y/n) " -n 1 -r
    echo ""
    
    if [[ $REPLY =~ ^[Yy]$ ]]; then
        rm "$BACKEND_ENV"
        echo "✅ Removed: $BACKEND_ENV"
        echo "✅ Backup available at: $BACKUP_FILE"
    else
        echo "❌ Cancelled - keeping file"
        echo "Backup available at: $BACKUP_FILE"
    fi
else
    echo "✅ No duplicate .env file found in backend - already clean!"
fi

echo ""
echo "🎯 Next steps:"
echo "1. Verify the root .env file has all required values:"
echo "   cat '$PROJECT_ROOT/.env'"
echo ""
echo "2. Test the centralized config:"
echo "   python -c 'from trading_signals.config import config; print(config)'"
echo ""
echo "3. Run your test suite:"
echo "   python test_trading_signals.py"
echo ""
echo "Done! 🎉"
