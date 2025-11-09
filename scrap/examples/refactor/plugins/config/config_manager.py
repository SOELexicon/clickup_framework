"""
Plugin Configuration Manager

This module provides functionality for managing plugin configurations,
including loading, saving, validating, and providing default values.
"""

import json
import logging
import os
from pathlib import Path
from typing import Any, Dict, List, Optional, Set, Tuple, Union

from ...common.exceptions import ConfigError


logger = logging.getLogger(__name__)


class PluginConfigManager:
    """
    Manages configuration for plugins.
    
    This class handles:
    - Loading configuration from files
    - Validating configuration against schema
    - Providing default values
    - Saving configuration to files
    """
    
    def __init__(self, config_dir: Optional[str] = None):
        """
        Initialize the plugin configuration manager.
        
        Args:
            config_dir: Directory to store plugin configurations.
                        Defaults to ~/.clickup_json_manager/configs/
        """
        self.config_dir = config_dir or os.path.expanduser("~/.clickup_json_manager/configs")
        os.makedirs(self.config_dir, exist_ok=True)
        
        # Dictionary mapping plugin_id -> config
        self.configs: Dict[str, Dict[str, Any]] = {}
        
        # Dictionary mapping plugin_id -> schema
        self.schemas: Dict[str, Dict[str, Dict[str, Any]]] = {}
    
    def register_plugin_config(
        self, 
        plugin_id: str, 
        schema: Dict[str, Dict[str, Any]]
    ) -> None:
        """
        Register a plugin's configuration schema.
        
        Args:
            plugin_id: Plugin identifier
            schema: Configuration schema
        """
        self.schemas[plugin_id] = schema
        
        # Try to load existing config or create with defaults
        if not self.load_config(plugin_id):
            # Create config with default values
            config = self._create_default_config(schema)
            self.configs[plugin_id] = config
            
            # Save the default config
            self.save_config(plugin_id)
    
    def _create_default_config(self, schema: Dict[str, Dict[str, Any]]) -> Dict[str, Any]:
        """
        Create a configuration with default values from schema.
        
        Args:
            schema: Configuration schema
            
        Returns:
            Dict with default values for all schema fields
        """
        config = {}
        
        for key, field_schema in schema.items():
            if "default" in field_schema:
                config[key] = field_schema["default"]
                
        return config
    
    def load_config(self, plugin_id: str) -> bool:
        """
        Load plugin configuration from file.
        
        Args:
            plugin_id: Plugin identifier
            
        Returns:
            True if config was loaded successfully, False otherwise
        """
        config_path = self._get_config_path(plugin_id)
        
        try:
            if os.path.exists(config_path):
                with open(config_path, "r", encoding="utf-8") as f:
                    config = json.load(f)
                    
                # Validate the loaded config
                is_valid, _ = self.validate_config(plugin_id, config)
                if not is_valid:
                    logger.warning(f"Invalid configuration for plugin {plugin_id}, using defaults")
                    config = self._create_default_config(self.schemas.get(plugin_id, {}))
                
                self.configs[plugin_id] = config
                return True
            return False
        except Exception as e:
            logger.error(f"Error loading config for plugin {plugin_id}: {str(e)}")
            return False
    
    def save_config(self, plugin_id: str) -> bool:
        """
        Save plugin configuration to file.
        
        Args:
            plugin_id: Plugin identifier
            
        Returns:
            True if config was saved successfully, False otherwise
        """
        config_path = self._get_config_path(plugin_id)
        
        try:
            config = self.configs.get(plugin_id, {})
            
            with open(config_path, "w", encoding="utf-8") as f:
                json.dump(config, f, indent=2)
                
            logger.debug(f"Saved configuration for plugin {plugin_id}")
            return True
        except Exception as e:
            logger.error(f"Error saving config for plugin {plugin_id}: {str(e)}")
            return False
    
    def get_config(self, plugin_id: str) -> Dict[str, Any]:
        """
        Get the configuration for a plugin.
        
        Args:
            plugin_id: Plugin identifier
            
        Returns:
            Configuration dictionary
        """
        return self.configs.get(plugin_id, {})
    
    def update_config(self, plugin_id: str, config: Dict[str, Any], validate: bool = True) -> bool:
        """
        Update the configuration for a plugin.
        
        Args:
            plugin_id: Plugin identifier
            config: New configuration values
            validate: Whether to validate the configuration before updating
            
        Returns:
            True if config was updated successfully, False otherwise
        """
        if validate:
            is_valid, error = self.validate_config(plugin_id, config)
            if not is_valid:
                logger.error(f"Invalid configuration for plugin {plugin_id}: {error}")
                return False
        
        # Get existing config and update it
        existing_config = self.configs.get(plugin_id, {})
        existing_config.update(config)
        self.configs[plugin_id] = existing_config
        
        # Save updated config
        return self.save_config(plugin_id)
    
    def validate_config(self, plugin_id: str, config: Dict[str, Any]) -> Tuple[bool, Optional[str]]:
        """
        Validate a configuration against its schema.
        
        Args:
            plugin_id: Plugin identifier
            config: Configuration to validate
            
        Returns:
            Tuple of (is_valid, error_message)
        """
        schema = self.schemas.get(plugin_id)
        if not schema:
            return True, None  # No schema to validate against
        
        # Check required fields
        for key, field_schema in schema.items():
            if field_schema.get("required", False) and key not in config:
                return False, f"Required field '{key}' is missing"
        
        # Validate field types
        for key, value in config.items():
            if key not in schema:
                continue  # Skip unknown fields
                
            field_schema = schema[key]
            field_type = field_schema.get("type")
            
            if field_type == "string" and not isinstance(value, str):
                return False, f"Field '{key}' must be a string"
                
            elif field_type == "number" and not isinstance(value, (int, float)):
                return False, f"Field '{key}' must be a number"
                
            elif field_type == "integer" and not isinstance(value, int):
                return False, f"Field '{key}' must be an integer"
                
            elif field_type == "boolean" and not isinstance(value, bool):
                return False, f"Field '{key}' must be a boolean"
                
            elif field_type == "array" and not isinstance(value, list):
                return False, f"Field '{key}' must be an array"
                
            elif field_type == "object" and not isinstance(value, dict):
                return False, f"Field '{key}' must be an object"
        
        return True, None
    
    def get_config_value(
        self, 
        plugin_id: str, 
        key: str, 
        default: Any = None
    ) -> Any:
        """
        Get a specific configuration value for a plugin.
        
        Args:
            plugin_id: Plugin identifier
            key: Configuration key
            default: Default value if key doesn't exist
            
        Returns:
            Configuration value or default
        """
        config = self.configs.get(plugin_id, {})
        return config.get(key, default)
    
    def set_config_value(
        self, 
        plugin_id: str, 
        key: str, 
        value: Any, 
        save: bool = True
    ) -> bool:
        """
        Set a specific configuration value for a plugin.
        
        Args:
            plugin_id: Plugin identifier
            key: Configuration key
            value: Configuration value
            save: Whether to save the configuration to file
            
        Returns:
            True if value was set successfully, False otherwise
        """
        schema = self.schemas.get(plugin_id, {})
        field_schema = schema.get(key)
        
        if field_schema:
            # Validate the value type
            field_type = field_schema.get("type")
            
            if field_type == "string" and not isinstance(value, str):
                logger.error(f"Field '{key}' must be a string")
                return False
                
            elif field_type == "number" and not isinstance(value, (int, float)):
                logger.error(f"Field '{key}' must be a number")
                return False
                
            elif field_type == "integer" and not isinstance(value, int):
                logger.error(f"Field '{key}' must be an integer")
                return False
                
            elif field_type == "boolean" and not isinstance(value, bool):
                logger.error(f"Field '{key}' must be a boolean")
                return False
                
            elif field_type == "array" and not isinstance(value, list):
                logger.error(f"Field '{key}' must be an array")
                return False
                
            elif field_type == "object" and not isinstance(value, dict):
                logger.error(f"Field '{key}' must be an object")
                return False
        
        # Update the config
        config = self.configs.get(plugin_id, {})
        config[key] = value
        self.configs[plugin_id] = config
        
        # Save if requested
        if save:
            return self.save_config(plugin_id)
            
        return True
    
    def _get_config_path(self, plugin_id: str) -> str:
        """
        Get the path to a plugin's configuration file.
        
        Args:
            plugin_id: Plugin identifier
            
        Returns:
            Path to the configuration file
        """
        return os.path.join(self.config_dir, f"{plugin_id}.json")
    
    def delete_config(self, plugin_id: str) -> bool:
        """
        Delete a plugin's configuration.
        
        Args:
            plugin_id: Plugin identifier
            
        Returns:
            True if config was deleted successfully, False otherwise
        """
        config_path = self._get_config_path(plugin_id)
        
        try:
            if os.path.exists(config_path):
                os.remove(config_path)
                
            if plugin_id in self.configs:
                del self.configs[plugin_id]
                
            if plugin_id in self.schemas:
                del self.schemas[plugin_id]
                
            logger.debug(f"Deleted configuration for plugin {plugin_id}")
            return True
        except Exception as e:
            logger.error(f"Error deleting config for plugin {plugin_id}: {str(e)}")
            return False


# Global config manager instance
config_manager = PluginConfigManager() 