"""
Centralized Configuration Management for Trading Signals

This module provides a single source of truth for all environment variables
and configuration across the entire project, eliminating the need for
multiple .env files.

Usage:
    from trading_signals.config import config
    
    api_key = config.KITE_API_KEY
    access_token = config.KITE_ACCESS_TOKEN
"""

import os
from pathlib import Path
from typing import Optional
from dotenv import load_dotenv


class Config:
    """Centralized configuration singleton"""
    
    _instance = None
    _initialized = False
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(Config, cls).__new__(cls)
        return cls._instance
    
    def __init__(self):
        """Initialize configuration from environment"""
        if not self._initialized:
            self._load_environment()
            self._initialized = True
    
    def _load_environment(self):
        """Load environment variables from .env file in project root"""
        # Find project root (where .env should be)
        project_root = Path(__file__).parent.parent
        env_path = project_root / '.env'
        
        if env_path.exists():
            load_dotenv(dotenv_path=env_path, override=True)
            print(f"✅ Loaded configuration from {env_path}")
        else:
            print(f"⚠️  No .env file found at {env_path}, using system environment")
    
    # Kite API Configuration
    @property
    def KITE_API_KEY(self) -> Optional[str]:
        """Kite API Key"""
        return os.getenv('KITE_API_KEY') or os.getenv('API_KEY')
    
    @property
    def KITE_API_SECRET(self) -> Optional[str]:
        """Kite API Secret"""
        return os.getenv('KITE_API_SECRET') or os.getenv('API_SECRET')
    
    @property
    def KITE_ACCESS_TOKEN(self) -> Optional[str]:
        """Kite Access Token"""
        return os.getenv('KITE_ACCESS_TOKEN') or os.getenv('ACCESS_TOKEN')
    
    @property
    def KITE_REFRESH_TOKEN(self) -> Optional[str]:
        """Kite Refresh Token"""
        return os.getenv('KITE_REFRESH_TOKEN')
    
    # Trading Configuration
    @property
    def INITIAL_CAPITAL(self) -> float:
        """Initial trading capital"""
        return float(os.getenv('INITIAL_CAPITAL', '100000'))
    
    @property
    def MAX_POSITION_SIZE(self) -> float:
        """Maximum position size as fraction of capital"""
        return float(os.getenv('MAX_POSITION_SIZE', '0.1'))
    
    @property
    def RISK_PER_TRADE(self) -> float:
        """Risk per trade as fraction of capital"""
        return float(os.getenv('RISK_PER_TRADE', '0.02'))
    
    # Server Configuration
    @property
    def FLASK_PORT(self) -> int:
        """Flask backend port"""
        return int(os.getenv('FLASK_PORT', '5003'))
    
    @property
    def REACT_PORT(self) -> int:
        """React frontend port"""
        return int(os.getenv('REACT_PORT', '3001'))
    
    @property
    def ENVIRONMENT(self) -> str:
        """Application environment (development/production)"""
        return os.getenv('ENVIRONMENT', 'development')
    
    @property
    def DEBUG(self) -> bool:
        """Debug mode enabled"""
        return self.ENVIRONMENT == 'development'
    
    # Helper methods
    def validate(self) -> tuple[bool, list[str]]:
        """
        Validate that required configuration is present
        
        Returns:
            tuple: (is_valid, list of missing fields)
        """
        required_fields = ['KITE_API_KEY', 'KITE_API_SECRET']
        missing = []
        
        for field in required_fields:
            if not getattr(self, field):
                missing.append(field)
        
        return len(missing) == 0, missing
    
    def reload(self):
        """Reload configuration from environment"""
        self._initialized = False
        self._load_environment()
        self._initialized = True
    
    def get_project_root(self) -> Path:
        """Get project root directory"""
        return Path(__file__).parent.parent
    
    def __repr__(self):
        """String representation (masks sensitive data)"""
        return (
            f"Config("
            f"KITE_API_KEY={'***' if self.KITE_API_KEY else None}, "
            f"ENVIRONMENT={self.ENVIRONMENT}, "
            f"FLASK_PORT={self.FLASK_PORT})"
        )


# Singleton instance
config = Config()


# Convenience function for validation
def ensure_config_valid() -> None:
    """
    Ensure configuration is valid, raise exception if not
    
    Raises:
        ValueError: If required configuration is missing
    """
    is_valid, missing = config.validate()
    if not is_valid:
        raise ValueError(
            f"Missing required configuration: {', '.join(missing)}. "
            f"Please check your .env file at {config.get_project_root() / '.env'}"
        )
