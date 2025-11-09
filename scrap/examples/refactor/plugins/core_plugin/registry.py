"""
Task: tsk_3f55d115 - Update Plugins Module Comments
Document: refactor/plugins/core_plugin/registry.py
dohcount: 1

Related Tasks:
    - tsk_0a733101 - Code Comments Enhancement (parent)
    - tsk_bf28d342 - Update CLI Module Comments (sibling)
    - tsk_4c899138 - Update Storage Module Comments (sibling)

Used By:
    - CoreManager: Manages plugin lifecycle using this registry
    - PluginManager: Coordinates plugin discovery using registry functionality
    - TaskService: Accesses task-related plugins through registry
    - CommandSystem: Uses registry to find and execute plugin commands

Purpose:
    Provides the core functionality for plugin registration, discovery, and lifecycle
    management. Handles plugin dependencies, initialization, startup, and shutdown.

Requirements:
    - Plugin discovery must work across multiple filesystem locations
    - Plugin registry must handle plugin dependencies correctly
    - Plugin lifecycle transitions must be managed safely
    - CRITICAL: Plugin failures must be isolated to prevent system crashes
    - CRITICAL: Plugin initialization must follow correct dependency order
    - CRITICAL: Plugin registry must work with both manifest-based and code-based plugins

Plugin registry implementation module.

This module provides the core functionality for plugin registration, discovery,
and lifecycle management.
"""

import os
import sys
import importlib
import importlib.util
import inspect
import logging
import pkgutil
import yaml
from typing import Dict, List, Any, Optional, Set, Union, Callable, Type, TypeVar

from refactor.plugins.core_plugin.interface import CorePluginInterface, PluginContext


logger = logging.getLogger(__name__)


