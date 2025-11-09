"""
Task: tsk_7e3a4709 - Update Common Module Comments
Document: refactor/common/config/config_manager.py
dohcount: 1

Related Tasks:
    - tsk_0a733101 - Code Comments Enhancement (parent)
    - tsk_bf28d342 - Update CLI Module Comments (sibling)
    - tsk_4c899138 - Update Storage Module Comments (sibling)
    - tsk_3f55d115 - Update Plugins Module Comments (sibling)

Used By:
    - CoreManager: Uses ConfigManager as the primary configuration system
    - PluginManager: Loads and validates plugin configurations
    - StorageManager: Configures storage backend settings
    - LoggingSystem: Configures logging based on configuration settings
    - CommandSystem: Uses for command-specific configuration options

Purpose:
    Implements a robust configuration management system that supports
    multiple configuration sources (file, environment, in-memory),
    with hierarchical configuration, type validation, and fallback
    mechanisms for graceful degradation.

Requirements:
    - Must support hierarchical configuration with dot notation
    - Must validate configuration types for type safety
    - Must allow easy addition of new configuration sources
    - CRITICAL: Must handle missing configuration gracefully
    - CRITICAL: Must respect configuration source order for overrides
    - CRITICAL: Must securely handle sensitive configuration values

Configuration Manager Module

This module provides a configuration management system for the ClickUp JSON Manager with:
- Multiple configuration sources (file, environment, dict)
- Hierarchical configuration with override capabilities
- Type validation and conversion
- Default values
"""
from typing import Dict, Any, Optional, List, Union, TypeVar, Generic, Type, cast
from abc import ABC, abstractmethod
import os
import json
from ..exceptions import MissingConfigurationError, InvalidConfigurationError
from pathlib import Path

T = TypeVar('T')


class ConfigurationSource(ABC):
    """Abstract base class for configuration sources."""
    
    @abstractmethod
    def get(self, key: str, default: Optional[Any] = None) -> Any:
        """
        Get a configuration value from the source.
        
        Args:
            key: The configuration key
            default: Default value if key is not found
            
        Returns:
            The configuration value or default
        """
        pass
    
    @abstractmethod
    def has(self, key: str) -> bool:
        """
        Check if a configuration key exists in the source.
        
        Args:
            key: The configuration key
            
        Returns:
            True if the key exists, False otherwise
        """
        pass


class DictConfigurationSource(ConfigurationSource):
    """Dictionary-based configuration source."""
    
    def __init__(self, config_data: Dict[str, Any]):
        """
        Initialize with a dictionary of configuration data.
        
        Args:
            config_data: The configuration data
        """
        self.config_data = config_data
    
    def get(self, key: str, default: Optional[Any] = None) -> Any:
        """Get a configuration value from the dictionary."""
        # Support nested keys with dot notation
        if '.' in key:
            parts = key.split('.')
            current = self.config_data
            for part in parts:
                if not isinstance(current, dict) or part not in current:
                    return default
                current = current[part]
            return current
        return self.config_data.get(key, default)
    
    def has(self, key: str) -> bool:
        """Check if a configuration key exists in the dictionary."""
        # Support nested keys with dot notation
        if '.' in key:
            parts = key.split('.')
            current = self.config_data
            for part in parts:
                if not isinstance(current, dict) or part not in current:
                    return False
                current = current[part]
            return True
        return key in self.config_data


class FileConfigurationSource(ConfigurationSource):
    """File-based configuration source."""
    
    def __init__(self, file_path: str, optional: bool = False):
        """
        Initialize with a path to a JSON configuration file.
        
        Args:
            file_path: Path to the JSON configuration file
            optional: Whether the file is optional (default: False)
        """
        self.file_path = file_path
        self.config_data = {}
        self._load()
        self.optional = optional
    
    def _load(self) -> None:
        """Load configuration from the file."""
        if os.path.exists(self.file_path):
            try:
                with open(self.file_path, 'r', encoding='utf-8') as f:
                    self.config_data = json.load(f)
            except json.JSONDecodeError as e:
                # Fall back to empty config on error
                self.config_data = {}
    
    def get(self, key: str, default: Optional[Any] = None) -> Any:
        """Get a configuration value from the file."""
        # Delegate to dictionary source
        source = DictConfigurationSource(self.config_data)
        return source.get(key, default)
    
    def has(self, key: str) -> bool:
        """Check if a configuration key exists in the file."""
        # Delegate to dictionary source
        source = DictConfigurationSource(self.config_data)
        return source.has(key)


class EnvironmentConfigurationSource(ConfigurationSource):
    """Environment variable-based configuration source."""
    
    def __init__(self, prefix: str = "CLICKUP_"):
        """
        Initialize with a prefix for environment variables.
        
        Args:
            prefix: Prefix for environment variables (default: "CLICKUP_")
        """
        self.prefix = prefix
    
    def _env_key(self, key: str) -> str:
        """Convert a configuration key to an environment variable name."""
        # Convert key to uppercase and replace dots with underscores
        env_key = key.upper().replace('.', '_')
        return f"{self.prefix}{env_key}"
    
    def get(self, key: str, default: Optional[Any] = None) -> Any:
        """Get a configuration value from the environment."""
        env_key = self._env_key(key)
        return os.environ.get(env_key, default)
    
    def has(self, key: str) -> bool:
        """Check if a configuration key exists in the environment."""
        env_key = self._env_key(key)
        return env_key in os.environ


