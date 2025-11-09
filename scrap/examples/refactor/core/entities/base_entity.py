"""
Task: tsk_0fa698f3 - Update Core Module Comments
Document: refactor/core/entities/base_entity.py
dohcount: 1

Related Tasks:
    - tsk_0a733101 - Code Comments Enhancement (parent)
    - tsk_65df3554 - Update TaskType Enum (sibling)

Used By:
    - All Entity Classes: Inherit from BaseEntity to leverage common functionality
    - Repositories: Use BaseEntity methods for CRUD operations
    - Services: Use validation and serialization capabilities
    - CLI Commands: Rely on entity serialization for display

Purpose:
    Defines the abstract BaseEntity class that all domain entities extend,
    providing common functionality for identity, validation, serialization,
    property management, and hook system integration.

Requirements:
    - Must support unique ID generation for all entity types
    - Must provide validation framework for entity-specific rules
    - Must handle serialization/deserialization consistently
    - Must maintain creation and update timestamps
    - CRITICAL: Must enforce entity type enumeration for all entities
    - CRITICAL: Must trigger appropriate hooks for entity lifecycle events

Changes:
    - v1: Initial implementation with basic entity functionality
    - v2: Added property management and serialization
    - v3: Integrated with hook system for event notifications
    - v4: Enhanced validation framework with entity-specific rules
    - v5: Added support for specialized entity types like documents

Lessons Learned:
    - Proper validation at the entity level prevents data corruption
    - Hook system integration enables powerful extensibility with minimal coupling
    - Consistent serialization approach simplifies storage and API integrations
    - Timestamp management provides valuable audit trail capabilities
"""

import abc
import enum
import json
from typing import Dict, List, Any, Optional, Set, Tuple, TypeVar, Generic, Union
from datetime import datetime
import uuid
import re

# Import plugin system for hooks
from refactor.plugins.hooks.hook_system import global_hook_registry


class EntityType(enum.Enum):
    """
    Task: tsk_0fa698f3 - Update Core Module Comments
    Document: refactor/core/entities/base_entity.py
    dohcount: 1
    
    Used By:
        - BaseEntity: For entity type identification
        - Repositories: For entity filtering and querying
        - Services: For type-based operation restrictions
    
    Purpose:
        Defines all possible entity types in the system, ensuring consistent
        type identification across the application.
    
    Requirements:
        - Each entity type must have a unique string value
        - Values must be lowercase and consistent with JSON serialization
        - CRITICAL: Never remove existing enum values as they are used in stored data
    
    Changes:
        - v1: Initial implementation with core entity types
        - v2: Added checklist and comment types
        - v3: Added document and document section types
    """
    TASK = "task"
    SUBTASK = "subtask"
    LIST = "list"
    FOLDER = "folder" 
    SPACE = "space"
    CHECKLIST = "checklist"
    CHECKLIST_ITEM = "checklist_item"
    COMMENT = "comment"
    TAG = "tag"
    UNKNOWN = "unknown"
    DOCUMENT = "document"
    DOCUMENT_SECTION = "document_section"


