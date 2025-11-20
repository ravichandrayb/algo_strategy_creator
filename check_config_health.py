#!/usr/bin/env python3
"""
Configuration Health Check Script

Verifies that the centralized configuration system is working correctly
and identifies any remaining issues.
"""

import sys
from pathlib import Path

# Add project to path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

def check_config_module():
    """Check if config module can be imported"""
    print("1️⃣  Checking config module...")
    try:
        from trading_signals.config import config, ensure_config_valid
        print("   ✅ Config module imported successfully")
        print(f"   📍 Config: {config}")
        return True
    except ImportError as e:
        print(f"   ❌ Failed to import config: {e}")
        return False
    except Exception as e:
        print(f"   ❌ Error: {e}")
        return False


def check_env_files():
    """Check for .env files"""
    print("\n2️⃣  Checking .env files...")
    
    root_env = project_root / '.env'
    backend_env = project_root / 'strategy_ui' / 'backend' / '.env'
    
    if root_env.exists():
        print(f"   ✅ Root .env exists: {root_env}")
    else:
        print(f"   ⚠️  Root .env NOT found: {root_env}")
    
    if backend_env.exists():
        print(f"   ⚠️  Duplicate backend .env found: {backend_env}")
        print("   💡 Run ./cleanup_env_files.sh to remove it")
        return False
    else:
        print(f"   ✅ No duplicate backend .env")
    
    return True


def check_validation():
    """Check config validation"""
    print("\n3️⃣  Validating configuration...")
    try:
        from trading_signals.config import config
        is_valid, missing = config.validate()
        
        if is_valid:
            print("   ✅ Configuration is valid")
            return True
        else:
            print(f"   ❌ Missing required fields: {', '.join(missing)}")
            print(f"   💡 Add these to {project_root / '.env'}")
            return False
    except Exception as e:
        print(f"   ❌ Validation error: {e}")
        return False


def check_config_values():
    """Check config values"""
    print("\n4️⃣  Checking configuration values...")
    try:
        from trading_signals.config import config
        
        checks = {
            'KITE_API_KEY': config.KITE_API_KEY,
            'KITE_API_SECRET': config.KITE_API_SECRET,
            'FLASK_PORT': config.FLASK_PORT,
            'ENVIRONMENT': config.ENVIRONMENT,
        }
        
        all_good = True
        for key, value in checks.items():
            if value:
                # Mask sensitive values
                display_value = '***' if 'KEY' in key or 'SECRET' in key else value
                print(f"   ✅ {key}: {display_value}")
            else:
                print(f"   ⚠️  {key}: Not set")
                if 'KEY' in key or 'SECRET' in key:
                    all_good = False
        
        return all_good
    except Exception as e:
        print(f"   ❌ Error: {e}")
        return False


def check_old_patterns():
    """Check for old dotenv patterns in code"""
    print("\n5️⃣  Checking for old patterns...")
    
    import subprocess
    
    # Check for load_dotenv calls
    try:
        result = subprocess.run(
            ['grep', '-r', 'load_dotenv', '--include=*.py', 
             '--exclude-dir=venv', '--exclude-dir=node_modules', 
             '--exclude-dir=__pycache__', '.'],
            cwd=project_root,
            capture_output=True,
            text=True
        )
        
        if result.returncode == 0:
            # Filter out false positives
            lines = [l for l in result.stdout.split('\n') 
                    if l and 'config.py' not in l 
                    and 'check_config_health.py' not in l
                    and '.md' not in l]
            if lines:
                print("   ⚠️  Found load_dotenv calls (should use config module):")
                for line in lines[:5]:  # Show first 5
                    print(f"      {line}")
                if len(lines) > 5:
                    print(f"      ... and {len(lines) - 5} more")
                return False
            else:
                print("   ✅ No old load_dotenv patterns found")
                return True
        else:
            print("   ✅ No old load_dotenv patterns found")
            return True
    except Exception as e:
        print(f"   ⚠️  Could not check: {e}")
        return True


def main():
    """Run all checks"""
    print("🏥 Configuration Health Check")
    print("=" * 50)
    
    results = []
    results.append(('Config Module', check_config_module()))
    results.append(('.env Files', check_env_files()))
    results.append(('Validation', check_validation()))
    results.append(('Config Values', check_config_values()))
    results.append(('Old Patterns', check_old_patterns()))
    
    print("\n" + "=" * 50)
    print("📊 Summary:")
    print("=" * 50)
    
    all_passed = True
    for name, passed in results:
        status = "✅ PASS" if passed else "❌ FAIL"
        print(f"{status}: {name}")
        if not passed:
            all_passed = False
    
    print("=" * 50)
    
    if all_passed:
        print("\n🎉 All checks passed! Configuration system is healthy.")
        print("\n💡 Next steps:")
        print("   - Run ./cleanup_env_files.sh to remove duplicate .env")
        print("   - Start using: from trading_signals.config import config")
        return 0
    else:
        print("\n⚠️  Some checks failed. Please review the issues above.")
        print("\n📚 See CONFIG_README.md for help")
        return 1


if __name__ == '__main__':
    sys.exit(main())
