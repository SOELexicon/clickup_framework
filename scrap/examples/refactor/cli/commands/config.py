"""
Task: tsk_c6160cc0 - Add Configuration System
Document: refactor/cli/commands/config.py
dohcount: 1

Related Tasks:
    - tsk_7b62351d - Enhance Task List Hierarchy View (parent)
    - tsk_8838881f - Add Comprehensive Tests (blocked by this)
    
Used By:
    - CLI Interface: For managing user configuration

Purpose:
    Provides the CLI command to view, set, and reset configuration settings.

Requirements:
    - Must allow listing all configuration settings
    - Must allow setting individual configuration values
    - Must allow resetting configuration to defaults
    - CRITICAL: Must validate configuration values before setting
    - CRITICAL: Must prompt for confirmation before destructive operations

Changes:
    - v1: Initial implementation
"""

from argparse import ArgumentParser, Namespace
from typing import Dict, List, Optional, Union, Any
import logging
import sys

from refactor.cli.command import Command
from refactor.cli.error_handling import CLIError, handle_cli_error
from refactor.utils.config import (
    get_config_manager, get_formatted_config,
    DEFAULT_CONFIG
)
from refactor.utils.colors import colorize, TextColor, DefaultTheme

logger = logging.getLogger(__name__)


class ConfigCommand(Command):
    """Command for managing configuration settings."""
    
    def __init__(self, core_manager):
        """Initialize with a core manager."""
        self._core_manager = core_manager
    
    @property
    def name(self) -> str:
        """Get the command name."""
        return "config"
    
    @property
    def description(self) -> str:
        """Get the command description."""
        return "View and manage configuration settings"
    
    def configure_parser(self, parser):
        """Configure the parser for configuration command."""
        subparsers = parser.add_subparsers(
            dest="subcommand",
            help="Configuration subcommands"
        )
        subparsers.required = True
        
        # Show configuration
        show_parser = subparsers.add_parser(
            "show",
            help="Show current configuration"
        )
        
        # Get specific configuration value
        get_parser = subparsers.add_parser(
            "get",
            help="Get a specific configuration value"
        )
        get_parser.add_argument(
            "key_path",
            help="Key path (e.g., 'display.content_preview.enabled')"
        )
        
        # Set configuration value
        set_parser = subparsers.add_parser(
            "set",
            help="Set a configuration value"
        )
        set_parser.add_argument(
            "key_path",
            help="Key path (e.g., 'display.content_preview.enabled')"
        )
        set_parser.add_argument(
            "value",
            help="Value to set"
        )
        set_parser.add_argument(
            "--no-validate",
            action="store_true",
            help="Skip validation of the value (use with caution)"
        )
        
        # Reset configuration
        reset_parser = subparsers.add_parser(
            "reset",
            help="Reset configuration to defaults"
        )
        reset_parser.add_argument(
            "--section",
            help="Specific section to reset (e.g., 'display.content_preview')"
        )
        reset_parser.add_argument(
            "--force",
            action="store_true",
            help="Force reset without confirmation"
        )
    
    def execute(self, args):
        """
        Execute the configuration command.
        
        Returns:
            Exit code (0 for success, non-zero for failure)
        """
        try:
            if args.subcommand == "show":
                return self._show_config()
            elif args.subcommand == "get":
                return self._get_config_value(args.key_path)
            elif args.subcommand == "set":
                return self._set_config_value(args.key_path, args.value, not args.no_validate)
            elif args.subcommand == "reset":
                return self._reset_config(args.section, args.force)
        except Exception as e:
            logger.error(f"Error executing config command: {str(e)}", exc_info=True)
            print(colorize(f"Error: {str(e)}", TextColor.RED))
            return 1
    
    def _show_config(self):
        """
        Show current configuration.
        
        Returns:
            Exit code (0 for success)
        """
        formatted_config = get_formatted_config()
        print(formatted_config)
        return 0
    
    def _get_config_value(self, key_path):
        """
        Get a specific configuration value.
        
        Args:
            key_path: Key path as a dot-separated string
            
        Returns:
            Exit code (0 for success)
        """
        config = get_config_manager()
        value = config.get(key_path)
        
        if value is None:
            print(colorize(f"Configuration key '{key_path}' not found", TextColor.YELLOW))
            return 1
        
        print(f"{key_path} = {value}")
        return 0
    
    def _set_config_value(self, key_path, value_str, validate=True):
        """
        Set a configuration value.
        
        Args:
            key_path: Key path as a dot-separated string
            value_str: String representation of the value to set
            validate: Whether to validate the value
            
        Returns:
            Exit code (0 for success)
        """
        config = get_config_manager()
        
        # Parse and validate the value
        value = self._parse_value(value_str)
        
        if validate:
            # Get the default value to determine the expected type
            default_value = self._get_default_value(key_path)
            
            if default_value is not None and not isinstance(value, type(default_value)):
                # Try to convert the value to the expected type
                try:
                    if isinstance(default_value, bool):
                        value = value_str.lower() in ('true', 'yes', 'y', '1')
                    elif isinstance(default_value, int):
                        value = int(value_str)
                    elif isinstance(default_value, float):
                        value = float(value_str)
                    elif isinstance(default_value, str):
                        value = str(value_str)
                    elif isinstance(default_value, list):
                        if not isinstance(value, list):
                            value = [value]
                    else:
                        print(colorize(f"Warning: Cannot validate value type for '{key_path}'", TextColor.YELLOW))
                except (ValueError, TypeError):
                    print(colorize(f"Error: Value '{value_str}' is not a valid {type(default_value).__name__}", TextColor.RED))
                    return 1
        
        # Set the value
        success = config.set(key_path, value, persist=True)
        
        if success:
            print(colorize(f"Set {key_path} = {value}", TextColor.GREEN))
            return 0
        else:
            print(colorize(f"Error setting configuration value", TextColor.RED))
            return 1
    
    def _reset_config(self, section=None, force=False):
        """
        Reset configuration to defaults.
        
        Args:
            section: Specific section to reset (None for all)
            force: Whether to force reset without confirmation
            
        Returns:
            Exit code (0 for success)
        """
        config = get_config_manager()
        
        if not force:
            # Prompt for confirmation
            if section:
                prompt = f"Reset section '{section}' to defaults? (y/n): "
            else:
                prompt = "Reset all configuration to defaults? (y/n): "
                
            response = input(prompt).strip().lower()
            if response not in ('y', 'yes'):
                print("Reset cancelled")
                return 0
        
        if section:
            # Reset a specific section
            if section not in config.config and '.' not in section:
                print(colorize(f"Section '{section}' not found in configuration", TextColor.YELLOW))
                return 1
                
            # Get the default value for the section
            if '.' in section:
                # Handle nested section (e.g., display.content_preview)
                parts = section.split('.')
                current_default = DEFAULT_CONFIG
                for part in parts:
                    if part not in current_default:
                        print(colorize(f"Section '{section}' not found in default configuration", TextColor.YELLOW))
                        return 1
                    current_default = current_default[part]
                
                # Set the section to default
                config.set(section, current_default, persist=True)
            else:
                # Handle top-level section
                if section not in DEFAULT_CONFIG:
                    print(colorize(f"Section '{section}' not found in default configuration", TextColor.YELLOW))
                    return 1
                    
                config.config[section] = dict(DEFAULT_CONFIG[section])
                config.save_config()
                
            print(colorize(f"Reset section '{section}' to defaults", TextColor.GREEN))
        else:
            # Reset all configuration
            success = config.reset_to_defaults(persist=True)
            
            if success:
                print(colorize("Reset all configuration to defaults", TextColor.GREEN))
            else:
                print(colorize("Error resetting configuration", TextColor.RED))
                return 1
                
        return 0
    
    def _parse_value(self, value_str):
        """
        Parse a string value into the appropriate type.
        
        Args:
            value_str: String representation of the value
            
        Returns:
            Parsed value with the appropriate type
        """
        # Try to detect and convert the value type
        if value_str.lower() in ('true', 'false'):
            return value_str.lower() == 'true'
        elif value_str.lower() in ('none', 'null'):
            return None
        elif value_str.startswith('[') and value_str.endswith(']'):
            # Simple list parsing
            items = value_str[1:-1].split(',')
            return [item.strip() for item in items if item.strip()]
        else:
            try:
                # Try to convert to int or float
                if '.' in value_str:
                    return float(value_str)
                else:
                    return int(value_str)
            except ValueError:
                # Fall back to string if numeric conversion fails
                return value_str
    
    def _get_default_value(self, key_path):
        """
        Get the default value for a configuration key.
        
        Args:
            key_path: Key path as a dot-separated string
            
        Returns:
            Default value or None if not found
        """
        parts = key_path.split('.')
        current = DEFAULT_CONFIG
        
        try:
            for part in parts:
                current = current[part]
            return current
        except (KeyError, TypeError):
            return None 