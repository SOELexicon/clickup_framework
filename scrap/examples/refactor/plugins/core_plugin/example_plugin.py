"""
Example plugin implementation module.

This module provides an example plugin that demonstrates how to implement
various plugin interfaces and hook into the core system.
"""

from typing import Dict, List, Any, Optional

from refactor.plugins.core_plugin.interface import (
    CorePluginInterface,
    TaskPluginInterface,
    SearchPluginInterface
)
from refactor.plugins.core_plugin.hook_system import hook_impl


class ExampleCorePlugin(CorePluginInterface):
    """
    Example core plugin implementation.
    
    This plugin demonstrates the basic implementation of a Core Plugin Interface.
    """
    
    def __init__(self, plugin_id: str = "example_core_plugin",
                 plugin_name: str = "Example Core Plugin",
                 version: str = "1.0.0"):
        """
        Initialize the example core plugin.
        
        Args:
            plugin_id: Unique identifier for the plugin
            plugin_name: Human-readable name of the plugin
            version: Plugin version string
        """
        super().__init__(plugin_id, plugin_name, version)
    
    def initialize(self) -> bool:
        """
        Initialize the plugin.
        
        Returns:
            True indicating successful initialization
        """
        if self.context:
            self.context.logger.info(f"Initializing {self.plugin_name} v{self.version}")
        return True
    
    def start(self) -> bool:
        """
        Start the plugin.
        
        Returns:
            True indicating successful start
        """
        if self.context:
            self.context.logger.info(f"Starting {self.plugin_name}")
        return True
    
    def stop(self) -> bool:
        """
        Stop the plugin.
        
        Returns:
            True indicating successful stop
        """
        if self.context:
            self.context.logger.info(f"Stopping {self.plugin_name}")
        return True
    
    def get_capabilities(self) -> List[str]:
        """
        Get the list of capabilities this plugin provides.
        
        Returns:
            List of capability strings
        """
        return ["core.example"]
    
    @hook_impl("core.initialize")
    def on_core_initialize(self) -> None:
        """
        Handle core initialization hook.
        
        This method is called during system initialization.
        """
        if self.context:
            self.context.logger.info("Core system is initializing")
    
    @hook_impl("core.shutdown")
    def on_core_shutdown(self) -> None:
        """
        Handle core shutdown hook.
        
        This method is called during system shutdown.
        """
        if self.context:
            self.context.logger.info("Core system is shutting down")


