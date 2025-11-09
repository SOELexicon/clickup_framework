"""
Task: tsk_3f55d115 - Update Plugins Module Comments
Document: refactor/plugins/plugin_interface.py
dohcount: 1

Related Tasks:
    - tsk_0a733101 - Code Comments Enhancement (parent)
    - tsk_bf28d342 - Update CLI Module Comments (sibling)
    - tsk_4c899138 - Update Storage Module Comments (sibling)

Used By:
    - PluginManager: Uses these interfaces to categorize and manage plugins
    - CorePlugins: Implements these interfaces for core functionality
    - CustomPlugins: Third-party plugins implement these interfaces

Purpose:
    Defines the base interfaces for different types of plugins in the ClickUp JSON Manager.
    Provides a comprehensive type system for plugin categorization and standardized API.

Requirements:
    - All plugin implementations MUST inherit from at least one interface
    - Plugin interfaces must define clear contracts with abstract methods
    - CRITICAL: Plugin type enums must be maintained for backward compatibility

Plugin Interfaces

This module defines the base interfaces for different types of plugins
in the ClickUp JSON Manager.
"""

import abc
from enum import Enum, auto
from typing import Any, Dict, List, Optional, Set, Tuple, Type, Union

from ..common.exceptions import PluginError
from .plugin_manager import Plugin


class PluginType(Enum):
    """Enum defining different types of plugins."""
    TASK_OPERATION = auto()     # Extends task operations
    ENTITY_TYPE = auto()        # Adds new entity types
    VISUALIZATION = auto()      # Provides visualization capabilities
    INTEGRATION = auto()        # Integrates with external services
    UI_EXTENSION = auto()       # Extends the UI
    QUERY_EXTENSION = auto()    # Extends search and query capabilities
    DATA_PROCESSOR = auto()     # Processes data
    NOTIFICATION = auto()       # Provides notification capabilities
    FIELD_VALIDATOR = auto()    # Validates fields
    EXPORTER = auto()           # Exports data
    IMPORTER = auto()           # Imports data
    UTILITY = auto()            # Utility plugins


class TaskOperationPlugin(Plugin):
    """
    Interface for plugins that extend task operations.
    
    Task operation plugins can add new operations for tasks,
    such as custom status transitions, validation rules, etc.
    """
    
    @property
    def plugin_type(self) -> PluginType:
        """Get the plugin type."""
        return PluginType.TASK_OPERATION
    
    @abc.abstractmethod
    def get_supported_operations(self) -> List[str]:
        """
        Get the list of task operations supported by this plugin.
        
        Returns:
            List[str]: Names of supported operations
        """
        pass


class EntityTypePlugin(Plugin):
    """
    Interface for plugins that add new entity types.
    
    Entity type plugins can define new entity types beyond the
    core entities (task, space, folder, list).
    """
    
    @property
    def plugin_type(self) -> PluginType:
        """Get the plugin type."""
        return PluginType.ENTITY_TYPE
    
    @abc.abstractmethod
    def get_entity_types(self) -> List[Tuple[str, Type]]:
        """
        Get the entity types defined by this plugin.
        
        Returns:
            List[Tuple[str, Type]]: List of (entity_type_name, entity_class) tuples
        """
        pass


class VisualizationPlugin(Plugin):
    """
    Interface for plugins that provide visualization capabilities.
    
    Visualization plugins can render data in different formats,
    such as charts, graphs, etc.
    """
    
    @property
    def plugin_type(self) -> PluginType:
        """Get the plugin type."""
        return PluginType.VISUALIZATION
    
    @abc.abstractmethod
    def get_visualization_types(self) -> List[str]:
        """
        Get the visualization types supported by this plugin.
        
        Returns:
            List[str]: Names of supported visualization types
        """
        pass
    
    @abc.abstractmethod
    def render(self, visualization_type: str, data: Any, options: Dict[str, Any]) -> str:
        """
        Render data using the specified visualization type.
        
        Args:
            visualization_type: Type of visualization to use
            data: Data to visualize
            options: Visualization options
            
        Returns:
            str: Rendered visualization (e.g., HTML, SVG, ASCII art)
        """
        pass


