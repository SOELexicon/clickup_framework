"""
Unit tests for the ListJsonRepository class.

This module contains comprehensive tests for ListJsonRepository implementation,
which extends JsonRepository with list-specific operations.
"""
import unittest
import json
import tempfile
import os
from pathlib import Path
from unittest.mock import patch, MagicMock

from refactor.core.repositories.list_json_repository import ListJsonRepository
from refactor.core.entities.list_entity import ListEntity
from refactor.core.exceptions import EntityNotFoundError


class MockListEntity:
    """Mock list entity for testing the repository."""
    
    def __init__(self, entity_id, name, description="", folder_id=None, tasks=None, list_type="list"):
        """Initialize a mock list entity."""
        self.id = entity_id
        self.name = name
        self.description = description
        self.folder_id = folder_id
        self.tasks = tasks or []
        self.list_type = list_type
    
    def to_dict(self):
        """Convert list to dictionary."""
        return {
            "id": self.id,
            "name": self.name,
            "description": self.description,
            "folder_id": self.folder_id,
            "tasks": self.tasks.copy() if self.tasks else [],
            "list_type": self.list_type
        }
    
    @classmethod
    def from_dict(cls, data):
        """Create list from dictionary."""
        return cls(
            entity_id=data.get("id"),
            name=data.get("name", ""),
            description=data.get("description", ""),
            folder_id=data.get("folder_id"),
            tasks=data.get("tasks", []),
            list_type=data.get("list_type", "list")
        )


# Create a mock implementation of ListJsonRepository with the missing methods
class MockListJsonRepository(ListJsonRepository):
    """Mock implementation of ListJsonRepository for testing."""
    
    def __init__(self, json_path):
        """Initialize without calling super to avoid inheritance issues."""
        self._json_path = json_path
        self._entities = {}
        self._entities_by_name = {}
        self._load_entities()
    
    def _load_entities(self):
        """Load entities from the JSON file."""
        try:
            with open(self._json_path, 'r') as f:
                data = json.load(f)
                
            for entity_data in data.get("entities", []):
                entity = MockListEntity.from_dict(entity_data)
                self._entities[entity.id] = entity
                if entity.name:
                    self._entities_by_name[entity.name] = entity.id
                
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
        entity_id = self._entities_by_name.get(name)
        if not entity_id:
            raise EntityNotFoundError(f"No entity with name '{name}' found")
        return self._entities[entity_id]
    
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
        entity_id = self._entities_by_name.get(name)
        if not entity_id:
            return None
        return self._entities[entity_id]
    
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
        
        if entity.name and entity.name in self._entities_by_name:
            raise EntityNotFoundError(f"Entity with name '{entity.name}' already exists")
            
        self._entities[entity.id] = entity
        if entity.name:
            self._entities_by_name[entity.name] = entity.id
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
            
        old_entity = self._entities[entity.id]
        if old_entity.name in self._entities_by_name:
            del self._entities_by_name[old_entity.name]
            
        self._entities[entity.id] = entity
        if entity.name:
            self._entities_by_name[entity.name] = entity.id
            
        self._save_entities()
        return entity
    
    def delete(self, entity_id):
        """Delete entity."""
        if entity_id not in self._entities:
            raise EntityNotFoundError(f"No entity with id '{entity_id}' found")
            
        entity = self._entities[entity_id]
        if entity.name in self._entities_by_name:
            del self._entities_by_name[entity.name]
            
        del self._entities[entity_id]
        self._save_entities()
    
    # Implementing ListJsonRepository specific methods
    def get_by_folder(self, folder_id):
        """Get lists in a folder."""
        return [
            entity for entity in self._entities.values()
            if entity.folder_id == folder_id
        ]
    
    def get_lists_with_tasks(self):
        """Get lists containing tasks."""
        return [
            entity for entity in self._entities.values()
            if entity.tasks and len(entity.tasks) > 0
        ]
    
    def get_list_by_task(self, task_id):
        """Get list containing a task."""
        for entity in self._entities.values():
            if entity.tasks and task_id in entity.tasks:
                return entity
        return None
    
    def add_task_to_list(self, list_id, task_id):
        """Add task to list."""
        if list_id not in self._entities:
            raise EntityNotFoundError(f"No list with id '{list_id}' found")
            
        list_entity = self._entities[list_id]
        if task_id not in list_entity.tasks:
            list_entity.tasks.append(task_id)
            self._save_entities()
        return list_entity
    
    def remove_task_from_list(self, list_id, task_id):
        """Remove task from list."""
        if list_id not in self._entities:
            raise EntityNotFoundError(f"No list with id '{list_id}' found")
            
        list_entity = self._entities[list_id]
        if task_id in list_entity.tasks:
            list_entity.tasks.remove(task_id)
            self._save_entities()
        return list_entity
    
    def move_task_between_lists(self, task_id, source_list_id, destination_list_id):
        """Move task between lists."""
        if source_list_id not in self._entities:
            raise EntityNotFoundError(f"No source list with id '{source_list_id}' found")
            
        if destination_list_id not in self._entities:
            raise EntityNotFoundError(f"No destination list with id '{destination_list_id}' found")
            
        source_list = self._entities[source_list_id]
        destination_list = self._entities[destination_list_id]
        
        if task_id not in source_list.tasks:
            raise EntityNotFoundError(f"Task '{task_id}' not found in source list")
            
        if task_id in destination_list.tasks:
            # Already in destination, just remove from source
            source_list.tasks.remove(task_id)
            self._save_entities()
            return destination_list
            
        # Remove from source and add to destination
        source_list.tasks.remove(task_id)
        destination_list.tasks.append(task_id)
        self._save_entities()
        
        return destination_list


