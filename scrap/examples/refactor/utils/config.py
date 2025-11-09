"""
Task: tsk_c6160cc0 - Add Configuration System
Document: refactor/utils/config.py
dohcount: 1

Related Tasks:
    - tsk_7b62351d - Enhance Task List Hierarchy View (parent)
    - tsk_0a68bf93 - Implement Content Preview System (sibling)
    - tsk_8838881f - Add Comprehensive Tests (blocked by this)
    
Used By:
    - CLI Commands: For reading/writing configuration values
    - Task Display: For content preview and display settings
    - Colors: For theme and styling preferences

Purpose:
    Configuration system to manage and persist user preferences for display settings and other options,
    with a focus on content preview parameters and visualization preferences.

Requirements:
    - Must provide hierarchical configuration (default, user, command-line override)
    - Must persist settings to a config file
    - CRITICAL: Must never override user settings without explicit permission
    - CRITICAL: Must handle file I/O errors gracefully
    - Must provide sensible defaults

Changes:
    - v1: Initial implementation with support for content preview settings

Lessons Learned:
    - Using XDG directories ensures compatibility with different systems
    - JSON is more human-editable than other formats for user configuration
"""

import os
import json
import logging
from pathlib import Path
from typing import Dict, Any, Optional, Union, List, Tuple

logger = logging.getLogger(__name__)

# Default configuration directory - follow XDG Base Directory specification
DEFAULT_CONFIG_DIR = os.path.expanduser("~/.config/clickup_json_manager")
DEFAULT_CONFIG_FILE = "config.json"

# Default configuration values - used if no config file exists
DEFAULT_CONFIG = {
    "display": {
        "colors": {
            "enabled": True,  # Use colors by default
            "theme": "default",  # Default color theme
        },
        "content_preview": {
            "enabled": True,  # Show content preview by default
            "description_length": 80,  # Max description preview length
            "max_comments": 1,  # Default number of comments to show
            "comment_length": 80,  # Max comment preview length
            "truncation_indicator": "..."  # Indicator for truncated text
        },
        "tree_view": {
            "enabled": False,  # Don't use tree view by default
            "indent": 2,  # Spaces per indentation level
            "show_relationships": False,  # Don't show relationships by default
            "max_relationship_count": 2,  # Number of relationships to show per type
        },
        "task_list": {
            "hide_completed": True,  # Hide completed tasks by default
            "sort_by": "total",  # Default sort metric
            "reverse_sort": True,  # Sort in descending order
            "detailed_scores": False,  # Don't show detailed scores by default
        }
    },
    "behavior": {
        "force_prompt": True,  # Always prompt for confirmation on force operations
        "auto_save": True,  # Auto-save changes to template
    }
}


