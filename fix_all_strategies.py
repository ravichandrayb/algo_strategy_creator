#!/usr/bin/env python3
"""
Script to add DataFrame normalization to all option strategies
"""
import os
import re
from pathlib import Path

def fix_strategy_file(filepath):
    """Add normalize_dataframe() call to strategy's generate_signals method"""
    
    with open(filepath, 'r') as f:
        content = f.read()
    
    # Skip if already has normalization
    if 'normalize_dataframe' in content:
        print(f"✓ {filepath.name} - Already has normalization")
        return False
    
    # Pattern to find generate_signals method
    # Look for: def generate_signals(self, df: pd.DataFrame)
    # And add normalization after the method starts
    
    pattern = r'(def generate_signals\(self, df: pd\.DataFrame\).*?:\n)(        signals = \[\])'
    
    replacement = r'\1        signals = []\n        \n        # Normalize column names to lowercase\n        df = self.normalize_dataframe(df)'
    
    new_content = re.sub(pattern, replacement, content, count=1, flags=re.DOTALL)
    
    if new_content != content:
        with open(filepath, 'w') as f:
            f.write(new_content)
        print(f"✅ {filepath.name} - Added normalization")
        return True
    else:
        print(f"⚠️  {filepath.name} - Pattern not found, skipping")
        return False

def main():
    # Get all option strategy files
    option_strategies_dir = Path("trading_signals/strategies/option_strategies")
    
    if not option_strategies_dir.exists():
        print(f"Error: {option_strategies_dir} not found")
        return
    
    strategy_files = [
        f for f in option_strategies_dir.glob("*.py")
        if f.name != "__init__.py" and f.name != "covered_call.py"  # Skip covered_call as it's already done
    ]
    
    print(f"Found {len(strategy_files)} option strategies to update\n")
    
    updated = 0
    skipped = 0
    already_done = 0
    
    for filepath in sorted(strategy_files):
        result = fix_strategy_file(filepath)
        if result:
            updated += 1
        elif 'normalize_dataframe' in filepath.read_text():
            already_done += 1
        else:
            skipped += 1
    
    print(f"\n{'='*60}")
    print(f"Summary:")
    print(f"  ✅ Updated: {updated}")
    print(f"  ✓ Already done: {already_done}")
    print(f"  ⚠️  Skipped: {skipped}")
    print(f"{'='*60}")

if __name__ == "__main__":
    main()