class PluginRegistry:
    """
    Registry for managing plugins throughout their lifecycle.
    
    This class provides methods to register, discover, initialize, and 
    manage plugins across the application.
    """
    
    def __init__(self):
        """Initialize the plugin registry."""
        self._plugins: Dict[str, CorePluginInterface] = {}
        self._plugin_classes: Dict[str, Type[CorePluginInterface]] = {}
        self._plugin_paths: List[str] = []
        self._initialized = False
        self._contexts: Dict[str, PluginContext] = {}
    
    def register_plugin_path(self, path: str) -> None:
        """
        Register a path to search for plugins.
        
        Args:
            path: Directory path to search for plugins
        """
        if os.path.isdir(path) and path not in self._plugin_paths:
            self._plugin_paths.append(path)
            # Add path to Python module search path if it's not already there
            if path not in sys.path:
                sys.path.append(path)
    
    def register_plugin_class(self, plugin_class: Type[CorePluginInterface]) -> bool:
        """
        Register a plugin class.
        
        Args:
            plugin_class: Plugin class to register
            
        Returns:
            True if registration was successful, False otherwise
        """
        # Create a temporary instance to get plugin metadata
        try:
            temp_instance = plugin_class("temp_id", "temp_name", "0.0.0")
            plugin_id = temp_instance.plugin_id
            
            if plugin_id in self._plugin_classes:
                logger.warning(f"Plugin class with ID '{plugin_id}' already registered")
                return False
            
            self._plugin_classes[plugin_id] = plugin_class
            return True
        
        except Exception as e:
            logger.error(f"Failed to register plugin class: {e}")
            return False
    
    def discover_plugins(self) -> List[str]:
        """
        Discover plugins in registered paths.
        
        Returns:
            List of discovered plugin IDs
        """
        discovered_plugins = []
        
        for path in self._plugin_paths:
            logger.info(f"Searching for plugins in: {path}")
            self._discover_plugins_in_path(path, discovered_plugins)
        
        return discovered_plugins
    
    def _discover_plugins_in_path(self, path: str, discovered_plugins: List[str]) -> None:
        """
        Discover plugins in a specific path.
        
        Args:
            path: Path to search
            discovered_plugins: List to add discovered plugin IDs to
        """
        # Look for Python modules in the path
        for _, name, is_pkg in pkgutil.iter_modules([path]):
            module_path = os.path.join(path, name)
            
            if is_pkg:
                # If it's a package, check if it has a plugin manifest
                manifest_path = os.path.join(module_path, "plugin.yaml")
                if os.path.exists(manifest_path):
                    self._load_plugin_from_manifest(manifest_path, discovered_plugins)
                else:
                    # Recursively search in subpackages
                    self._discover_plugins_in_path(module_path, discovered_plugins)
            else:
                # If it's a module, check if it contains plugin classes
                self._load_plugin_from_module(name, discovered_plugins)
    
    def _load_plugin_from_manifest(self, manifest_path: str, discovered_plugins: List[str]) -> None:
        """
        Load a plugin using its manifest file.
        
        Args:
            manifest_path: Path to the plugin manifest
            discovered_plugins: List to add discovered plugin IDs to
        """
        try:
            with open(manifest_path, 'r') as f:
                manifest = yaml.safe_load(f)
            
            plugin_id = manifest.get('id')
            plugin_name = manifest.get('name')
            version = manifest.get('version')
            main_module = manifest.get('main_module')
            main_class = manifest.get('main_class')
            
            if not all([plugin_id, plugin_name, version, main_module, main_class]):
                logger.warning(f"Invalid plugin manifest at {manifest_path}")
                return
            
            # Import the module
            module_path = os.path.dirname(manifest_path)
            module_name = os.path.basename(module_path)
            
            full_module_name = f"{module_name}.{main_module}"
            try:
                module = importlib.import_module(full_module_name)
                
                # Get the plugin class
                if hasattr(module, main_class):
                    plugin_class = getattr(module, main_class)
                    if inspect.isclass(plugin_class) and issubclass(plugin_class, CorePluginInterface):
                        # Register the plugin
                        self._plugin_classes[plugin_id] = plugin_class
                        discovered_plugins.append(plugin_id)
                        logger.info(f"Discovered plugin from manifest: {plugin_id} ({plugin_name} v{version})")
                    else:
                        logger.warning(f"Class {main_class} is not a valid plugin class")
                else:
                    logger.warning(f"Module {full_module_name} does not contain class {main_class}")
            
            except ImportError as e:
                logger.error(f"Failed to import plugin module {full_module_name}: {e}")
            
        except Exception as e:
            logger.error(f"Failed to load plugin manifest {manifest_path}: {e}")
    
    def _load_plugin_from_module(self, module_name: str, discovered_plugins: List[str]) -> None:
        """
        Load plugins from a Python module.
        
        Args:
            module_name: Name of the module
            discovered_plugins: List to add discovered plugin IDs to
        """
        try:
            module = importlib.import_module(module_name)
            
            # Find plugin classes in the module
            for name, obj in inspect.getmembers(module, inspect.isclass):
                if (issubclass(obj, CorePluginInterface) and 
                    obj is not CorePluginInterface and 
                    module_name == obj.__module__):
                    
                    # Create temporary instance to get plugin ID
                    temp_instance = obj("temp_id", f"Discovered {name}", "0.0.0")
                    plugin_id = temp_instance.plugin_id
                    
                    # Register the plugin class
                    self._plugin_classes[plugin_id] = obj
                    discovered_plugins.append(plugin_id)
                    logger.info(f"Discovered plugin from module: {plugin_id} ({name})")
        
        except ImportError as e:
            logger.warning(f"Failed to import module {module_name}: {e}")
        except Exception as e:
            logger.warning(f"Error inspecting module {module_name}: {e}")
    
    def create_plugin(self, plugin_id: str, config: Dict[str, Any] = None) -> Optional[CorePluginInterface]:
        """
        Create a plugin instance from a registered plugin class.
        
        Args:
            plugin_id: ID of the plugin to create
            config: Configuration for the plugin
            
        Returns:
            Plugin instance, or None if creation failed
        """
        if plugin_id not in self._plugin_classes:
            logger.warning(f"Plugin class with ID '{plugin_id}' not found")
            return None
        
        try:
            plugin_class = self._plugin_classes[plugin_id]
            plugin = plugin_class(plugin_id, plugin_class.__name__, "1.0.0")
            
            # Create and set plugin context
            context = PluginContext(plugin_id, config)
            plugin.set_context(context)
            self._contexts[plugin_id] = context
            
            # Register the plugin
            self._plugins[plugin_id] = plugin
            
            return plugin
        
        except Exception as e:
            logger.error(f"Failed to create plugin instance: {e}")
            return None
    
    def get_plugin(self, plugin_id: str) -> Optional[CorePluginInterface]:
        """
        Get a plugin instance by ID.
        
        Args:
            plugin_id: ID of the plugin
            
        Returns:
            Plugin instance, or None if not found
        """
        return self._plugins.get(plugin_id)
    
    def get_plugin_context(self, plugin_id: str) -> Optional[PluginContext]:
        """
        Get a plugin context by plugin ID.
        
        Args:
            plugin_id: ID of the plugin
            
        Returns:
            Plugin context, or None if not found
        """
        return self._contexts.get(plugin_id)
    
    def initialize_plugin(self, plugin_id: str) -> bool:
        """
        Initialize a plugin.
        
        Args:
            plugin_id: ID of the plugin to initialize
            
        Returns:
            True if initialization was successful, False otherwise
        """
        plugin = self.get_plugin(plugin_id)
        if not plugin:
            logger.warning(f"Plugin '{plugin_id}' not found")
            return False
        
        try:
            # Check dependencies
            dependencies = plugin.get_dependencies()
            for dep_id in dependencies:
                dep_plugin = self.get_plugin(dep_id)
                if not dep_plugin:
                    logger.warning(f"Dependency '{dep_id}' for plugin '{plugin_id}' not found")
                    return False
                if not dep_plugin.is_initialized:
                    logger.warning(f"Dependency '{dep_id}' for plugin '{plugin_id}' not initialized")
                    return False
            
            # Initialize the plugin
            result = plugin.initialize()
            if result:
                plugin._is_initialized = True
                logger.info(f"Plugin '{plugin_id}' initialized successfully")
            else:
                logger.warning(f"Plugin '{plugin_id}' initialization returned False")
            
            return result
        
        except Exception as e:
            logger.error(f"Failed to initialize plugin '{plugin_id}': {e}")
            return False
    
    def start_plugin(self, plugin_id: str) -> bool:
        """
        Start a plugin.
        
        Args:
            plugin_id: ID of the plugin to start
            
        Returns:
            True if startup was successful, False otherwise
        """
        plugin = self.get_plugin(plugin_id)
        if not plugin:
            logger.warning(f"Plugin '{plugin_id}' not found")
            return False
        
        if not plugin.is_initialized:
            logger.warning(f"Plugin '{plugin_id}' not initialized")
            return False
        
        try:
            # Start the plugin
            result = plugin.start()
            if result:
                plugin._is_active = True
                logger.info(f"Plugin '{plugin_id}' started successfully")
            else:
                logger.warning(f"Plugin '{plugin_id}' start returned False")
            
            return result
        
        except Exception as e:
            logger.error(f"Failed to start plugin '{plugin_id}': {e}")
            return False
    
    def stop_plugin(self, plugin_id: str) -> bool:
        """
        Stop a plugin.
        
        Args:
            plugin_id: ID of the plugin to stop
            
        Returns:
            True if shutdown was successful, False otherwise
        """
        plugin = self.get_plugin(plugin_id)
        if not plugin:
            logger.warning(f"Plugin '{plugin_id}' not found")
            return False
        
        if not plugin.is_active:
            logger.warning(f"Plugin '{plugin_id}' not active")
            return False
        
        try:
            # Stop the plugin
            result = plugin.stop()
            if result:
                plugin._is_active = False
                logger.info(f"Plugin '{plugin_id}' stopped successfully")
            else:
                logger.warning(f"Plugin '{plugin_id}' stop returned False")
            
            return result
        
        except Exception as e:
            logger.error(f"Failed to stop plugin '{plugin_id}': {e}")
            return False
    
    def cleanup_plugin(self, plugin_id: str) -> bool:
        """
        Clean up a plugin.
        
        Args:
            plugin_id: ID of the plugin to clean up
            
        Returns:
            True if cleanup was successful, False otherwise
        """
        plugin = self.get_plugin(plugin_id)
        if not plugin:
            logger.warning(f"Plugin '{plugin_id}' not found")
            return False
        
        try:
            # Clean up the plugin
            plugin.cleanup()
            
            # Remove the plugin
            del self._plugins[plugin_id]
            if plugin_id in self._contexts:
                del self._contexts[plugin_id]
            
            logger.info(f"Plugin '{plugin_id}' cleaned up successfully")
            return True
        
        except Exception as e:
            logger.error(f"Failed to clean up plugin '{plugin_id}': {e}")
            return False
    
    def get_active_plugins(self) -> List[str]:
        """
        Get the list of active plugin IDs.
        
        Returns:
            List of active plugin IDs
        """
        return [plugin_id for plugin_id, plugin in self._plugins.items() if plugin.is_active]
    
    def get_initialized_plugins(self) -> List[str]:
        """
        Get the list of initialized plugin IDs.
        
        Returns:
            List of initialized plugin IDs
        """
        return [plugin_id for plugin_id, plugin in self._plugins.items() if plugin.is_initialized]
    
    def get_plugin_capabilities(self, plugin_id: str) -> List[str]:
        """
        Get the capabilities of a plugin.
        
        Args:
            plugin_id: ID of the plugin
            
        Returns:
            List of capability strings, empty if plugin not found
        """
        plugin = self.get_plugin(plugin_id)
        if plugin:
            return plugin.get_capabilities()
        return []
    
    def get_plugins_with_capability(self, capability: str) -> List[str]:
        """
        Get the list of plugin IDs that provide a specific capability.
        
        Args:
            capability: Capability to search for
            
        Returns:
            List of plugin IDs
        """
        return [
            plugin_id for plugin_id, plugin in self._plugins.items()
            if capability in plugin.get_capabilities() and plugin.is_active
        ]
    
    def configure_plugin(self, plugin_id: str, config: Dict[str, Any]) -> bool:
        """
        Configure a plugin.
        
        Args:
            plugin_id: ID of the plugin
            config: Configuration to apply
            
        Returns:
            True if configuration was successful, False otherwise
        """
        plugin = self.get_plugin(plugin_id)
        if plugin:
            return plugin.configure(config)
        return False
    
    def load_plugins(self) -> bool:
        """
        Discover, create, initialize, and start all plugins.
        
        Returns:
            True if all plugins were loaded successfully, False otherwise
        """
        if self._initialized:
            logger.warning("Plugin registry already initialized")
            return False
        
        try:
            # Discover plugins
            discovered_plugins = self.discover_plugins()
            logger.info(f"Discovered {len(discovered_plugins)} plugins")
            
            # Create plugin instances
            for plugin_id in discovered_plugins:
                self.create_plugin(plugin_id)
            
            # Initialize plugins (respecting dependencies)
            initialized_plugins = []
            remaining_plugins = list(self._plugins.keys())
            
            # Keep trying to initialize plugins until no more can be initialized
            while remaining_plugins:
                progress = False
                
                for plugin_id in list(remaining_plugins):
                    plugin = self.get_plugin(plugin_id)
                    if not plugin:
                        remaining_plugins.remove(plugin_id)
                        continue
                    
                    # Check if all dependencies are initialized
                    dependencies = plugin.get_dependencies()
                    dependencies_initialized = all(dep_id in initialized_plugins for dep_id in dependencies)
                    
                    if dependencies_initialized:
                        # Initialize the plugin
                        if self.initialize_plugin(plugin_id):
                            initialized_plugins.append(plugin_id)
                            remaining_plugins.remove(plugin_id)
                            progress = True
                
                # If no progress was made in this iteration, we have a dependency cycle
                if not progress and remaining_plugins:
                    logger.error(f"Dependency cycle detected in plugins: {remaining_plugins}")
                    break
            
            # Start initialized plugins
            for plugin_id in initialized_plugins:
                self.start_plugin(plugin_id)
            
            self._initialized = True
            return True
        
        except Exception as e:
            logger.error(f"Failed to load plugins: {e}")
            return False
    
    def unload_plugins(self) -> bool:
        """
        Stop and clean up all plugins.
        
        Returns:
            True if all plugins were unloaded successfully, False otherwise
        """
        if not self._initialized:
            logger.warning("Plugin registry not initialized")
            return False
        
        try:
            # Stop active plugins in reverse dependency order
            active_plugins = self.get_active_plugins()
            
            # Build dependency graph
            dependency_graph = {}
            for plugin_id in active_plugins:
                plugin = self.get_plugin(plugin_id)
                if plugin:
                    dependencies = plugin.get_dependencies()
                    dependency_graph[plugin_id] = dependencies
            
            # Determine stopping order (reverse topological sort)
            stopping_order = self._topological_sort(dependency_graph)
            stopping_order.reverse()
            
            # Stop plugins in the determined order
            for plugin_id in stopping_order:
                if plugin_id in active_plugins:
                    self.stop_plugin(plugin_id)
            
            # Clean up all plugins
            for plugin_id in list(self._plugins.keys()):
                self.cleanup_plugin(plugin_id)
            
            self._initialized = False
            return True
        
        except Exception as e:
            logger.error(f"Failed to unload plugins: {e}")
            return False
    
    def _topological_sort(self, dependency_graph: Dict[str, List[str]]) -> List[str]:
        """
        Perform a topological sort on the dependency graph.
        
        Args:
            dependency_graph: Dependency graph mapping plugin IDs to their dependencies
            
        Returns:
            Sorted list of plugin IDs
        """
        # Create a complete graph with all nodes
        graph = dependency_graph.copy()
        for plugin_id in dependency_graph:
            for dep_id in dependency_graph[plugin_id]:
                if dep_id not in graph:
                    graph[dep_id] = []
        
        result = []
        visited = set()
        temp_visited = set()
        
        def visit(node):
            if node in temp_visited:
                raise ValueError(f"Dependency cycle detected for plugin {node}")
            
            if node not in visited:
                temp_visited.add(node)
                
                for dependency in graph.get(node, []):
                    visit(dependency)
                
                temp_visited.remove(node)
                visited.add(node)
                result.append(node)
        
        for node in graph:
            if node not in visited:
                visit(node)
        
        return result


