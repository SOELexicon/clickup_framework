#!/usr/bin/env python3
"""
Simple test for the repository interfaces.

This is a standalone test that can be run without the full application context.
"""
import unittest
import os
import sys
from abc import ABC, abstractmethod
from typing import TypeVar, Generic, Callable, List, Optional

# Define a base entity type
class BaseEntity:
    """Base entity class."""
    
    @property
    def id(self) -> str:
        """Get entity ID."""
        return self._id
        
    @property
    def name(self) -> str:
        """Get entity name."""
        return self._name

# Define the entity type variable for generic implementations
T = TypeVar('T', bound=BaseEntity)

# Define repository errors
class RepositoryError(Exception):
    """Base exception class for repository-related errors."""
    pass

class EntityNotFoundError(RepositoryError):
    """Error raised when trying to access a non-existent entity."""
    pass

class EntityAlreadyExistsError(RepositoryError):
    """Error raised when trying to add an entity with a duplicate ID."""
    pass

class ValidationError(RepositoryError):
    """Error raised when entity validation fails."""
    pass

# Define the repository interface
class IRepository(Generic[T], ABC):
    """
    Generic interface for entity repositories.
    
    All entity repositories should implement this interface to provide
    a standard way to interact with entities.
    """
    
    @abstractmethod
    def add(self, entity: T) -> T:
        """Add a new entity to the repository."""
        pass
    
    @abstractmethod
    def update(self, entity: T) -> T:
        """Update an existing entity in the repository."""
        pass
    
    @abstractmethod
    def get(self, entity_id: str) -> T:
        """Get an entity by its ID."""
        pass
    
    @abstractmethod
    def get_by_name(self, name: str) -> T:
        """Get an entity by its name."""
        pass
    
    @abstractmethod
    def exists(self, entity_id: str) -> bool:
        """Check if an entity with the given ID exists."""
        pass
    
    @abstractmethod
    def delete(self, entity_id: str) -> bool:
        """Delete an entity by its ID."""
        pass
    
    @abstractmethod
    def list_all(self) -> List[T]:
        """Get all entities in the repository."""
        pass
    
    @abstractmethod
    def count(self) -> int:
        """Get the number of entities in the repository."""
        pass
    
    @abstractmethod
    def find(self, predicate: Callable[[T], bool]) -> List[T]:
        """Find entities that match a predicate."""
        pass

# Define a task-specific repository interface
class ITaskRepository(IRepository['TaskEntity'], ABC):
    """Interface for task repositories."""
    
    @abstractmethod
    def get_by_status(self, status: str) -> List['TaskEntity']:
        """Get tasks with a specific status."""
        pass
    
    @abstractmethod
    def get_by_priority(self, priority: int) -> List['TaskEntity']:
        """Get tasks with a specific priority."""
        pass
    
    @abstractmethod
    def get_by_tag(self, tag: str) -> List['TaskEntity']:
        """Get tasks with a specific tag."""
        pass
    
    @abstractmethod
    def get_subtasks(self, parent_id: str) -> List['TaskEntity']:
        """Get all subtasks of a given task."""
        pass
    
    @abstractmethod
    def get_related_tasks(self, task_id: str, relationship_type: str) -> List['TaskEntity']:
        """Get tasks related to a given task by a specific relationship type."""
        pass
    
    @abstractmethod
    def search(self, 
              query: str, 
              statuses: Optional[List[str]] = None,
              priorities: Optional[List[int]] = None,
              tags: Optional[List[str]] = None,
              parent_id: Optional[str] = None) -> List['TaskEntity']:
        """Search for tasks based on various criteria."""
        pass

# Define a simple task entity for testing
class TaskEntity(BaseEntity):
    """Task entity for testing."""
    
    def __init__(self, task_id: str, name: str, status: str = "to do", 
                priority: int = 1, tags: List[str] = None):
        """Initialize task entity."""
        self._id = task_id
        self._name = name
        self._status = status
        self._priority = priority
        self._tags = tags or []
    
    @property
    def status(self) -> str:
        """Get task status."""
        return self._status
    
    @status.setter
    def status(self, value: str) -> None:
        """Set task status."""
        self._status = value
    
    @property
    def priority(self) -> int:
        """Get task priority."""
        return self._priority
    
    @priority.setter
    def priority(self, value: int) -> None:
        """Set task priority."""
        self._priority = value
    
    @property
    def tags(self) -> List[str]:
        """Get task tags."""
        return self._tags