class ValidationResult:
    """
    Task: tsk_0fa698f3 - Update Core Module Comments
    Document: refactor/core/entities/base_entity.py
    dohcount: 1
    
    Used By:
        - BaseEntity: For validation operations
        - Repositories: For pre-save validation checks
        - Services: For business rule validation
    
    Purpose:
        Encapsulates the result of a validation operation, including success/failure
        status and a collection of error messages.
    
    Requirements:
        - Must track whether validation passed overall
        - Must store and deduplicate error messages
        - Must support merging multiple validation results
        - Must be usable in boolean contexts
    
    Changes:
        - v1: Initial implementation with basic validation tracking
        - v2: Added merge capability for combining validation results
        - v3: Added factory methods for common validation scenarios
    """
    
    def __init__(self, is_valid: bool, errors: Optional[List[str]] = None):
        """
        Initialize a validation result.
        
        Args:
            is_valid: Whether the validation passed
            errors: List of error messages if validation failed
            
        Requirements:
            - Must initialize with empty error list if None provided
            - Must honor the is_valid flag regardless of errors list state
        """
        self.is_valid = is_valid
        self.errors = errors or []
    
    @property
    def has_errors(self) -> bool:
        """
        Check if there are any validation errors.
        
        Returns:
            True if there are validation errors, False otherwise
        """
        return len(self.errors) > 0
    
    def add_error(self, error: str) -> None:
        """
        Add an error message to the validation result.
        
        Adds the error to the list if it's not empty and not already present,
        and marks the validation result as invalid.
        
        Args:
            error: Error message to add
            
        Side Effects:
            - Sets is_valid to False
            - Adds error to errors list if not already present
        """
        if error and error not in self.errors:
            self.errors.append(error)
            self.is_valid = False
    
    def merge(self, other: 'ValidationResult') -> None:
        """
        Merge another validation result into this one.
        
        If the other result is invalid, this result becomes invalid and
        incorporates all unique errors from the other result.
        
        Args:
            other: ValidationResult to merge with this one
            
        Side Effects:
            - May set is_valid to False based on other result
            - May add errors from other result to this result
        """
        if not other.is_valid:
            self.is_valid = False
            for error in other.errors:
                if error not in self.errors:
                    self.errors.append(error)
    
    @classmethod
    def valid(cls) -> 'ValidationResult':
        """
        Create a valid validation result with no errors.
        
        Returns:
            A new ValidationResult instance marked as valid with empty errors
        """
        return cls(True, [])
    
    @classmethod
    def invalid(cls, error: str) -> 'ValidationResult':
        """
        Create an invalid validation result with the given error.
        
        Args:
            error: The validation error message
            
        Returns:
            A new ValidationResult instance marked as invalid with the provided error
        """
        return cls(False, [error])
    
    def __bool__(self) -> bool:
        """
        Allow using the validation result in boolean context.
        
        Returns:
            The is_valid value for direct use in if statements
        """
        return self.is_valid


T = TypeVar('T', bound='BaseEntity')


