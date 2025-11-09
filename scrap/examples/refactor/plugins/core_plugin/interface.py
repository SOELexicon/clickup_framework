"""
Task: tsk_3f55d115 - Update Plugins Module Comments
Document: refactor/plugins/core_plugin/interface.py
dohcount: 1

Related Tasks:
    - tsk_0a733101 - Code Comments Enhancement (parent)
    - tsk_bf28d342 - Update CLI Module Comments (sibling)
    - tsk_4c899138 - Update Storage Module Comments (sibling)

Used By:
    - PluginManager: Integrates with these interfaces for core plugin operations
    - CorePluginRegistry: Registers plugins implementing these interfaces
    - HookSystem: Connects plugin events to core functionality

Purpose:
    Defines the primary interfaces and base classes for the plugin system used
    throughout the Core Module. Provides specialized plugin interfaces for 
    different functional areas (tasks, search, visualization, etc.).

Requirements:
    - All core plugins MUST implement CorePluginInterface and at least one specialized interface
    - Plugin lifecycle methods must be implemented correctly
    - Plugin context must be used for accessing shared services
    - CRITICAL: Core plugin interfaces must maintain backward compatibility
    - CRITICAL: Plugin implementations must handle configuration changes safely

Core plugin interface module.

This module defines the primary interfaces and base classes for the plugin system
used throughout the Core Module.
"""

import abc
from typing import Dict, List, Any, Optional, Set, Union, Callable, TypeVar
import logging

# Type variables for generic methods
T = TypeVar('T')


class PluginContext:
    """
    Class representing the context provided to plugins during execution.
    
    This context contains information about the execution environment, configuration,
    and provides access to shared services.
    """
    
    def __init__(self, 
                 plugin_id: str,
                 config: Dict[str, Any] = None,
                 logger: Optional[logging.Logger] = None):
        """
        Initialize a plugin context.
        
        Args:
            plugin_id: Unique identifier for the plugin
            config: Plugin-specific configuration
            logger: Logger instance for the plugin
        """
        self._plugin_id = plugin_id
        self._config = config or {}
        self._logger = logger or logging.getLogger(f"plugin.{plugin_id}")
        self._services = {}
        self._data = {}
    
    @property
    def plugin_id(self) -> str:
        """Get the plugin ID."""
        return self._plugin_id
    
    @property
    def config(self) -> Dict[str, Any]:
        """Get the plugin configuration."""
        return self._config.copy()
    
    def get_config(self, key: str, default: Any = None) -> Any:
        """
        Get a specific configuration value.
        
        Args:
            key: Configuration key
            default: Default value if key is not found
            
        Returns:
            Configuration value or default
        """
        return self._config.get(key, default)
    
    @property
    def logger(self) -> logging.Logger:
        """Get the plugin logger."""
        return self._logger
    
    def register_service(self, name: str, service: Any) -> None:
        """
        Register a service to be accessible by the plugin.
        
        Args:
            name: Service name
            service: Service instance
        """
        self._services[name] = service
    
    def get_service(self, name: str) -> Any:
        """
        Get a registered service.
        
        Args:
            name: Service name
            
        Returns:
            Service instance
            
        Raises:
            KeyError: If service is not registered
        """
        if name not in self._services:
            raise KeyError(f"Service '{name}' not registered in plugin context")
        return self._services[name]
    
    def set_data(self, key: str, value: Any) -> None:
        """
        Store data in the plugin context.
        
        Args:
            key: Data key
            value: Data value
        """
        self._data[key] = value
    
    def get_data(self, key: str, default: Any = None) -> Any:
        """
        Get data from the plugin context.
        
        Args:
            key: Data key
            default: Default value if key is not found
            
        Returns:
            Data value or default
        """
        return self._data.get(key, default)