# Simple in-memory task repository implementation
class TaskRepository(ITaskRepository):
    """In-memory implementation of task repository."""
    
    def __init__(self):
        """Initialize repository."""
        self._tasks = {}
        self._name_index = {}
    
    def add(self, entity: TaskEntity) -> TaskEntity:
        """Add a task to the repository."""
        if self.exists(entity.id):
            raise EntityAlreadyExistsError(f"Task with ID {entity.id} already exists")
        
        if entity.name in self._name_index:
            raise EntityAlreadyExistsError(f"Task with name '{entity.name}' already exists")
        
        self._tasks[entity.id] = entity
        self._name_index[entity.name] = entity.id
        return entity
    
    def update(self, entity: TaskEntity) -> TaskEntity:
        """Update a task in the repository."""
        if not self.exists(entity.id):
            raise EntityNotFoundError(f"Task with ID {entity.id} not found")
        
        old_entity = self._tasks[entity.id]
        if old_entity.name != entity.name:
            # Update name index
            if entity.name in self._name_index:
                # Only if the name is already used by another entity
                if self._name_index[entity.name] != entity.id:
                    raise ValidationError(f"Task name '{entity.name}' is already in use")
            
            del self._name_index[old_entity.name]
            self._name_index[entity.name] = entity.id
        
        self._tasks[entity.id] = entity
        return entity
    
    def get(self, entity_id: str) -> TaskEntity:
        """Get a task by ID."""
        if not self.exists(entity_id):
            raise EntityNotFoundError(f"Task with ID {entity_id} not found")
        
        return self._tasks[entity_id]
    
    def get_by_name(self, name: str) -> TaskEntity:
        """Get a task by name."""
        if name not in self._name_index:
            raise EntityNotFoundError(f"Task with name '{name}' not found")
        
        return self._tasks[self._name_index[name]]
    
    def exists(self, entity_id: str) -> bool:
        """Check if a task exists."""
        return entity_id in self._tasks
    
    def delete(self, entity_id: str) -> bool:
        """Delete a task."""
        if not self.exists(entity_id):
            return False
        
        entity = self._tasks[entity_id]
        del self._name_index[entity.name]
        del self._tasks[entity_id]
        return True
    
    def list_all(self) -> List[TaskEntity]:
        """List all tasks."""
        return list(self._tasks.values())
    
    def count(self) -> int:
        """Count tasks."""
        return len(self._tasks)
    
    def find(self, predicate: Callable[[TaskEntity], bool]) -> List[TaskEntity]:
        """Find tasks by predicate."""
        return [task for task in self._tasks.values() if predicate(task)]
    
    def get_by_status(self, status: str) -> List[TaskEntity]:
        """Get tasks by status."""
        return [task for task in self._tasks.values() if task.status == status]
    
    def get_by_priority(self, priority: int) -> List[TaskEntity]:
        """Get tasks by priority."""
        return [task for task in self._tasks.values() if task.priority == priority]
    
    def get_by_tag(self, tag: str) -> List[TaskEntity]:
        """Get tasks by tag."""
        return [task for task in self._tasks.values() if tag in task.tags]
    
    def get_subtasks(self, parent_id: str) -> List[TaskEntity]:
        """Get subtasks (not implemented in this simple version)."""
        return []
    
    def get_related_tasks(self, task_id: str, relationship_type: str) -> List[TaskEntity]:
        """Get related tasks (not implemented in this simple version)."""
        return []
    
    def search(self, query: str, statuses=None, priorities=None, tags=None, parent_id=None) -> List[TaskEntity]:
        """Search for tasks (simplified implementation)."""
        results = self.list_all()
        
        # Filter by name (simplified)
        if query:
            results = [task for task in results if query.lower() in task.name.lower()]
        
        # Filter by status
        if statuses:
            results = [task for task in results if task.status in statuses]
        
        # Filter by priority
        if priorities:
            results = [task for task in results if task.priority in priorities]
        
        # Filter by tag
        if tags:
            results = [task for task in results 
                     if any(tag in task.tags for tag in tags)]
        
        return results


class TestRepositoryInterface(unittest.TestCase):
    """Test the repository interfaces and implementation."""
    
    def test_repository_error_inheritance(self):
        """Test repository error inheritance."""
        self.assertTrue(issubclass(RepositoryError, Exception))
        self.assertTrue(issubclass(EntityNotFoundError, RepositoryError))
        self.assertTrue(issubclass(EntityAlreadyExistsError, RepositoryError))
        self.assertTrue(issubclass(ValidationError, RepositoryError))
    
    def test_task_repository_operations(self):
        """Test basic task repository operations."""
        repo = TaskRepository()
        
        # Add a task
        task1 = TaskEntity("tsk_1001", "Test Task 1", "to do", 1, ["test", "important"])
        repo.add(task1)
        
        # Add another task
        task2 = TaskEntity("tsk_1002", "Test Task 2", "in progress", 2, ["test"])
        repo.add(task2)
        
        # Check task count
        self.assertEqual(repo.count(), 2)
        
        # Get task by ID
        retrieved_task = repo.get("tsk_1001")
        self.assertEqual(retrieved_task.name, "Test Task 1")
        
        # Get task by name
        retrieved_task = repo.get_by_name("Test Task 2")
        self.assertEqual(retrieved_task.id, "tsk_1002")
        
        # Update task
        task1.status = "in progress"
        repo.update(task1)
        self.assertEqual(repo.get("tsk_1001").status, "in progress")
        
        # Find tasks
        in_progress_tasks = repo.get_by_status("in progress")
        self.assertEqual(len(in_progress_tasks), 2)
        
        # Find by predicate
        important_tasks = repo.find(lambda t: "important" in t.tags)
        self.assertEqual(len(important_tasks), 1)
        self.assertEqual(important_tasks[0].id, "tsk_1001")
        
        # Search
        search_results = repo.search("Task 1", statuses=["in progress"])
        self.assertEqual(len(search_results), 1)
        self.assertEqual(search_results[0].id, "tsk_1001")
        
        # Delete task
        self.assertTrue(repo.delete("tsk_1001"))
        self.assertEqual(repo.count(), 1)
        
        # Try to get deleted task
        with self.assertRaises(EntityNotFoundError):
            repo.get("tsk_1001")


if __name__ == "__main__":
    unittest.main() 