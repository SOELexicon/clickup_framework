"""
Task Entity Module

This module defines the TaskEntity class and related enums that represent the core
data model for tasks in the ClickUp JSON Manager.
"""
from enum import Enum, auto
from typing import List, Dict, Any, Optional, Union
from datetime import datetime
from refactor.core.entities.document_section_entity import DocumentSection, SectionType, DocumentFormat
from refactor.core.entities.task_type import TaskType  # Import the new TaskType
from dataclasses import dataclass, field


class RelationshipType(Enum):
    """Enumeration of possible task relationship types."""
    
    DEPENDS_ON = "depends_on"  # This task depends on the target task
    BLOCKS = "blocks"          # This task blocks the target task
    RELATED_TO = "related_to"  # This task is related to the target task
    DOCUMENTS = "documents"    # This task documents the target task
    DOCUMENTED_BY = "documented_by"  # This task is documented by the target task
    
    @classmethod
    def from_string(cls, rel_type_str: str) -> 'RelationshipType':
        """
        Convert a string to a RelationshipType enum value.
        
        Args:
            rel_type_str: The relationship type string to convert
            
        Returns:
            The corresponding RelationshipType enum value
            
        Raises:
            ValueError: If the string does not match any relationship type
        """
        if not rel_type_str:
            raise ValueError("Relationship type cannot be empty")
            
        rel_type_map = {
            "depends_on": cls.DEPENDS_ON,
            "blocks": cls.BLOCKS,
            "related_to": cls.RELATED_TO,
            "documents": cls.DOCUMENTS,
            "documented_by": cls.DOCUMENTED_BY
        }
        
        lower_rel_type = rel_type_str.lower()
        if lower_rel_type not in rel_type_map:
            valid_rel_types = ", ".join(rel_type_map.keys())
            raise ValueError(f"Invalid relationship type: '{rel_type_str}'. Valid types are: {valid_rel_types}")
        
        return rel_type_map[lower_rel_type]
    
    @property
    def inverse(self) -> 'RelationshipType':
        """
        Get the inverse relationship type.
        
        Returns:
            The inverse relationship type
            
        Example:
            DEPENDS_ON.inverse returns BLOCKS
            DOCUMENTS.inverse returns DOCUMENTED_BY
        """
        inverse_map = {
            self.DEPENDS_ON: self.BLOCKS,
            self.BLOCKS: self.DEPENDS_ON,
            self.RELATED_TO: self.RELATED_TO,
            self.DOCUMENTS: self.DOCUMENTED_BY,
            self.DOCUMENTED_BY: self.DOCUMENTS
        }
        
        return inverse_map[self]


class ValidationResult:
    """
    Represents the result of entity validation.
    
    Attributes:
        is_valid: Whether the entity is valid
        errors: List of validation error messages
    """
    
    def __init__(self, is_valid: bool, errors: List[str] = None):
        """
        Initialize a validation result.
        
        Args:
            is_valid: Whether the entity is valid
            errors: List of validation error messages, defaults to empty list
        """
        self.is_valid = is_valid
        self.errors = errors or []
    
    def add_error(self, error: str) -> None:
        """
        Add an error message to the validation result.
        
        Args:
            error: The error message to add
        """
        self.errors.append(error)
        self.is_valid = False
    
    def __bool__(self) -> bool:
        """Allow using the validation result in boolean contexts."""
        return self.is_valid
    
    def __str__(self) -> str:
        """Get a string representation of the validation result."""
        if self.is_valid:
            return "Valid"
        return f"Invalid: {'; '.join(self.errors)}"