class CorePluginInterface(abc.ABC):
    """
    Base interface for all Core Module plugins.
    
    This interface defines the lifecycle methods and core functionality
    that all plugins must implement.
    """
    
    def __init__(self, plugin_id: str, plugin_name: str, version: str):
        """
        Initialize a core plugin.
        
        Args:
            plugin_id: Unique identifier for the plugin
            plugin_name: Human-readable name of the plugin
            version: Plugin version string
        """
        self._plugin_id = plugin_id
        self._plugin_name = plugin_name
        self._version = version
        self._context = None
        self._is_initialized = False
        self._is_active = False
    
    @property
    def plugin_id(self) -> str:
        """Get the plugin ID."""
        return self._plugin_id
    
    @property
    def plugin_name(self) -> str:
        """Get the plugin name."""
        return self._plugin_name
    
    @property
    def version(self) -> str:
        """Get the plugin version."""
        return self._version
    
    @property
    def context(self) -> Optional[PluginContext]:
        """Get the plugin context."""
        return self._context
    
    @property
    def is_initialized(self) -> bool:
        """Check if the plugin is initialized."""
        return self._is_initialized
    
    @property
    def is_active(self) -> bool:
        """Check if the plugin is active."""
        return self._is_active
    
    def set_context(self, context: PluginContext) -> None:
        """
        Set the plugin context.
        
        Args:
            context: Context for the plugin
        """
        self._context = context
    
    @abc.abstractmethod
    def initialize(self) -> bool:
        """
        Initialize the plugin.
        
        This method should perform any setup needed before the plugin
        can be used, such as validating configuration, setting up
        resources, etc.
        
        Returns:
            True if initialization is successful, False otherwise
        """
        pass
    
    @abc.abstractmethod
    def start(self) -> bool:
        """
        Start the plugin.
        
        This method is called when the plugin should begin its active operation.
        It should register any hooks, set up event listeners, etc.
        
        Returns:
            True if startup is successful, False otherwise
        """
        pass
    
    @abc.abstractmethod
    def stop(self) -> bool:
        """
        Stop the plugin.
        
        This method is called when the plugin should cease its active operation.
        It should unregister hooks, clean up resources, etc.
        
        Returns:
            True if shutdown is successful, False otherwise
        """
        pass
    
    def cleanup(self) -> None:
        """
        Clean up resources used by the plugin.
        
        This method is called during system shutdown to allow the plugin
        to release any resources it might be holding.
        """
        # Default implementation does nothing
        pass
    
    def get_dependencies(self) -> List[str]:
        """
        Get the list of plugin IDs this plugin depends on.
        
        Returns:
            List of plugin IDs
        """
        # Default implementation has no dependencies
        return []
    
    def configure(self, config: Dict[str, Any]) -> bool:
        """
        Configure the plugin with the provided settings.
        
        Args:
            config: Configuration dictionary
            
        Returns:
            True if configuration was successful, False otherwise
        """
        if self._context:
            for key, value in config.items():
                self._context._config[key] = value
            return True
        return False
    
    def get_capabilities(self) -> List[str]:
        """
        Get the list of capabilities this plugin provides.
        
        Capabilities are used to categorize plugins and determine 
        what features they provide.
        
        Returns:
            List of capability strings
        """
        # Default implementation has no capabilities
        return []


