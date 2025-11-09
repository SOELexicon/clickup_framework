"""
Plugin service module.

This module provides a service for integrating the plugin system into the
core module and managing plugin interactions.
"""

import logging
import os
from typing import Dict, List, Any, Optional, Set, Union, Callable, Type

from refactor.core.entities.base_entity import BaseEntity
from refactor.core.services.base_service import BaseService
from refactor.plugins.core_plugin import (
    CorePluginInterface,
    PluginContext,
    global_plugin_registry,
    global_hook_registry,
    register_plugin_path,
    hook_caller,
    load_plugins,
    unload_plugins,
    get_plugin,
    get_plugins_with_capability
)


logger = logging.getLogger(__name__)


class PluginService(BaseService):
    """
    Service for managing plugin integration with the core module.
    
    This service initializes the plugin system, loads plugins, and provides
    methods for interacting with plugins from the core module.
    """
    
    def __init__(self, plugin_dir: Optional[str] = None):
        """
        Initialize the plugin service.
        
        Args:
            plugin_dir: Optional directory to search for plugins,
                        defaults to 'plugins' in the current directory
        """
        super().__init__()
        self._plugin_dir = plugin_dir or os.path.join(os.getcwd(), 'plugins')
        self._initialized = False
    
    def initialize(self) -> bool:
        """
        Initialize the plugin system.
        
        Returns:
            True if initialization was successful, False otherwise
        """
        if self._initialized:
            logger.warning("Plugin service already initialized")
            return False
        
        try:
            # Register default plugin directories
            register_plugin_path(self._plugin_dir)
            
            # Register any additional plugin directories from configuration
            # ...
            
            # Initialize core hooks
            self._register_core_hooks()
            
            # Call initialization hook
            hook_caller("core.initialize").call()
            
            # Load plugins
            load_plugins()
            
            self._initialized = True
            logger.info("Plugin service initialized successfully")
            return True
        
        except Exception as e:
            logger.error(f"Failed to initialize plugin service: {e}")
            return False
    
    def shutdown(self) -> bool:
        """
        Shut down the plugin system.
        
        Returns:
            True if shutdown was successful, False otherwise
        """
        if not self._initialized:
            logger.warning("Plugin service not initialized")
            return False
        
        try:
            # Call shutdown hook
            hook_caller("core.shutdown").call()
            
            # Unload plugins
            unload_plugins()
            
            self._initialized = False
            logger.info("Plugin service shut down successfully")
            return True
        
        except Exception as e:
            logger.error(f"Failed to shut down plugin service: {e}")
            return False
    
    def _register_core_hooks(self) -> None:
        """Register core hooks used by the plugin system."""
        # Task hooks
        hook_caller("task.validate").call = self._call_task_validate
        hook_caller("task.pre_create").call = self._call_task_pre_create
        hook_caller("task.post_create").call = self._call_task_post_create
        hook_caller("task.pre_update").call = self._call_task_pre_update
        hook_caller("task.post_update").call = self._call_task_post_update
        hook_caller("task.status_change").call = self._call_task_status_change
        
        # Search hooks
        hook_caller("search.pre_query").call = self._call_search_pre_query
        hook_caller("search.post_query").call = self._call_search_post_query
        
        # UI hooks
        hook_caller("ui.dashboard.render").call = self._call_ui_dashboard_render
        hook_caller("ui.task_view.render").call = self._call_ui_task_view_render
    
    def _call_task_validate(self, task_data: Dict[str, Any]) -> List[str]:
        """
        Call the task.validate hook.
        
        Args:
            task_data: Task data to validate
            
        Returns:
            List of validation error messages
        """
        results = global_hook_registry.execute_hook("task.validate", task_data)
        # Flatten and deduplicate error messages
        errors = []
        for result in results:
            if isinstance(result, list):
                for error in result:
                    if error and error not in errors:
                        errors.append(error)
        return errors
    
    def _call_task_pre_create(self, task_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Call the task.pre_create hook.
        
        Args:
            task_data: Task data to process
            
        Returns:
            Processed task data
        """
        processed_data = task_data.copy()
        results = global_hook_registry.execute_hook("task.pre_create", processed_data)
        
        # Merge changes from each hook implementation
        for result in results:
            if isinstance(result, dict):
                # Update with non-None values
                for key, value in result.items():
                    if value is not None:
                        processed_data[key] = value
        
        return processed_data
    
    def _call_task_post_create(self, task_id: str, task_data: Dict[str, Any]) -> None:
        """
        Call the task.post_create hook.
        
        Args:
            task_id: ID of the created task
            task_data: Task data of the created task
        """
        global_hook_registry.execute_hook("task.post_create", task_id, task_data)
    
    def _call_task_pre_update(self, task_id: str, original_data: Dict[str, Any], 
                             updated_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Call the task.pre_update hook.
        
        Args:
            task_id: ID of the task being updated
            original_data: Original task data
            updated_data: Updated task data
            
        Returns:
            Processed updated task data
        """
        processed_data = updated_data.copy()
        results = global_hook_registry.execute_hook(
            "task.pre_update", task_id, original_data, processed_data
        )
        
        # Merge changes from each hook implementation
        for result in results:
            if isinstance(result, dict):
                # Update with non-None values
                for key, value in result.items():
                    if value is not None:
                        processed_data[key] = value
        
        return processed_data
    
    def _call_task_post_update(self, task_id: str, original_data: Dict[str, Any], 
                              updated_data: Dict[str, Any]) -> None:
        """
        Call the task.post_update hook.
        
        Args:
            task_id: ID of the updated task
            original_data: Original task data
            updated_data: Updated task data
        """
        global_hook_registry.execute_hook(
            "task.post_update", task_id, original_data, updated_data
        )
    
    def _call_task_status_change(self, task_id: str, previous_status: str, 
                                new_status: str, comment: Optional[str] = None) -> None:
        """
        Call the task.status_change hook.
        
        Args:
            task_id: ID of the task being updated
            previous_status: Previous task status
            new_status: New task status
            comment: Optional comment for the status change
        """
        global_hook_registry.execute_hook(
            "task.status_change", task_id, previous_status, new_status, comment
        )
    
    def _call_search_pre_query(self, query: str) -> str:
        """
        Call the search.pre_query hook.
        
        Args:
            query: Original search query
            
        Returns:
            Processed search query
        """
        results = global_hook_registry.execute_hook("search.pre_query", query)
        
        # Process query sequentially through all hooks
        processed_query = query
        for result in results:
            if isinstance(result, str):
                processed_query = result
        
        return processed_query
    
    def _call_search_post_query(self, results: List[Any], query: str) -> List[Any]:
        """
        Call the search.post_query hook.
        
        Args:
            results: Original search results
            query: Search query that produced the results
            
        Returns:
            Processed search results
        """
        processed_results = results
        hook_results = global_hook_registry.execute_hook("search.post_query", processed_results, query)
        
        # Process results sequentially through all hooks
        for hook_result in hook_results:
            if isinstance(hook_result, list):
                processed_results = hook_result
        
        return processed_results
    
    def _call_ui_dashboard_render(self, dashboard_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Call the ui.dashboard.render hook.
        
        Args:
            dashboard_data: Dashboard data to render
            
        Returns:
            Processed dashboard data
        """
        processed_data = dashboard_data.copy()
        results = global_hook_registry.execute_hook("ui.dashboard.render", processed_data)
        
        # Merge changes from each hook implementation
        for result in results:
            if isinstance(result, dict):
                # Update with non-None values
                for key, value in result.items():
                    if value is not None:
                        processed_data[key] = value
        
        return processed_data
    
    def _call_ui_task_view_render(self, task_view_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Call the ui.task_view.render hook.
        
        Args:
            task_view_data: Task view data to render
            
        Returns:
            Processed task view data
        """
        processed_data = task_view_data.copy()
        results = global_hook_registry.execute_hook("ui.task_view.render", processed_data)
        
        # Merge changes from each hook implementation
        for result in results:
            if isinstance(result, dict):
                # Update with non-None values
                for key, value in result.items():
                    if value is not None:
                        processed_data[key] = value
        
        return processed_data
    
    def is_initialized(self) -> bool:
        """
        Check if the plugin service is initialized.
        
        Returns:
            True if initialized, False otherwise
        """
        return self._initialized
    
    def get_active_plugins(self) -> List[str]:
        """
        Get the list of active plugin IDs.
        
        Returns:
            List of active plugin IDs
        """
        return global_plugin_registry.get_active_plugins()
    
    def get_plugins_with_capability(self, capability: str) -> List[str]:
        """
        Get the list of plugin IDs that provide a specific capability.
        
        Args:
            capability: Capability to search for
            
        Returns:
            List of plugin IDs
        """
        return get_plugins_with_capability(capability)
    
    def validate_task(self, task_data: Dict[str, Any]) -> List[str]:
        """
        Validate a task using task plugins.
        
        Args:
            task_data: Task data to validate
            
        Returns:
            List of validation error messages, empty if valid
        """
        return self._call_task_validate(task_data)
    
    def process_task_creation(self, task_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Process task data before creation using task plugins.
        
        Args:
            task_data: Task data to process
            
        Returns:
            Processed task data
        """
        return self._call_task_pre_create(task_data)
    
    def notify_task_created(self, task_id: str, task_data: Dict[str, Any]) -> None:
        """
        Notify plugins that a task was created.
        
        Args:
            task_id: ID of the created task
            task_data: Task data of the created task
        """
        self._call_task_post_create(task_id, task_data)
    
    def process_task_update(self, task_id: str, original_data: Dict[str, Any], 
                           updated_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Process task data before update using task plugins.
        
        Args:
            task_id: ID of the task being updated
            original_data: Original task data
            updated_data: Updated task data
            
        Returns:
            Processed updated task data
        """
        return self._call_task_pre_update(task_id, original_data, updated_data)
    
    def notify_task_updated(self, task_id: str, original_data: Dict[str, Any], 
                           updated_data: Dict[str, Any]) -> None:
        """
        Notify plugins that a task was updated.
        
        Args:
            task_id: ID of the updated task
            original_data: Original task data
            updated_data: Updated task data
        """
        self._call_task_post_update(task_id, original_data, updated_data)
    
    def notify_task_status_changed(self, task_id: str, previous_status: str, 
                                  new_status: str, comment: Optional[str] = None) -> None:
        """
        Notify plugins that a task's status was changed.
        
        Args:
            task_id: ID of the task being updated
            previous_status: Previous task status
            new_status: New task status
            comment: Optional comment for the status change
        """
        self._call_task_status_change(task_id, previous_status, new_status, comment)
    
    def process_search_query(self, query: str) -> str:
        """
        Process a search query using search plugins.
        
        Args:
            query: Original search query
            
        Returns:
            Processed search query
        """
        return self._call_search_pre_query(query)
    
    def process_search_results(self, results: List[Any], query: str) -> List[Any]:
        """
        Process search results using search plugins.
        
        Args:
            results: Original search results
            query: Search query that produced the results
            
        Returns:
            Processed search results
        """
        return self._call_search_post_query(results, query)
    
    def process_dashboard_rendering(self, dashboard_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Process dashboard data before rendering using UI plugins.
        
        Args:
            dashboard_data: Dashboard data to render
            
        Returns:
            Processed dashboard data
        """
        return self._call_ui_dashboard_render(dashboard_data)
    
    def process_task_view_rendering(self, task_view_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Process task view data before rendering using UI plugins.
        
        Args:
            task_view_data: Task view data to render
            
        Returns:
            Processed task view data
        """
        return self._call_ui_task_view_render(task_view_data)
    
    def get_plugin(self, plugin_id: str) -> Optional[CorePluginInterface]:
        """
        Get a plugin instance by ID.
        
        Args:
            plugin_id: ID of the plugin
            
        Returns:
            Plugin instance, or None if not found
        """
        return get_plugin(plugin_id)


# Global plugin service instance
plugin_service = PluginService() 