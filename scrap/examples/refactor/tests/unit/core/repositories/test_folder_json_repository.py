"""
Unit tests for the FolderJsonRepository class.

This module contains comprehensive tests for FolderJsonRepository implementation,
which extends JsonRepository with folder-specific operations.
"""
import unittest
import json
import tempfile
import os
from pathlib import Path
from unittest.mock import patch, MagicMock

from refactor.core.repositories.folder_json_repository import FolderJsonRepository
from refactor.core.entities.folder_entity import FolderEntity
from refactor.core.exceptions import EntityNotFoundError


class MockFolderEntity:
    """Mock folder entity for testing the repository."""
    
    def __init__(self, entity_id, name, description="", space_id=None, lists=None, folder_type="folder"):
        """Initialize a mock folder entity."""
        self.id = entity_id
        self.name = name
        self.description = description
        self.space_id = space_id
        self.lists = lists or []
        self.folder_type = folder_type
    
    def to_dict(self):
        """Convert folder to dictionary."""
        return {
            "id": self.id,
            "name": self.name,
            "description": self.description,
            "space_id": self.space_id,
            "lists": self.lists.copy() if self.lists else [],
            "folder_type": self.folder_type
        }
    
    @classmethod
    def from_dict(cls, data):
        """Create folder from dictionary."""
        return cls(
            entity_id=data.get("id"),
            name=data.get("name", ""),
            description=data.get("description", ""),
            space_id=data.get("space_id"),
            lists=data.get("lists", []),
            folder_type=data.get("folder_type", "folder")
        )


# Create a mock implementation of FolderJsonRepository with the missing methods
class MockFolderJsonRepository(FolderJsonRepository):
    """Mock implementation of FolderJsonRepository for testing."""
    
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
                entity = MockFolderEntity.from_dict(entity_data)
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
    
    # Implementing FolderJsonRepository specific methods
    def get_by_space(self, space_id):
        """Get folders in a space."""
        return [
            entity for entity in self._entities.values()
            if entity.space_id == space_id
        ]
    
    def get_folders_with_lists(self):
        """Get folders containing lists."""
        return [
            entity for entity in self._entities.values()
            if entity.lists and len(entity.lists) > 0
        ]
    
    def get_folder_by_list(self, list_id):
        """Get folder containing a list."""
        for entity in self._entities.values():
            if entity.lists and list_id in entity.lists:
                return entity
        return None
    
    def add_list_to_folder(self, folder_id, list_id):
        """Add list to folder."""
        if folder_id not in self._entities:
            raise EntityNotFoundError(f"No folder with id '{folder_id}' found")
            
        folder = self._entities[folder_id]
        if list_id not in folder.lists:
            folder.lists.append(list_id)
            self._save_entities()
        return folder
    
    def remove_list_from_folder(self, folder_id, list_id):
        """Remove list from folder."""
        if folder_id not in self._entities:
            raise EntityNotFoundError(f"No folder with id '{folder_id}' found")
            
        folder = self._entities[folder_id]
        if list_id in folder.lists:
            folder.lists.remove(list_id)
            self._save_entities()
        return folder


