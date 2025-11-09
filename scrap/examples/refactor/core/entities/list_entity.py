"""
List entity module.

This module defines the ListEntity class that represents a list in the system.
"""

from typing import Dict, List, Any, Optional, Set, Union
from datetime import datetime

from refactor.core.entities.base_entity import BaseEntity, EntityType, ValidationResult


class ListEntity(BaseEntity):
    """
    Class representing a list entity in the system.
    
    A list is a container for tasks, generally belonging to a folder and space.
    """
    
    def __init__(self, 
                 entity_id: Optional[str] = None,
                 name: str = "",
                 folder_id: Optional[str] = None,
                 space_id: str = "",
                 created_at: Optional[int] = None,
                 updated_at: Optional[int] = None,
                 properties: Optional[Dict[str, Any]] = None):
        """
        Initialize a list entity.
        
        Args:
            entity_id: Optional ID for the list, generated if not provided
            name: Name of the list
            folder_id: Optional ID of the parent folder
            space_id: ID of the space the list belongs to
            created_at: Timestamp when list was created
            updated_at: Timestamp when list was last updated
            properties: Additional properties stored with the list
        """
        super().__init__(
            entity_id=entity_id,
            name=name,
            created_at=created_at,
            updated_at=updated_at,
            properties=properties
        )
        
        self._folder_id = folder_id
        self._space_id = space_id
        self._task_ids = []
        
    def get_entity_type(self) -> EntityType:
        """
        Get the entity type.
        
        Returns:
            EntityType.LIST
        """
        return EntityType.LIST
    
    @property
    def folder_id(self) -> Optional[str]:
        """Get the parent folder ID."""
        return self._folder_id
    
    @folder_id.setter
    def folder_id(self, value: Optional[str]) -> None:
        """
        Set the parent folder ID.
        
        Args:
            value: New folder ID
        """
        if value != self._folder_id:
            old_folder_id = self._folder_id
            self._folder_id = value
            self.touch()
            self._trigger_hook('list.folder_changed', self, old_folder_id, value)
    
    @property
    def space_id(self) -> str:
        """Get the space ID."""
        return self._space_id
    
    @space_id.setter
    def space_id(self, value: str) -> None:
        """
        Set the space ID.
        
        Args:
            value: New space ID
        """
        if value and value != self._space_id:
            old_space_id = self._space_id
            self._space_id = value
            self.touch()
            self._trigger_hook('list.space_changed', self, old_space_id, value)
    
    @property
    def task_ids(self) -> List[str]:
        """Get the list of task IDs in this list."""
        return self._task_ids.copy()
    
    def add_task(self, task_id: str) -> bool:
        """
        Add a task ID to the list.
        
        Args:
            task_id: ID of task to add
            
        Returns:
            True if task was added, False if it already existed
        """
        if task_id and task_id not in self._task_ids:
            self._task_ids.append(task_id)
            self.touch()
            self._trigger_hook('list.task_added', self, task_id)
            return True
        return False
    
    def remove_task(self, task_id: str) -> bool:
        """
        Remove a task ID from the list.
        
        Args:
            task_id: ID of task to remove
            
        Returns:
            True if task was removed, False if it didn't exist
        """
        if task_id in self._task_ids:
            self._task_ids.remove(task_id)
            self.touch()
            self._trigger_hook('list.task_removed', self, task_id)
            return True
        return False
    
    def move_task(self, task_id: str, new_position: int) -> bool:
        """
        Move a task to a new position in the list.
        
        Args:
            task_id: ID of task to move
            new_position: New position for the task (0-based index)
            
        Returns:
            True if task was moved, False if it doesn't exist or position is invalid
        """
        if task_id not in self._task_ids:
            return False
            
        if new_position < 0 or new_position >= len(self._task_ids):
            return False
            
        current_position = self._task_ids.index(task_id)
        if current_position == new_position:
            return True  # Already in the correct position
            
        # Move the task
        self._task_ids.remove(task_id)
        self._task_ids.insert(new_position, task_id)
        self.touch()
        
        self._trigger_hook('list.task_moved', self, task_id, current_position, new_position)
        return True
    
    def _validate(self, result: ValidationResult) -> None:
        """
        Perform list-specific validations.
        
        Args:
            result: ValidationResult to add errors to
        """
        # Space ID must be present
        if not self._space_id:
            result.add_error("List must have a space ID")
    
    def _to_dict(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Add list-specific data to dictionary representation.
        
        Args:
            data: Base dictionary with common properties
            
        Returns:
            Dictionary with list-specific properties added
        """
        list_data = data.copy()
        
        list_data['space_id'] = self._space_id
        
        if self._folder_id:
            list_data['folder_id'] = self._folder_id
            
        if self._task_ids:
            list_data['task_ids'] = self._task_ids.copy()
            
        return list_data
    
    @classmethod
    def _from_dict(cls, data: Dict[str, Any]) -> 'ListEntity':
        """
        Create a ListEntity from dictionary representation.
        
        Args:
            data: Dictionary representation of the list
            
        Returns:
            Instantiated ListEntity
        """
        entity_id = data.get('id')
        name = data.get('name', '')
        folder_id = data.get('folder_id')
        space_id = data.get('space_id', '')
        created_at = data.get('created_at')
        updated_at = data.get('updated_at')
        properties = data.get('properties', {})
        
        # Create the list
        list_entity = cls(
            entity_id=entity_id,
            name=name,
            folder_id=folder_id,
            space_id=space_id,
            created_at=created_at,
            updated_at=updated_at,
            properties=properties.copy() if properties else {}
        )
        
        # Load task IDs
        task_ids = data.get('task_ids', [])
        if task_ids:
            list_entity._task_ids = task_ids.copy()
            
        return list_entity 