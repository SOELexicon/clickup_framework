"""
Task: tsk_3f55d115 - Update Plugins Module Comments
Document: refactor/plugins/base_plugin.py
dohcount: 1

Related Tasks:
    - tsk_0a733101 - Code Comments Enhancement (parent)
    - tsk_bf28d342 - Update CLI Module Comments (sibling)
    - tsk_4c899138 - Update Storage Module Comments (sibling)

Used By:
    - PluginManager: Uses BasePlugin as the foundation for plugin discovery and loading
    - CustomPlugins: All plugins must inherit from BasePlugin
    - CorePlugins: Core functionality plugins extend this base class

Purpose:
    Defines the core plugin interfaces and base classes for the ClickUp JSON Manager
    plugin system. Provides the foundation for plugin metadata and lifecycle management.

Requirements:
    - All plugins MUST inherit from BasePlugin
    - Plugins must implement the lifecycle methods (initialize, activate, deactivate)
    - CRITICAL: Plugin metadata must be properly defined for discovery
    - CRITICAL: Plugin initialization must not depend on service availability

Base Plugin Classes and Interfaces

This module defines the core plugin interfaces and base classes for the
ClickUp JSON Manager plugin system. All plugins must implement these interfaces.
"""

from abc import ABC, abstractmethod
from typing import Any, Dict, List, Optional, Union


class PluginMetadata:
    """Contains metadata about a plugin."""

    def __init__(
        self,
        id: str,
        name: str,
        version: str,
        author: str,
        description: str = "",
        website: str = "",
        dependencies: Optional[List[str]] = None
    ):
        """
        Initialize plugin metadata.

        Args:
            id: Unique identifier for the plugin
            name: Human-readable name
            version: Semantic version string
            author: Plugin author or organization
            description: Optional plugin description
            website: Optional URL for plugin documentation/source
            dependencies: Optional list of plugin IDs this plugin depends on
        """
        self.id = id
        self.name = name
        self.version = version
        self.author = author
        self.description = description
        self.website = website
        self.dependencies = dependencies or []

    def __str__(self) -> str:
        """Return string representation of the plugin metadata."""
        return f"{self.name} v{self.version} by {self.author}"


class BasePlugin(ABC):
    """
    Base class for all plugins in the ClickUp JSON Manager.
    
    All plugins must implement this interface to be discovered and loaded
    by the plugin system.
    """
    
    @property
    @abstractmethod
    def metadata(self) -> PluginMetadata:
        """
        Get plugin metadata.
        
        Returns:
            PluginMetadata: Information about the plugin
        """
        pass
    
    @abstractmethod
    def initialize(self, config: Dict[str, Any]) -> bool:
        """
        Initialize the plugin with the provided configuration.
        
        This is called during plugin discovery, before the plugin is activated.
        Perform validation and setup that doesn't require other plugins.
        
        Args:
            config: Plugin-specific configuration values
            
        Returns:
            bool: True if initialization succeeds, False otherwise
        """
        pass
    
    @abstractmethod
    def activate(self) -> bool:
        """
        Activate the plugin.
        
        This is called after all plugins have been initialized and dependencies
        have been resolved. Perform resource allocation and hook registration here.
        
        Returns:
            bool: True if activation succeeds, False otherwise
        """
        pass
    
    @abstractmethod
    def deactivate(self) -> bool:
        """
        Deactivate the plugin.
        
        This is called when the plugin is being unloaded. Perform cleanup
        and resource release here.
        
        Returns:
            bool: True if deactivation succeeds, False otherwise
        """
        pass


# To be expanded with hook registration decorators and specific plugin type interfaces 