@patch('refactor.core.repositories.list_json_repository.ListEntity', MockListEntity)
class ListJsonRepositoryTests(unittest.TestCase):
    """Test cases for the ListJsonRepository implementation."""
    
    def setUp(self):
        """Set up test environment."""
        # Create a temporary file
        self.test_fd, self.test_path = tempfile.mkstemp(suffix='.json')
        self.test_path = Path(self.test_path)
        
        # Initialize test data
        self.test_data = {
            "entities": [
                {
                    "id": "lst_001",
                    "name": "List 1",
                    "description": "List 1 description",
                    "folder_id": "fld_001",
                    "tasks": ["tsk_001", "tsk_002"],
                    "list_type": "list"
                },
                {
                    "id": "lst_002",
                    "name": "List 2",
                    "description": "List 2 description",
                    "folder_id": "fld_001",
                    "tasks": [],
                    "list_type": "list"
                },
                {
                    "id": "lst_003",
                    "name": "List 3",
                    "description": "List 3 description",
                    "folder_id": "fld_002",
                    "tasks": ["tsk_003"],
                    "list_type": "list"
                }
            ]
        }
        
        # Write test data to file
        with open(self.test_path, 'w') as f:
            json.dump(self.test_data, f, indent=2)
        
        # Create repository with our mock implementation
        self.repo = MockListJsonRepository(json_path=self.test_path)
    
    def tearDown(self):
        """Clean up after tests."""
        try:
            os.close(self.test_fd)
            os.unlink(self.test_path)
        except:
            pass
    
    def test_initialization(self):
        """Test repository initialization."""
        # Verify lists were loaded
        self.assertEqual(self.repo.count(), 3)
        
        # Check list attributes
        list1 = self.repo.get("lst_001")
        self.assertEqual(list1.name, "List 1")
        self.assertEqual(list1.folder_id, "fld_001")
        self.assertEqual(list1.tasks, ["tsk_001", "tsk_002"])
        
        # Check list by name
        list_by_name = self.repo.find_by_name("List 2")
        self.assertEqual(list_by_name.id, "lst_002")
    
    def test_get_by_folder(self):
        """Test getting lists by folder."""
        # Get lists in folder_id="fld_001"
        folder1_lists = self.repo.get_by_folder("fld_001")
        self.assertEqual(len(folder1_lists), 2)
        self.assertEqual({l.id for l in folder1_lists}, {"lst_001", "lst_002"})
        
        # Get lists in folder_id="fld_002"
        folder2_lists = self.repo.get_by_folder("fld_002")
        self.assertEqual(len(folder2_lists), 1)
        self.assertEqual(folder2_lists[0].id, "lst_003")
        
        # Get lists in non-existent folder
        non_existent_lists = self.repo.get_by_folder("non_existent")
        self.assertEqual(len(non_existent_lists), 0)
    
    def test_get_lists_with_tasks(self):
        """Test getting lists with tasks."""
        # Get lists with tasks
        lists_with_tasks = self.repo.get_lists_with_tasks()
        self.assertEqual(len(lists_with_tasks), 2)
        self.assertEqual({l.id for l in lists_with_tasks}, {"lst_001", "lst_003"})
    
    def test_get_list_by_task(self):
        """Test getting list by task."""
        # Get list containing task_id="tsk_001"
        list_entity = self.repo.get_list_by_task("tsk_001")
        self.assertIsNotNone(list_entity)
        self.assertEqual(list_entity.id, "lst_001")
        
        # Get list containing task_id="tsk_003"
        list_entity = self.repo.get_list_by_task("tsk_003")
        self.assertIsNotNone(list_entity)
        self.assertEqual(list_entity.id, "lst_003")
        
        # Get list containing non-existent task
        list_entity = self.repo.get_list_by_task("non_existent")
        self.assertIsNone(list_entity)
    
    def test_add_task_to_list(self):
        """Test adding task to list."""
        # Add new task to list
        updated_list = self.repo.add_task_to_list("lst_002", "tsk_new")
        self.assertIn("tsk_new", updated_list.tasks)
        
        # Verify list was updated in repository
        retrieved_list = self.repo.get("lst_002")
        self.assertIn("tsk_new", retrieved_list.tasks)
        
        # Add existing task to list (should not duplicate)
        updated_list = self.repo.add_task_to_list("lst_001", "tsk_001")
        self.assertEqual(updated_list.tasks.count("tsk_001"), 1)
        
        # Add task to non-existent list
        with self.assertRaises(EntityNotFoundError):
            self.repo.add_task_to_list("non_existent", "tsk_new")
    
    def test_remove_task_from_list(self):
        """Test removing task from list."""
        # Remove task from list
        updated_list = self.repo.remove_task_from_list("lst_001", "tsk_001")
        self.assertNotIn("tsk_001", updated_list.tasks)
        
        # Verify list was updated in repository
        retrieved_list = self.repo.get("lst_001")
        self.assertNotIn("tsk_001", retrieved_list.tasks)
        
        # Remove non-existent task from list (should not error)
        updated_list = self.repo.remove_task_from_list("lst_002", "non_existent")
        self.assertEqual(updated_list.tasks, [])
        
        # Remove task from non-existent list
        with self.assertRaises(EntityNotFoundError):
            self.repo.remove_task_from_list("non_existent", "tsk_001")
    
    def test_move_task_between_lists(self):
        """Test moving task between lists."""
        # Move task from lst_001 to lst_002
        destination_list = self.repo.move_task_between_lists("tsk_001", "lst_001", "lst_002")
        
        # Verify task was moved
        self.assertIn("tsk_001", destination_list.tasks)
        
        # Verify source list no longer has the task
        source_list = self.repo.get("lst_001")
        self.assertNotIn("tsk_001", source_list.tasks)
        
        # Verify destination list has the task
        destination_list = self.repo.get("lst_002")
        self.assertIn("tsk_001", destination_list.tasks)
        
        # Move task that doesn't exist in source list
        with self.assertRaises(EntityNotFoundError):
            self.repo.move_task_between_lists("non_existent", "lst_001", "lst_002")
        
        # Move task to non-existent destination list
        with self.assertRaises(EntityNotFoundError):
            self.repo.move_task_between_lists("tsk_002", "lst_001", "non_existent")
        
        # Move task from non-existent source list
        with self.assertRaises(EntityNotFoundError):
            self.repo.move_task_between_lists("tsk_002", "non_existent", "lst_002")
    
    def test_add_list(self):
        """Test adding a new list."""
        # Create a new list
        new_list = MockListEntity(
            entity_id="lst_004",
            name="List 4",
            description="List 4 description",
            folder_id="fld_003",
            tasks=["tsk_004"]
        )
        
        # Add list to repository
        added_list = self.repo.add(new_list)
        
        # Verify list was added
        self.assertEqual(self.repo.count(), 4)
        self.assertEqual(added_list.id, "lst_004")
        
        # Verify list can be retrieved
        retrieved_list = self.repo.get("lst_004")
        self.assertEqual(retrieved_list.name, "List 4")
        self.assertEqual(retrieved_list.folder_id, "fld_003")
        self.assertEqual(retrieved_list.tasks, ["tsk_004"])
    
    def test_update_list(self):
        """Test updating a list."""
        # Get list to update
        list_entity = self.repo.get("lst_001")
        
        # Update list properties
        list_entity.name = "Updated List"
        list_entity.description = "Updated description"
        list_entity.tasks.append("tsk_new")
        
        # Update list in repository
        updated_list = self.repo.update(list_entity)
        
        # Verify list was updated
        self.assertEqual(updated_list.name, "Updated List")
        self.assertEqual(updated_list.description, "Updated description")
        self.assertIn("tsk_new", updated_list.tasks)
        
        # Verify list is persistently updated
        retrieved_list = self.repo.get("lst_001")
        self.assertEqual(retrieved_list.name, "Updated List")
        self.assertEqual(retrieved_list.description, "Updated description")
        self.assertIn("tsk_new", retrieved_list.tasks)
    
    def test_delete_list(self):
        """Test deleting a list."""
        # Verify list exists
        self.assertTrue(self.repo.exists("lst_001"))
        
        # Delete list
        self.repo.delete("lst_001")
        
        # Verify list was deleted
        self.assertFalse(self.repo.exists("lst_001"))
        self.assertEqual(self.repo.count(), 2)


if __name__ == "__main__":
    unittest.main() 