class ConfigManager:
    """
    Configuration manager for ClickUp JSON Manager CLI.
    
    Handles loading, saving, and accessing configuration settings.
    Provides a hierarchical configuration system with defaults, user settings,
    and command-line overrides.
    """
    
    def __init__(self, config_dir: Optional[str] = None, config_file: Optional[str] = None):
        """
        Initialize the configuration manager.
        
        Args:
            config_dir: Optional custom configuration directory path
            config_file: Optional custom configuration filename
        """
        self.config_dir = config_dir or DEFAULT_CONFIG_DIR
        self.config_file = config_file or DEFAULT_CONFIG_FILE
        self.config_path = os.path.join(self.config_dir, self.config_file)
        
        # Current configuration (loaded from file or defaults)
        self.config = dict(DEFAULT_CONFIG)
        
        # Command-line overrides (higher precedence than loaded config)
        self.overrides = {}
        
        # Load configuration if it exists
        self._ensure_config_dir()
        self._load_config()
    
    def _ensure_config_dir(self) -> None:
        """
        Ensure the configuration directory exists.
        
        Creates the directory if it doesn't exist.
        """
        try:
            os.makedirs(self.config_dir, exist_ok=True)
        except OSError as e:
            logger.warning(f"Could not create config directory {self.config_dir}: {e}")
    
    def _load_config(self) -> None:
        """
        Load configuration from file.
        
        Falls back to defaults if file doesn't exist or is invalid.
        """
        if not os.path.exists(self.config_path):
            logger.info(f"Config file {self.config_path} does not exist, using defaults")
            return
        
        try:
            with open(self.config_path, 'r') as f:
                user_config = json.load(f)
            
            # Deep update the default config with user settings
            self._deep_update(self.config, user_config)
            logger.info(f"Loaded configuration from {self.config_path}")
        except (json.JSONDecodeError, OSError) as e:
            logger.warning(f"Error loading config from {self.config_path}: {e}")
            logger.info("Using default configuration")
    
    def save_config(self) -> bool:
        """
        Save current configuration to file.
        
        Returns:
            True if save was successful, False otherwise
        """
        try:
            # Create a clean config without overrides
            clean_config = dict(self.config)
            
            with open(self.config_path, 'w') as f:
                json.dump(clean_config, f, indent=2)
            
            logger.info(f"Saved configuration to {self.config_path}")
            return True
        except OSError as e:
            logger.error(f"Error saving config to {self.config_path}: {e}")
            return False
    
    def _deep_update(self, target: Dict[str, Any], source: Dict[str, Any]) -> None:
        """
        Recursively update a nested dictionary.
        
        Args:
            target: Target dictionary to update
            source: Source dictionary with updates
        """
        for key, value in source.items():
            if key in target and isinstance(target[key], dict) and isinstance(value, dict):
                # Recursively update nested dictionaries
                self._deep_update(target[key], value)
            else:
                # Update or add the value
                target[key] = value
    
    def set_override(self, key_path: Union[str, List[str]], value: Any) -> None:
        """
        Set a configuration override from command-line arguments.
        
        Args:
            key_path: Key path as a dot-separated string (e.g., "display.colors.enabled")
                     or a list of keys (e.g., ["display", "colors", "enabled"])
            value: Value to set for the override
        """
        if isinstance(key_path, str):
            key_parts = key_path.split('.')
        else:
            key_parts = key_path
        
        # Build nested structure for overrides
        current = self.overrides
        for i, part in enumerate(key_parts[:-1]):
            if part not in current:
                current[part] = {}
            current = current[part]
        
        # Set the value
        current[key_parts[-1]] = value
    
    def get(self, key_path: Union[str, List[str]], default: Any = None) -> Any:
        """
        Get a configuration value with support for nested keys.
        
        Args:
            key_path: Key path as a dot-separated string (e.g., "display.colors.enabled")
                     or a list of keys (e.g., ["display", "colors", "enabled"])
            default: Default value to return if key is not found
            
        Returns:
            Configuration value or default if not found
        """
        if isinstance(key_path, str):
            key_parts = key_path.split('.')
        else:
            key_parts = key_path
        
        # First check overrides
        value = self._get_nested(self.overrides, key_parts)
        if value is not None:
            return value
        
        # Then check config
        value = self._get_nested(self.config, key_parts)
        if value is not None:
            return value
        
        # Fall back to default
        return default
    
    def _get_nested(self, d: Dict[str, Any], keys: List[str]) -> Any:
        """
        Get a value from a nested dictionary.
        
        Args:
            d: Dictionary to search
            keys: List of nested keys to traverse
            
        Returns:
            Value if found, None otherwise
        """
        current = d
        for key in keys:
            if not isinstance(current, dict) or key not in current:
                return None
            current = current[key]
        return current
    
    def set(self, key_path: Union[str, List[str]], value: Any, persist: bool = False) -> bool:
        """
        Set a configuration value with support for nested keys.
        
        Args:
            key_path: Key path as a dot-separated string (e.g., "display.colors.enabled")
                     or a list of keys (e.g., ["display", "colors", "enabled"])
            value: Value to set
            persist: Whether to save the configuration to file after setting the value
            
        Returns:
            True if successful, False otherwise
        """
        if isinstance(key_path, str):
            key_parts = key_path.split('.')
        else:
            key_parts = key_path
        
        # Update the configuration
        try:
            current = self.config
            for i, part in enumerate(key_parts[:-1]):
                if part not in current:
                    current[part] = {}
                current = current[part]
            
            current[key_parts[-1]] = value
            
            # Save if requested
            if persist:
                return self.save_config()
            return True
        except Exception as e:
            logger.error(f"Error setting config value for {key_path}: {e}")
            return False
    
    def get_display_config(self) -> Dict[str, Any]:
        """
        Get all display-related configuration settings.
        
        Returns:
            Dictionary of display settings
        """
        # Start with the config values
        display_config = dict(self.config.get('display', {}))
        
        # Apply any overrides
        if 'display' in self.overrides:
            self._deep_update(display_config, self.overrides['display'])
        
        return display_config
    
    def get_content_preview_config(self) -> Dict[str, Any]:
        """
        Get content preview configuration settings.
        
        Returns:
            Dictionary of content preview settings
        """
        # Get from display config to handle nested overrides properly
        display_config = self.get_display_config()
        return display_config.get('content_preview', {})
    
    def reset_to_defaults(self, persist: bool = False) -> bool:
        """
        Reset configuration to defaults.
        
        Args:
            persist: Whether to save the configuration to file after resetting
            
        Returns:
            True if successful, False otherwise
        """
        self.config = dict(DEFAULT_CONFIG)
        self.overrides = {}
        
        if persist:
            return self.save_config()
        return True


