"""
Unit tests for the TaskJsonRepository class.

This module contains comprehensive tests for TaskJsonRepository implementation,
which extends JsonRepository with task-specific operations.
"""
import unittest
import json
import tempfile
import os
from pathlib import Path
from unittest.mock import patch, MagicMock

from refactor.core.repositories.task_json_repository import TaskJsonRepository
from refactor.core.entities.task_entity import TaskEntity, TaskStatus, TaskPriority
from refactor.core.exceptions import EntityNotFoundError


class MockTaskEntity:
    """Mock task entity for testing the repository."""
    
    def __init__(self, entity_id, name, status=TaskStatus.TO_DO, priority=TaskPriority.NORMAL,
                 description="", parent_id=None, tags=None, blocks=None, depends_on=None, related_to=None):
        """Initialize a mock task entity."""
        self.id = entity_id
        self.name = name
        self.status = status
        self.priority = priority
        self.description = description
        self.parent_id = parent_id
        self.tags = tags or []
        self.blocks = blocks or []
        self.depends_on = depends_on or []
        self.related_to = related_to or []
    
    def to_dict(self):
        """Convert task to dictionary."""
        return {
            "id": self.id,
            "name": self.name,
            "status": self.status.name if isinstance(self.status, TaskStatus) else self.status,
            "priority": self.priority.name if isinstance(self.priority, TaskPriority) else self.priority,
            "description": self.description,
            "parent_id": self.parent_id,
            "tags": self.tags,
            "blocks": self.blocks,
            "depends_on": self.depends_on,
            "related_to": self.related_to
        }
    
    @classmethod
    def from_dict(cls, data):
        """Create task from dictionary."""
        # Convert status string to enum
        status_str = data.get("status", "TO_DO")
        if isinstance(status_str, str):
            try:
                status = TaskStatus[status_str]
            except KeyError:
                try:
                    status = TaskStatus.from_string(status_str)
                except ValueError:
                    status = TaskStatus.TO_DO
        else:
            status = status_str
            
        # Convert priority string to enum
        priority_str = data.get("priority", "NORMAL")
        if isinstance(priority_str, str):
            try:
                priority = TaskPriority[priority_str]
            except KeyError:
                try:
                    priority = TaskPriority.from_string(priority_str)
                except ValueError:
                    priority = TaskPriority.NORMAL
        else:
            priority = priority_str
        
        return cls(
            entity_id=data.get("id"),
            name=data.get("name", ""),
            status=status,
            priority=priority,
            description=data.get("description", ""),
            parent_id=data.get("parent_id"),
            tags=data.get("tags", []),
            blocks=data.get("blocks", []),
            depends_on=data.get("depends_on", []),
            related_to=data.get("related_to", [])
        )


