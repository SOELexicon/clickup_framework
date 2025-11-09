"""
Task: tsk_0fa698f3 - Update Core Module Comments
Document: refactor/core/entities/checklist_entity.py
dohcount: 1

Related Tasks:
    - tsk_0a733101 - Code Comments Enhancement (parent)
    - tsk_65df3554 - Update TaskType Enum (sibling)

Used By:
    - ChecklistService: Manages checklist operations through this entity
    - TaskEntity: Stores references to checklists through ChecklistEntity objects
    - CoreManager: Coordinates operations on checklists and their items

Purpose:
    Defines the ChecklistEntity and ChecklistItemEntity classes that represent
    checklists and their items in the system, providing functionality for tracking
    task progress through discrete, checkable steps.

Requirements:
    - Must support parent-child relationship between checklists and tasks
    - Must track checked status with timestamps
    - Must maintain order of checklist items
    - CRITICAL: Checklist items must always have a parent checklist reference
    - CRITICAL: Checklists must always have a parent task reference

Changes:
    - v1: Initial implementation with basic checklist and item functionality
    - v2: Added support for tracking when items were checked with timestamps
    - v3: Enhanced validation and added hook system integration

Lessons Learned:
    - Tracking timestamps for check operations provides valuable metrics on task completion
    - Validating parent references is essential to maintain data integrity
    - Using hook system for check/uncheck operations enables event-driven extensions
"""

from typing import Dict, List, Any, Optional, Set, Union
from datetime import datetime

from refactor.core.entities.base_entity import BaseEntity, EntityType, ValidationResult