class IntegrationPlugin(Plugin):
    """
    Interface for plugins that integrate with external services.
    
    Integration plugins can connect to external services such as
    GitHub, Slack, etc.
    """
    
    @property
    def plugin_type(self) -> PluginType:
        """Get the plugin type."""
        return PluginType.INTEGRATION
    
    @abc.abstractmethod
    def get_integration_name(self) -> str:
        """
        Get the name of the integration.
        
        Returns:
            str: Name of the integration
        """
        pass
    
    @abc.abstractmethod
    def get_required_config(self) -> Dict[str, Dict[str, Any]]:
        """
        Get the configuration required for this integration.
        
        Returns:
            Dict[str, Dict[str, Any]]: Configuration schema
        """
        pass
    
    @abc.abstractmethod
    def validate_config(self, config: Dict[str, Any]) -> Tuple[bool, Optional[str]]:
        """
        Validate the configuration for this integration.
        
        Args:
            config: Configuration to validate
            
        Returns:
            Tuple[bool, Optional[str]]: (is_valid, error_message)
        """
        pass


class UIExtensionPlugin(Plugin):
    """
    Interface for plugins that extend the UI.
    
    UI extension plugins can add new UI components, views, etc.
    """
    
    @property
    def plugin_type(self) -> PluginType:
        """Get the plugin type."""
        return PluginType.UI_EXTENSION
    
    @abc.abstractmethod
    def get_extension_points(self) -> List[str]:
        """
        Get the UI extension points this plugin supports.
        
        Returns:
            List[str]: Names of supported extension points
        """
        pass
    
    @abc.abstractmethod
    def render_extension(self, extension_point: str, context: Dict[str, Any]) -> str:
        """
        Render the UI extension for the specified extension point.
        
        Args:
            extension_point: Name of the extension point
            context: Context data for rendering
            
        Returns:
            str: Rendered UI extension (e.g., HTML, ASCII art)
        """
        pass


class QueryExtensionPlugin(Plugin):
    """
    Interface for plugins that extend search and query capabilities.
    
    Query extension plugins can add new search operators, custom
    filters, etc.
    """
    
    @property
    def plugin_type(self) -> PluginType:
        """Get the plugin type."""
        return PluginType.QUERY_EXTENSION
    
    @abc.abstractmethod
    def get_query_operators(self) -> List[str]:
        """
        Get the query operators supported by this plugin.
        
        Returns:
            List[str]: Names of supported query operators
        """
        pass
    
    @abc.abstractmethod
    def evaluate_operator(self, operator: str, args: List[Any], context: Dict[str, Any]) -> Any:
        """
        Evaluate a query operator.
        
        Args:
            operator: Name of the operator
            args: Arguments for the operator
            context: Evaluation context
            
        Returns:
            Any: Result of the operator evaluation
        """
        pass


class DataProcessorPlugin(Plugin):
    """
    Interface for plugins that process data.
    
    Data processor plugins can transform, analyze, or enhance data.
    """
    
    @property
    def plugin_type(self) -> PluginType:
        """Get the plugin type."""
        return PluginType.DATA_PROCESSOR
    
    @abc.abstractmethod
    def get_processor_types(self) -> List[str]:
        """
        Get the data processor types supported by this plugin.
        
        Returns:
            List[str]: Names of supported processor types
        """
        pass
    
    @abc.abstractmethod
    def process(self, processor_type: str, data: Any, options: Dict[str, Any]) -> Any:
        """
        Process data using the specified processor type.
        
        Args:
            processor_type: Type of processor to use
            data: Data to process
            options: Processing options
            
        Returns:
            Any: Processed data
        """
        pass