# Create a singleton instance for application-wide access
_config_manager = None

def get_config_manager(config_dir: Optional[str] = None, config_file: Optional[str] = None) -> ConfigManager:
    """
    Get or create the singleton ConfigManager instance.
    
    Args:
        config_dir: Optional custom configuration directory path
        config_file: Optional custom configuration filename
        
    Returns:
        ConfigManager instance
    """
    global _config_manager
    
    if _config_manager is None:
        _config_manager = ConfigManager(config_dir, config_file)
    
    return _config_manager


def apply_command_line_args(args) -> None:
    """
    Apply command-line arguments as configuration overrides.
    
    Args:
        args: Parsed command-line arguments
    """
    config = get_config_manager()
    
    # Apply any relevant command-line options to config overrides
    if hasattr(args, 'show_descriptions'):
        config.set_override('display.content_preview.enabled', args.show_descriptions)
    
    if hasattr(args, 'description_length'):
        config.set_override('display.content_preview.description_length', args.description_length)
    
    if hasattr(args, 'show_comments') and args.show_comments > 0:
        config.set_override('display.content_preview.max_comments', min(args.show_comments, 3))
    
    if hasattr(args, 'tree'):
        config.set_override('display.tree_view.enabled', args.tree)
    
    if hasattr(args, 'show_relationships'):
        config.set_override('display.tree_view.show_relationships', args.show_relationships)
    
    if hasattr(args, 'complete'):
        config.set_override('display.task_list.hide_completed', not args.complete)
    
    if hasattr(args, 'sort_by'):
        config.set_override('display.task_list.sort_by', args.sort_by)
    
    if hasattr(args, 'show_score'):
        config.set_override('display.task_list.detailed_scores', args.show_score)


def get_formatted_config() -> str:
    """
    Get a human-readable formatted representation of the current configuration.
    
    Returns:
        Formatted string with configuration details
    """
    config = get_config_manager()
    
    # Format the configuration for display
    lines = ["Current Configuration:"]
    
    def format_section(section_name, section_data, indent=0):
        section_lines = []
        indent_str = " " * indent
        
        section_lines.append(f"{indent_str}{section_name}:")
        
        for key, value in section_data.items():
            if isinstance(value, dict):
                section_lines.extend(format_section(key, value, indent + 2))
            else:
                section_lines.append(f"{indent_str}  {key}: {value}")
        
        return section_lines
    
    for section, data in config.config.items():
        lines.extend(format_section(section, data))
    
    if config.overrides:
        lines.append("\nCommand-line Overrides:")
        for section, data in config.overrides.items():
            lines.extend(format_section(section, data))
    
    return "\n".join(lines) 