class TaskPluginInterface(CorePluginInterface):
    """
    Interface for plugins that interact with task entities.
    
    This interface adds task-specific functionality to the core plugin interface.
    """
    
    @abc.abstractmethod
    def validate_task(self, task_data: Dict[str, Any]) -> List[str]:
        """
        Validate task data before creation or update.
        
        Args:
            task_data: Task data to validate
            
        Returns:
            List of validation error messages, empty if valid
        """
        pass
    
    @abc.abstractmethod
    def process_task_creation(self, task_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Process task data during creation.
        
        This method allows plugins to modify task data before a task is created.
        
        Args:
            task_data: Task data to process
            
        Returns:
            Processed task data
        """
        pass
    
    @abc.abstractmethod
    def process_task_update(self, 
                           task_id: str, 
                           original_data: Dict[str, Any], 
                           updated_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Process task data during update.
        
        This method allows plugins to modify task data before a task is updated.
        
        Args:
            task_id: ID of the task being updated
            original_data: Original task data
            updated_data: Updated task data
            
        Returns:
            Processed updated task data
        """
        pass
    
    @abc.abstractmethod
    def on_task_status_change(self, 
                             task_id: str, 
                             previous_status: str, 
                             new_status: str,
                             comment: Optional[str]) -> None:
        """
        Handle task status change events.
        
        Args:
            task_id: ID of the task being updated
            previous_status: Previous task status
            new_status: New task status
            comment: Optional comment for the status change
        """
        pass


class SearchPluginInterface(CorePluginInterface):
    """
    Interface for plugins that extend search functionality.
    
    This interface adds search-specific functionality to the core plugin interface.
    """
    
    @abc.abstractmethod
    def process_search_query(self, query: str) -> str:
        """
        Process and potentially modify a search query.
        
        Args:
            query: Original search query
            
        Returns:
            Processed search query
        """
        pass
    
    @abc.abstractmethod
    def filter_search_results(self, results: List[Any], query: str) -> List[Any]:
        """
        Filter search results based on custom criteria.
        
        Args:
            results: Original search results
            query: Search query that produced the results
            
        Returns:
            Filtered search results
        """
        pass
    
    @abc.abstractmethod
    def sort_search_results(self, results: List[Any], query: str) -> List[Any]:
        """
        Sort search results based on custom criteria.
        
        Args:
            results: Original search results
            query: Search query that produced the results
            
        Returns:
            Sorted search results
        """
        pass


class VisualizationPluginInterface(CorePluginInterface):
    """
    Interface for plugins that provide visualization capabilities.
    
    This interface adds visualization-specific functionality to the core plugin interface.
    """
    
    @abc.abstractmethod
    def get_visualization_types(self) -> List[str]:
        """
        Get the list of visualization types this plugin provides.
        
        Returns:
            List of visualization type strings
        """
        pass
    
    @abc.abstractmethod
    def generate_visualization(self, 
                              vis_type: str, 
                              data: Any, 
                              options: Dict[str, Any] = None) -> str:
        """
        Generate a visualization of the specified type.
        
        Args:
            vis_type: Type of visualization to generate
            data: Data to visualize
            options: Options for the visualization
            
        Returns:
            Generated visualization (typically HTML or text)
        """
        pass


class ImportExportPluginInterface(CorePluginInterface):
    """
    Interface for plugins that provide import/export capabilities.
    
    This interface adds import/export-specific functionality to the core plugin interface.
    """
    
    @abc.abstractmethod
    def get_supported_formats(self) -> Dict[str, Dict[str, bool]]:
        """
        Get the list of formats supported by this plugin.
        
        Returns:
            Dictionary mapping format names to capabilities dict 
            (e.g., {"csv": {"import": True, "export": True}})
        """
        pass
    
    @abc.abstractmethod
    def import_data(self, format_name: str, data: str) -> Dict[str, Any]:
        """
        Import data from the specified format.
        
        Args:
            format_name: Format to import from
            data: Data to import
            
        Returns:
            Imported data as a dictionary
        """
        pass
    
    @abc.abstractmethod
    def export_data(self, format_name: str, data: Dict[str, Any]) -> str:
        """
        Export data to the specified format.
        
        Args:
            format_name: Format to export to
            data: Data to export
            
        Returns:
            Exported data as a string
        """
        pass


class NotificationPluginInterface(CorePluginInterface):
    """
    Interface for plugins that provide notification capabilities.
    
    This interface adds notification-specific functionality to the core plugin interface.
    """
    
    @abc.abstractmethod
    def get_notification_channels(self) -> List[str]:
        """
        Get the list of notification channels this plugin provides.
        
        Returns:
            List of channel names
        """
        pass
    
    @abc.abstractmethod
    def send_notification(self, 
                         channel: str, 
                         subject: str, 
                         message: str, 
                         recipients: List[str] = None,
                         options: Dict[str, Any] = None) -> bool:
        """
        Send a notification through the specified channel.
        
        Args:
            channel: Channel to send the notification through
            subject: Notification subject
            message: Notification message
            recipients: List of recipient identifiers
            options: Additional options for the notification
            
        Returns:
            True if the notification was sent successfully, False otherwise
        """
        pass
    
    @abc.abstractmethod
    def on_task_event(self, event_type: str, task_data: Dict[str, Any]) -> None:
        """
        Handle task-related events for notifications.
        
        Args:
            event_type: Type of event (e.g., "created", "updated", "status_changed")
            task_data: Task data for the event
        """
        pass 