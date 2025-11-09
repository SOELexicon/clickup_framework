"""
Task Entity Module

This module defines the Task entity and its related data structures.
"""
from dataclasses import dataclass, field
from typing import List, Dict, Any, Optional
from datetime import datetime


@dataclass
class Task:
    """
    Task entity representing a task in the system.
    
    This class represents a task with its properties and relationships.
    
    Attributes:
        id: Unique task identifier
        name: Task name
        description: Task description
        status: Current task status
        priority: Task priority
        tags: List of task tags
        parent_id: ID of parent task (None for top-level tasks)
        is_parent: Boolean indicating if this is a top-level task with no parent
        subtasks: List of subtask IDs
        comments: List of comment dictionaries
        relationships: Dictionary of relationship types to lists of task IDs
        metadata: Additional task metadata
        created_at: Task creation timestamp
        updated_at: Last update timestamp
    """
    id: str
    name: str
    description: str = ""
    status: str = "to do"
    priority: int = 0
    tags: List[str] = field(default_factory=list)
    parent_id: Optional[str] = None
    is_parent: bool = field(default=False)  # New field for parent status
    subtasks: List[str] = field(default_factory=list)
    comments: List[Dict[str, Any]] = field(default_factory=list)
    relationships: Dict[str, List[str]] = field(default_factory=dict)
    metadata: Dict[str, Any] = field(default_factory=dict)
    created_at: datetime = field(default_factory=datetime.now)
    updated_at: datetime = field(default_factory=datetime.now)
    
    def to_dict(self) -> Dict[str, Any]:
        """
        Convert the task to a dictionary.
        
        Returns:
            Dictionary representation of the task
        """
        return {
            "id": self.id,
            "name": self.name,
            "description": self.description,
            "status": self.status,
            "priority": self.priority,
            "tags": self.tags,
            "parent_id": self.parent_id,
            "is_parent": self.is_parent,  # Include is_parent in dictionary
            "subtasks": self.subtasks,
            "comments": self.comments,
            "relationships": self.relationships,
            "metadata": self.metadata,
            "created_at": self.created_at.isoformat(),
            "updated_at": self.updated_at.isoformat()
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'Task':
        """
        Create a task from a dictionary.
        
        Args:
            data: Dictionary containing task data
            
        Returns:
            Task instance
        """
        # Handle timestamps
        created_at = datetime.fromisoformat(data["created_at"]) if "created_at" in data else datetime.now()
        updated_at = datetime.fromisoformat(data["updated_at"]) if "updated_at" in data else datetime.now()
        
        # Create task with is_parent field
        return cls(
            id=data["id"],
            name=data["name"],
            description=data.get("description", ""),
            status=data.get("status", "to do"),
            priority=data.get("priority", 0),
            tags=data.get("tags", []),
            parent_id=data.get("parent_id"),
            is_parent=data.get("is_parent", False),  # Default to False if not specified
            subtasks=data.get("subtasks", []),
            comments=data.get("comments", []),
            relationships=data.get("relationships", {}),
            metadata=data.get("metadata", {}),
            created_at=created_at,
            updated_at=updated_at
        )
    
    def add_comment(self, comment: str, author: Optional[str] = None) -> None:
        """
        Add a comment to the task.
        
        Args:
            comment: Comment text
            author: Optional author name
        """
        self.comments.append({
            "text": comment,
            "author": author,
            "created_at": datetime.now().isoformat()
        })
        self.updated_at = datetime.now()
    
    def update_status(self, status: str) -> None:
        """
        Update the task status.
        
        Args:
            status: New status
        """
        self.status = status
        self.updated_at = datetime.now()
    
    def update_tags(self, tags: List[str]) -> None:
        """
        Update the task tags.
        
        Args:
            tags: New list of tags
        """
        self.tags = tags
        self.updated_at = datetime.now()
    
    def add_subtask(self, subtask_id: str) -> None:
        """
        Add a subtask to the task.
        
        Args:
            subtask_id: ID of the subtask
        """
        if subtask_id not in self.subtasks:
            self.subtasks.append(subtask_id)
            self.updated_at = datetime.now()
    
    def remove_subtask(self, subtask_id: str) -> None:
        """
        Remove a subtask from the task.
        
        Args:
            subtask_id: ID of the subtask
        """
        if subtask_id in self.subtasks:
            self.subtasks.remove(subtask_id)
            self.updated_at = datetime.now()
    
    def add_relationship(self, relationship_type: str, task_id: str) -> None:
        """
        Add a relationship to another task.
        
        Args:
            relationship_type: Type of relationship
            task_id: ID of the related task
        """
        if relationship_type not in self.relationships:
            self.relationships[relationship_type] = []
        if task_id not in self.relationships[relationship_type]:
            self.relationships[relationship_type].append(task_id)
            self.updated_at = datetime.now()
    
    def remove_relationship(self, relationship_type: str, task_id: str) -> None:
        """
        Remove a relationship to another task.
        
        Args:
            relationship_type: Type of relationship
            task_id: ID of the related task
        """
        if relationship_type in self.relationships and task_id in self.relationships[relationship_type]:
            self.relationships[relationship_type].remove(task_id)
            if not self.relationships[relationship_type]:
                del self.relationships[relationship_type]
            self.updated_at = datetime.now()
    
    def get_relationships(self, relationship_type: Optional[str] = None) -> Dict[str, List[str]]:
        """
        Get task relationships.
        
        Args:
            relationship_type: Optional type of relationship to filter by
            
        Returns:
            Dictionary of relationship types to lists of task IDs
        """
        if relationship_type:
            return {relationship_type: self.relationships.get(relationship_type, [])}
        return self.relationships 