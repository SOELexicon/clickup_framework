"""
Folder entity module.

This module defines the FolderEntity class that represents a folder in the system.
"""

from typing import Dict, List, Any, Optional, Set, Union
from datetime import datetime

from refactor.core.entities.base_entity import BaseEntity, EntityType, ValidationResult


class FolderEntity(BaseEntity):
    """
    Class representing a folder entity in the system.
    
    A folder is a container for lists, belonging to a space.
    """
    
    def __init__(self, 
                 entity_id: Optional[str] = None,
                 name: str = "",
                 space_id: str = "",
                 created_at: Optional[int] = None,
                 updated_at: Optional[int] = None,
                 properties: Optional[Dict[str, Any]] = None):
        """
        Initialize a folder entity.
        
        Args:
            entity_id: Optional ID for the folder, generated if not provided
            name: Name of the folder
            space_id: ID of the space the folder belongs to
            created_at: Timestamp when folder was created
            updated_at: Timestamp when folder was last updated
            properties: Additional properties stored with the folder
        """
        super().__init__(
            entity_id=entity_id,
            name=name,
            created_at=created_at,
            updated_at=updated_at,
            properties=properties
        )
        
        self._space_id = space_id
        self._list_ids = []
        
    def get_entity_type(self) -> EntityType:
        """
        Get the entity type.
        
        Returns:
            EntityType.FOLDER
        """
        return EntityType.FOLDER
    
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
            self._trigger_hook('folder.space_changed', self, old_space_id, value)
    
    @property
    def list_ids(self) -> List[str]:
        """Get the list of list IDs in this folder."""
        return self._list_ids.copy()
    
    def add_list(self, list_id: str) -> bool:
        """
        Add a list ID to the folder.
        
        Args:
            list_id: ID of list to add
            
        Returns:
            True if list was added, False if it already existed
        """
        if list_id and list_id not in self._list_ids:
            self._list_ids.append(list_id)
            self.touch()
            self._trigger_hook('folder.list_added', self, list_id)
            return True
        return False
    
    def remove_list(self, list_id: str) -> bool:
        """
        Remove a list ID from the folder.
        
        Args:
            list_id: ID of list to remove
            
        Returns:
            True if list was removed, False if it didn't exist
        """
        if list_id in self._list_ids:
            self._list_ids.remove(list_id)
            self.touch()
            self._trigger_hook('folder.list_removed', self, list_id)
            return True
        return False
    
    def move_list(self, list_id: str, new_position: int) -> bool:
        """
        Move a list to a new position in the folder.
        
        Args:
            list_id: ID of list to move
            new_position: New position for the list (0-based index)
            
        Returns:
            True if list was moved, False if it doesn't exist or position is invalid
        """
        if list_id not in self._list_ids:
            return False
            
        if new_position < 0 or new_position >= len(self._list_ids):
            return False
            
        current_position = self._list_ids.index(list_id)
        if current_position == new_position:
            return True  # Already in the correct position
            
        # Move the list
        self._list_ids.remove(list_id)
        self._list_ids.insert(new_position, list_id)
        self.touch()
        
        self._trigger_hook('folder.list_moved', self, list_id, current_position, new_position)
        return True
    
    def _validate(self, result: ValidationResult) -> None:
        """
        Perform folder-specific validations.
        
        Args:
            result: ValidationResult to add errors to
        """
        # Space ID must be present
        if not self._space_id:
            result.add_error("Folder must have a space ID")
    
    def _to_dict(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Add folder-specific data to dictionary representation.
        
        Args:
            data: Base dictionary with common properties
            
        Returns:
            Dictionary with folder-specific properties added
        """
        folder_data = data.copy()
        
        folder_data['space_id'] = self._space_id
        
        if self._list_ids:
            folder_data['list_ids'] = self._list_ids.copy()
            
        return folder_data
    
    @classmethod
    def _from_dict(cls, data: Dict[str, Any]) -> 'FolderEntity':
        """
        Create a FolderEntity from dictionary representation.
        
        Args:
            data: Dictionary representation of the folder
            
        Returns:
            Instantiated FolderEntity
        """
        entity_id = data.get('id')
        name = data.get('name', '')
        space_id = data.get('space_id', '')
        created_at = data.get('created_at')
        updated_at = data.get('updated_at')
        properties = data.get('properties', {})
        
        # Create the folder
        folder = cls(
            entity_id=entity_id,
            name=name,
            space_id=space_id,
            created_at=created_at,
            updated_at=updated_at,
            properties=properties.copy() if properties else {}
        )
        
        # Load list IDs
        list_ids = data.get('list_ids', [])
        if list_ids:
            folder._list_ids = list_ids.copy()
            
        return folder 