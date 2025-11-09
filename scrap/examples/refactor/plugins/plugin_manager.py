"""
Task: tsk_3f55d115 - Update Plugins Module Comments
Document: refactor/plugins/plugin_manager.py
dohcount: 1

Related Tasks:
    - tsk_0a733101 - Code Comments Enhancement (parent)
    - tsk_bf28d342 - Update CLI Module Comments (sibling)
    - tsk_4c899138 - Update Storage Module Comments (sibling)

Used By:
    - CoreManager: Leverages PluginManager to discover and load plugins
    - CLI Commands: Plugin-related commands use this for plugin management
    - CustomPlugins: Plugin instances are managed by this component

Purpose:
    Provides the core plugin management functionality for the ClickUp JSON Manager,
    including plugin discovery, loading, dependency resolution, and lifecycle management.

Requirements:
    - Must handle plugin dependencies correctly and prevent circular dependencies
    - Must isolate plugin failures to prevent system-wide issues
    - CRITICAL: Plugin loading order must respect dependencies
    - CRITICAL: Plugin configuration must be persisted and validated
    - CRITICAL: Plugin state transitions must be atomic and consistent

Plugin Manager

This module provides the core plugin management functionality for the
ClickUp JSON Manager, including plugin discovery, loading, and lifecycle
management.
"""

import importlib
import inspect
import json
import logging
import os
import pkgutil
import sys
from dataclasses import dataclass
from enum import Enum, auto
from pathlib import Path
from types import ModuleType
from typing import Any, Callable, Dict, List, Optional, Set, Type, Union, Tuple

from ..common.exceptions import PluginError


# Initialize logger
logger = logging.getLogger(__name__)


class PluginStatus(Enum):
    """Enum representing the current status of a plugin."""
    DISCOVERED = auto()
    LOADED = auto()
    ENABLED = auto()
    DISABLED = auto()
    ERROR = auto()


@dataclass
class PluginInfo:
    """Information about a plugin."""
    # Required fields
    id: str
    name: str
    version: str
    description: str
    entry_point: str
    
    # Optional fields
    author: Optional[str] = None
    website: Optional[str] = None
    license: Optional[str] = None
    min_app_version: Optional[str] = None
    max_app_version: Optional[str] = None
    tags: List[str] = None
    dependencies: List[str] = None
    
    # Runtime fields (not in manifest)
    status: PluginStatus = PluginStatus.DISCOVERED
    error_message: Optional[str] = None
    module: Optional[ModuleType] = None
    path: Optional[str] = None
    
    def __post_init__(self):
        """Initialize default values for collections."""
        if self.tags is None:
            self.tags = []
        if self.dependencies is None:
            self.dependencies = []


class Plugin:
    """
    Base class that all plugins must inherit from.
    
    Plugins must implement the initialize and cleanup methods.
    """
    
    def __init__(self, plugin_id: str, manager: 'PluginManager'):
        """Initialize the plugin with its ID and a reference to the plugin manager."""
        self.plugin_id = plugin_id
        self.manager = manager
        self.initialized = False
        self._config = {}
    
    def initialize(self) -> bool:
        """
        Initialize the plugin.
        
        This method is called when the plugin is enabled.
        
        Returns:
            bool: True if initialization was successful, False otherwise.
        """
        self.initialized = True
        return True
    
    def cleanup(self) -> bool:
        """
        Clean up resources used by the plugin.
        
        This method is called when the plugin is disabled.
        
        Returns:
            bool: True if cleanup was successful, False otherwise.
        """
        self.initialized = False
        return True
    
    def get_config_schema(self) -> Dict[str, Dict[str, Any]]:
        """
        Get the configuration schema for this plugin.
        
        Returns:
            Dict[str, Dict[str, Any]]: Configuration schema
        """
        return {}
    
    def get_config(self) -> Dict[str, Any]:
        """
        Get the current configuration for this plugin.
        
        Returns:
            Dict[str, Any]: Current configuration
        """
        return self._config
    
    def set_config(self, config: Dict[str, Any]) -> None:
        """
        Set the configuration for this plugin.
        
        Args:
            config: New configuration values
        """
        self._config = config
    
    def validate_config(self, config: Dict[str, Any]) -> Tuple[bool, Optional[str]]:
        """
        Validate the configuration for this plugin.
        
        Args:
            config: Configuration to validate
            
        Returns:
            Tuple[bool, Optional[str]]: (is_valid, error_message)
        """
        return True, None


