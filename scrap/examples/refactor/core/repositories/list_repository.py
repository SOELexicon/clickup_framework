"""
List repository implementation.

This module provides the concrete implementation of the list repository interface.
"""

from typing import Dict, List, Any, Optional, Callable, Set, TypeVar, cast
import json
from pathlib import Path

from refactor.core.repositories.repository_interface import (
    IListRepository,
    EntityNotFoundError,
    EntityAlreadyExistsError,
    ValidationError
)
from refactor.core.entities.list_entity import ListEntity
from refactor.core.entities.task_entity import TaskEntity

# Import TaskRepository for accessing task entities
from refactor.core.repositories.task_repository import TaskRepository


class ListRepository(IListRepository):
    """
    Concrete implementation of the list repository interface.
    
    This repository stores lists in memory and can be initialized from a JSON file.
    """
    
    def __init__(self, json_path: Optional[Path] = None, task_repository: Optional[TaskRepository] = None):
        """
        Initialize a new list repository.
        
        Args:
            json_path: Optional path to a JSON file containing list data
            task_repository: Optional task repository to use for fetching task entities
        """
        self._lists: Dict[str, ListEntity] = {}
        self._lists_by_name: Dict[str, str] = {}  # name -> id mapping
        self._tasks_by_list: Dict[str, List[str]] = {}  # list_id -> [task_id, ...]
        self._lists_by_folder: Dict[str, List[str]] = {}  # folder_id -> [list_id, ...]
        self._lists_by_space: Dict[str, List[str]] = {}  # space_id -> [list_id, ...]
        self._task_repository = task_repository
        
        if json_path is not None:
            self._load_from_json(json_path)
            
    def _load_from_json(self, json_path: Path) -> None:
        """
        Load list data from a JSON file.
        
        Args:
            json_path: Path to the JSON file
            
        Raises:
            FileNotFoundError: If the JSON file doesn't exist
            json.JSONDecodeError: If the JSON file is invalid
        """
        try:
            with open(json_path, 'r') as f:
                data = json.load(f)
            
            # Load lists
            for list_data in data.get('lists', []):
                list_entity = ListEntity.from_dict(list_data)
                self._lists[list_entity.id] = list_entity
                self._lists_by_name[list_entity.name] = list_entity.id
                
                # Initialize empty task array for this list
                self._tasks_by_list[list_entity.id] = []
                
                # Add list to folder mapping if it belongs to a folder
                if list_entity.folder_id:
                    if list_entity.folder_id not in self._lists_by_folder:
                        self._lists_by_folder[list_entity.folder_id] = []
                    self._lists_by_folder[list_entity.folder_id].append(list_entity.id)
                
                # Add list to space mapping if it belongs to a space
                if list_entity.space_id:
                    if list_entity.space_id not in self._lists_by_space:
                        self._lists_by_space[list_entity.space_id] = []
                    self._lists_by_space[list_entity.space_id].append(list_entity.id)
            
            # Load tasks into lists
            for task_data in data.get('tasks', []):
                if 'list_id' in task_data and task_data['list_id'] in self._tasks_by_list:
                    list_id = task_data['list_id']
                    task_id = task_data['id']
                    self._tasks_by_list[list_id].append(task_id)
                    
        except FileNotFoundError:
            raise FileNotFoundError(f"List JSON file not found: {json_path}")
        except json.JSONDecodeError:
            raise ValueError(f"Invalid JSON in list file: {json_path}")
    
    def add(self, entity: ListEntity) -> ListEntity:
        """
        Add a new list to the repository.
        
        Args:
            entity: List entity to add
            
        Returns:
            The added list entity
            
        Raises:
            EntityAlreadyExistsError: If a list with the same ID or name already exists
            ValidationError: If the list entity fails validation
        """
        # Validate entity ID
        if not entity.id:
            raise ValidationError("List ID cannot be empty")
            
        # Validate entity name
        if not entity.name:
            raise ValidationError("List name cannot be empty")
            
        # Check for existing ID
        if self.exists(entity.id):
            raise EntityAlreadyExistsError(f"List with ID {entity.id} already exists")
            
        # Check for existing name
        if entity.name in self._lists_by_name:
            raise EntityAlreadyExistsError(f"List with name '{entity.name}' already exists")
            
        # Add the entity
        self._lists[entity.id] = entity
        self._lists_by_name[entity.name] = entity.id
        self._tasks_by_list[entity.id] = []
        
        # Add list to folder mapping if it belongs to a folder
        if entity.folder_id:
            if entity.folder_id not in self._lists_by_folder:
                self._lists_by_folder[entity.folder_id] = []
            self._lists_by_folder[entity.folder_id].append(entity.id)
        
        # Add list to space mapping if it belongs to a space
        if entity.space_id:
            if entity.space_id not in self._lists_by_space:
                self._lists_by_space[entity.space_id] = []
            self._lists_by_space[entity.space_id].append(entity.id)
            
        return entity
    
    def update(self, entity: ListEntity) -> ListEntity:
        """
        Update an existing list in the repository.
        
        Args:
            entity: List entity with updated data
            
        Returns:
            The updated list entity
            
        Raises:
            EntityNotFoundError: If the list doesn't exist
            ValidationError: If the list entity fails validation
        """
        # Validate entity ID
        if not entity.id:
            raise ValidationError("List ID cannot be empty")
            
        # Validate entity name
        if not entity.name:
            raise ValidationError("List name cannot be empty")
            
        # Check if entity exists
        if not self.exists(entity.id):
            raise EntityNotFoundError(f"List with ID {entity.id} not found")
            
        old_list = self._lists[entity.id]
        
        # Handle name change
        if old_list.name != entity.name:
            if entity.name in self._lists_by_name:
                # Check if the name is already used by another list
                if self._lists_by_name[entity.name] != entity.id:
                    raise ValidationError(f"List name '{entity.name}' is already in use")
            
            # Remove old name mapping and add new one
            del self._lists_by_name[old_list.name]
            self._lists_by_name[entity.name] = entity.id
        
        # Handle folder change
        if old_list.folder_id != entity.folder_id:
            # Remove from old folder
            if old_list.folder_id and old_list.folder_id in self._lists_by_folder:
                if entity.id in self._lists_by_folder[old_list.folder_id]:
                    self._lists_by_folder[old_list.folder_id].remove(entity.id)
            
            # Add to new folder
            if entity.folder_id:
                if entity.folder_id not in self._lists_by_folder:
                    self._lists_by_folder[entity.folder_id] = []
                self._lists_by_folder[entity.folder_id].append(entity.id)
        
        # Handle space change
        if old_list.space_id != entity.space_id:
            # Remove from old space
            if old_list.space_id and old_list.space_id in self._lists_by_space:
                if entity.id in self._lists_by_space[old_list.space_id]:
                    self._lists_by_space[old_list.space_id].remove(entity.id)
            
            # Add to new space
            if entity.space_id:
                if entity.space_id not in self._lists_by_space:
                    self._lists_by_space[entity.space_id] = []
                self._lists_by_space[entity.space_id].append(entity.id)
        
        # Update the entity
        self._lists[entity.id] = entity
        return entity
    
    def get(self, entity_id: str) -> ListEntity:
        """
        Get a list by its ID.
        
        Args:
            entity_id: ID of the list to get
            
        Returns:
            The list entity with the given ID
            
        Raises:
            EntityNotFoundError: If no list with the given ID exists
            ValidationError: If the entity ID is empty
        """
        # Validate entity ID
        if not entity_id:
            raise ValidationError("List ID cannot be empty")
            
        # Check if entity exists
        if not self.exists(entity_id):
            raise EntityNotFoundError(f"List with ID {entity_id} not found")
            
        return self._lists[entity_id]
    
    def get_by_name(self, name: str) -> ListEntity:
        """
        Get a list by its name.
        
        Args:
            name: Name of the list to get
            
        Returns:
            The list entity with the given name
            
        Raises:
            EntityNotFoundError: If no list with the given name exists
            ValidationError: If the name is empty
        """
        # Validate name
        if not name:
            raise ValidationError("List name cannot be empty")
            
        # Check if entity exists by name
        if name not in self._lists_by_name:
            raise EntityNotFoundError(f"List with name '{name}' not found")
            
        list_id = self._lists_by_name[name]
        return self._lists[list_id]
    
    def exists(self, entity_id: str) -> bool:
        """
        Check if a list with the given ID exists.
        
        Args:
            entity_id: ID to check
            
        Returns:
            True if a list with the given ID exists, False otherwise
        """
        return entity_id in self._lists
    
    def delete(self, entity_id: str) -> bool:
        """
        Delete a list by its ID.
        
        Args:
            entity_id: ID of the list to delete
            
        Returns:
            True if the list was deleted, False if it didn't exist
        """
        if not self.exists(entity_id):
            return False
            
        list_entity = self._lists[entity_id]
        
        # Remove list from name mapping
        del self._lists_by_name[list_entity.name]
        
        # Remove list from folder mapping
        if list_entity.folder_id and list_entity.folder_id in self._lists_by_folder:
            if list_entity.id in self._lists_by_folder[list_entity.folder_id]:
                self._lists_by_folder[list_entity.folder_id].remove(list_entity.id)
        
        # Remove list from space mapping
        if list_entity.space_id and list_entity.space_id in self._lists_by_space:
            if list_entity.id in self._lists_by_space[list_entity.space_id]:
                self._lists_by_space[list_entity.space_id].remove(list_entity.id)
        
        # Remove list's tasks mapping
        if entity_id in self._tasks_by_list:
            del self._tasks_by_list[entity_id]
        
        # Remove the list itself
        del self._lists[entity_id]
        return True
    
    def list_all(self) -> List[ListEntity]:
        """
        Get all lists in the repository.
        
        Returns:
            List of all list entities
        """
        return list(self._lists.values())
    
    def count(self) -> int:
        """
        Get the number of lists in the repository.
        
        Returns:
            Number of list entities
        """
        return len(self._lists)
    
    def find(self, predicate: Callable[[ListEntity], bool]) -> List[ListEntity]:
        """
        Find lists that match a predicate.
        
        Args:
            predicate: Function that takes a list entity and returns True for matches
            
        Returns:
            List of matching list entities
        """
        return [list_entity for list_entity in self._lists.values() if predicate(list_entity)]
    
    def get_by_folder(self, folder_id: str) -> List[ListEntity]:
        """
        Get lists in a specific folder.
        
        Args:
            folder_id: ID of the folder
            
        Returns:
            List of list entities in the folder
            
        Raises:
            ValidationError: If the folder ID is empty
        """
        # Validate folder ID
        if not folder_id:
            raise ValidationError("Folder ID cannot be empty")
            
        # Get list IDs in the folder
        list_ids = self._lists_by_folder.get(folder_id, [])
        
        # Get list entities by their IDs
        return [self._lists[list_id] for list_id in list_ids if list_id in self._lists]
    
    def get_by_space(self, space_id: str) -> List[ListEntity]:
        """
        Get lists in a specific space (directly in the space, not in folders).
        
        Args:
            space_id: ID of the space
            
        Returns:
            List of list entities in the space
            
        Raises:
            ValidationError: If the space ID is empty
        """
        # Validate space ID
        if not space_id:
            raise ValidationError("Space ID cannot be empty")
            
        # Get list IDs in the space
        list_ids = self._lists_by_space.get(space_id, [])
        
        # Get list entities by their IDs
        return [self._lists[list_id] for list_id in list_ids if list_id in self._lists]
    
    def get_tasks(self, list_id: str) -> List[TaskEntity]:
        """
        Get all tasks in a list.
        
        Args:
            list_id: ID of the list to get tasks for
            
        Returns:
            List of task entities in the list
            
        Raises:
            EntityNotFoundError: If no list with the given ID exists
            ValidationError: If the list ID is empty
        """
        # Validate list ID
        if not list_id:
            raise ValidationError("List ID cannot be empty")
            
        # Check if list exists
        if not self.exists(list_id):
            raise EntityNotFoundError(f"List with ID {list_id} not found")
        
        # Check if there's a task repository available
        if not self._task_repository:
            raise RuntimeError("Task repository not available. Cannot fetch task entities.")
            
        # Get task IDs for this list
        task_ids = self._tasks_by_list.get(list_id, [])
        
        # Get actual task entities from the task repository
        task_entities = []
        for task_id in task_ids:
            try:
                task_entity = self._task_repository.get(task_id)
                task_entities.append(task_entity)
            except EntityNotFoundError:
                # Skip tasks that don't exist in the task repository
                continue
                
        return task_entities