# Global plugin registry instance
global_plugin_registry = PluginRegistry()


def register_plugin_path(path: str) -> None:
    """
    Register a path to search for plugins in the global registry.
    
    Args:
        path: Directory path to search for plugins
    """
    global_plugin_registry.register_plugin_path(path)


def register_plugin_class(plugin_class: Type[CorePluginInterface]) -> bool:
    """
    Register a plugin class in the global registry.
    
    Args:
        plugin_class: Plugin class to register
        
    Returns:
        True if registration was successful, False otherwise
    """
    return global_plugin_registry.register_plugin_class(plugin_class)


def get_plugin(plugin_id: str) -> Optional[CorePluginInterface]:
    """
    Get a plugin instance by ID from the global registry.
    
    Args:
        plugin_id: ID of the plugin
        
    Returns:
        Plugin instance, or None if not found
    """
    return global_plugin_registry.get_plugin(plugin_id)


def get_plugins_with_capability(capability: str) -> List[str]:
    """
    Get the list of plugin IDs that provide a specific capability from the global registry.
    
    Args:
        capability: Capability to search for
        
    Returns:
        List of plugin IDs
    """
    return global_plugin_registry.get_plugins_with_capability(capability)


def load_plugins() -> bool:
    """
    Load all plugins in the global registry.
    
    Returns:
        True if all plugins were loaded successfully, False otherwise
    """
    return global_plugin_registry.load_plugins()


def unload_plugins() -> bool:
    """
    Unload all plugins in the global registry.
    
    Returns:
        True if all plugins were unloaded successfully, False otherwise
    """
    return global_plugin_registry.unload_plugins() 