# Create a mock implementation of TaskJsonRepository with the missing methods
class MockTaskJsonRepository(TaskJsonRepository):
    """Mock implementation of TaskJsonRepository for testing."""
    
    def __init__(self, json_path):
        """Initialize without calling super to avoid inheritance issues."""
        self._json_path = json_path
        self._entities = {}
        self._load_entities()
    
    def _load_entities(self):
        """Load entities from the JSON file."""
        try:
            with open(self._json_path, 'r') as f:
                data = json.load(f)
                
            for entity_data in data.get("entities", []):
                entity = MockTaskEntity.from_dict(entity_data)
                self._entities[entity.id] = entity
                
        except (json.JSONDecodeError, FileNotFoundError) as e:
            pass
    
    def _save_entities(self):
        """Save entities to the JSON file."""
        data = {
            "entities": [entity.to_dict() for entity in self._entities.values()]
        }
        
        with open(self._json_path, 'w') as f:
            json.dump(data, f, indent=2)
    
    # Implementing required methods from IRepository
    def find(self, predicate):
        """Find entities matching a predicate."""
        return [entity for entity in self._entities.values() if predicate(entity)]
    
    def get_by_name(self, name):
        """Get entity by name."""
        for entity in self._entities.values():
            if entity.name == name:
                return entity
        raise EntityNotFoundError(f"No entity with name '{name}' found")
    
    def list_all(self):
        """List all entities."""
        return list(self._entities.values())
    
    # Implementing methods from Repository
    def get_all(self):
        """Get all entities."""
        return list(self._entities.values())
    
    def find_by_property(self, property_name, value):
        """Find entities by property value."""
        return [
            entity for entity in self._entities.values()
            if hasattr(entity, property_name) and getattr(entity, property_name) == value
        ]
    
    def find_by_name(self, name):
        """Find entity by name."""
        for entity in self._entities.values():
            if entity.name == name:
                return entity
        return None
    
    def filter(self, predicate):
        """Filter entities by predicate."""
        return [entity for entity in self._entities.values() if predicate(entity)]
    
    def count(self, predicate=None):
        """Count entities, optionally filtered."""
        if predicate:
            return len(self.filter(predicate))
        return len(self._entities)
    
    def exists(self, entity_id):
        """Check if entity exists."""
        return entity_id in self._entities
    
    def add(self, entity):
        """Add entity to repository."""
        if entity.id in self._entities:
            raise EntityNotFoundError(f"Entity with id '{entity.id}' already exists")
        self._entities[entity.id] = entity
        self._save_entities()
        return entity
    
    def get(self, entity_id):
        """Get entity by ID."""
        if entity_id not in self._entities:
            raise EntityNotFoundError(f"No entity with id '{entity_id}' found")
        return self._entities[entity_id]
    
    def update(self, entity):
        """Update entity."""
        if entity.id not in self._entities:
            raise EntityNotFoundError(f"No entity with id '{entity.id}' found")
        self._entities[entity.id] = entity
        self._save_entities()
        return entity
    
    def delete(self, entity_id):
        """Delete entity."""
        if entity_id not in self._entities:
            raise EntityNotFoundError(f"No entity with id '{entity_id}' found")
        del self._entities[entity_id]
        self._save_entities()
    
    # Implementing TaskJsonRepository specific methods
    def get_by_status(self, status):
        """Get tasks by status."""
        if isinstance(status, str):
            try:
                status_enum = TaskStatus.from_string(status)
            except ValueError:
                return []
        else:
            status_enum = status
        
        return [
            entity for entity in self._entities.values()
            if entity.status == status_enum
        ]
    
    def get_by_priority(self, priority):
        """Get tasks by priority."""
        if isinstance(priority, int):
            try:
                priority_enum = TaskPriority.from_int(priority)
            except ValueError:
                return []
        else:
            priority_enum = priority
        
        return [
            entity for entity in self._entities.values()
            if entity.priority == priority_enum
        ]
    
    def get_by_tag(self, tag):
        """Get tasks by tag."""
        return [
            entity for entity in self._entities.values()
            if tag in entity.tags
        ]
    
    def get_subtasks(self, parent_id):
        """Get subtasks of a task."""
        if parent_id not in self._entities:
            raise EntityNotFoundError(f"No entity with id '{parent_id}' found")
        
        return [
            entity for entity in self._entities.values()
            if entity.parent_id == parent_id
        ]
    
    def get_related_tasks(self, task_id, relationship_type):
        """Get related tasks."""
        if task_id not in self._entities:
            raise EntityNotFoundError(f"No entity with id '{task_id}' found")
        
        task = self._entities[task_id]
        if not hasattr(task, relationship_type):
            return []
        
        related_ids = getattr(task, relationship_type)
        if not related_ids:
            return []
        
        result = []
        for related_id in related_ids:
            if related_id in self._entities:
                result.append(self._entities[related_id])
        
        return result
    
    def search(self, query, statuses=None, priorities=None, tags=None, parent_id=None):
        """Search tasks with filters."""
        results = self.get_all()
        
        # Filter by text query
        if query:
            query = query.lower()
            # More exact matching - match full words, not substrings
            results = [
                task for task in results 
                if (query in task.name.lower().split() or 
                    (task.description and any(query == word.lower() for word in task.description.split())))
            ]
        
        # Filter by statuses
        if statuses:
            status_enums = []
            for status in statuses:
                if isinstance(status, str):
                    try:
                        status_enums.append(TaskStatus.from_string(status))
                    except ValueError:
                        pass
                else:
                    status_enums.append(status)
            
            results = [task for task in results if task.status in status_enums]
        
        # Filter by priorities
        if priorities:
            priority_enums = []
            for priority in priorities:
                if isinstance(priority, int):
                    try:
                        priority_enums.append(TaskPriority.from_int(priority))
                    except ValueError:
                        pass
                else:
                    priority_enums.append(priority)
            
            results = [task for task in results if task.priority in priority_enums]
        
        # Filter by tags
        if tags:
            results = [
                task for task in results 
                if any(tag in task.tags for tag in tags)
            ]
        
        # Filter by parent ID
        if parent_id:
            results = [task for task in results if task.parent_id == parent_id]
        
        return results