class ConfigManager:
    """
    Configuration manager that handles multiple configuration sources.
    
    Configuration is retrieved from sources in the order they were added,
    with later sources overriding earlier ones.
    """
    
    def __init__(self, sources: Optional[List[ConfigurationSource]] = None):
        """
        Initialize with a list of configuration sources.
        
        Args:
            sources: List of configuration sources (default: None)
        """
        self.sources = sources or []
    
    def add_source(self, source: ConfigurationSource) -> 'ConfigManager':
        """
        Add a configuration source.
        
        Args:
            source: The configuration source to add
            
        Returns:
            Self, for method chaining
        """
        self.sources.append(source)
        return self
    
    def get(self, key: str, default: Optional[Any] = None) -> Any:
        """
        Get a configuration value.
        
        Args:
            key: The configuration key
            default: Default value if key is not found in any source
            
        Returns:
            The configuration value or default
        """
        # Try each source in reverse order (to respect overrides)
        for source in reversed(self.sources):
            if source.has(key):
                return source.get(key)
        
        return default
    
    def get_required(self, key: str) -> Any:
        """
        Get a required configuration value.
        
        Args:
            key: The configuration key
            
        Returns:
            The configuration value
            
        Raises:
            MissingConfigurationError: If the key is not found in any source
        """
        value = self.get(key)
        if value is None:
            raise MissingConfigurationError(key)
        return value
    
    def get_typed(self, key: str, expected_type: Type[T], default: Optional[T] = None) -> T:
        """
        Get a configuration value with type checking.
        
        Args:
            key: The configuration key
            expected_type: The expected type
            default: Default value if key is not found or type is incorrect
            
        Returns:
            The configuration value or default
        """
        value = self.get(key, default)
        
        # Skip type checking for None values
        if value is None:
            return value
        
        # Check type
        if not isinstance(value, expected_type):
            try:
                # Try to convert to the expected type
                if expected_type == bool and isinstance(value, str):
                    # Handle boolean strings
                    if value.lower() in ('true', 'yes', '1', 'on'):
                        return cast(T, True)
                    elif value.lower() in ('false', 'no', '0', 'off'):
                        return cast(T, False)
                
                # Try standard conversion
                converted_value = expected_type(value)
                return converted_value
            except (ValueError, TypeError):
                return default
        
        return value
    
    def get_required_typed(self, key: str, expected_type: Type[T]) -> T:
        """
        Get a required configuration value with type checking.
        
        Args:
            key: The configuration key
            expected_type: The expected type
            
        Returns:
            The configuration value
            
        Raises:
            MissingConfigurationError: If the key is not found in any source
            InvalidConfigurationError: If the value cannot be converted to the expected type
        """
        value = self.get_required(key)
        
        # Check type
        if not isinstance(value, expected_type):
            try:
                # Try to convert to the expected type
                if expected_type == bool and isinstance(value, str):
                    # Handle boolean strings
                    if value.lower() in ('true', 'yes', '1', 'on'):
                        return cast(T, True)
                    elif value.lower() in ('false', 'no', '0', 'off'):
                        return cast(T, False)
                
                # Try standard conversion
                converted_value = expected_type(value)
                return converted_value
            except (ValueError, TypeError):
                raise InvalidConfigurationError(
                    key, value, f"Expected type {expected_type.__name__}")
        
        return value


# Create a default configuration manager with common sources
def create_default_config() -> 'ConfigManager':
    """
    Create a default configuration manager with standard configuration sources.
    
    The configuration sources are loaded in the following order (higher priority last):
    1. Default internal settings
    2. Global config file (~/.clickup_json_manager/config.json)
    3. Local config file (./.clickup_json_manager.json)
    4. Environment variables with CLICKUP_JSON_ prefix
    
    Returns:
        ConfigManager: Configured manager with default sources
    """
    # Default internal settings
    default_settings = {
        'log_level': 'info',
        'log_to_file': False,
        'log_file_path': '~/.clickup_json_manager/logs/app.log',
        'template_dir': '~/.clickup_json_manager/templates',
        'max_history_entries': 100,
        'backup_files': True,
        'backup_dir': '~/.clickup_json_manager/backups',
        'default_template': 'default.json',
        'auto_save': True,
        'auto_save_interval_seconds': 300,  # 5 minutes
        'editor_command': '',  # Empty uses system default
        'use_colors': True,
        'page_size': 20,
        'date_format': '%Y-%m-%d',
        'time_format': '%H:%M:%S',
        'id_prefix_length': 5,
        'show_full_ids': False
    }
    
    # Create the sources
    sources = [
        # Base default settings (lowest priority)
        DictConfigurationSource(default_settings),
        
        # Global config file
        FileConfigurationSource(
            os.path.expanduser('~/.clickup_json_manager/config.json'),
            optional=True
        ),
        
        # Local config file
        FileConfigurationSource(
            './.clickup_json_manager.json',
            optional=True
        ),
        
        # Environment variables (highest priority)
        EnvironmentConfigurationSource(prefix='CLICKUP_JSON_')
    ]
    
    # Create and return the manager with the sources
    return ConfigManager(sources)


# Default configuration manager instance
default_config = create_default_config() 