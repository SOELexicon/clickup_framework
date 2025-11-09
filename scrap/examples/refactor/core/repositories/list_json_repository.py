"""
List JSON Repository

This module implements a JSON repository specifically for list entities.
It extends the JsonRepository with list-specific operations.
"""
from pathlib import Path
from typing import List, Dict, Any, Optional, Type, Union

from refactor.core.entities.list_entity import ListEntity
from refactor.core.entities.task_entity import TaskEntity
from refactor.core.repositories.json_repository import JsonRepository
from refactor.core.repositories.repository_interface import IListRepository
from refactor.core.repositories.task_json_repository import TaskJsonRepository
from refactor.core.exceptions import EntityNotFoundError, ValidationError


class ListJsonRepository(JsonRepository[ListEntity], IListRepository):
    """
    JSON repository implementation for list entities.
    
    This repository extends the generic JsonRepository with list-specific
    operations and implements the IListRepository interface.
    """
    
    def __init__(self, 
                json_path: Path, 
                task_repository: Optional[TaskJsonRepository] = None,
                **kwargs):
        """
        Initialize a new list JSON repository.
        
        Args:
            json_path: Path to the JSON file for list persistence
            task_repository: Optional task repository for retrieving task entities
            **kwargs: Additional arguments to pass to JsonRepository constructor
        """
        super().__init__(ListEntity, json_path, **kwargs)
        self._task_repository = task_repository
        
        # Initialize additional mappings
        self._tasks_by_list: Dict[str, List[str]] = {}  # list_id -> [task_id, ...]
        self._lists_by_folder: Dict[str, List[str]] = {}  # folder_id -> [list_id, ...]
        self._lists_by_space: Dict[str, List[str]] = {}  # space_id -> [list_id, ...]
        
        # Build mappings from the loaded entities
        self._build_mappings()
    
    def _build_mappings(self) -> None:
        """
        Build mappings for tasks, folders, and spaces based on loaded entities.
        """
        # Clear existing mappings
        self._tasks_by_list = {}
        self._lists_by_folder = {}
        self._lists_by_space = {}
        
        # Create mappings for folders and spaces
        for list_entity in self.get_all():
            list_id = self._get_entity_id(list_entity)
            
            # Initialize empty task array for this list
            self._tasks_by_list[list_id] = []
            
            # Map list to folder
            if list_entity.folder_id:
                if list_entity.folder_id not in self._lists_by_folder:
                    self._lists_by_folder[list_entity.folder_id] = []
                self._lists_by_folder[list_entity.folder_id].append(list_id)
            
            # Map list to space
            if list_entity.space_id:
                if list_entity.space_id not in self._lists_by_space:
                    self._lists_by_space[list_entity.space_id] = []
                self._lists_by_space[list_entity.space_id].append(list_id)
        
        # Map tasks to lists if task repository is available
        if self._task_repository:
            for task in self._task_repository.get_all():
                if hasattr(task, 'list_id') and task.list_id:
                    list_id = task.list_id
                    if list_id in self._tasks_by_list:
                        self._tasks_by_list[list_id].append(task.id)
    
    def add(self, entity: ListEntity) -> ListEntity:
        """
        Add a new list entity to the repository.
        
        Args:
            entity: The list entity to add
            
        Returns:
            The added list entity
            
        Raises:
            EntityAlreadyExistsError: If an entity with the same ID already exists
            ValidationError: If the entity is invalid
        """
        # Perform basic validation before passing to parent
        if not entity.name:
            raise ValidationError("List name cannot be empty")
        
        # Add the entity using parent method
        added_entity = super().add(entity)
        
        # Update mappings
        list_id = self._get_entity_id(added_entity)
        
        # Initialize empty task array
        self._tasks_by_list[list_id] = []
        
        # Map list to folder
        if added_entity.folder_id:
            if added_entity.folder_id not in self._lists_by_folder:
                self._lists_by_folder[added_entity.folder_id] = []
            self._lists_by_folder[added_entity.folder_id].append(list_id)
        
        # Map list to space
        if added_entity.space_id:
            if added_entity.space_id not in self._lists_by_space:
                self._lists_by_space[added_entity.space_id] = []
            self._lists_by_space[added_entity.space_id].append(list_id)
        
        return added_entity
    
    def update(self, entity: ListEntity) -> ListEntity:
        """
        Update an existing list entity.
        
        Args:
            entity: The list entity with updated values
            
        Returns:
            The updated list entity
            
        Raises:
            EntityNotFoundError: If the entity does not exist
            ValidationError: If the updated entity is invalid
        """
        # Verify entity exists
        entity_id = self._get_entity_id(entity)
        if not self.exists(entity_id):
            raise EntityNotFoundError(entity_id, "List")
        
        # Get the old entity
        old_entity = self.get(entity_id)
        
        # Handle folder change
        if old_entity.folder_id != entity.folder_id:
            # Remove from old folder
            if old_entity.folder_id and old_entity.folder_id in self._lists_by_folder:
                if entity_id in self._lists_by_folder[old_entity.folder_id]:
                    self._lists_by_folder[old_entity.folder_id].remove(entity_id)
            
            # Add to new folder
            if entity.folder_id:
                if entity.folder_id not in self._lists_by_folder:
                    self._lists_by_folder[entity.folder_id] = []
                self._lists_by_folder[entity.folder_id].append(entity_id)
        
        # Handle space change
        if old_entity.space_id != entity.space_id:
            # Remove from old space
            if old_entity.space_id and old_entity.space_id in self._lists_by_space:
                if entity_id in self._lists_by_space[old_entity.space_id]:
                    self._lists_by_space[old_entity.space_id].remove(entity_id)
            
            # Add to new space
            if entity.space_id:
                if entity.space_id not in self._lists_by_space:
                    self._lists_by_space[entity.space_id] = []
                self._lists_by_space[entity.space_id].append(entity_id)
        
        # Update the entity using parent method
        return super().update(entity)
    
    def delete(self, entity_id: str) -> None:
        """
        Delete a list entity by its ID.
        
        Args:
            entity_id: The ID of the list entity to delete
            
        Raises:
            EntityNotFoundError: If no entity with the given ID exists
            ValidationError: If the list has tasks
        """
        # Verify entity exists
        if not self.exists(entity_id):
            raise EntityNotFoundError(entity_id, "List")
        
        # Check if list has tasks
        if entity_id in self._tasks_by_list and self._tasks_by_list[entity_id]:
            raise ValidationError(f"Cannot delete list with {len(self._tasks_by_list[entity_id])} tasks. "
                                 "Move or delete tasks first.")
        
        # Get the entity
        entity = self.get(entity_id)
        
        # Remove list from folder mapping
        if entity.folder_id and entity.folder_id in self._lists_by_folder:
            if entity_id in self._lists_by_folder[entity.folder_id]:
                self._lists_by_folder[entity.folder_id].remove(entity_id)
        
        # Remove list from space mapping
        if entity.space_id and entity.space_id in self._lists_by_space:
            if entity_id in self._lists_by_space[entity.space_id]:
                self._lists_by_space[entity.space_id].remove(entity_id)
        
        # Remove task mapping
        if entity_id in self._tasks_by_list:
            del self._tasks_by_list[entity_id]
        
        # Delete the entity using parent method
        super().delete(entity_id)
    
    def get_by_folder(self, folder_id: str) -> List[ListEntity]:
        """
        Get all lists in a specific folder.
        
        Args:
            folder_id: ID of the folder to get lists for
            
        Returns:
            List of list entities in the folder
        """
        if not folder_id or folder_id not in self._lists_by_folder:
            return []
        
        return [self.get(list_id) for list_id in self._lists_by_folder[folder_id]
                if self.exists(list_id)]
    
    def get_by_space(self, space_id: str) -> List[ListEntity]:
        """
        Get all lists in a specific space.
        
        Args:
            space_id: ID of the space to get lists for
            
        Returns:
            List of list entities in the space
        """
        if not space_id or space_id not in self._lists_by_space:
            return []
        
        return [self.get(list_id) for list_id in self._lists_by_space[space_id]
                if self.exists(list_id)]
    
    def get_tasks(self, list_id: str) -> List[TaskEntity]:
        """
        Get all tasks in a specific list.
        
        Args:
            list_id: ID of the list to get tasks for
            
        Returns:
            List of task entities in the list
            
        Raises:
            EntityNotFoundError: If no list with the given ID exists
        """
        # Verify list exists
        if not self.exists(list_id):
            raise EntityNotFoundError(list_id, "List")
        
        # Check if task repository is available
        if not self._task_repository:
            return []
        
        # Get task IDs for this list
        task_ids = self._tasks_by_list.get(list_id, [])
        
        # Get task entities
        tasks = []
        for task_id in task_ids:
            try:
                task = self._task_repository.get(task_id)
                tasks.append(task)
            except EntityNotFoundError:
                # Skip tasks that don't exist
                continue
        
        return tasks
    
    def add_task_to_list(self, list_id: str, task_id: str) -> None:
        """
        Add a task to a list.
        
        Args:
            list_id: ID of the list
            task_id: ID of the task to add
            
        Raises:
            EntityNotFoundError: If the list or task doesn't exist
        """
        # Verify list exists
        if not self.exists(list_id):
            raise EntityNotFoundError(list_id, "List")
        
        # Verify task exists if task repository is available
        if self._task_repository and not self._task_repository.exists(task_id):
            raise EntityNotFoundError(task_id, "Task")
        
        # Initialize task list if needed
        if list_id not in self._tasks_by_list:
            self._tasks_by_list[list_id] = []
        
        # Add task ID to list if not already there
        if task_id not in self._tasks_by_list[list_id]:
            self._tasks_by_list[list_id].append(task_id)
    
    def remove_task_from_list(self, list_id: str, task_id: str) -> None:
        """
        Remove a task from a list.
        
        Args:
            list_id: ID of the list
            task_id: ID of the task to remove
            
        Raises:
            EntityNotFoundError: If the list doesn't exist
        """
        # Verify list exists
        if not self.exists(list_id):
            raise EntityNotFoundError(list_id, "List")
        
        # Remove task ID from list if present
        if list_id in self._tasks_by_list and task_id in self._tasks_by_list[list_id]:
            self._tasks_by_list[list_id].remove(task_id)
    
    def search(self, 
              query: str,
              folder_id: Optional[str] = None,
              space_id: Optional[str] = None) -> List[ListEntity]:
        """
        Search for lists matching various criteria.
        
        Args:
            query: Text to search for in list name and description
            folder_id: Optional folder ID to filter by
            space_id: Optional space ID to filter by
            
        Returns:
            List of matching list entities
        """
        # Start with all lists
        results = self.get_all()
        
        # Filter by text query
        if query:
            query = query.lower()
            results = [list_entity for list_entity in results 
                      if query in list_entity.name.lower() or 
                         (hasattr(list_entity, 'description') and 
                          list_entity.description and 
                          query in list_entity.description.lower())]
        
        # Filter by folder ID
        if folder_id:
            results = [list_entity for list_entity in results 
                      if list_entity.folder_id == folder_id]
        
        # Filter by space ID
        if space_id:
            results = [list_entity for list_entity in results 
                      if list_entity.space_id == space_id]
        
        return results 