class PluginManager:
    """
    Manages the discovery, loading, and lifecycle of plugins.
    """
    
    def __init__(self, plugin_dirs: Optional[List[str]] = None):
        """
        Initialize the plugin manager.
        
        Args:
            plugin_dirs: List of directories to search for plugins.
        """
        self.plugin_dirs = plugin_dirs or []
        self._add_default_plugin_dirs()
        
        # Dictionary of plugin_id -> PluginInfo
        self.plugins: Dict[str, PluginInfo] = {}
        
        # Dictionary of plugin_id -> Plugin instance
        self.instances: Dict[str, Plugin] = {}
        
        # Set of enabled plugin IDs
        self.enabled_plugins: Set[str] = set()
        
        # Set to True after all global services are registered
        self.services_registered = False
        
        # Dictionary of service_name -> service_instance
        self.services: Dict[str, Any] = {}
    
    def _add_default_plugin_dirs(self):
        """Add default plugin directories to the search path."""
        # Add the built-in plugins directory
        self.plugin_dirs.append(os.path.join(os.path.dirname(__file__), "builtin"))
        
        # Add user plugins directory
        user_plugins_dir = os.path.expanduser("~/.clickup_json_manager/plugins")
        self.plugin_dirs.append(user_plugins_dir)
        
        # Add current working directory plugins
        self.plugin_dirs.append(os.path.join(os.getcwd(), "plugins"))
    
    def register_services(self) -> None:
        """
        Register global services for plugins to use.
        
        This should be called after importing all necessary modules.
        """
        if self.services_registered:
            return
            
        # Import here to avoid circular imports
        from .config import config_manager
        from .hooks.hook_system import registry as hook_registry
        
        # Register services
        self.services = {
            "config_manager": config_manager,
            "hook_registry": hook_registry
        }
        
        self.services_registered = True
        logger.debug("Global services registered")
    
    def get_service(self, service_name: str) -> Optional[Any]:
        """
        Get a global service by name.
        
        Args:
            service_name: Name of the service
            
        Returns:
            Service instance, or None if not found
        """
        return self.services.get(service_name)
    
    def discover_plugins(self) -> List[PluginInfo]:
        """
        Discover plugins in the configured plugin directories.
        
        Returns:
            List[PluginInfo]: Information about discovered plugins.
        """
        discovered_plugins = []
        
        for plugin_dir in self.plugin_dirs:
            if not os.path.exists(plugin_dir):
                logger.debug(f"Plugin directory does not exist: {plugin_dir}")
                continue
            
            logger.debug(f"Scanning for plugins in: {plugin_dir}")
            for item in os.listdir(plugin_dir):
                item_path = os.path.join(plugin_dir, item)
                
                # Skip non-directories
                if not os.path.isdir(item_path):
                    continue
                
                # Check for manifest file
                manifest_path = os.path.join(item_path, "manifest.json")
                if not os.path.exists(manifest_path):
                    logger.debug(f"No manifest.json found in: {item_path}")
                    continue
                
                try:
                    # Load and validate the manifest
                    plugin_info = self._load_manifest(manifest_path)
                    plugin_info.path = item_path
                    
                    # Add to discovered plugins
                    discovered_plugins.append(plugin_info)
                    self.plugins[plugin_info.id] = plugin_info
                    
                    logger.info(f"Discovered plugin: {plugin_info.name} ({plugin_info.id})")
                except Exception as e:
                    logger.error(f"Error loading plugin manifest from {manifest_path}: {str(e)}")
        
        return discovered_plugins
    
    def _load_manifest(self, manifest_path: str) -> PluginInfo:
        """
        Load and validate a plugin manifest file.
        
        Args:
            manifest_path: Path to the manifest.json file.
            
        Returns:
            PluginInfo: Information about the plugin.
            
        Raises:
            PluginError: If the manifest is invalid or missing required fields.
        """
        try:
            with open(manifest_path, "r", encoding="utf-8") as f:
                manifest = json.load(f)
            
            # Check required fields
            required_fields = ["id", "name", "version", "description", "entry_point"]
            for field in required_fields:
                if field not in manifest:
                    raise PluginError(f"Plugin manifest missing required field: {field}")
            
            # Create PluginInfo from manifest
            return PluginInfo(
                id=manifest["id"],
                name=manifest["name"],
                version=manifest["version"],
                description=manifest["description"],
                entry_point=manifest["entry_point"],
                author=manifest.get("author"),
                website=manifest.get("website"),
                license=manifest.get("license"),
                min_app_version=manifest.get("min_app_version"),
                max_app_version=manifest.get("max_app_version"),
                tags=manifest.get("tags", []),
                dependencies=manifest.get("dependencies", []),
                status=PluginStatus.DISCOVERED
            )
        except json.JSONDecodeError as e:
            raise PluginError(f"Invalid JSON in plugin manifest: {str(e)}")
        except Exception as e:
            raise PluginError(f"Error loading plugin manifest: {str(e)}")
    
    def load_plugin(self, plugin_id: str) -> bool:
        """
        Load a plugin by its ID.
        
        This imports the plugin module but does not initialize it.
        
        Args:
            plugin_id: The ID of the plugin to load.
            
        Returns:
            bool: True if the plugin was loaded successfully, False otherwise.
        """
        if plugin_id not in self.plugins:
            logger.error(f"Cannot load unknown plugin: {plugin_id}")
            return False
        
        plugin_info = self.plugins[plugin_id]
        
        if plugin_info.status in (PluginStatus.LOADED, PluginStatus.ENABLED):
            logger.debug(f"Plugin already loaded: {plugin_id}")
            return True
        
        try:
            # Add plugin directory to path temporarily
            sys.path.insert(0, plugin_info.path)
            
            # Import the module
            module_path = plugin_info.entry_point
            module = importlib.import_module(module_path)
            
            # Find plugin class (must subclass Plugin)
            plugin_class = None
            for name, obj in inspect.getmembers(module):
                if (inspect.isclass(obj) and issubclass(obj, Plugin) and 
                        obj is not Plugin):
                    plugin_class = obj
                    break
            
            if plugin_class is None:
                raise PluginError(f"No Plugin subclass found in {module_path}")
            
            # Store the module in plugin info
            plugin_info.module = module
            plugin_info.status = PluginStatus.LOADED
            
            # Create plugin instance
            plugin_instance = plugin_class(plugin_id, self)
            self.instances[plugin_id] = plugin_instance
            
            # Register plugin configuration
            self._register_plugin_config(plugin_id, plugin_instance)
            
            logger.info(f"Successfully loaded plugin: {plugin_info.name} ({plugin_id})")
            return True
            
        except Exception as e:
            error_msg = f"Error loading plugin {plugin_id}: {str(e)}"
            logger.error(error_msg)
            plugin_info.status = PluginStatus.ERROR
            plugin_info.error_message = error_msg
            return False
        finally:
            # Remove the plugin directory from path
            if plugin_info.path in sys.path:
                sys.path.remove(plugin_info.path)
    
    def _register_plugin_config(self, plugin_id: str, plugin_instance: Plugin) -> None:
        """
        Register plugin configuration with the config manager.
        
        Args:
            plugin_id: Plugin identifier
            plugin_instance: Plugin instance
        """
        # Ensure services are registered
        if not self.services_registered:
            self.register_services()
        
        # Get config manager
        config_manager = self.get_service("config_manager")
        if not config_manager:
            logger.warning(f"Cannot register config for plugin {plugin_id}: config_manager not available")
            return
        
        # Get config schema from plugin
        schema = plugin_instance.get_config_schema()
        if not schema:
            logger.debug(f"Plugin {plugin_id} does not provide a config schema")
            return
        
        # Register config with manager
        config_manager.register_plugin_config(plugin_id, schema)
        
        # Get the initial config
        config = config_manager.get_config(plugin_id)
        
        # Set the config on the plugin instance
        plugin_instance.set_config(config)
    
    def enable_plugin(self, plugin_id: str) -> bool:
        """
        Enable a plugin by its ID.
        
        This loads the plugin if it isn't already loaded and then initializes it.
        
        Args:
            plugin_id: The ID of the plugin to enable.
            
        Returns:
            bool: True if the plugin was enabled successfully, False otherwise.
        """
        if plugin_id not in self.plugins:
            logger.error(f"Cannot enable unknown plugin: {plugin_id}")
            return False
        
        plugin_info = self.plugins[plugin_id]
        
        # If plugin is already enabled, return True
        if plugin_info.status == PluginStatus.ENABLED:
            return True
        
        # Load the plugin if it's not loaded
        if plugin_info.status not in (PluginStatus.LOADED, PluginStatus.ENABLED):
            if not self.load_plugin(plugin_id):
                return False
        
        # Check for plugin dependencies
        for dep_id in plugin_info.dependencies:
            if dep_id not in self.enabled_plugins:
                logger.error(f"Cannot enable {plugin_id}: dependency {dep_id} is not enabled")
                return False
        
        # Initialize the plugin
        try:
            plugin_instance = self.instances[plugin_id]
            if plugin_instance.initialize():
                plugin_info.status = PluginStatus.ENABLED
                self.enabled_plugins.add(plugin_id)
                logger.info(f"Successfully enabled plugin: {plugin_info.name} ({plugin_id})")
                return True
            else:
                error_msg = f"Plugin {plugin_id} failed to initialize"
                logger.error(error_msg)
                plugin_info.status = PluginStatus.ERROR
                plugin_info.error_message = error_msg
                return False
        except Exception as e:
            error_msg = f"Error enabling plugin {plugin_id}: {str(e)}"
            logger.error(error_msg)
            plugin_info.status = PluginStatus.ERROR
            plugin_info.error_message = error_msg
            return False
    
    def disable_plugin(self, plugin_id: str) -> bool:
        """
        Disable a plugin by its ID.
        
        Args:
            plugin_id: The ID of the plugin to disable.
            
        Returns:
            bool: True if the plugin was disabled successfully, False otherwise.
        """
        if plugin_id not in self.plugins:
            logger.error(f"Cannot disable unknown plugin: {plugin_id}")
            return False
        
        plugin_info = self.plugins[plugin_id]
        
        # If plugin is not enabled, do nothing
        if plugin_info.status != PluginStatus.ENABLED:
            return True
        
        # Check for dependent plugins
        dependent_plugins = []
        for pid, pinfo in self.plugins.items():
            if plugin_id in pinfo.dependencies and pid in self.enabled_plugins:
                dependent_plugins.append(pid)
        
        if dependent_plugins:
            logger.error(f"Cannot disable {plugin_id}: other plugins depend on it: {dependent_plugins}")
            return False
        
        # Cleanup the plugin
        try:
            plugin_instance = self.instances[plugin_id]
            if plugin_instance.cleanup():
                plugin_info.status = PluginStatus.LOADED
                self.enabled_plugins.remove(plugin_id)
                logger.info(f"Successfully disabled plugin: {plugin_info.name} ({plugin_id})")
                return True
            else:
                error_msg = f"Plugin {plugin_id} failed to clean up"
                logger.error(error_msg)
                plugin_info.status = PluginStatus.ERROR
                plugin_info.error_message = error_msg
                return False
        except Exception as e:
            error_msg = f"Error disabling plugin {plugin_id}: {str(e)}"
            logger.error(error_msg)
            plugin_info.status = PluginStatus.ERROR
            plugin_info.error_message = error_msg
            return False
    
    def get_plugin_info(self, plugin_id: str) -> Optional[PluginInfo]:
        """
        Get information about a plugin.
        
        Args:
            plugin_id: The ID of the plugin.
            
        Returns:
            Optional[PluginInfo]: Information about the plugin, or None if not found.
        """
        return self.plugins.get(plugin_id)
    
    def get_plugin_instance(self, plugin_id: str) -> Optional[Plugin]:
        """
        Get the instance of a plugin.
        
        Args:
            plugin_id: The ID of the plugin.
            
        Returns:
            Optional[Plugin]: The plugin instance, or None if not found or not loaded.
        """
        return self.instances.get(plugin_id)
    
    def get_all_plugins(self) -> Dict[str, PluginInfo]:
        """
        Get information about all discovered plugins.
        
        Returns:
            Dict[str, PluginInfo]: Dictionary mapping plugin IDs to plugin information.
        """
        return self.plugins
    
    def get_enabled_plugins(self) -> Dict[str, PluginInfo]:
        """
        Get information about all enabled plugins.
        
        Returns:
            Dict[str, PluginInfo]: Dictionary mapping plugin IDs to plugin information
            for enabled plugins.
        """
        return {pid: self.plugins[pid] for pid in self.enabled_plugins if pid in self.plugins}
    
    def load_all_plugins(self) -> bool:
        """
        Load all discovered plugins.
        
        Returns:
            bool: True if all plugins were loaded successfully, False otherwise.
        """
        success = True
        for plugin_id in list(self.plugins.keys()):
            if not self.load_plugin(plugin_id):
                success = False
        return success
    
    def enable_all_plugins(self) -> bool:
        """
        Enable all discovered and loaded plugins.
        
        Returns:
            bool: True if all plugins were enabled successfully, False otherwise.
        """
        # First load all plugins
        self.load_all_plugins()
        
        # Find plugins with no dependencies and enable them first
        no_deps = [pid for pid, pinfo in self.plugins.items() 
                  if not pinfo.dependencies and pinfo.status == PluginStatus.LOADED]
        
        for plugin_id in no_deps:
            self.enable_plugin(plugin_id)
        
        # Enable remaining plugins with dependencies, trying to resolve dependencies
        remaining = [pid for pid, pinfo in self.plugins.items() 
                    if pinfo.status == PluginStatus.LOADED]
        
        # Keep trying to enable plugins until we make no progress or all are enabled
        while remaining:
            progress = False
            for plugin_id in list(remaining):
                if self.enable_plugin(plugin_id):
                    remaining.remove(plugin_id)
                    progress = True
            
            # If we made no progress, we can't resolve dependencies
            if not progress:
                break
        
        return not remaining


# Create a global plugin manager instance
plugin_manager = PluginManager() 