class NotificationPlugin(Plugin):
    """
    Interface for plugins that provide notification capabilities.
    
    Notification plugins can send notifications via different
    channels, such as email, Slack, etc.
    """
    
    @property
    def plugin_type(self) -> PluginType:
        """Get the plugin type."""
        return PluginType.NOTIFICATION
    
    @abc.abstractmethod
    def get_notification_channels(self) -> List[str]:
        """
        Get the notification channels supported by this plugin.
        
        Returns:
            List[str]: Names of supported notification channels
        """
        pass
    
    @abc.abstractmethod
    def send_notification(self, channel: str, message: str, options: Dict[str, Any]) -> bool:
        """
        Send a notification using the specified channel.
        
        Args:
            channel: Notification channel to use
            message: Notification message
            options: Notification options
            
        Returns:
            bool: True if the notification was sent successfully, False otherwise
        """
        pass


class FieldValidatorPlugin(Plugin):
    """
    Interface for plugins that validate fields.
    
    Field validator plugins can validate fields based on custom rules.
    """
    
    @property
    def plugin_type(self) -> PluginType:
        """Get the plugin type."""
        return PluginType.FIELD_VALIDATOR
    
    @abc.abstractmethod
    def get_supported_fields(self) -> List[str]:
        """
        Get the fields supported by this validator.
        
        Returns:
            List[str]: Names of supported fields
        """
        pass
    
    @abc.abstractmethod
    def validate(self, field_name: str, field_value: Any, context: Dict[str, Any]) -> Tuple[bool, Optional[str]]:
        """
        Validate a field value.
        
        Args:
            field_name: Name of the field to validate
            field_value: Value of the field to validate
            context: Validation context
            
        Returns:
            Tuple[bool, Optional[str]]: (is_valid, error_message)
        """
        pass


class ExporterPlugin(Plugin):
    """
    Interface for plugins that export data.
    
    Exporter plugins can export data to different formats,
    such as CSV, JSON, etc.
    """
    
    @property
    def plugin_type(self) -> PluginType:
        """Get the plugin type."""
        return PluginType.EXPORTER
    
    @abc.abstractmethod
    def get_export_formats(self) -> List[str]:
        """
        Get the export formats supported by this plugin.
        
        Returns:
            List[str]: Names of supported export formats
        """
        pass
    
    @abc.abstractmethod
    def export(self, format: str, data: Any, options: Dict[str, Any]) -> Union[str, bytes]:
        """
        Export data to the specified format.
        
        Args:
            format: Export format to use
            data: Data to export
            options: Export options
            
        Returns:
            Union[str, bytes]: Exported data
        """
        pass


class ImporterPlugin(Plugin):
    """
    Interface for plugins that import data.
    
    Importer plugins can import data from different formats,
    such as CSV, JSON, etc.
    """
    
    @property
    def plugin_type(self) -> PluginType:
        """Get the plugin type."""
        return PluginType.IMPORTER
    
    @abc.abstractmethod
    def get_import_formats(self) -> List[str]:
        """
        Get the import formats supported by this plugin.
        
        Returns:
            List[str]: Names of supported import formats
        """
        pass
    
    @abc.abstractmethod
    def import_data(self, format: str, data: Union[str, bytes], options: Dict[str, Any]) -> Any:
        """
        Import data from the specified format.
        
        Args:
            format: Import format to use
            data: Data to import
            options: Import options
            
        Returns:
            Any: Imported data
        """
        pass


class UtilityPlugin(Plugin):
    """
    Interface for utility plugins.
    
    Utility plugins provide miscellaneous functionality that
    doesn't fit into other categories.
    """
    
    @property
    def plugin_type(self) -> PluginType:
        """Get the plugin type."""
        return PluginType.UTILITY
    
    @abc.abstractmethod
    def get_utility_functions(self) -> List[str]:
        """
        Get the utility functions provided by this plugin.
        
        Returns:
            List[str]: Names of provided utility functions
        """
        pass
    
    @abc.abstractmethod
    def call_function(self, function_name: str, args: List[Any], kwargs: Dict[str, Any]) -> Any:
        """
        Call a utility function.
        
        Args:
            function_name: Name of the function to call
            args: Positional arguments
            kwargs: Keyword arguments
            
        Returns:
            Any: Result of the function call
        """
        pass 