class ExampleTaskPlugin(TaskPluginInterface):
    """
    Example task plugin implementation.
    
    This plugin demonstrates how to implement a Task Plugin Interface
    to interact with task entities.
    """
    
    def __init__(self, plugin_id: str = "example_task_plugin",
                 plugin_name: str = "Example Task Plugin",
                 version: str = "1.0.0"):
        """
        Initialize the example task plugin.
        
        Args:
            plugin_id: Unique identifier for the plugin
            plugin_name: Human-readable name of the plugin
            version: Plugin version string
        """
        super().__init__(plugin_id, plugin_name, version)
    
    def initialize(self) -> bool:
        """
        Initialize the plugin.
        
        Returns:
            True indicating successful initialization
        """
        if self.context:
            self.context.logger.info(f"Initializing {self.plugin_name} v{self.version}")
        return True
    
    def start(self) -> bool:
        """
        Start the plugin.
        
        Returns:
            True indicating successful start
        """
        if self.context:
            self.context.logger.info(f"Starting {self.plugin_name}")
        return True
    
    def stop(self) -> bool:
        """
        Stop the plugin.
        
        Returns:
            True indicating successful stop
        """
        if self.context:
            self.context.logger.info(f"Stopping {self.plugin_name}")
        return True
    
    def get_capabilities(self) -> List[str]:
        """
        Get the list of capabilities this plugin provides.
        
        Returns:
            List of capability strings
        """
        return ["task.validation", "task.processing"]
    
    def validate_task(self, task_data: Dict[str, Any]) -> List[str]:
        """
        Validate task data before creation or update.
        
        Args:
            task_data: Task data to validate
            
        Returns:
            List of validation error messages, empty if valid
        """
        errors = []
        
        # Example validation: Ensure task has a name
        if not task_data.get("name"):
            errors.append("Task must have a name")
        
        # Example validation: Ensure task name is not too long
        name = task_data.get("name", "")
        if len(name) > 100:
            errors.append("Task name cannot exceed 100 characters")
        
        return errors
    
    def process_task_creation(self, task_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Process task data during creation.
        
        Args:
            task_data: Task data to process
            
        Returns:
            Processed task data
        """
        # Example processing: Add a created_by field if not present
        if "created_by" not in task_data:
            task_data["created_by"] = "example_plugin"
        
        # Example processing: Add a custom field
        if "custom_fields" not in task_data:
            task_data["custom_fields"] = {}
        
        task_data["custom_fields"]["processed_by_example"] = True
        
        return task_data
    
    def process_task_update(self, 
                           task_id: str, 
                           original_data: Dict[str, Any], 
                           updated_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Process task data during update.
        
        Args:
            task_id: ID of the task being updated
            original_data: Original task data
            updated_data: Updated task data
            
        Returns:
            Processed updated task data
        """
        # Example processing: Add a last_modified_by field
        updated_data["last_modified_by"] = "example_plugin"
        
        # Example processing: Track changes
        if "change_history" not in updated_data:
            updated_data["change_history"] = []
        
        # Record what fields changed
        changed_fields = []
        for key, value in updated_data.items():
            if key in original_data and original_data[key] != value:
                changed_fields.append(key)
        
        if changed_fields:
            updated_data["change_history"].append({
                "plugin": self.plugin_id,
                "changed_fields": changed_fields,
            })
        
        return updated_data
    
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
        if self.context:
            self.context.logger.info(
                f"Task {task_id} status changed from '{previous_status}' to '{new_status}'"
            )
            if comment:
                self.context.logger.info(f"Comment: {comment}")
    
    @hook_impl("task.validate")
    def on_task_validate(self, task_data: Dict[str, Any]) -> List[str]:
        """
        Handle task validation hook.
        
        Args:
            task_data: Task data to validate
            
        Returns:
            List of validation error messages
        """
        return self.validate_task(task_data)
    
    @hook_impl("task.pre_create")
    def on_task_pre_create(self, task_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Handle task pre-creation hook.
        
        Args:
            task_data: Task data to process
            
        Returns:
            Processed task data
        """
        return self.process_task_creation(task_data)
    
    @hook_impl("task.status_change")
    def on_task_status_change_hook(self, 
                                  task_id: str, 
                                  previous_status: str, 
                                  new_status: str,
                                  comment: Optional[str]) -> None:
        """
        Handle task status change hook.
        
        Args:
            task_id: ID of the task being updated
            previous_status: Previous task status
            new_status: New task status
            comment: Optional comment for the status change
        """
        self.on_task_status_change(task_id, previous_status, new_status, comment)


class ExampleSearchPlugin(SearchPluginInterface):
    """
    Example search plugin implementation.
    
    This plugin demonstrates how to implement a Search Plugin Interface
    to extend search functionality.
    """
    
    def __init__(self, plugin_id: str = "example_search_plugin",
                 plugin_name: str = "Example Search Plugin",
                 version: str = "1.0.0"):
        """
        Initialize the example search plugin.
        
        Args:
            plugin_id: Unique identifier for the plugin
            plugin_name: Human-readable name of the plugin
            version: Plugin version string
        """
        super().__init__(plugin_id, plugin_name, version)
    
    def initialize(self) -> bool:
        """
        Initialize the plugin.
        
        Returns:
            True indicating successful initialization
        """
        if self.context:
            self.context.logger.info(f"Initializing {self.plugin_name} v{self.version}")
        return True
    
    def start(self) -> bool:
        """
        Start the plugin.
        
        Returns:
            True indicating successful start
        """
        if self.context:
            self.context.logger.info(f"Starting {self.plugin_name}")
        return True
    
    def stop(self) -> bool:
        """
        Stop the plugin.
        
        Returns:
            True indicating successful stop
        """
        if self.context:
            self.context.logger.info(f"Stopping {self.plugin_name}")
        return True
    
    def get_capabilities(self) -> List[str]:
        """
        Get the list of capabilities this plugin provides.
        
        Returns:
            List of capability strings
        """
        return ["search.query_processing", "search.result_filtering"]
    
    def process_search_query(self, query: str) -> str:
        """
        Process and potentially modify a search query.
        
        Args:
            query: Original search query
            
        Returns:
            Processed search query
        """
        # Example processing: Add default sorting if not specified
        if "sort:" not in query.lower():
            query += " sort:priority"
        
        # Example processing: Add default status filter if not specified
        if "status:" not in query.lower():
            query += " status:active"
        
        return query
    
    def filter_search_results(self, results: List[Any], query: str) -> List[Any]:
        """
        Filter search results based on custom criteria.
        
        Args:
            results: Original search results
            query: Search query that produced the results
            
        Returns:
            Filtered search results
        """
        # Example filtering: Remove items marked as hidden
        filtered_results = [
            result for result in results
            if not result.get("hidden", False)
        ]
        
        return filtered_results
    
    def sort_search_results(self, results: List[Any], query: str) -> List[Any]:
        """
        Sort search results based on custom criteria.
        
        Args:
            results: Original search results
            query: Search query that produced the results
            
        Returns:
            Sorted search results
        """
        # Example sorting: Sort by custom relevance score if available
        if any("relevance_score" in result for result in results):
            sorted_results = sorted(
                results,
                key=lambda x: x.get("relevance_score", 0),
                reverse=True
            )
            return sorted_results
        
        return results
    
    @hook_impl("search.pre_query")
    def on_search_pre_query(self, query: str) -> str:
        """
        Handle search pre-query hook.
        
        Args:
            query: Original search query
            
        Returns:
            Processed search query
        """
        return self.process_search_query(query)
    
    @hook_impl("search.post_query")
    def on_search_post_query(self, results: List[Any], query: str) -> List[Any]:
        """
        Handle search post-query hook.
        
        Args:
            results: Original search results
            query: Search query that produced the results
            
        Returns:
            Filtered and sorted search results
        """
        filtered_results = self.filter_search_results(results, query)
        sorted_results = self.sort_search_results(filtered_results, query)
        return sorted_results 