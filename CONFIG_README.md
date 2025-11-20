# Environment Configuration - Quick Reference

## 🎯 Current Status

You now have a **centralized configuration system** that eliminates the need for multiple `.env` files.

## 📁 File Structure

```
Algo Strategy Signals/
├── .env                          ← ✅ ONLY .env file (keep this)
├── .env.example                  ← Template for new users
├── trading_signals/
│   └── config.py                 ← ✅ Centralized config module
└── strategy_ui/
    └── backend/
        ├── .env                  ← ❌ DELETE this duplicate
        └── .env.backup.*         ← Backup (auto-created)
```

## 🚀 Quick Start

### 1. Clean Up Duplicate Files

```bash
# Run the cleanup script
./cleanup_env_files.sh
```

### 2. Verify Root .env File

Ensure your root `.env` file contains all required values:

```bash
cat .env
```

Required variables:
- `KITE_API_KEY`
- `KITE_API_SECRET`
- `KITE_ACCESS_TOKEN` (optional, auto-generated)

### 3. Use the New Config System

**In any Python file:**

```python
from trading_signals.config import config

# Access values
api_key = config.KITE_API_KEY
port = config.FLASK_PORT
capital = config.INITIAL_CAPITAL

# Validate configuration
from trading_signals.config import ensure_config_valid
ensure_config_valid()  # Raises error if config is invalid
```

## 🔄 Migration Status

### ✅ Already Updated
- `trading_signals/config.py` - New centralized config module
- `strategy_ui/backend/strategy_executor.py` - Now uses centralized config
- `test_trading_signals.py` - Now uses centralized config
- `trading_signals/__init__.py` - Exports config module

### 📝 May Need Updates
Check these files if you have custom scripts:
- Any file that does `from dotenv import load_dotenv`
- Any file that does `os.getenv('KITE_...')`

Search for them:
```bash
grep -r "load_dotenv" --include="*.py"
grep -r "os.getenv.*KITE" --include="*.py"
```

## 🎁 Benefits

1. **Single Source of Truth**: Only one `.env` file to manage
2. **Type Safety**: Config properties have proper types
3. **Validation**: Built-in validation of required fields
4. **Auto-completion**: Better IDE support
5. **Testability**: Easy to mock in tests
6. **No Sync Issues**: No more duplicate files getting out of sync

## 🧪 Testing

```bash
# Test the config module
python -c "from trading_signals.config import config; print(config)"

# Run full test suite
python test_trading_signals.py

# Start backend (uses new config)
cd strategy_ui/backend
python app.py
```

## 🔒 Security

The `.gitignore` files are already configured correctly:
- Root `.gitignore`: Ignores `.env`, `.env.local`, `.env.production`
- Strategy UI `.gitignore`: Ignores `backend/.env` and `frontend/.env*`

**Never commit `.env` files to git!**

## 📚 Available Configuration

```python
# Kite API
config.KITE_API_KEY
config.KITE_API_SECRET
config.KITE_ACCESS_TOKEN
config.KITE_REFRESH_TOKEN

# Trading
config.INITIAL_CAPITAL        # default: 100000
config.MAX_POSITION_SIZE      # default: 0.1
config.RISK_PER_TRADE         # default: 0.02

# Server
config.FLASK_PORT             # default: 5003
config.REACT_PORT             # default: 3001
config.ENVIRONMENT            # default: 'development'
config.DEBUG                  # True if development

# Utilities
config.validate()             # Returns (is_valid, missing_fields)
config.reload()               # Reload from .env file
config.get_project_root()     # Get project root path
```

## 🆘 Troubleshooting

**Config not loading:**
```python
from trading_signals.config import config
config.reload()
print(config)
```

**Missing values:**
```python
from trading_signals.config import config
is_valid, missing = config.validate()
if not is_valid:
    print(f"Missing: {missing}")
```

**Check .env location:**
```python
from trading_signals.config import config
print(config.get_project_root() / '.env')
```

## 📖 Full Documentation

See `MIGRATION_GUIDE.md` for detailed migration instructions.

---

**Questions or Issues?**
The centralized config system is backward compatible and still reads from the same root `.env` file.