class TaskStatus(Enum):
    """Enumeration of possible task statuses."""
    
    TO_DO = 1
    IN_PROGRESS = 2
    COMPLETE = 3
    
    @classmethod
    def from_string(cls, status_str: str) -> 'TaskStatus':
        """
        Convert a string to a TaskStatus enum value.
        
        Args:
            status_str: The status string to convert
            
        Returns:
            The corresponding TaskStatus enum value
            
        Raises:
            ValueError: If the string does not match any status
        """
        if isinstance(status_str, TaskStatus):
            return status_str
            
        status_map = {
            "to do": cls.TO_DO,
            "todo": cls.TO_DO,
            "in progress": cls.IN_PROGRESS,
            "inprogress": cls.IN_PROGRESS,
            "in_progress": cls.IN_PROGRESS,  # Added to handle underscores
            "complete": cls.COMPLETE,
            "completed": cls.COMPLETE,
            "done": cls.COMPLETE
        }
        
        # Handle case insensitivity by converting to lowercase
        if isinstance(status_str, str):
            lower_status = status_str.lower()
            # Handle direct enum name matching (like "IN_PROGRESS" → "in_progress")
            if lower_status not in status_map:
                # Try converting enum name format to status format
                for enum_member in cls:
                    if lower_status == enum_member.name.lower() or lower_status == str(enum_member.value):
                        return enum_member
                
                # If still not found, raise error
                valid_statuses = ", ".join(status_map.keys())
                raise ValueError(f"Invalid status: '{status_str}'. Valid statuses are: {valid_statuses}")
            
            return status_map[lower_status]
        elif isinstance(status_str, int):
            # If an integer is provided, use from_int
            return cls.from_int(status_str)
        else:
            raise ValueError(f"Invalid status type: {type(status_str).__name__}")
    
    @classmethod
    def from_int(cls, status_int: int) -> 'TaskStatus':
        """
        Convert an integer to a TaskStatus enum value.
        
        Args:
            status_int: The status integer to convert
            
        Returns:
            The corresponding TaskStatus enum value
            
        Raises:
            ValueError: If the integer does not match any status
        """
        for status in cls:
            if status.value == status_int:
                return status
        
        valid_values = ", ".join(str(status.value) for status in cls)
        raise ValueError(f"Invalid status value: {status_int}. Valid values are: {valid_values}")


class TaskPriority(Enum):
    """Enumeration of possible task priorities."""
    
    URGENT = 1
    HIGH = 2
    NORMAL = 3
    LOW = 4
    
    @classmethod
    def from_string(cls, priority_str: str) -> 'TaskPriority':
        """
        Convert a string to a TaskPriority enum value.
        
        Args:
            priority_str: The priority string to convert
            
        Returns:
            The corresponding TaskPriority enum value
            
        Raises:
            ValueError: If the string does not match any priority
        """
        if isinstance(priority_str, TaskPriority):
            return priority_str
            
        priority_map = {
            "urgent": cls.URGENT,
            "critical": cls.URGENT,
            "high": cls.HIGH,
            "normal": cls.NORMAL,
            "medium": cls.NORMAL,
            "low": cls.LOW
        }
        
        # Handle case insensitivity by converting to lowercase
        if isinstance(priority_str, str):
            lower_priority = priority_str.lower()
            # Handle direct enum name matching
            if lower_priority not in priority_map:
                # Try converting enum name format to priority format
                for enum_member in cls:
                    if lower_priority == enum_member.name.lower() or lower_priority == str(enum_member.value):
                        return enum_member
                
                # If still not found, raise error
                valid_priorities = ", ".join(priority_map.keys())
                raise ValueError(f"Invalid priority: '{priority_str}'. Valid priorities are: {valid_priorities}")
            
            return priority_map[lower_priority]
        elif isinstance(priority_str, int):
            # If an integer is provided, use from_int
            return cls.from_int(priority_str)
        else:
            raise ValueError(f"Invalid priority type: {type(priority_str).__name__}")
    
    @classmethod
    def from_int(cls, priority_int: int) -> 'TaskPriority':
        """
        Convert an integer to a TaskPriority enum value.
        
        Args:
            priority_int: The priority integer to convert
            
        Returns:
            The corresponding TaskPriority enum value
            
        Raises:
            ValueError: If the integer does not match any priority
        """
        for priority in cls:
            if priority.value == priority_int:
                return priority
        
        valid_values = ", ".join(str(priority.value) for priority in cls)
        raise ValueError(f"Invalid priority value: {priority_int}. Valid values are: {valid_values}")


