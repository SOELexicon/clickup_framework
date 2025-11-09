"""
Task JSON Repository

This module implements a JSON repository specifically for task entities.
It extends the JsonRepository with task-specific operations.
"""
from pathlib import Path
from typing import List, Dict, Any, Optional, Type, Union

from refactor.core.entities.task_entity import TaskEntity, TaskStatus, TaskPriority
from refactor.core.repositories.json_repository import JsonRepository
from refactor.core.repositories.repository_interface import ITaskRepository
from refactor.core.exceptions import EntityNotFoundError


class TaskJsonRepository(JsonRepository[TaskEntity], ITaskRepository):
    """
    JSON repository implementation for task entities.
    
    This repository extends the generic JsonRepository with task-specific
    operations and implements the ITaskRepository interface.
    """
    
    def __init__(self, json_path: Path, **kwargs):
        """
        Initialize a new task JSON repository.
        
        Args:
            json_path: Path to the JSON file for task persistence
            **kwargs: Additional arguments to pass to JsonRepository constructor
        """
        super().__init__(TaskEntity, json_path, **kwargs)
    
    def get_by_status(self, status: Union[str, TaskStatus]) -> List[TaskEntity]:
        """
        Get tasks with a specific status.
        
        Args:
            status: Status to filter by (string or enum)
            
        Returns:
            List of tasks with the given status
        """
        # Convert string status to enum if needed
        if isinstance(status, str):
            try:
                status_enum = TaskStatus.from_string(status)
            except ValueError:
                # If conversion fails, return empty list
                return []
        else:
            status_enum = status
        
        # Use find_by_property for actual filtering
        return self.find_by_property("status", status_enum)
    
    def get_by_priority(self, priority: Union[int, TaskPriority]) -> List[TaskEntity]:
        """
        Get tasks with a specific priority.
        
        Args:
            priority: Priority to filter by (integer or enum)
            
        Returns:
            List of tasks with the given priority
        """
        # Convert integer priority to enum if needed
        if isinstance(priority, int):
            try:
                priority_enum = TaskPriority.from_int(priority)
            except ValueError:
                # If conversion fails, return empty list
                return []
        else:
            priority_enum = priority
        
        # Use find_by_property for actual filtering
        return self.find_by_property("priority", priority_enum)
    
    def get_by_tag(self, tag: str) -> List[TaskEntity]:
        """
        Get tasks with a specific tag.
        
        Args:
            tag: Tag to filter by
            
        Returns:
            List of tasks with the given tag
        """
        # Custom filtering for tags (find_by_property doesn't handle lists well)
        return [task for task in self.get_all() if tag in task.tags]
    
    def get_subtasks(self, parent_id: str) -> List[TaskEntity]:
        """
        Get all subtasks of a given task.
        
        Args:
            parent_id: ID of the parent task
            
        Returns:
            List of subtasks
            
        Raises:
            EntityNotFoundError: If the parent task doesn't exist
        """
        # Verify parent task exists
        if not self.exists(parent_id):
            raise EntityNotFoundError(parent_id, "Task")
        
        # Find all tasks with this parent ID
        return self.find_by_property("parent_id", parent_id)
    
    def get_related_tasks(self, task_id: str, relationship_type: str) -> List[TaskEntity]:
        """
        Get tasks related to a given task by a specific relationship type.
        
        Args:
            task_id: ID of the task to get related tasks for
            relationship_type: Type of relationship to filter by (e.g., 'depends_on', 'blocks')
            
        Returns:
            List of related tasks
            
        Raises:
            EntityNotFoundError: If the task doesn't exist
        """
        # Verify task exists
        if not self.exists(task_id):
            raise EntityNotFoundError(task_id, "Task")
        
        # Get the task
        task = self.get(task_id)
        
        # Get related task IDs
        if not hasattr(task, relationship_type):
            return []
        
        related_ids = getattr(task, relationship_type)
        if not related_ids:
            return []
        
        # Get related task entities
        result = []
        for related_id in related_ids:
            if self.exists(related_id):
                result.append(self.get(related_id))
        
        return result
    
    def search(self, 
              query: str, 
              statuses: Optional[List[Union[str, TaskStatus]]] = None,
              priorities: Optional[List[Union[int, TaskPriority]]] = None,
              tags: Optional[List[str]] = None,
              parent_id: Optional[str] = None) -> List[TaskEntity]:
        """
        Search for tasks matching various criteria.
        
        Args:
            query: Text to search for in task name and description
            statuses: Optional list of statuses to filter by
            priorities: Optional list of priorities to filter by
            tags: Optional list of tags to filter by
            parent_id: Optional parent ID to filter by
            
        Returns:
            List of matching tasks
        """
        # Start with all tasks
        results = self.get_all()
        
        # Filter by text query
        if query:
            query = query.lower()
            results = [task for task in results 
                     if query in task.name.lower() or 
                        (hasattr(task, 'description') and 
                         task.description and 
                         query in task.description.lower())]
        
        # Filter by statuses if provided
        if statuses:
            # Convert string statuses to enums
            status_enums = []
            for status in statuses:
                if isinstance(status, str):
                    try:
                        status_enums.append(TaskStatus.from_string(status))
                    except ValueError:
                        pass
                else:
                    status_enums.append(status)
            
            results = [task for task in results if task.status in status_enums]
        
        # Filter by priorities if provided
        if priorities:
            # Convert integer priorities to enums
            priority_enums = []
            for priority in priorities:
                if isinstance(priority, int):
                    try:
                        priority_enums.append(TaskPriority.from_int(priority))
                    except ValueError:
                        pass
                else:
                    priority_enums.append(priority)
            
            results = [task for task in results if task.priority in priority_enums]
        
        # Filter by tags if provided
        if tags:
            results = [task for task in results 
                     if any(tag in task.tags for tag in tags)]
        
        # Filter by parent ID if provided
        if parent_id:
            results = [task for task in results if task.parent_id == parent_id]
        
        return results 