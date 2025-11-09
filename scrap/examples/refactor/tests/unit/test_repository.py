"""
Test ID: TEST-005
Test Name: In-Memory Repository Testing
Component: Tests/Utils
Priority: High
Test Type: Unit Test

Test Objective:
Verify that the InMemoryRepository correctly implements the Repository interface
and provides in-memory storage capabilities for testing.
"""
import unittest
from typing import List, Optional, Dict, Any

from refactor.core.entities.base_entity import BaseEntity, EntityType, ValidationResult
from refactor.core.exceptions import EntityNotFoundError, EntityAlreadyExistsError, ValidationError
from refactor.tests.utils.mock_repository import InMemoryRepository


class TestEntity(BaseEntity):
    """Simple entity implementation for testing."""
    
    def __init__(self, entity_id: str = None, name: str = "Test Entity"):
        """Initialize a test entity."""
        super().__init__(entity_id=entity_id, name=name)
        self.value = 0
        
    def get_entity_type(self):
        """Get the entity type."""
        return EntityType.TASK
        
    def _validate(self, result: ValidationResult) -> None:
        """Validate the entity."""
        # No additional validation required for test entity
        pass
        
    def _to_dict(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Convert to dictionary representation."""
        data['value'] = self.value
        return data
        
    @classmethod
    def _from_dict(cls, data: Dict[str, Any]) -> 'BaseEntity':
        """Create from dictionary representation."""
        entity = cls(
            entity_id=data.get('id'),
            name=data.get('name', 'Test Entity')
        )
        entity.value = data.get('value', 0)
        return entity


class TestInMemoryRepository(unittest.TestCase):
    """
    Test suite for InMemoryRepository.
    
    This tests the implementation of the Repository interface
    by the InMemoryRepository class.
    """
    
    def setUp(self):
        """Set up test fixtures."""
        self.repository = InMemoryRepository(TestEntity)
        
        # Add some test entities
        self.entity1 = TestEntity(entity_id="test1", name="Entity 1")
        self.entity1.value = 10
        self.repository.add(self.entity1)
        
        self.entity2 = TestEntity(entity_id="test2", name="Entity 2")
        self.entity2.value = 20
        self.repository.add(self.entity2)
        
        self.entity3 = TestEntity(entity_id="test3", name="Entity 3")
        self.entity3.value = 30
        self.repository.add(self.entity3)
    
    def test_add_entity(self):
        """Test adding an entity to the repository."""
        # Arrange
        entity = TestEntity(entity_id="test4", name="Entity 4")
        entity.value = 40
        
        # Act
        added_entity = self.repository.add(entity)
        
        # Assert
        self.assertEqual(added_entity.id, "test4")
        self.assertEqual(added_entity.name, "Entity 4")
        self.assertEqual(added_entity.value, 40)
        
        # Verify it was actually added
        stored_entity = self.repository.get("test4")
        self.assertEqual(stored_entity.id, "test4")
        self.assertEqual(stored_entity.name, "Entity 4")
        self.assertEqual(stored_entity.value, 40)
    
    def test_add_duplicate_entity(self):
        """Test adding an entity with a duplicate ID raises an error."""
        # Arrange
        entity = TestEntity(entity_id="test1", name="Duplicate Entity")
        
        # Act/Assert
        with self.assertRaises(EntityAlreadyExistsError):
            self.repository.add(entity)
    
    def test_get_entity(self):
        """Test getting an entity by ID."""
        # Act
        entity = self.repository.get("test2")
        
        # Assert
        self.assertEqual(entity.id, "test2")
        self.assertEqual(entity.name, "Entity 2")
        self.assertEqual(entity.value, 20)
    
    def test_get_nonexistent_entity(self):
        """Test getting a nonexistent entity raises an error."""
        # Act/Assert
        with self.assertRaises(EntityNotFoundError):
            self.repository.get("nonexistent")
    
    def test_update_entity(self):
        """Test updating an entity."""
        # Arrange
        entity = self.repository.get("test1")
        entity.name = "Updated Entity 1"
        entity.value = 15
        
        # Act
        updated_entity = self.repository.update(entity)
        
        # Assert
        self.assertEqual(updated_entity.id, "test1")
        self.assertEqual(updated_entity.name, "Updated Entity 1")
        self.assertEqual(updated_entity.value, 15)
        
        # Verify it was actually updated
        stored_entity = self.repository.get("test1")
        self.assertEqual(stored_entity.id, "test1")
        self.assertEqual(stored_entity.name, "Updated Entity 1")
        self.assertEqual(stored_entity.value, 15)
    
    def test_update_nonexistent_entity(self):
        """Test updating a nonexistent entity raises an error."""
        # Arrange
        entity = TestEntity(entity_id="nonexistent", name="Nonexistent Entity")
        
        # Act/Assert
        with self.assertRaises(EntityNotFoundError):
            self.repository.update(entity)
    
    def test_delete_entity(self):
        """Test deleting an entity."""
        # Act
        self.repository.delete("test3")
        
        # Assert - should not be found
        self.assertFalse(self.repository.exists("test3"))
        
        # Trying to get the entity should raise an error
        with self.assertRaises(EntityNotFoundError):
            self.repository.get("test3")
    
    def test_delete_nonexistent_entity(self):
        """Test deleting a nonexistent entity raises an error."""
        # Act/Assert
        with self.assertRaises(EntityNotFoundError):
            self.repository.delete("nonexistent")
    
    def test_get_all(self):
        """Test getting all entities."""
        # Act
        entities = self.repository.get_all()
        
        # Assert
        self.assertEqual(len(entities), 3)
        
        # Check that all entities are included
        entity_ids = [entity.id for entity in entities]
        self.assertIn("test1", entity_ids)
        self.assertIn("test2", entity_ids)
        self.assertIn("test3", entity_ids)
    
    def test_find_by_name(self):
        """Test finding an entity by name."""
        # Act
        entity = self.repository.find_by_name("Entity 2")
        
        # Assert
        self.assertIsNotNone(entity)
        self.assertEqual(entity.id, "test2")
        self.assertEqual(entity.name, "Entity 2")
        self.assertEqual(entity.value, 20)
    
    def test_find_by_name_nonexistent(self):
        """Test finding a nonexistent entity by name returns None."""
        # Act
        entity = self.repository.find_by_name("Nonexistent Entity")
        
        # Assert
        self.assertIsNone(entity)
    
    def test_find_by_property(self):
        """Test finding entities by a property value."""
        # Act
        entities = self.repository.find_by_property("value", 20)
        
        # Assert
        self.assertEqual(len(entities), 1)
        self.assertEqual(entities[0].id, "test2")
        self.assertEqual(entities[0].name, "Entity 2")
        self.assertEqual(entities[0].value, 20)
    
    def test_find_by_property_multiple(self):
        """Test finding multiple entities by a property value."""
        # Arrange
        entity4 = TestEntity(entity_id="test4", name="Entity 4")
        entity4.value = 20  # Same value as entity2
        self.repository.add(entity4)
        
        # Act
        entities = self.repository.find_by_property("value", 20)
        
        # Assert
        self.assertEqual(len(entities), 2)
        
        # Check that both entities with value=20 are included
        entity_ids = [entity.id for entity in entities]
        self.assertIn("test2", entity_ids)
        self.assertIn("test4", entity_ids)
    
    def test_find_by_property_nonexistent(self):
        """Test finding entities by a nonexistent property value returns an empty list."""
        # Act
        entities = self.repository.find_by_property("value", 999)
        
        # Assert
        self.assertEqual(len(entities), 0)
    
    def test_register_filter(self):
        """Test registering a filter for get_all operations."""
        # Arrange
        def filter_by_value(entity: TestEntity) -> bool:
            return entity.value > 15
        
        # Act
        self.repository.register_filter(filter_by_value)
        entities = self.repository.get_all()
        
        # Assert
        self.assertEqual(len(entities), 2)  # Only entity2 and entity3 have value > 15
        
        # Check that only entities with value > 15 are included
        entity_ids = [entity.id for entity in entities]
        self.assertNotIn("test1", entity_ids)  # value = 10
        self.assertIn("test2", entity_ids)     # value = 20
        self.assertIn("test3", entity_ids)     # value = 30
    
    def test_register_multiple_filters(self):
        """Test registering multiple filters for get_all operations."""
        # Arrange
        def filter_by_min_value(entity: TestEntity) -> bool:
            return entity.value > 15
            
        def filter_by_max_value(entity: TestEntity) -> bool:
            return entity.value < 25
        
        # Act
        self.repository.register_filter(filter_by_min_value)
        self.repository.register_filter(filter_by_max_value)
        entities = self.repository.get_all()
        
        # Assert
        self.assertEqual(len(entities), 1)  # Only entity2 has 15 < value < 25
        self.assertEqual(entities[0].id, "test2")
    
    def test_clear_filters(self):
        """Test clearing filters."""
        # Arrange
        def filter_func(entity: TestEntity) -> bool:
            return entity.value > 15
            
        self.repository.register_filter(filter_func)
        
        # Act
        self.repository.clear_filters()
        entities = self.repository.get_all()
        
        # Assert
        self.assertEqual(len(entities), 3)  # All entities should be returned
    
    def test_count(self):
        """Test counting entities."""
        # Act
        count = self.repository.count()
        
        # Assert
        self.assertEqual(count, 3)
    
    def test_clear(self):
        """Test clearing all entities."""
        # Act
        self.repository.clear()
        
        # Assert
        self.assertEqual(self.repository.count(), 0)
        self.assertEqual(len(self.repository.get_all()), 0)
    
    def test_entity_isolation(self):
        """Test that repository operations maintain entity isolation."""
        # Arrange
        entity = self.repository.get("test1")
        original_value = entity.value
        
        # Act - modify the entity outside the repository
        entity.value = 999
        
        # Assert - the stored entity should not be affected
        stored_entity = self.repository.get("test1")
        self.assertEqual(stored_entity.value, original_value)
        self.assertNotEqual(stored_entity.value, 999)


# Run the tests
if __name__ == "__main__":
    unittest.main() 