@dataclass
class StatusHistoryEntry:
    """Represents a single entry in the task status history."""
    from_status: TaskStatus
    to_status: TaskStatus
    timestamp: datetime
    comment: str = ""

    def to_dict(self) -> Dict[str, Any]:
        """Serialize the history entry to a dictionary."""
        return {
            "from_status": self.from_status.name, # Store enum name
            "to_status": self.to_status.name,   # Store enum name
            "timestamp": self.timestamp.isoformat(),
            "comment": self.comment
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'StatusHistoryEntry':
        """Deserialize a history entry from a dictionary."""
        return cls(
            from_status=TaskStatus[data['from_status']], # Create enum from name
            to_status=TaskStatus[data['to_status']],   # Create enum from name
            timestamp=datetime.fromisoformat(data['timestamp']),
            comment=data.get('comment', '')
        )


class TaskEntity:
    """
    Represents a task entity with properties, relationships, and behavior.
    
    The TaskEntity is the core data model for tasks in the ClickUp JSON Manager,
    providing methods for task manipulation, validation, and serialization.
    """
    
    def __init__(
        self,
        name: str,
        entity_id: Optional[str] = None,
        task_id: Optional[str] = None,
        description: str = "",
        status: Union[str, int, TaskStatus] = "to do",
        priority: Union[str, int, TaskPriority] = "normal",
        parent_id: Optional[str] = None,
        is_parent: bool = False,  # New field for parent status
        container_id: Optional[str] = None,  # New field for container assignment
        tags: Optional[List[str]] = None,
        due_date: Optional[str] = None,
        created_at: Optional[Union[str, datetime]] = None,
        updated_at: Optional[Union[str, datetime]] = None,
        completed_at: Optional[Union[str, datetime]] = None,
        start_date: Optional[Union[str, datetime]] = None,
        comments: Optional[List[Dict[str, Any]]] = None,
        subtasks: Optional[List['TaskEntity']] = None,
        space: Optional[str] = None,
        folder: Optional[str] = None,
        list_name: Optional[str] = None,
        assigned_to: Optional[List[str]] = None,
        metadata: Optional[Dict[str, Any]] = None,
        checklist: Optional[Dict[str, Any]] = None,
        relationships: Optional[Dict[str, List[str]]] = None,
        task_type: Optional[Union[str, TaskType]] = None,
        document_section: Optional[Union[str, DocumentSection]] = None,
        format: Optional[str] = None,
        target_audience: Optional[List[str]] = None,
        status_history: Optional[List[Dict[str, Any]]] = None,
    ):
        """
        Initialize a new TaskEntity instance.
        
        Args:
            name: Task name (required)
            entity_id: Unique task ID (optional, will be generated if not provided)
            task_id: Alternative field for ID (for backward compatibility)
            description: Task description
            status: Task status (string, integer, or TaskStatus enum)
            priority: Task priority (string, integer, or TaskPriority enum)
            parent_id: ID of parent task, if this is a subtask
            is_parent: Boolean indicating if this is a top-level task with no parent
            container_id: ID of container task, if this is a subtask
            tags: List of tags associated with the task
            due_date: Due date for the task
            created_at: Task creation timestamp
            updated_at: Task last update timestamp
            completed_at: Task completion timestamp
            start_date: Task start date
            comments: List of comment dictionaries
            subtasks: List of TaskEntity objects that are subtasks of this task
            space: Name of the space the task belongs to
            folder: Name of the folder the task belongs to
            list_name: Name of the list the task belongs to
            assigned_to: List of users assigned to the task
            metadata: Additional custom data for the task
            checklist: Dictionary containing checklist items and states
            relationships: Dictionary of relationship types to lists of related task IDs
            task_type: Type of task (regular task, bug, feature, etc.)
            document_section: If task is a documentation task, the section it documents
            format: Format for documentation (e.g., markdown, html)
            target_audience: Target audience for the task output
            status_history: List of status history entries
        """
        # Set basic properties
        self._name = name
        self._id = entity_id or task_id or f"tsk_{hash(name) & 0xffffffff:08x}"
        self._description = description
        
        # Set task type
        self._task_type = TaskType.TASK
        if task_type:
            self._task_type = task_type if isinstance(task_type, TaskType) else TaskType.from_string(task_type)
        
        # Set status and priority
        if isinstance(status, TaskStatus):
            self._status = status
        else:
            self._status = TaskStatus.from_string(status)
            
        if isinstance(priority, TaskPriority):
            self._priority = priority
        else:
            self._priority = TaskPriority.from_string(priority)
        
        # Set timestamps
        # Convert string timestamps to datetime objects if needed
        if created_at is None:
            self._created_at = datetime.now()
        elif isinstance(created_at, str):
            try:
                self._created_at = datetime.fromisoformat(created_at.replace('Z', '+00:00'))
            except ValueError:
                # If parsing fails, use current time
                self._created_at = datetime.now()
        else:
            self._created_at = created_at
            
        if updated_at is None:
            self._updated_at = self._created_at
        elif isinstance(updated_at, str):
            try:
                self._updated_at = datetime.fromisoformat(updated_at.replace('Z', '+00:00'))
            except ValueError:
                # If parsing fails, use current time
                self._updated_at = datetime.now()
        else:
            self._updated_at = updated_at
        
        # Set completion timestamp
        if completed_at is None:
            self._completed_at = None
        elif isinstance(completed_at, str):
            try:
                self._completed_at = datetime.fromisoformat(completed_at.replace('Z', '+00:00'))
            except ValueError:
                # If parsing fails, set to None
                self._completed_at = None
        else:
            self._completed_at = completed_at
        
        # Set start date
        if start_date is None:
            self._start_date = None
        elif isinstance(start_date, str):
            try:
                self._start_date = datetime.fromisoformat(start_date.replace('Z', '+00:00'))
            except ValueError:
                # If parsing fails, set to None
                self._start_date = None
        else:
            self._start_date = start_date
        
        # Set references
        self._parent_id = parent_id
        self._is_parent = is_parent  # New field initialization
        self._container_id = container_id  # New container_id initialization
        
        # Set collections
        self._tags = tags or []
        self._comments = comments or []
        self._subtasks = subtasks or []
        self._assigned_to = assigned_to or []
        self._target_audience = target_audience or []
        
        # Add relationships
        self._relationships = relationships or {}
        # Ensure all relationship types exist (even empty)
        self._blocks = self._relationships.get('blocks', [])
        # Handle both 'depends_on' and 'blocked_by' for depends_on list
        self._depends_on = self._relationships.get('depends_on', self._relationships.get('blocked_by', []))
        self._related_to = self._relationships.get('related_to', [])
        
        # Set metadata
        self._metadata = metadata or {}
        self._due_date = due_date
        self._space = space
        self._folder = folder
        self._list_name = list_name
        
        # Set documentation-specific properties
        self._document_section = document_section
        self._format = format
        
        # Set checklist
        self._checklist = checklist or {"name": "Default Checklist", "items": []}
        
        # Initialize status history
        self._status_history: List[StatusHistoryEntry] = [
            StatusHistoryEntry.from_dict(entry) for entry in status_history
        ] if status_history else []
        
        # Ensure initial status has a history entry if history is empty
        if not self._status_history and self.status:
             # Add an initial entry if created with a status but no history
             initial_entry = StatusHistoryEntry(
                 from_status=self.status, # Use current status as from/to for initial
                 to_status=self.status,
                 timestamp=self.created_at or datetime.now(),
                 comment="Task created"
             )
             self._status_history.append(initial_entry)
    
    @property
    def id(self) -> str:
        """Get the task ID."""
        return self._id
        
    @property
    def task_type(self) -> TaskType:
        """Get the task type."""
        return self._task_type
    
    @task_type.setter
    def task_type(self, value: Union[str, TaskType]) -> None:
        """Set the task type."""
        if isinstance(value, TaskType):
            self._task_type = value
        else:
            self._task_type = TaskType.from_string(value)
    
    @property
    def document_section(self) -> Optional[DocumentSection]:
        """Get the document section."""
        return self._document_section
    
    @document_section.setter
    def document_section(self, value: Union[str, DocumentSection, None]) -> None:
        """Set the document section."""
        if value is None:
            self._document_section = None
        elif isinstance(value, DocumentSection):
            self._document_section = value
        else:
            try:
                self._document_section = DocumentSection.from_string(value)
            except (ValueError, AttributeError):
                # If conversion fails, set section type directly
                self._document_section = DocumentSection(
                    section_type=SectionType.OTHER,
                    name=value,
                    description=f"Custom section: {value}"
                )
    
    @property
    def format(self) -> str:
        """Get the document format."""
        return self._format
    
    @format.setter
    def format(self, value: str) -> None:
        """Set the document format."""
        self._format = value
    
    @property
    def target_audience(self) -> List[str]:
        """Get the target audience."""
        return self._target_audience
    
    @target_audience.setter
    def target_audience(self, value: List[str]) -> None:
        """Set the target audience."""
        self._target_audience = value
    
    def validate(self) -> ValidationResult:
        """
        Validate the task entity.
        
        Returns:
            ValidationResult object indicating whether the entity is valid
        """
        result = ValidationResult(True)
        
        # Validate required fields
        if not self._name:
            result.add_error("Task name is required")
        
        # Validate ID format
        if not self._id:
            result.add_error("Task ID is required")
        elif not (self._id.startswith("tsk_") or self._id.startswith("stk_")):
            result.add_error("Task ID must start with 'tsk_' or 'stk_'")
        
        # Validate status and priority are of correct enum types
        if not isinstance(self._status, TaskStatus):
            result.add_error(f"Task status must be a TaskStatus enum, got {type(self._status)}")
        
        if not isinstance(self._priority, TaskPriority):
            result.add_error(f"Task priority must be a TaskPriority enum, got {type(self._priority)}")
        
        # Validate task type
        if not isinstance(self._task_type, TaskType):
            result.add_error(f"Task type must be a TaskType enum, got {type(self._task_type)}")
        
        # Validate collections contain correct types
        if not all(isinstance(tag, str) for tag in self._tags):
            result.add_error("All tags must be strings")
        
        if not all(isinstance(comment, dict) for comment in self._comments):
            result.add_error("All comments must be dictionaries")
        
        # Validate relationship types
        for rel_type, rel_ids in self._relationships.items():
            try:
                RelationshipType.from_string(rel_type)
            except ValueError as e:
                result.add_error(str(e))
            
            if not all(isinstance(rel_id, str) for rel_id in rel_ids):
                result.add_error(f"All {rel_type} relationship IDs must be strings")
        
        # Validate parent/child relationship consistency
        if self._is_parent and self._parent_id is not None:
            result.add_error("Task cannot be marked as parent if it has a parent_id")
        
        # Validate container_id format if provided
        if self._container_id and not (
            self._container_id.startswith("lst_") or
            self._container_id.startswith("fld_") or
            self._container_id.startswith("spc_")
        ):
            result.add_error("Container ID must start with 'lst_', 'fld_', or 'spc_'")
        
        return result
    
    def to_dict(self) -> Dict[str, Any]:
        """
        Convert the task entity to a dictionary.
        
        Returns:
            Dictionary representation of the task entity
        """
        # Format timestamps for serialization
        created_at_iso = self._created_at.isoformat() if self._created_at else None
        updated_at_iso = self._updated_at.isoformat() if self._updated_at else None
        completed_at_iso = self._completed_at.isoformat() if self._completed_at else None
        start_date_iso = self._start_date.isoformat() if hasattr(self, '_start_date') and self._start_date else None
        
        # Build relationship dictionary for serialization
        relationships = {}
        if self._blocks:
            relationships['blocks'] = self._blocks
        if self._depends_on:
            relationships['depends_on'] = self._depends_on
        if self._related_to:
            relationships['related_to'] = self._related_to
        
        # Build the dictionary representation
        result = {
            'id': self._id,
            'name': self._name,
            'description': self._description,
            'status': self._status.name, # Use enum name for status
            'priority': self._priority.name, # Use enum name for priority
            'parent_id': self._parent_id,
            'is_parent': self._is_parent,  # Include is_parent in dictionary
            'container_id': self._container_id,  # Include container_id in dictionary
            'tags': self._tags,
            'created_at': created_at_iso,
            'updated_at': updated_at_iso,
            'type': self._task_type.value
        }
        
        # Add completed_at only if it has a value
        if self._completed_at:
            result['completed_at'] = completed_at_iso
            
        # Add start_date only if it has a value
        if hasattr(self, '_start_date') and self._start_date:
            result['start_date'] = start_date_iso
        
        # Add optional fields only if they have values
        if self._due_date:
            result['due_date'] = self._due_date
            
        if self._space:
            result['space'] = self._space
            
        if self._folder:
            result['folder'] = self._folder
            
        if self._list_name:
            result['list'] = self._list_name
            
        if self._assigned_to:
            result['assigned_to'] = self._assigned_to
            
        if self._metadata:
            result['metadata'] = self._metadata
            
        if self._checklist and (self._checklist.get('items') or self._checklist.get('name') != "Default Checklist"):
            result['checklist'] = self._checklist
            
        if relationships:
            result['relationships'] = relationships
            
        if self._document_section:
            result['document_section'] = self._document_section.to_dict() if hasattr(self._document_section, 'to_dict') else str(self._document_section)
            
        if self._format:
            result['format'] = self._format
            
        if self._target_audience:
            result['target_audience'] = self._target_audience
        
        # Add status history
        result['status_history'] = [entry.to_dict() for entry in self._status_history]
        
        return result
    
    @property
    def start_date(self) -> Optional[datetime]:
        """Get the task start date timestamp."""
        return self._start_date

    @property
    def completed_at(self) -> Optional[datetime]:
        """Get the task completion timestamp."""
        return self._completed_at

    @classmethod
    def from_dict(cls, task_dict: Dict[str, Any]) -> 'TaskEntity':
        """
        Create a task entity from a dictionary.
        
        Args:
            task_dict: Dictionary representation of a task entity
            
        Returns:
            New TaskEntity instance
        """
        # Extract basic fields with defaults
        task_id = task_dict.get('id')
        name = task_dict.get('name', '')
        description = task_dict.get('description', '')
        
        # Handle status and priority - they might be strings, integers, or already converted enums
        status_value = task_dict.get('status', TaskStatus.TO_DO)
        if isinstance(status_value, int):
            status = TaskStatus.from_int(status_value)
        else:
            status = status_value
            
        priority_value = task_dict.get('priority', TaskPriority.NORMAL)
        if isinstance(priority_value, int):
            priority = TaskPriority.from_int(priority_value)
        else:
            priority = priority_value
        
        # Extract references
        parent_id = task_dict.get('parent_id')
        is_parent = task_dict.get('is_parent', False)  # Default to False if not specified
        container_id = task_dict.get('container_id')  # Extract container_id
        
        # Extract collections
        tags = task_dict.get('tags', [])
        comments = task_dict.get('comments', [])
        
        # Extract timestamps
        created_at = task_dict.get('created_at')
        updated_at = task_dict.get('updated_at')
        completed_at = task_dict.get('completed_at')
        start_date = task_dict.get('start_date')
        
        # Extract relationships
        relationships = task_dict.get('relationships', {})
        
        # Extract metadata
        due_date = task_dict.get('due_date')
        space = task_dict.get('space')
        folder = task_dict.get('folder')
        list_name = task_dict.get('list')
        assigned_to = task_dict.get('assigned_to', [])
        metadata = task_dict.get('metadata', {})
        checklist = task_dict.get('checklist', {})
        
        # Extract documentation-specific properties
        task_type_value = task_dict.get('type', 'task')
        task_type = TaskType.from_string(task_type_value)
        
        document_section_value = task_dict.get('document_section')
        document_section = None
        if document_section_value:
            if isinstance(document_section_value, dict):
                # TODO: Convert dict to DocumentSection object
                document_section = document_section_value
            else:
                document_section = document_section_value
        
        format_value = task_dict.get('format')
        target_audience = task_dict.get('target_audience', [])
        
        # Extract status history
        status_history_data = task_dict.get('status_history')
        
        # Create and return the entity
        return cls(
            name=name,
            entity_id=task_id,
            description=description,
            status=status,
            priority=priority,
            parent_id=parent_id,
            is_parent=is_parent,
            container_id=container_id,  # Pass container_id to constructor
            tags=tags,
            due_date=due_date,
            created_at=created_at,
            updated_at=updated_at,
            completed_at=completed_at,
            start_date=start_date,
            comments=comments,
            space=space,
            folder=folder,
            list_name=list_name,
            assigned_to=assigned_to,
            metadata=metadata,
            checklist=checklist,
            relationships=relationships,
            task_type=task_type,
            document_section=document_section,
            format=format_value,
            target_audience=target_audience,
            status_history=status_history_data,
        )
    
    def __eq__(self, other: object) -> bool:
        """
        Check if this task is equal to another task.
        
        Args:
            other: Another object to compare with this task
            
        Returns:
            True if the tasks are equal (based on ID only), False otherwise
        """
        if not isinstance(other, TaskEntity):
            return False
        
        # Two tasks are equal if they have the same ID
        return self.id == other.id # Compare only ID
    
    def __hash__(self) -> int:
        """Get a hash for this task entity."""
        return hash((self.id, self._name))
    
    def __str__(self) -> str:
        """Get a string representation of this task entity."""
        return f"Task(id={self.id}, name={self._name}, status={self._status.name})"
    
    # Property getters and setters
    @property
    def name(self) -> str:
        """Get the task name."""
        return self._name
    
    @name.setter
    def name(self, value: str) -> None:
        """Set the task name and update timestamp."""
        self._name = value
        self._updated_at = datetime.now()
    
    @property
    def description(self) -> str:
        """Get the task description."""
        return self._description
    
    @description.setter
    def description(self, value: str) -> None:
        """Set the task description and update timestamp."""
        self._description = value
        self._updated_at = datetime.now()
    
    @property
    def status(self) -> TaskStatus:
        """Get the task status."""
        return self._status
    
    @status.setter
    def status(self, value: Union[str, int, TaskStatus]) -> None:
        """Set the task status."""
        old_status = self._status
        new_status = TaskStatus.from_string(value) if isinstance(value, (str, int)) else value
        if new_status != old_status:
            self._status = new_status
            if new_status == TaskStatus.COMPLETE:
                self._completed_at = datetime.now()
            else:
                self._completed_at = None # Clear completion date if moving away from complete
            self._updated_at = datetime.now()
            
            # Add status history entry
            new_entry = StatusHistoryEntry(
                from_status=old_status,
                to_status=self._status,
                timestamp=datetime.now(),
                comment=f"Status changed from {old_status.name} to {self._status.name}"
            )
            self.add_status_history_entry(new_entry)
    
    @property
    def priority(self) -> TaskPriority:
        """Get the task priority."""
        return self._priority
    
    @priority.setter
    def priority(self, value: Union[str, int, TaskPriority]) -> None:
        """Set the task priority and update timestamp."""
        if isinstance(value, TaskPriority):
            self._priority = value
        else:
            self._priority = TaskPriority.from_string(value)
        self._updated_at = datetime.now()
    
    @property
    def parent_id(self) -> Optional[str]:
        """Get the parent task ID."""
        return self._parent_id
    
    @parent_id.setter
    def parent_id(self, value: Optional[str]) -> None:
        """Set the parent task ID and update timestamp."""
        self._parent_id = value
        self._updated_at = datetime.now()
    
    @property
    def container_id(self) -> Optional[str]:
        """Get the container ID."""
        return self._container_id
    
    @container_id.setter
    def container_id(self, value: Optional[str]) -> None:
        """Set the container ID and update timestamp."""
        self._container_id = value
        self._updated_at = datetime.now()
    
    @property
    def tags(self) -> List[str]:
        """Get the task tags."""
        return self._tags
    
    @tags.setter
    def tags(self, value: List[str]) -> None:
        """Set the task tags and update timestamp."""
        self._tags = value
        self._updated_at = datetime.now()
    
    @property
    def created_at(self) -> datetime:
        """Get the task creation timestamp."""
        return self._created_at
    
    @property
    def updated_at(self) -> datetime:
        """Get the task update timestamp."""
        return self._updated_at
    
    @property
    def comments(self) -> List[Dict[str, Any]]:
        """Get the task comments."""
        return self._comments
    
    @property
    def blocks(self) -> List[str]:
        """Get the list of task IDs that this task blocks."""
        return self._blocks
    
    @property
    def depends_on(self) -> List[str]:
        """Get the list of task IDs that this task depends on."""
        return self._depends_on
    
    @property
    def related_to(self) -> List[str]:
        """Get the list of task IDs that this task is related to."""
        return self._related_to
    
    def add_tag(self, tag: str) -> None:
        """
        Add a tag to the task.
        
        Args:
            tag: The tag to add
        """
        if tag not in self._tags:
            self._tags.append(tag)
            self._updated_at = datetime.now()
    
    def remove_tag(self, tag: str) -> None:
        """
        Remove a tag from the task.
        
        Args:
            tag: The tag to remove
        """
        if tag in self._tags:
            self._tags.remove(tag)
            self._updated_at = datetime.now()
    
    def add_comment(self, content: str, author: str = None) -> Dict[str, Any]:
        """
        Add a comment to the task.
        
        Args:
            content: The comment content
            author: The comment author
            
        Returns:
            The created comment dictionary
        """
        comment_id = f"cmt_{hash(content + str(datetime.now())) & 0xffffffff:08x}"
        comment = {
            "id": comment_id,
            "content": content,
            "author": author or "Unknown",
            "created_at": datetime.now().isoformat()
        }
        
        self._comments.append(comment)
        self._updated_at = datetime.now()
        
        return comment
    
    def add_relationship(self, rel_type: Union[str, RelationshipType], task_id: str) -> None:
        """
        Add a relationship to another task.
        
        Args:
            rel_type: The relationship type
            task_id: The ID of the related task
        """
        if isinstance(rel_type, str):
            rel_type = RelationshipType.from_string(rel_type)
        
        rel_name = rel_type.value
        
        # Ensure the relationship list exists
        if rel_name not in self._relationships:
            self._relationships[rel_name] = []
        
        # Add the related task ID if not already present
        if task_id not in self._relationships[rel_name]:
            self._relationships[rel_name].append(task_id)
            
            # Update the appropriate relationship property
            if rel_name == 'blocks':
                self._blocks = self._relationships[rel_name]
            elif rel_name == 'depends_on':
                self._depends_on = self._relationships[rel_name]
            elif rel_name == 'related_to':
                self._related_to = self._relationships[rel_name]
            
            self._updated_at = datetime.now()
    
    def remove_relationship(self, rel_type: Union[str, RelationshipType], task_id: str) -> None:
        """
        Remove a relationship to another task.
        
        Args:
            rel_type: The relationship type
            task_id: The ID of the related task
        """
        if isinstance(rel_type, str):
            rel_type = RelationshipType.from_string(rel_type)
        
        rel_name = rel_type.value
        
        # Remove the related task ID if present
        if rel_name in self._relationships and task_id in self._relationships[rel_name]:
            self._relationships[rel_name].remove(task_id)
            
            # Update the appropriate relationship property
            if rel_name == 'blocks':
                self._blocks = self._relationships[rel_name]
            elif rel_name == 'depends_on':
                self._depends_on = self._relationships[rel_name]
            elif rel_name == 'related_to':
                self._related_to = self._relationships[rel_name]
            
            self._updated_at = datetime.now()
    
    # Add property for is_parent
    @property
    def is_parent(self) -> bool:
        """Get whether this is a top-level task with no parent."""
        return self._is_parent
    
    @is_parent.setter
    def is_parent(self, value: bool) -> None:
        """Set whether this is a top-level task with no parent."""
        self._is_parent = value
        self._updated_at = datetime.now()
    
    def add_status_history_entry(self, entry: StatusHistoryEntry) -> None:
        """Add a status history entry to the task."""
        if not isinstance(entry, StatusHistoryEntry):
            raise TypeError("entry must be an instance of StatusHistoryEntry")
        self._status_history.append(entry)
        self._updated_at = datetime.now() # Touch updated_at when history changes

    @property
    def status_history(self) -> List[StatusHistoryEntry]:
        """Get the task's status history (returns a copy)."""
        return self._status_history.copy()

    def set_status(self, status: Union[str, int, TaskStatus]) -> None:
        """
        Set the task status.
        
        Args:
            status: The new status
        """
        old_status = self._status
        
        if isinstance(status, TaskStatus):
            self._status = status
        else:
            self._status = TaskStatus.from_string(status)
        
        # Set start_date when task is marked as in progress for the first time
        if (self._status == TaskStatus.IN_PROGRESS and 
            old_status != TaskStatus.IN_PROGRESS and 
            old_status != TaskStatus.COMPLETE and
            not hasattr(self, '_start_date')):
            self._start_date = datetime.now()
            
        # Update completed_at timestamp when task is marked as complete
        if self._status == TaskStatus.COMPLETE and old_status != TaskStatus.COMPLETE:
            self._completed_at = datetime.now()
        # Clear completed_at if task was complete and is now not complete
        elif self._status != TaskStatus.COMPLETE and old_status == TaskStatus.COMPLETE:
            self._completed_at = None
            
        self._updated_at = datetime.now()

    def set_priority(self, priority: Union[str, int, TaskPriority]) -> None:
        """
        Set the task priority.
        
        Args:
            priority: The new priority
        """
        if isinstance(priority, TaskPriority):
            self._priority = priority
        else:
            self._priority = TaskPriority.from_string(priority)
        self._updated_at = datetime.now() 