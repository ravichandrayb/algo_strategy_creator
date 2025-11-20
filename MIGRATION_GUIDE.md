# Configuration Migration Guide

## Problem
The project currently has multiple `.env` files in different locations:
- Root: `/Algo Startegy Signals/.env`
- Backend: `/Algo Startegy Signals/strategy_ui/backend/.env`

This is error-prone and leads to:
- Duplicate credentials
- Sync issues
- Security risks
- Confusion about which file is active

## Solution
We've implemented a **centralized configuration system** using `trading_signals/config.py`.

## Migration Steps

### 1. Keep Only ONE .env File
Keep only the root `.env` file and delete the backend one:

```bash
# Navigate to project root
cd "/Users/ravi/Documents/personal/Algo Startegy Signals"

# Backup the backend .env (just in case)
cp strategy_ui/backend/.env strategy_ui/backend/.env.backup

# Remove the duplicate .env file
rm strategy_ui/backend/.env
```

### 2. Update Your Code

**Before (Old Way):**
```python
# Multiple places loading different .env files
from dotenv import load_dotenv
load_dotenv()
import os
api_key = os.getenv('KITE_API_KEY')
```

**After (New Way):**
```python
# Single import, works everywhere
from trading_signals.config import config

api_key = config.KITE_API_KEY
access_token = config.KITE_ACCESS_TOKEN
initial_capital = config.INITIAL_CAPITAL
```

### 3. Files That Need Updates

The following files need to be updated to use the new config system:

1. **`strategy_ui/backend/strategy_executor.py`** (lines 65-80)
2. **`test_trading_signals.py`** (lines 24-25)
3. Any other custom scripts that load `.env` files

### 4. Benefits

✅ **Single Source of Truth**: Only one `.env` file to manage
✅ **Type Safety**: Properties with proper types and defaults
✅ **Validation**: Built-in validation of required fields
✅ **IDE Support**: Better autocomplete and documentation
✅ **Testability**: Easy to mock in tests
✅ **Consistency**: Same config object used everywhere

### 5. Usage Examples

```python
from trading_signals.config import config, ensure_config_valid

# Validate configuration on startup
try:
    ensure_config_valid()
except ValueError as e:
    print(f"Configuration error: {e}")
    exit(1)

# Access configuration values
api_key = config.KITE_API_KEY
port = config.FLASK_PORT
is_debug = config.DEBUG

# Reload configuration if needed
config.reload()

# Check what's loaded (safely - no secrets exposed)
print(config)  # Config(KITE_API_KEY=***, ENVIRONMENT=development, FLASK_PORT=5003)
```

### 6. .gitignore Cleanup

The `.gitignore` files are already correctly configured to ignore `.env` files:
- Root `.gitignore` ignores `.env`, `.env.local`, `.env.production`
- `strategy_ui/.gitignore` ignores `backend/.env` and `frontend/.env*`

Keep these entries as they prevent accidental commits of secrets.

### 7. Documentation Updates Needed

Update these files to reference the new config system:
- `README.md` - Setup instructions
- `strategy_ui/README.md` - Backend setup
- `strategy_ui/QUICKSTART.md` - Quick start guide

## Testing

After migration, test that everything works:

```bash
# Test the config module
python -c "from trading_signals.config import config; print(config)"

# Run your test suite
python test_trading_signals.py

# Start the backend
cd strategy_ui/backend
python app.py
```

## Rollback Plan

If you need to rollback:

```bash
# Restore the backend .env
cp strategy_ui/backend/.env.backup strategy_ui/backend/.env

# Revert code changes using git
git checkout -- strategy_ui/backend/strategy_executor.py
git checkout -- test_trading_signals.py
```

## Questions?

The new config system is backward compatible - it still reads from the same root `.env` file.
The only change is HOW the values are accessed in the code.