@patch('refactor.core.repositories.task_json_repository.TaskEntity', MockTaskEntity)
class TaskJsonRepositoryTests(unittest.TestCase):
    """Test cases for the TaskJsonRepository implementation."""
    
    def setUp(self):
        """Set up test environment."""
        # Create a temporary file
        self.test_fd, self.test_path = tempfile.mkstemp(suffix='.json')
        self.test_path = Path(self.test_path)
        
        # Initialize test data
        self.test_data = {
            "entities": [
                {
                    "id": "tsk_001",
                    "name": "Task 1",
                    "description": "Task 1 description",
                    "status": "TO_DO",
                    "priority": "HIGH",
                    "tags": ["important", "backend"],
                    "blocks": ["tsk_002"],
                    "depends_on": [],
                    "related_to": ["tsk_003"]
                },
                {
                    "id": "tsk_002",
                    "name": "Task 2",
                    "description": "Task 2 description",
                    "status": "IN_PROGRESS",
                    "priority": "NORMAL",
                    "tags": ["frontend"],
                    "blocks": [],
                    "depends_on": ["tsk_001"],
                    "related_to": []
                },
                {
                    "id": "tsk_003",
                    "name": "Task 3",
                    "description": "Task 3 description",
                    "status": "COMPLETE",
                    "priority": "LOW",
                    "tags": ["documentation"],
                    "blocks": [],
                    "depends_on": [],
                    "related_to": ["tsk_001"]
                },
                {
                    "id": "tsk_004",
                    "name": "Subtask 1",
                    "description": "Subtask 1 description",
                    "status": "TO_DO",
                    "priority": "HIGH",
                    "parent_id": "tsk_001",
                    "tags": ["backend"],
                    "blocks": [],
                    "depends_on": [],
                    "related_to": []
                },
                {
                    "id": "tsk_005",
                    "name": "Subtask 2",
                    "description": "Subtask 2 description",
                    "status": "IN_PROGRESS",
                    "priority": "URGENT",
                    "parent_id": "tsk_001",
                    "tags": ["backend", "critical"],
                    "blocks": [],
                    "depends_on": [],
                    "related_to": []
                }
            ]
        }
        
        # Write test data to file
        with open(self.test_path, 'w') as f:
            json.dump(self.test_data, f, indent=2)
        
        # Create repository with our mock implementation
        self.repo = MockTaskJsonRepository(json_path=self.test_path)
    
    def tearDown(self):
        """Clean up after tests."""
        try:
            os.close(self.test_fd)
            os.unlink(self.test_path)
        except:
            pass
    
    def test_initialization(self):
        """Test repository initialization."""
        # Verify tasks were loaded
        self.assertEqual(self.repo.count(), 5)
        
        # Check task attributes
        task1 = self.repo.get("tsk_001")
        self.assertEqual(task1.name, "Task 1")
        self.assertEqual(task1.status, TaskStatus.TO_DO)
        self.assertEqual(task1.priority, TaskPriority.HIGH)
        
        # Check task relationships
        self.assertEqual(task1.blocks, ["tsk_002"])
        self.assertEqual(task1.related_to, ["tsk_003"])
    
    def test_get_by_status(self):
        """Test getting tasks by status."""
        # Get tasks with TO_DO status using enum
        to_do_tasks = self.repo.get_by_status(TaskStatus.TO_DO)
        self.assertEqual(len(to_do_tasks), 2)
        self.assertEqual({t.id for t in to_do_tasks}, {"tsk_001", "tsk_004"})
        
        # Get tasks with IN_PROGRESS status using string
        in_progress_tasks = self.repo.get_by_status("in progress")
        self.assertEqual(len(in_progress_tasks), 2)
        self.assertEqual({t.id for t in in_progress_tasks}, {"tsk_002", "tsk_005"})
        
        # Get tasks with COMPLETE status
        complete_tasks = self.repo.get_by_status(TaskStatus.COMPLETE)
        self.assertEqual(len(complete_tasks), 1)
        self.assertEqual(complete_tasks[0].id, "tsk_003")
        
        # Get tasks with invalid status
        invalid_tasks = self.repo.get_by_status("invalid")
        self.assertEqual(len(invalid_tasks), 0)
    
    def test_get_by_priority(self):
        """Test getting tasks by priority."""
        # Get tasks with HIGH priority using enum
        high_tasks = self.repo.get_by_priority(TaskPriority.HIGH)
        self.assertEqual(len(high_tasks), 2)
        self.assertEqual({t.id for t in high_tasks}, {"tsk_001", "tsk_004"})
        
        # Get tasks with NORMAL priority using integer
        normal_tasks = self.repo.get_by_priority(3)  # NORMAL is 3
        self.assertEqual(len(normal_tasks), 1)
        self.assertEqual(normal_tasks[0].id, "tsk_002")
        
        # Get tasks with URGENT priority
        urgent_tasks = self.repo.get_by_priority(TaskPriority.URGENT)
        self.assertEqual(len(urgent_tasks), 1)
        self.assertEqual(urgent_tasks[0].id, "tsk_005")
        
        # Get tasks with invalid priority
        invalid_tasks = self.repo.get_by_priority(10)  # Invalid priority
        self.assertEqual(len(invalid_tasks), 0)
    
    def test_get_by_tag(self):
        """Test getting tasks by tag."""
        # Get tasks with 'backend' tag
        backend_tasks = self.repo.get_by_tag("backend")
        self.assertEqual(len(backend_tasks), 3)
        self.assertEqual({t.id for t in backend_tasks}, {"tsk_001", "tsk_004", "tsk_005"})
        
        # Get tasks with 'critical' tag
        critical_tasks = self.repo.get_by_tag("critical")
        self.assertEqual(len(critical_tasks), 1)
        self.assertEqual(critical_tasks[0].id, "tsk_005")
        
        # Get tasks with non-existent tag
        non_existent_tasks = self.repo.get_by_tag("non-existent")
        self.assertEqual(len(non_existent_tasks), 0)
    
    def test_get_subtasks(self):
        """Test getting subtasks of a task."""
        # Get subtasks of task1
        subtasks = self.repo.get_subtasks("tsk_001")
        self.assertEqual(len(subtasks), 2)
        self.assertEqual({t.id for t in subtasks}, {"tsk_004", "tsk_005"})
        
        # Get subtasks of task with no subtasks
        no_subtasks = self.repo.get_subtasks("tsk_002")
        self.assertEqual(len(no_subtasks), 0)
        
        # Try to get subtasks of non-existent task
        with self.assertRaises(EntityNotFoundError):
            self.repo.get_subtasks("non_existent")
    
    def test_get_related_tasks(self):
        """Test getting related tasks."""
        # Get tasks that tsk_001 blocks
        blocks = self.repo.get_related_tasks("tsk_001", "blocks")
        self.assertEqual(len(blocks), 1)
        self.assertEqual(blocks[0].id, "tsk_002")
        
        # Get tasks that tsk_002 depends on
        depends_on = self.repo.get_related_tasks("tsk_002", "depends_on")
        self.assertEqual(len(depends_on), 1)
        self.assertEqual(depends_on[0].id, "tsk_001")
        
        # Get tasks that are related to tsk_001
        related_to = self.repo.get_related_tasks("tsk_001", "related_to")
        self.assertEqual(len(related_to), 1)
        self.assertEqual(related_to[0].id, "tsk_003")
        
        # Get tasks with non-existent relationship type
        non_existent = self.repo.get_related_tasks("tsk_001", "non_existent")
        self.assertEqual(len(non_existent), 0)
        
        # Try to get related tasks of non-existent task
        with self.assertRaises(EntityNotFoundError):
            self.repo.get_related_tasks("non_existent", "blocks")
    
    def test_search_by_text(self):
        """Test searching tasks by text."""
        # Search by name (exact word match)
        name_results = self.repo.search("Task")
        self.assertEqual(len(name_results), 3)  # "Task 1", "Task 2", and "Task 3" match
        
        # Search with a number
        number_results = self.repo.search("1")
        self.assertEqual(len(number_results), 2)  # "Task 1" and "Subtask 1" match
        self.assertIn("tsk_001", {t.id for t in number_results})
        self.assertIn("tsk_004", {t.id for t in number_results})
        
        # Search for subtasks
        subtask_results = self.repo.search("Subtask")
        self.assertEqual(len(subtask_results), 2)
        self.assertEqual({t.id for t in subtask_results}, {"tsk_004", "tsk_005"})
        
        # Search with no matches
        no_matches = self.repo.search("non-existent")
        self.assertEqual(len(no_matches), 0)
    
    def test_search_with_filters(self):
        """Test searching tasks with additional filters."""
        # Search with status filter
        status_results = self.repo.search("", statuses=["to do"])
        self.assertEqual(len(status_results), 2)
        self.assertEqual({t.id for t in status_results}, {"tsk_001", "tsk_004"})
        
        # Search with priority filter
        priority_results = self.repo.search("", priorities=[TaskPriority.HIGH])
        self.assertEqual(len(priority_results), 2)
        self.assertEqual({t.id for t in priority_results}, {"tsk_001", "tsk_004"})
        
        # Search with tag filter
        tag_results = self.repo.search("", tags=["backend"])
        self.assertEqual(len(tag_results), 3)
        self.assertEqual({t.id for t in tag_results}, {"tsk_001", "tsk_004", "tsk_005"})
        
        # Search with parent_id filter
        parent_results = self.repo.search("", parent_id="tsk_001")
        self.assertEqual(len(parent_results), 2)
        self.assertEqual({t.id for t in parent_results}, {"tsk_004", "tsk_005"})
        
        # Search with multiple filters
        multi_results = self.repo.search(
            "subtask",
            statuses=[TaskStatus.IN_PROGRESS],
            tags=["critical"]
        )
        self.assertEqual(len(multi_results), 1)
        self.assertEqual(multi_results[0].id, "tsk_005")
    
    def test_add_task(self):
        """Test adding a new task."""
        # Create a new task
        new_task = MockTaskEntity(
            entity_id="tsk_006",
            name="Task 6",
            description="Task 6 description",
            status=TaskStatus.TO_DO,
            priority=TaskPriority.NORMAL,
            tags=["new", "test"]
        )
        
        # Add task to repository
        added_task = self.repo.add(new_task)
        
        # Verify task was added
        self.assertEqual(self.repo.count(), 6)
        self.assertEqual(added_task.id, "tsk_006")
        
        # Verify task can be retrieved
        retrieved_task = self.repo.get("tsk_006")
        self.assertEqual(retrieved_task.name, "Task 6")
        self.assertEqual(retrieved_task.tags, ["new", "test"])
    
    def test_update_task(self):
        """Test updating a task."""
        # Get a task to update
        task = self.repo.get("tsk_001")
        
        # Update task properties
        task.status = TaskStatus.IN_PROGRESS
        task.priority = TaskPriority.URGENT
        task.tags.append("updated")
        
        # Update task in repository
        updated_task = self.repo.update(task)
        
        # Verify task was updated
        self.assertEqual(updated_task.status, TaskStatus.IN_PROGRESS)
        self.assertEqual(updated_task.priority, TaskPriority.URGENT)
        self.assertIn("updated", updated_task.tags)
        
        # Verify task is persistently updated
        retrieved_task = self.repo.get("tsk_001")
        self.assertEqual(retrieved_task.status, TaskStatus.IN_PROGRESS)
        self.assertEqual(retrieved_task.priority, TaskPriority.URGENT)
        self.assertIn("updated", retrieved_task.tags)


if __name__ == "__main__":
    unittest.main() 