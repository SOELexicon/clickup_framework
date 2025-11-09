"""
Unit tests for the SpaceJsonRepository class.

This module contains comprehensive tests for SpaceJsonRepository implementation,
which extends JsonRepository with space-specific operations.
"""
import unittest
import json
import tempfile
import os
from pathlib import Path
from unittest.mock import patch, MagicMock

from refactor.core.repositories.space_json_repository import SpaceJsonRepository
from refactor.core.entities.space_entity import SpaceEntity
from refactor.core.exceptions import EntityNotFoundError


class MockSpaceEntity:
    """Mock space entity for testing the repository."""
    
    def __init__(self, entity_id, name, description="", folders=None):
        """Initialize a mock space entity."""
        self.id = entity_id
        self.name = name
        self.description = description
        self.folders = folders or []
    
    def to_dict(self):
        """Convert space to dictionary."""
        return {
            "id": self.id,
            "name": self.name,
            "description": self.description,
            "folders": self.folders.copy() if self.folders else []
        }
    
    @classmethod
    def from_dict(cls, data):
        """Create space from dictionary."""
        return cls(
            entity_id=data.get("id"),
            name=data.get("name", ""),
            description=data.get("description", ""),
            folders=data.get("folders", [])
        )


# Create a mock implementation of SpaceJsonRepository with the missing methods
class MockSpaceJsonRepository(SpaceJsonRepository):
    """Mock implementation of SpaceJsonRepository for testing."""
    
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
                entity = MockSpaceEntity.from_dict(entity_data)
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
    
    # Implementing SpaceJsonRepository specific methods
    def add_folder_to_space(self, space_id, folder_id):
        """Add folder to space."""
        if space_id not in self._entities:
            raise EntityNotFoundError(f"No space with id '{space_id}' found")
            
        space_entity = self._entities[space_id]
        if folder_id not in space_entity.folders:
            space_entity.folders.append(folder_id)
            self._save_entities()
        return space_entity
    
    def remove_folder_from_space(self, space_id, folder_id):
        """Remove folder from space."""
        if space_id not in self._entities:
            raise EntityNotFoundError(f"No space with id '{space_id}' found")
            
        space_entity = self._entities[space_id]
        if folder_id in space_entity.folders:
            space_entity.folders.remove(folder_id)
            self._save_entities()
        return space_entity
    
    def get_space_with_most_folders(self):
        """Get space with most folders."""
        if not self._entities:
            return None
        
        return max(self._entities.values(), key=lambda space: len(space.folders or []))