class ChecklistItemEntity(BaseEntity):
    """
    Task: tsk_0fa698f3 - Update Core Module Comments
    Document: refactor/core/entities/checklist_entity.py
    dohcount: 1
    
    Used By:
        - ChecklistEntity: Contains references to ChecklistItemEntity objects
        - ChecklistService: Performs operations on checklist items
        - CLI Commands: Displays and manipulates checklist item status
    
    Purpose:
        Represents an individual checkable item within a checklist, tracking
        its completion status and associated metadata.
    
    Requirements:
        - Must store reference to parent checklist
        - Must track checked status and timestamp when checked
        - Must support being checked and unchecked with appropriate hooks
        - CRITICAL: Must maintain referential integrity with parent checklist
    
    Changes:
        - v1: Initial implementation with basic check/uncheck functionality
        - v2: Added checked_at timestamp tracking for analytics
        - v3: Integrated hook system for state change notifications
    """
    
    def __init__(self, 
                 entity_id: Optional[str] = None,
                 name: str = "",
                 is_checked: bool = False,
                 parent_checklist_id: Optional[str] = None,
                 created_at: Optional[int] = None,
                 updated_at: Optional[int] = None,
                 properties: Optional[Dict[str, Any]] = None):
        """
        Initialize a checklist item entity.
        
        Args:
            entity_id: Optional ID for the item, generated if not provided
            name: Content or text of the checklist item
            is_checked: Whether the item is checked/completed
            parent_checklist_id: ID of the parent checklist
            created_at: Timestamp when item was created
            updated_at: Timestamp when item was last updated
            properties: Additional properties stored with the item
            
        Requirements:
            - entity_id format must follow item_XXXXXXXX pattern if provided
            - parent_checklist_id must be provided for validation to pass
        """
        super().__init__(
            entity_id=entity_id,
            name=name,
            created_at=created_at,
            updated_at=updated_at,
            properties=properties
        )
        
        self._is_checked = is_checked
        self._parent_checklist_id = parent_checklist_id
        self._checked_at = None
        
    def get_entity_type(self) -> EntityType:
        """
        Get the entity type.
        
        Returns:
            EntityType.CHECKLIST_ITEM
        """
        return EntityType.CHECKLIST_ITEM
    
    @property
    def is_checked(self) -> bool:
        """
        Get whether the item is checked.
        
        Returns:
            Boolean indicating if the item has been completed
        """
        return self._is_checked
    
    @property
    def checked_at(self) -> Optional[int]:
        """
        Get the timestamp when the item was checked.
        
        Returns:
            Unix timestamp when the item was last checked, or None if never checked
        """
        return self._checked_at
    
    @property
    def parent_checklist_id(self) -> Optional[str]:
        """
        Get the parent checklist ID.
        
        Returns:
            ID of the checklist this item belongs to
        """
        return self._parent_checklist_id
    
    def check(self) -> bool:
        """
        Mark the item as checked.
        
        Sets the is_checked property to True, records the current timestamp,
        and triggers the checklist_item.checked hook for extensions.
        
        Returns:
            True if the item was checked, False if it was already checked
            
        Side Effects:
            - Updates checked_at timestamp
            - Updates updated_at timestamp via touch()
            - Triggers checklist_item.checked hook
        """
        if not self._is_checked:
            self._is_checked = True
            self._checked_at = int(datetime.now().timestamp())
            self.touch()
            self._trigger_hook('checklist_item.checked', self)
            return True
        return False
    
    def uncheck(self) -> bool:
        """
        Mark the item as unchecked.
        
        Sets the is_checked property to False, clears the checked_at timestamp,
        and triggers the checklist_item.unchecked hook for extensions.
        
        Returns:
            True if the item was unchecked, False if it was already unchecked
            
        Side Effects:
            - Clears checked_at timestamp
            - Updates updated_at timestamp via touch()
            - Triggers checklist_item.unchecked hook
        """
        if self._is_checked:
            self._is_checked = False
            self._checked_at = None
            self.touch()
            self._trigger_hook('checklist_item.unchecked', self)
            return True
        return False
    
    def _validate(self, result: ValidationResult) -> None:
        """
        Perform checklist-item-specific validations.
        
        Ensures that the item has a parent checklist reference for
        maintaining referential integrity.
        
        Args:
            result: ValidationResult to add errors to
            
        Side Effects:
            Adds error to result if parent_checklist_id is missing
        """
        if not self._parent_checklist_id:
            result.add_error("Checklist item must have a parent checklist")
    
    def _to_dict(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Add checklist-item-specific data to dictionary representation.
        
        Adds is_checked status, parent_checklist_id, and checked_at timestamp
        to the base entity dictionary.
        
        Args:
            data: Base dictionary with common properties
            
        Returns:
            Dictionary with checklist-item-specific properties added
        """
        item_data = data.copy()
        
        item_data['is_checked'] = self._is_checked
        item_data['parent_checklist_id'] = self._parent_checklist_id
        
        if self._checked_at:
            item_data['checked_at'] = self._checked_at
            
        return item_data
    
    @classmethod
    def _from_dict(cls, data: Dict[str, Any]) -> 'ChecklistItemEntity':
        """
        Create a ChecklistItemEntity from dictionary representation.
        
        Args:
            data: Dictionary representation of the checklist item
            
        Returns:
            Instantiated ChecklistItemEntity
            
        Requirements:
            - Dictionary must contain at minimum an id and parent_checklist_id
            - Other fields are populated with defaults if missing
        """
        entity_id = data.get('id')
        name = data.get('name', '')
        is_checked = data.get('is_checked', False)
        parent_checklist_id = data.get('parent_checklist_id')
        created_at = data.get('created_at')
        updated_at = data.get('updated_at')
        properties = data.get('properties', {})
        
        # Create the checklist item
        item = cls(
            entity_id=entity_id,
            name=name,
            is_checked=is_checked,
            parent_checklist_id=parent_checklist_id,
            created_at=created_at,
            updated_at=updated_at,
            properties=properties.copy() if properties else {}
        )
        
        # Set checked_at if provided
        checked_at = data.get('checked_at')
        if checked_at:
            item._checked_at = checked_at
            
        return item


class ChecklistEntity(BaseEntity):
    """
    Task: tsk_0fa698f3 - Update Core Module Comments
    Document: refactor/core/entities/checklist_entity.py
    dohcount: 1
    
    Used By:
        - TaskEntity: Contains ChecklistEntity objects to track implementation steps
        - ChecklistService: Manages operations on checklists
        - CLI Commands: Provides commands to manipulate checklists
    
    Purpose:
        Represents a collection of related ChecklistItemEntity objects that
        track progress on discrete steps needed to complete a task.
    
    Requirements:
        - Must maintain reference to parent task
        - Must store ordered list of checklist item IDs
        - Must support adding, removing, and reordering items
        - CRITICAL: Must maintain referential integrity with parent task
    
    Changes:
        - v1: Initial implementation with basic item management
        - v2: Added support for item ordering and repositioning
        - v3: Enhanced validation and hook system integration
    """
    
    def __init__(self, 
                 entity_id: Optional[str] = None,
                 name: str = "",
                 parent_task_id: Optional[str] = None,
                 created_at: Optional[int] = None,
                 updated_at: Optional[int] = None,
                 properties: Optional[Dict[str, Any]] = None):
        """
        Initialize a checklist entity.
        
        Args:
            entity_id: Optional ID for the checklist, generated if not provided
            name: Name of the checklist
            parent_task_id: ID of the parent task
            created_at: Timestamp when checklist was created
            updated_at: Timestamp when checklist was last updated
            properties: Additional properties stored with the checklist
            
        Requirements:
            - entity_id format must follow chk_XXXXXXXX pattern if provided
            - parent_task_id must be provided for validation to pass
        """
        super().__init__(
            entity_id=entity_id,
            name=name,
            created_at=created_at,
            updated_at=updated_at,
            properties=properties
        )
        
        self._parent_task_id = parent_task_id
        self._item_ids = []
    
    def get_entity_type(self) -> EntityType:
        """
        Get the entity type.
        
        Returns:
            EntityType.CHECKLIST
        """
        return EntityType.CHECKLIST
    
    @property
    def parent_task_id(self) -> Optional[str]:
        """
        Get the parent task ID.
        
        Returns:
            ID of the task this checklist belongs to
        """
        return self._parent_task_id
    
    @property
    def item_ids(self) -> List[str]:
        """
        Get the list of item IDs.
        
        Returns:
            Copy of the list of checklist item IDs in their ordered sequence
        """
        return self._item_ids.copy()
    
    def add_item(self, item_id: str) -> bool:
        """
        Add an item ID to the checklist.
        
        Appends the item ID to the end of the items list and
        triggers the checklist.item_added hook for extensions.
        
        Args:
            item_id: ID of item to add
            
        Returns:
            True if item was added, False if it already existed
            
        Side Effects:
            - Updates updated_at timestamp via touch()
            - Triggers checklist.item_added hook
        """
        if item_id and item_id not in self._item_ids:
            self._item_ids.append(item_id)
            self.touch()
            self._trigger_hook('checklist.item_added', self, item_id)
            return True
        return False
    
    def remove_item(self, item_id: str) -> bool:
        """
        Remove an item ID from the checklist.
        
        Removes the item ID from the items list and
        triggers the checklist.item_removed hook for extensions.
        
        Args:
            item_id: ID of item to remove
            
        Returns:
            True if item was removed, False if it didn't exist
            
        Side Effects:
            - Updates updated_at timestamp via touch()
            - Triggers checklist.item_removed hook
        """
        if item_id in self._item_ids:
            self._item_ids.remove(item_id)
            self.touch()
            self._trigger_hook('checklist.item_removed', self, item_id)
            return True
        return False
    
    def move_item(self, item_id: str, new_position: int) -> bool:
        """
        Move an item to a new position in the checklist.
        
        Reorders the item list by moving an item to a specific position,
        maintaining the order of other items.
        
        Args:
            item_id: ID of item to move
            new_position: New position for the item (0-based index)
            
        Returns:
            True if item was moved, False if it doesn't exist or position is invalid
            
        Side Effects:
            - Updates updated_at timestamp via touch()
            - Triggers checklist.item_moved hook
            
        Requirements:
            - new_position must be within valid range of existing items
            - item_id must exist in the checklist
        """
        if item_id not in self._item_ids:
            return False
            
        if new_position < 0 or new_position >= len(self._item_ids):
            return False
            
        current_position = self._item_ids.index(item_id)
        if current_position == new_position:
            return True  # Already in the correct position
            
        # Move the item
        self._item_ids.remove(item_id)
        self._item_ids.insert(new_position, item_id)
        self.touch()
        
        self._trigger_hook('checklist.item_moved', self, item_id, current_position, new_position)
        return True
    
    def _validate(self, result: ValidationResult) -> None:
        """
        Perform checklist-specific validations.
        
        Ensures that the checklist has a parent task reference for
        maintaining referential integrity.
        
        Args:
            result: ValidationResult to add errors to
            
        Side Effects:
            Adds error to result if parent_task_id is missing
        """
        if not self._parent_task_id:
            result.add_error("Checklist must have a parent task")
    
    def _to_dict(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Add checklist-specific data to dictionary representation.
        
        Adds parent_task_id and the ordered list of item_ids to the
        base entity dictionary.
        
        Args:
            data: Base dictionary with common properties
            
        Returns:
            Dictionary with checklist-specific properties added
        """
        checklist_data = data.copy()
        
        checklist_data['parent_task_id'] = self._parent_task_id
        
        if self._item_ids:
            checklist_data['item_ids'] = self._item_ids.copy()
            
        return checklist_data
    
    @classmethod
    def _from_dict(cls, data: Dict[str, Any]) -> 'ChecklistEntity':
        """
        Create a ChecklistEntity from dictionary representation.
        
        Args:
            data: Dictionary representation of the checklist
            
        Returns:
            Instantiated ChecklistEntity
            
        Requirements:
            - Dictionary must contain at minimum an id and parent_task_id
            - Other fields are populated with defaults if missing
        """
        entity_id = data.get('id')
        name = data.get('name', '')
        parent_task_id = data.get('parent_task_id')
        created_at = data.get('created_at')
        updated_at = data.get('updated_at')
        properties = data.get('properties', {})
        
        # Create the checklist
        checklist = cls(
            entity_id=entity_id,
            name=name,
            parent_task_id=parent_task_id,
            created_at=created_at,
            updated_at=updated_at,
            properties=properties.copy() if properties else {}
        )
        
        # Load item IDs
        item_ids = data.get('item_ids', [])
        if item_ids:
            checklist._item_ids = item_ids.copy()
            
        return checklist 