"""
Plugin Configuration UI

This module provides a simple text-based UI for managing plugin configurations.
"""

import logging
import sys
from typing import Any, Dict, List, Optional, Tuple

from .config_manager import PluginConfigManager, config_manager


logger = logging.getLogger(__name__)


class ConfigUI:
    """
    Text-based UI for plugin configuration management.
    
    This class provides functionality to:
    - List available plugins
    - View plugin configuration
    - Edit plugin configuration
    - Reset plugin configuration to defaults
    """
    
    def __init__(self, config_manager: Optional[PluginConfigManager] = None):
        """
        Initialize the configuration UI.
        
        Args:
            config_manager: Plugin configuration manager instance
        """
        self.config_manager = config_manager or config_manager
    
    def list_plugins(self) -> List[str]:
        """
        List all plugins with registered configurations.
        
        Returns:
            List of plugin IDs
        """
        return list(self.config_manager.schemas.keys())
    
    def display_plugin_config(self, plugin_id: str) -> None:
        """
        Display the configuration for a plugin.
        
        Args:
            plugin_id: Plugin identifier
        """
        if plugin_id not in self.config_manager.schemas:
            print(f"Plugin '{plugin_id}' not found")
            return
        
        schema = self.config_manager.schemas[plugin_id]
        config = self.config_manager.get_config(plugin_id)
        
        print(f"\nConfiguration for plugin: {plugin_id}\n")
        print("-" * 50)
        
        # Find the max key length for formatting
        max_key_len = max(len(key) for key in schema.keys())
        
        # Display each configuration item
        for key, field_schema in schema.items():
            description = field_schema.get("description", "")
            field_type = field_schema.get("type", "")
            required = field_schema.get("required", False)
            default = field_schema.get("default", "None")
            current = config.get(key, default)
            
            # Format the output
            print(f"{key:{max_key_len + 2}} : {current}")
            print(f"{'':{max_key_len + 4}}{description}")
            print(f"{'':{max_key_len + 4}}Type: {field_type}, Required: {required}, Default: {default}")
            print()
    
    def edit_plugin_config(self, plugin_id: str) -> bool:
        """
        Edit the configuration for a plugin.
        
        Args:
            plugin_id: Plugin identifier
            
        Returns:
            True if configuration was updated successfully, False otherwise
        """
        if plugin_id not in self.config_manager.schemas:
            print(f"Plugin '{plugin_id}' not found")
            return False
        
        schema = self.config_manager.schemas[plugin_id]
        config = self.config_manager.get_config(plugin_id)
        
        print(f"\nEditing configuration for plugin: {plugin_id}\n")
        print("(Enter empty line to keep current value)")
        print("-" * 50)
        
        updated_config = {}
        
        for key, field_schema in schema.items():
            description = field_schema.get("description", "")
            field_type = field_schema.get("type", "")
            current = config.get(key, field_schema.get("default", ""))
            
            print(f"\n{key} ({field_type}):")
            print(f"  {description}")
            print(f"  Current value: {current}")
            
            # Get new value
            try:
                input_val = input(f"  New value: ").strip()
                
                # Empty input means keep current value
                if not input_val:
                    updated_config[key] = current
                    continue
                
                # Convert to appropriate type
                if field_type == "string":
                    updated_config[key] = input_val
                elif field_type == "integer":
                    updated_config[key] = int(input_val)
                elif field_type == "number":
                    updated_config[key] = float(input_val)
                elif field_type == "boolean":
                    updated_config[key] = input_val.lower() in ("true", "yes", "y", "1")
                elif field_type == "array":
                    updated_config[key] = [item.strip() for item in input_val.split(",")]
                elif field_type == "object":
                    print("  (Cannot edit object type through this interface)")
                    updated_config[key] = current
            except ValueError:
                print(f"  Invalid value for type {field_type}, keeping current value")
                updated_config[key] = current
        
        # Validate and save the updated configuration
        is_valid, error = self.config_manager.validate_config(plugin_id, updated_config)
        if not is_valid:
            print(f"\nConfiguration validation failed: {error}")
            return False
        
        # Update the configuration
        success = self.config_manager.update_config(plugin_id, updated_config, validate=False)
        if success:
            print("\nConfiguration updated successfully")
        else:
            print("\nFailed to update configuration")
        
        return success
    
    def reset_plugin_config(self, plugin_id: str) -> bool:
        """
        Reset the configuration for a plugin to defaults.
        
        Args:
            plugin_id: Plugin identifier
            
        Returns:
            True if configuration was reset successfully, False otherwise
        """
        if plugin_id not in self.config_manager.schemas:
            print(f"Plugin '{plugin_id}' not found")
            return False
        
        schema = self.config_manager.schemas[plugin_id]
        
        # Create default configuration
        default_config = self.config_manager._create_default_config(schema)
        
        # Update the configuration
        success = self.config_manager.update_config(plugin_id, default_config, validate=False)
        if success:
            print(f"\nConfiguration for plugin '{plugin_id}' reset to defaults")
        else:
            print(f"\nFailed to reset configuration for plugin '{plugin_id}'")
        
        return success
    
    def run_interactive(self) -> None:
        """
        Run the configuration UI in interactive mode.
        """
        while True:
            print("\nPlugin Configuration Manager")
            print("-" * 30)
            print("1. List plugins")
            print("2. View plugin configuration")
            print("3. Edit plugin configuration")
            print("4. Reset plugin configuration to defaults")
            print("5. Exit")
            
            choice = input("\nEnter choice (1-5): ").strip()
            
            try:
                if choice == "1":
                    # List plugins
                    plugins = self.list_plugins()
                    print("\nAvailable plugins:")
                    for plugin_id in plugins:
                        print(f"- {plugin_id}")
                    
                    if not plugins:
                        print("No plugins found")
                
                elif choice == "2":
                    # View plugin configuration
                    plugins = self.list_plugins()
                    if not plugins:
                        print("\nNo plugins found")
                        continue
                    
                    print("\nAvailable plugins:")
                    for i, plugin_id in enumerate(plugins, 1):
                        print(f"{i}. {plugin_id}")
                    
                    plugin_choice = input("\nEnter plugin number: ").strip()
                    try:
                        idx = int(plugin_choice) - 1
                        if 0 <= idx < len(plugins):
                            self.display_plugin_config(plugins[idx])
                        else:
                            print("Invalid plugin number")
                    except ValueError:
                        print("Invalid input")
                
                elif choice == "3":
                    # Edit plugin configuration
                    plugins = self.list_plugins()
                    if not plugins:
                        print("\nNo plugins found")
                        continue
                    
                    print("\nAvailable plugins:")
                    for i, plugin_id in enumerate(plugins, 1):
                        print(f"{i}. {plugin_id}")
                    
                    plugin_choice = input("\nEnter plugin number: ").strip()
                    try:
                        idx = int(plugin_choice) - 1
                        if 0 <= idx < len(plugins):
                            self.edit_plugin_config(plugins[idx])
                        else:
                            print("Invalid plugin number")
                    except ValueError:
                        print("Invalid input")
                
                elif choice == "4":
                    # Reset plugin configuration
                    plugins = self.list_plugins()
                    if not plugins:
                        print("\nNo plugins found")
                        continue
                    
                    print("\nAvailable plugins:")
                    for i, plugin_id in enumerate(plugins, 1):
                        print(f"{i}. {plugin_id}")
                    
                    plugin_choice = input("\nEnter plugin number: ").strip()
                    try:
                        idx = int(plugin_choice) - 1
                        if 0 <= idx < len(plugins):
                            confirm = input(f"Reset configuration for '{plugins[idx]}' to defaults? (y/n): ").strip().lower()
                            if confirm in ("y", "yes"):
                                self.reset_plugin_config(plugins[idx])
                        else:
                            print("Invalid plugin number")
                    except ValueError:
                        print("Invalid input")
                
                elif choice == "5":
                    # Exit
                    print("\nExiting configuration manager")
                    break
                
                else:
                    print("\nInvalid choice, please try again")
            
            except Exception as e:
                print(f"\nError: {str(e)}")
                logger.exception("Error in interactive mode")


# Create a global config UI instance
config_ui = ConfigUI()


def main() -> None:
    """
    Main entry point for the configuration UI.
    """
    # Configure logging
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    )
    
    # Run the UI
    config_ui.run_interactive()


if __name__ == "__main__":
    main() 