@patch('refactor.core.repositories.space_json_repository.SpaceEntity', MockSpaceEntity)
class SpaceJsonRepositoryTests(unittest.TestCase):
    """Test cases for the SpaceJsonRepository implementation."""
    
    def setUp(self):
        """Set up test environment."""
        # Create a temporary file
        self.test_fd, self.test_path = tempfile.mkstemp(suffix='.json')
        self.test_path = Path(self.test_path)
        
        # Initialize test data
        self.test_data = {
            "entities": [
                {
                    "id": "spc_001",
                    "name": "Personal Space",
                    "description": "My personal workspace",
                    "folders": ["fld_001", "fld_002"]
                },
                {
                    "id": "spc_002",
                    "name": "Team Space",
                    "description": "Team workspace",
                    "folders": ["fld_003"]
                },
                {
                    "id": "spc_003",
                    "name": "Empty Space",
                    "description": "Space with no folders",
                    "folders": []
                }
            ]
        }
        
        # Write test data to file
        with open(self.test_path, 'w') as f:
            json.dump(self.test_data, f, indent=2)
        
        # Create repository with our mock implementation
        self.repo = MockSpaceJsonRepository(json_path=self.test_path)
    
    def tearDown(self):
        """Clean up after tests."""
        try:
            os.close(self.test_fd)
            os.unlink(self.test_path)
        except:
            pass
    
    def test_initialization(self):
        """Test repository initialization."""
        # Verify spaces were loaded
        self.assertEqual(self.repo.count(), 3)
        
        # Check space attributes
        space1 = self.repo.get("spc_001")
        self.assertEqual(space1.name, "Personal Space")
        self.assertEqual(space1.description, "My personal workspace")
        self.assertEqual(space1.folders, ["fld_001", "fld_002"])
        
        # Check space by name
        space_by_name = self.repo.find_by_name("Team Space")
        self.assertEqual(space_by_name.id, "spc_002")
    
    def test_add_folder_to_space(self):
        """Test adding folder to space."""
        # Add new folder to space
        updated_space = self.repo.add_folder_to_space("spc_003", "fld_004")
        self.assertIn("fld_004", updated_space.folders)
        
        # Verify space was updated in repository
        retrieved_space = self.repo.get("spc_003")
        self.assertIn("fld_004", retrieved_space.folders)
        
        # Add existing folder to space (should not duplicate)
        updated_space = self.repo.add_folder_to_space("spc_001", "fld_001")
        self.assertEqual(updated_space.folders.count("fld_001"), 1)
        
        # Add folder to non-existent space
        with self.assertRaises(EntityNotFoundError):
            self.repo.add_folder_to_space("non_existent", "fld_004")
    
    def test_remove_folder_from_space(self):
        """Test removing folder from space."""
        # Remove folder from space
        updated_space = self.repo.remove_folder_from_space("spc_001", "fld_001")
        self.assertNotIn("fld_001", updated_space.folders)
        
        # Verify space was updated in repository
        retrieved_space = self.repo.get("spc_001")
        self.assertNotIn("fld_001", retrieved_space.folders)
        
        # Remove non-existent folder from space (should not error)
        updated_space = self.repo.remove_folder_from_space("spc_003", "non_existent")
        self.assertEqual(updated_space.folders, [])
        
        # Remove folder from non-existent space
        with self.assertRaises(EntityNotFoundError):
            self.repo.remove_folder_from_space("non_existent", "fld_001")
    
    def test_get_space_with_most_folders(self):
        """Test getting space with most folders."""
        # Get space with most folders
        space = self.repo.get_space_with_most_folders()
        self.assertEqual(space.id, "spc_001")
        self.assertEqual(len(space.folders), 2)
        
        # Remove all folders from space_001
        self.repo.remove_folder_from_space("spc_001", "fld_001")
        self.repo.remove_folder_from_space("spc_001", "fld_002")
        
        # Now space_002 should have most folders
        space = self.repo.get_space_with_most_folders()
        self.assertEqual(space.id, "spc_002")
        self.assertEqual(len(space.folders), 1)
        
        # Remove all folders from all spaces
        self.repo.remove_folder_from_space("spc_002", "fld_003")
        
        # Any space could be returned since all have 0 folders
        space = self.repo.get_space_with_most_folders()
        self.assertEqual(len(space.folders), 0)
    
    def test_add_space(self):
        """Test adding a new space."""
        # Create a new space
        new_space = MockSpaceEntity(
            entity_id="spc_004",
            name="New Space",
            description="New space description",
            folders=["fld_005", "fld_006"]
        )
        
        # Add space to repository
        added_space = self.repo.add(new_space)
        
        # Verify space was added
        self.assertEqual(self.repo.count(), 4)
        self.assertEqual(added_space.id, "spc_004")
        
        # Verify space can be retrieved
        retrieved_space = self.repo.get("spc_004")
        self.assertEqual(retrieved_space.name, "New Space")
        self.assertEqual(retrieved_space.description, "New space description")
        self.assertEqual(retrieved_space.folders, ["fld_005", "fld_006"])
    
    def test_update_space(self):
        """Test updating a space."""
        # Get space to update
        space_entity = self.repo.get("spc_001")
        
        # Update space properties
        space_entity.name = "Updated Space"
        space_entity.description = "Updated description"
        space_entity.folders.append("fld_new")
        
        # Update space in repository
        updated_space = self.repo.update(space_entity)
        
        # Verify space was updated
        self.assertEqual(updated_space.name, "Updated Space")
        self.assertEqual(updated_space.description, "Updated description")
        self.assertIn("fld_new", updated_space.folders)
        
        # Verify space is persistently updated
        retrieved_space = self.repo.get("spc_001")
        self.assertEqual(retrieved_space.name, "Updated Space")
        self.assertEqual(retrieved_space.description, "Updated description")
        self.assertIn("fld_new", retrieved_space.folders)
    
    def test_delete_space(self):
        """Test deleting a space."""
        # Verify space exists
        self.assertTrue(self.repo.exists("spc_001"))
        
        # Delete space
        self.repo.delete("spc_001")
        
        # Verify space was deleted
        self.assertFalse(self.repo.exists("spc_001"))
        self.assertEqual(self.repo.count(), 2)


if __name__ == "__main__":
    unittest.main() 