"""
Test ID: TEST-006
Test Name: Mock Repository Factory Testing
Component: Tests/Utils
Priority: Medium
Test Type: Unit Test

Test Objective:
Verify that the MockRepositoryFactory correctly creates repository instances
for different entity types.
"""
import unittest
import uuid

from refactor.tests.utils.mock_repository import MockRepositoryFactory, InMemoryRepository
from refactor.core.entities.task_entity import TaskEntity
from refactor.core.entities.space_entity import SpaceEntity
from refactor.core.entities.folder_entity import FolderEntity
from refactor.core.entities.list_entity import ListEntity


class TestMockRepositoryFactory(unittest.TestCase):
    """
    Test suite for MockRepositoryFactory.
    
    This tests the creation of repository instances for different entity types.
    """
    
    def test_create_task_repository(self):
        """Test creating a task repository."""
        # Act
        repository = MockRepositoryFactory.create_task_repository()
        
        # Assert
        self.assertIsInstance(repository, InMemoryRepository)
        self.assertEqual(repository._entity_class, TaskEntity)
    
    def test_create_space_repository(self):
        """Test creating a space repository."""
        # Act
        repository = MockRepositoryFactory.create_space_repository()
        
        # Assert
        self.assertIsInstance(repository, InMemoryRepository)
        self.assertEqual(repository._entity_class, SpaceEntity)
    
    def test_create_folder_repository(self):
        """Test creating a folder repository."""
        # Act
        repository = MockRepositoryFactory.create_folder_repository()
        
        # Assert
        self.assertIsInstance(repository, InMemoryRepository)
        self.assertEqual(repository._entity_class, FolderEntity)
    
    def test_create_list_repository(self):
        """Test creating a list repository."""
        # Act
        repository = MockRepositoryFactory.create_list_repository()
        
        # Assert
        self.assertIsInstance(repository, InMemoryRepository)
        self.assertEqual(repository._entity_class, ListEntity)
    
    def test_create_all_repositories(self):
        """Test creating all repositories."""
        # Act
        repositories = MockRepositoryFactory.create_all_repositories()
        
        # Assert
        self.assertIsInstance(repositories, dict)
        self.assertEqual(len(repositories), 4)
        
        # Check that all repository types are included
        self.assertIn("task", repositories)
        self.assertIn("space", repositories)
        self.assertIn("folder", repositories)
        self.assertIn("list", repositories)
        
        # Check that each repository is of the correct type
        self.assertIsInstance(repositories["task"], InMemoryRepository)
        self.assertEqual(repositories["task"]._entity_class, TaskEntity)
        
        self.assertIsInstance(repositories["space"], InMemoryRepository)
        self.assertEqual(repositories["space"]._entity_class, SpaceEntity)
        
        self.assertIsInstance(repositories["folder"], InMemoryRepository)
        self.assertEqual(repositories["folder"]._entity_class, FolderEntity)
        
        self.assertIsInstance(repositories["list"], InMemoryRepository)
        self.assertEqual(repositories["list"]._entity_class, ListEntity)
    
    def test_repositories_are_independent(self):
        """Test that repositories created by the factory are independent."""
        # Arrange
        repositories = MockRepositoryFactory.create_all_repositories()
        task_repo = repositories["task"]
        space_repo = repositories["space"]
        
        # Add a task to the task repository
        task_id = "tsk_" + uuid.uuid4().hex[:8]
        task = TaskEntity(entity_id=task_id, name="Test Task")
        task_repo.add(task)
        
        # Add a space to the space repository
        space_id = "spc_" + uuid.uuid4().hex[:8]
        space = SpaceEntity(entity_id=space_id, name="Test Space")
        space_repo.add(space)
        
        # Act/Assert
        # Task repository should have 1 entity, space repository should have 1 entity
        self.assertEqual(task_repo.count(), 1)
        self.assertEqual(space_repo.count(), 1)
        
        # Clearing one repository shouldn't affect the other
        task_repo.clear()
        self.assertEqual(task_repo.count(), 0)
        self.assertEqual(space_repo.count(), 1)


# Run the tests
if __name__ == "__main__":
    unittest.main() 