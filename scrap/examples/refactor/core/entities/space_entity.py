"""
Space entity module.

This module defines the SpaceEntity class that represents a space in the system.
"""

from typing import Dict, List, Any, Optional, Set, Union
from datetime import datetime

from refactor.core.entities.base_entity import BaseEntity, EntityType, ValidationResult


class SpaceEntity(BaseEntity):
    """
    Class representing a space entity in the system.
    
    A space is a top-level container for folders and lists.
    """
    
    def __init__(self, 
                 entity_id: Optional[str] = None,
                 name: str = "",
                 created_at: Optional[int] = None,
                 updated_at: Optional[int] = None,
                 properties: Optional[Dict[str, Any]] = None):
        """
        Initialize a space entity.
        
        Args:
            entity_id: Optional ID for the space, generated if not provided
            name: Name of the space
            created_at: Timestamp when space was created
            updated_at: Timestamp when space was last updated
            properties: Additional properties stored with the space
        """
        super().__init__(
            entity_id=entity_id,
            name=name,
            created_at=created_at,
            updated_at=updated_at,
            properties=properties
        )
        
        self._folder_ids = []
        self._list_ids = []  # Lists not in folders
        
    def get_entity_type(self) -> EntityType:
        """
        Get the entity type.
        
        Returns:
            EntityType.SPACE
        """
        return EntityType.SPACE
    
    @property
    def folder_ids(self) -> List[str]:
        """Get the list of folder IDs in this space."""
        return self._folder_ids.copy()
    
    def add_folder(self, folder_id: str) -> bool:
        """
        Add a folder ID to the space.
        
        Args:
            folder_id: ID of folder to add
            
        Returns:
            True if folder was added, False if it already existed
        """
        if folder_id and folder_id not in self._folder_ids:
            self._folder_ids.append(folder_id)
            self.touch()
            self._trigger_hook('space.folder_added', self, folder_id)
            return True
        return False
    
    def remove_folder(self, folder_id: str) -> bool:
        """
        Remove a folder ID from the space.
        
        Args:
            folder_id: ID of folder to remove
            
        Returns:
            True if folder was removed, False if it didn't exist
        """
        if folder_id in self._folder_ids:
            self._folder_ids.remove(folder_id)
            self.touch()
            self._trigger_hook('space.folder_removed', self, folder_id)
            return True
        return False
    
    @property
    def list_ids(self) -> List[str]:
        """Get the list of list IDs directly in this space."""
        return self._list_ids.copy()
    
    def add_list(self, list_id: str) -> bool:
        """
        Add a list ID to the space.
        
        Args:
            list_id: ID of list to add
            
        Returns:
            True if list was added, False if it already existed
        """
        if list_id and list_id not in self._list_ids:
            self._list_ids.append(list_id)
            self.touch()
            self._trigger_hook('space.list_added', self, list_id)
            return True
        return False
    
    def remove_list(self, list_id: str) -> bool:
        """
        Remove a list ID from the space.
        
        Args:
            list_id: ID of list to remove
            
        Returns:
            True if list was removed, False if it didn't exist
        """
        if list_id in self._list_ids:
            self._list_ids.remove(list_id)
            self.touch()
            self._trigger_hook('space.list_removed', self, list_id)
            return True
        return False
    
    def _validate(self, result: ValidationResult) -> None:
        """
        Perform space-specific validations.
        
        Args:
            result: ValidationResult to add errors to
        """
        # No specific validations beyond what's in the base class
        pass
    
    def _to_dict(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Add space-specific data to dictionary representation.
        
        Args:
            data: Base dictionary with common properties
            
        Returns:
            Dictionary with space-specific properties added
        """
        space_data = data.copy()
        
        if self._folder_ids:
            space_data['folder_ids'] = self._folder_ids.copy()
            
        if self._list_ids:
            space_data['list_ids'] = self._list_ids.copy()
            
        return space_data
    
    @classmethod
    def _from_dict(cls, data: Dict[str, Any]) -> 'SpaceEntity':
        """
        Create a SpaceEntity from dictionary representation.
        
        Args:
            data: Dictionary representation of the space
            
        Returns:
            Instantiated SpaceEntity
        """
        entity_id = data.get('id')
        name = data.get('name', '')
        created_at = data.get('created_at')
        updated_at = data.get('updated_at')
        properties = data.get('properties', {})
        
        # Create the space
        space = cls(
            entity_id=entity_id,
            name=name,
            created_at=created_at,
            updated_at=updated_at,
            properties=properties.copy() if properties else {}
        )
        
        # Load folder IDs
        folder_ids = data.get('folder_ids', [])
        if folder_ids:
            space._folder_ids = folder_ids.copy()
            
        # Load list IDs
        list_ids = data.get('list_ids', [])
        if list_ids:
            space._list_ids = list_ids.copy()
            
        return space 