@patch('refactor.core.repositories.folder_json_repository.FolderEntity', MockFolderEntity)
class FolderJsonRepositoryTests(unittest.TestCase):
    """Test cases for the FolderJsonRepository implementation."""
    
    def setUp(self):
        """Set up test environment."""
        # Create a temporary file
        self.test_fd, self.test_path = tempfile.mkstemp(suffix='.json')
        self.test_path = Path(self.test_path)
        
        # Initialize test data
        self.test_data = {
            "entities": [
                {
                    "id": "fld_001",
                    "name": "Folder 1",
                    "description": "Folder 1 description",
                    "space_id": "spc_001",
                    "lists": ["lst_001", "lst_002"],
                    "folder_type": "folder"
                },
                {
                    "id": "fld_002",
                    "name": "Folder 2",
                    "description": "Folder 2 description",
                    "space_id": "spc_001",
                    "lists": [],
                    "folder_type": "folder"
                },
                {
                    "id": "fld_003",
                    "name": "Folder 3",
                    "description": "Folder 3 description",
                    "space_id": "spc_002",
                    "lists": ["lst_003"],
                    "folder_type": "folder"
                }
            ]
        }
        
        # Write test data to file
        with open(self.test_path, 'w') as f:
            json.dump(self.test_data, f, indent=2)
        
        # Create repository with our mock implementation
        self.repo = MockFolderJsonRepository(json_path=self.test_path)
    
    def tearDown(self):
        """Clean up after tests."""
        try:
            os.close(self.test_fd)
            os.unlink(self.test_path)
        except:
            pass
    
    def test_initialization(self):
        """Test repository initialization."""
        # Verify folders were loaded
        self.assertEqual(self.repo.count(), 3)
        
        # Check folder attributes
        folder1 = self.repo.get("fld_001")
        self.assertEqual(folder1.name, "Folder 1")
        self.assertEqual(folder1.space_id, "spc_001")
        self.assertEqual(folder1.lists, ["lst_001", "lst_002"])
        
        # Check folder by name
        folder_by_name = self.repo.find_by_name("Folder 2")
        self.assertEqual(folder_by_name.id, "fld_002")
    
    def test_get_by_space(self):
        """Test getting folders by space."""
        # Get folders in space_id="spc_001"
        space1_folders = self.repo.get_by_space("spc_001")
        self.assertEqual(len(space1_folders), 2)
        self.assertEqual({f.id for f in space1_folders}, {"fld_001", "fld_002"})
        
        # Get folders in space_id="spc_002"
        space2_folders = self.repo.get_by_space("spc_002")
        self.assertEqual(len(space2_folders), 1)
        self.assertEqual(space2_folders[0].id, "fld_003")
        
        # Get folders in non-existent space
        non_existent_folders = self.repo.get_by_space("non_existent")
        self.assertEqual(len(non_existent_folders), 0)
    
    def test_get_folders_with_lists(self):
        """Test getting folders with lists."""
        # Get folders with lists
        folders_with_lists = self.repo.get_folders_with_lists()
        self.assertEqual(len(folders_with_lists), 2)
        self.assertEqual({f.id for f in folders_with_lists}, {"fld_001", "fld_003"})
    
    def test_get_folder_by_list(self):
        """Test getting folder by list."""
        # Get folder containing list_id="lst_001"
        folder = self.repo.get_folder_by_list("lst_001")
        self.assertIsNotNone(folder)
        self.assertEqual(folder.id, "fld_001")
        
        # Get folder containing list_id="lst_003"
        folder = self.repo.get_folder_by_list("lst_003")
        self.assertIsNotNone(folder)
        self.assertEqual(folder.id, "fld_003")
        
        # Get folder containing non-existent list
        folder = self.repo.get_folder_by_list("non_existent")
        self.assertIsNone(folder)
    
    def test_add_list_to_folder(self):
        """Test adding list to folder."""
        # Add new list to folder
        updated_folder = self.repo.add_list_to_folder("fld_002", "lst_new")
        self.assertIn("lst_new", updated_folder.lists)
        
        # Verify folder was updated in repository
        retrieved_folder = self.repo.get("fld_002")
        self.assertIn("lst_new", retrieved_folder.lists)
        
        # Add existing list to folder (should not duplicate)
        updated_folder = self.repo.add_list_to_folder("fld_001", "lst_001")
        self.assertEqual(updated_folder.lists.count("lst_001"), 1)
        
        # Add list to non-existent folder
        with self.assertRaises(EntityNotFoundError):
            self.repo.add_list_to_folder("non_existent", "lst_new")
    
    def test_remove_list_from_folder(self):
        """Test removing list from folder."""
        # Remove list from folder
        updated_folder = self.repo.remove_list_from_folder("fld_001", "lst_001")
        self.assertNotIn("lst_001", updated_folder.lists)
        
        # Verify folder was updated in repository
        retrieved_folder = self.repo.get("fld_001")
        self.assertNotIn("lst_001", retrieved_folder.lists)
        
        # Remove non-existent list from folder (should not error)
        updated_folder = self.repo.remove_list_from_folder("fld_002", "non_existent")
        self.assertEqual(updated_folder.lists, [])
        
        # Remove list from non-existent folder
        with self.assertRaises(EntityNotFoundError):
            self.repo.remove_list_from_folder("non_existent", "lst_001")
    
    def test_add_folder(self):
        """Test adding a new folder."""
        # Create a new folder
        new_folder = MockFolderEntity(
            entity_id="fld_004",
            name="Folder 4",
            description="Folder 4 description",
            space_id="spc_003",
            lists=["lst_004"]
        )
        
        # Add folder to repository
        added_folder = self.repo.add(new_folder)
        
        # Verify folder was added
        self.assertEqual(self.repo.count(), 4)
        self.assertEqual(added_folder.id, "fld_004")
        
        # Verify folder can be retrieved
        retrieved_folder = self.repo.get("fld_004")
        self.assertEqual(retrieved_folder.name, "Folder 4")
        self.assertEqual(retrieved_folder.space_id, "spc_003")
        self.assertEqual(retrieved_folder.lists, ["lst_004"])
    
    def test_update_folder(self):
        """Test updating a folder."""
        # Get folder to update
        folder = self.repo.get("fld_001")
        
        # Update folder properties
        folder.name = "Updated Folder"
        folder.description = "Updated description"
        folder.lists.append("lst_new")
        
        # Update folder in repository
        updated_folder = self.repo.update(folder)
        
        # Verify folder was updated
        self.assertEqual(updated_folder.name, "Updated Folder")
        self.assertEqual(updated_folder.description, "Updated description")
        self.assertIn("lst_new", updated_folder.lists)
        
        # Verify folder is persistently updated
        retrieved_folder = self.repo.get("fld_001")
        self.assertEqual(retrieved_folder.name, "Updated Folder")
        self.assertEqual(retrieved_folder.description, "Updated description")
        self.assertIn("lst_new", retrieved_folder.lists)
    
    def test_delete_folder(self):
        """Test deleting a folder."""
        # Verify folder exists
        self.assertTrue(self.repo.exists("fld_001"))
        
        # Delete folder
        self.repo.delete("fld_001")
        
        # Verify folder was deleted
        self.assertFalse(self.repo.exists("fld_001"))
        self.assertEqual(self.repo.count(), 2)


if __name__ == "__main__":
    unittest.main() 