class BaseEntity(abc.ABC):
    """
    Task: tsk_0fa698f3 - Update Core Module Comments
    Document: refactor/core/entities/base_entity.py
    dohcount: 1
    
    Used By:
        - All Entity Classes: Extend this class for common functionality
        - Repositories: Use methods for entity management
        - Services: Use validation and hook capabilities
        - CLI Commands: Leverage serialization for display and storage
    
    Purpose:
        Provides the foundation for all domain entities with common functionality
        for identity, validation, serialization, properties, and hooks.
    
    Requirements:
        - Must enforce entity type identification through abstract method
        - Must provide ID generation for new entities
        - Must track creation and update timestamps
        - Must support property extension mechanism
        - Must integrate with hook system for entity lifecycle events
        - CRITICAL: Must enforce validation rules specific to each entity type
        - CRITICAL: Must ensure consistent serialization/deserialization
    
    Changes:
        - v1: Initial implementation with core entity functionality
        - v2: Added hook system integration
        - v3: Enhanced validation framework
        - v4: Added comprehensive property management
        - v5: Improved serialization with entity-specific customization
    """
    
    def __init__(self, 
                 entity_id: Optional[str] = None,
                 name: str = "",
                 created_at: Optional[int] = None,
                 updated_at: Optional[int] = None,
                 properties: Optional[Dict[str, Any]] = None):
        """
        Initialize a base entity.
        
        Args:
            entity_id: Optional ID for the entity, generated if not provided
            name: Name of the entity
            created_at: Timestamp when entity was created
            updated_at: Timestamp when entity was last updated 
            properties: Additional properties stored with the entity
            
        Side Effects:
            - Generates ID if not provided
            - Sets creation timestamp if not provided
            - Sets update timestamp to creation timestamp if not provided
            - Initializes properties dictionary
            - Triggers 'entity.created' hook
            
        Requirements:
            - entity_id must follow the pattern established by _generate_id if provided
            - created_at and updated_at must be valid Unix timestamps if provided
        """
        self._id = entity_id or self._generate_id()
        self._name = name
        self._created_at = created_at or int(datetime.now().timestamp())
        self._updated_at = updated_at or self._created_at
        self._properties = properties or {}
        
        # Call the entity creation hook
        self._trigger_hook('entity.created', self)
    
    @property
    def id(self) -> str:
        """
        Get the entity ID.
        
        Returns:
            The unique identifier string for this entity
        """
        return self._id
    
    @property
    def name(self) -> str:
        """
        Get the entity name.
        
        Returns:
            The display name of the entity
        """
        return self._name
    
    @name.setter
    def name(self, value: str) -> None:
        """
        Set the entity name.
        
        Updates the entity name and triggers the appropriate hook if changed.
        
        Args:
            value: New name for the entity
            
        Side Effects:
            - Updates entity name if different
            - Updates updated_at timestamp
            - Triggers 'entity.name_changed' hook with old and new names
        """
        if value != self._name:
            old_name = self._name
            self._name = value
            self._updated_at = int(datetime.now().timestamp())
            self._trigger_hook('entity.name_changed', self, old_name, value)
    
    @property
    def created_at(self) -> int:
        """
        Get the creation timestamp.
        
        Returns:
            Unix timestamp when the entity was created
        """
        return self._created_at
    
    @property
    def updated_at(self) -> int:
        """
        Get the last update timestamp.
        
        Returns:
            Unix timestamp when the entity was last modified
        """
        return self._updated_at
    
    def touch(self) -> None:
        """
        Update the entity's last update timestamp to now.
        
        Side Effects:
            Sets updated_at to the current timestamp
        """
        self._updated_at = int(datetime.now().timestamp())
    
    @property
    def properties(self) -> Dict[str, Any]:
        """
        Get all custom properties for the entity.
        
        Returns:
            A copy of the properties dictionary to prevent direct modification
        """
        return self._properties.copy()
    
    def get_property(self, key: str, default: Any = None) -> Any:
        """
        Get a specific property value.
        
        Args:
            key: Property key to retrieve
            default: Default value if property doesn't exist
            
        Returns:
            The property value or default
        """
        return self._properties.get(key, default)
    
    def set_property(self, key: str, value: Any) -> None:
        """
        Set a specific property value.
        
        Updates or adds a property and updates the entity's timestamp.
        
        Args:
            key: Property key to set
            value: Value to store for the property
            
        Side Effects:
            - Updates properties dictionary
            - Updates updated_at timestamp
            - Triggers 'entity.property_changed' hook
        """
        old_value = self._properties.get(key)
        if old_value != value:
            self._properties[key] = value
            self._updated_at = int(datetime.now().timestamp())
            self._trigger_hook('entity.property_changed', self, key, old_value, value)
    
    def remove_property(self, key: str) -> bool:
        """
        Remove a property if it exists.
        
        Args:
            key: Property key to remove
            
        Returns:
            True if property was removed, False if it didn't exist
        """
        if key in self._properties:
            old_value = self._properties.pop(key)
            self._updated_at = int(datetime.now().timestamp())
            self._trigger_hook('entity.property_removed', self, key, old_value)
            return True
        return False
    
    @abc.abstractmethod
    def get_entity_type(self) -> EntityType:
        """
        Get the entity type.
        
        Returns:
            EntityType enum value representing this entity's type
        """
        pass
    
    def validate(self) -> ValidationResult:
        """
        Validate the entity.
        
        This basic implementation just validates that the ID and name are present.
        Subclasses should override and extend this to validate specific properties.
        
        Returns:
            ValidationResult indicating whether the entity is valid
        """
        result = ValidationResult.valid()
        
        # ID must be present
        if not self._id:
            result.add_error("Entity ID is required")
        
        # Name must be present for most entity types
        if not self._name and self.get_entity_type() != EntityType.CHECKLIST_ITEM:
            result.add_error("Entity name is required")
        
        # Run additional validations defined by subclasses
        self._validate(result)
        
        # Run validation hooks
        self._trigger_hook('entity.validated', self, result)
        
        return result
    
    @abc.abstractmethod
    def _validate(self, result: ValidationResult) -> None:
        """
        Perform entity-specific validations.
        
        Subclasses should implement this to add their specific validation logic.
        
        Args:
            result: ValidationResult to add errors to
        """
        pass
    
    def to_dict(self) -> Dict[str, Any]:
        """
        Convert entity to dictionary representation.
        
        Returns:
            Dictionary representation of the entity
        """
        # Start with common properties
        data = {
            'id': self._id,
            'name': self._name,
            'created_at': self._created_at,
            'updated_at': self._updated_at,
            'type': self.get_entity_type().value,
        }
        
        # Add custom properties
        if self._properties:
            data['properties'] = self._properties.copy()
            
        # Call hook to allow plugins to modify dictionary
        modified_data = data.copy()
        self._trigger_hook('entity.to_dict', self, modified_data)
        
        # Add entity-specific data
        result = self._to_dict(modified_data)
        
        return result
    
    @abc.abstractmethod
    def _to_dict(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Add entity-specific data to dictionary representation.
        
        Subclasses should implement this to add their specific properties.
        
        Args:
            data: Base dictionary with common properties
            
        Returns:
            Dictionary with entity-specific properties added
        """
        pass
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'BaseEntity':
        """
        Create an entity from dictionary representation.
        
        Args:
            data: Dictionary representation of the entity
            
        Returns:
            Instantiated entity of the appropriate type
        """
        # Allow plugins to modify the data before entity creation
        modified_data = data.copy()
        try:
            global_hook_registry.execute_hook('entity.from_dict', None, modified_data)
        except KeyError:
            # Hook doesn't exist, silently continue
            pass
        except Exception as e:
            # Log other errors but don't fail
            import logging
            logging.getLogger(__name__).warning(f"Error executing hook entity.from_dict: {str(e)}")
        
        # Delegate to the class-specific implementation
        # This allows subclasses to handle their specific fields
        instance = cls._from_dict(modified_data)
        
        # Call hook after entity is loaded
        try:
            global_hook_registry.execute_hook('entity.loaded', None, instance, modified_data)
        except KeyError:
            # Hook doesn't exist, silently continue
            pass
        except Exception as e:
            # Log other errors but don't fail
            import logging
            logging.getLogger(__name__).warning(f"Error executing hook entity.loaded: {str(e)}")
        
        return instance
    
    @classmethod
    @abc.abstractmethod
    def _from_dict(cls, data: Dict[str, Any]) -> 'BaseEntity':
        """
        Populate entity-specific fields from dictionary representation.
        
        Subclasses should implement this to handle their specific properties.
        
        Args:
            data: Dictionary representation of the entity
            
        Returns:
            Instantiated entity
        """
        pass
    
    def _generate_id(self) -> str:
        """
        Generate a unique ID for the entity.
        
        Returns:
            New unique ID string
        """
        # Generate a UUID and format it as a short, URL-safe string
        # Format: 3-letter type prefix + 8 character hex
        entity_type_prefix = self.get_entity_type().value[:3]
        random_part = uuid.uuid4().hex[:8]
        return f"{entity_type_prefix}_{random_part}"
    
    def _trigger_hook(self, hook_name: str, *args, **kwargs) -> Any:
        """
        Trigger a hook for this entity.
        
        Args:
            hook_name: Name of the hook to trigger
            *args: Positional arguments to pass to the hook
            **kwargs: Keyword arguments to pass to the hook
            
        Returns:
            Result from the hook execution, if any
        """
        try:
            return global_hook_registry.execute_hook(hook_name, None, *args, **kwargs)
        except KeyError:
            # Hook doesn't exist, silently continue
            return None
        except Exception as e:
            # Log other errors but don't fail
            import logging
            logging.getLogger(__name__).warning(f"Error executing hook {hook_name}: {str(e)}")
            return None
    
    def __eq__(self, other: Any) -> bool:
        """
        Check if this entity equals another.
        
        Entities are considered equal if they have the same ID.
        
        Args:
            other: Entity to compare with
            
        Returns:
            True if entities are equal, False otherwise
        """
        if not isinstance(other, BaseEntity):
            return False
        return self._id == other._id
    
    def __hash__(self) -> int:
        """
        Generate a hash for the entity.
        
        Returns:
            Hash value based on the entity ID
        """
        return hash(self._id)
    
    def __str__(self) -> str:
        """
        Get string representation of the entity.
        
        Returns:
            String representation
        """
        return f"{self.get_entity_type().value}({self._id}): {self._name}"
    
    def __repr__(self) -> str:
        """
        Get debug representation of the entity.
        
        Returns:
            Debug representation
        """
        return f"{self.__class__.__name__}(id='{self._id}', name='{self._name}')" 