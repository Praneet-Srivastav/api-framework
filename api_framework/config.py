"""Configuration management for the API testing framework."""
import json
import os
from typing import Dict, Any, Optional

class Config:
    """Manages environment-specific configurations for API testing."""
    
    def __init__(self, env: str = "dev"):
        """
        Initialize configuration for specified environment.
        
        Args:
            env: Environment name (dev/qa/prod). Defaults to "dev".
        """
        self.env = env
        self._config_data: Optional[Dict[str, Any]] = None
        self._ensure_config_dir()
        
    def _ensure_config_dir(self) -> None:
        """Create config directory if it doesn't exist."""
        config_dir = os.path.join(os.path.dirname(__file__), "config")
        os.makedirs(config_dir, exist_ok=True)
        
    def _load_config(self) -> Dict[str, Any]:
        """Load configuration from JSON file based on environment."""
        if self._config_data is None:
            config_path = os.path.join(
                os.path.dirname(__file__),
                "config",
                f"{self.env}.json"
            )
            
            try:
                with open(config_path, 'r') as f:
                    self._config_data = json.load(f)
            except FileNotFoundError:
                self._config_data = {}
                # Create default config if file doesn't exist
                self.set_defaults()
                self.save()
                
        return self._config_data
    
    def get(self, key: str, default: Any = None) -> Any:
        """
        Get configuration value by key.
        
        Args:
            key: Configuration key to retrieve.
            default: Default value if key not found.
            
        Returns:
            Configuration value or default if not found.
        """
        return self._load_config().get(key, default)
    
    def set(self, key: str, value: Any) -> None:
        """
        Set configuration value.
        
        Args:
            key: Configuration key to set.
            value: Value to set for the key.
        """
        config = self._load_config()
        config[key] = value
        self.save()
        
    def save(self) -> None:
        """Save current configuration to file."""
        if self._config_data is not None:
            config_path = os.path.join(
                os.path.dirname(__file__),
                "config",
                f"{self.env}.json"
            )
            with open(config_path, 'w') as f:
                json.dump(self._config_data, f, indent=4)
                
    def set_defaults(self) -> None:
        """Set default configuration values."""
        defaults = {
            "base_url": "http://localhost:8000",
            "timeout": 30,
            "retry_attempts": 3,
            "retry_delay": 1,
            "log_file": "api_logs.txt",
            "log_level": "INFO",
            "auth": {
                "type": None,
                "username": None,
                "password": None,
                "token": None
            }
        }
        
        self._config_data = defaults