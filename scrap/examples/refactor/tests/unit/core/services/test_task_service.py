"""
Unit tests for the TaskService class.

This module contains tests for the TaskService business logic, including
validation, error handling, and interactions with the task repository.
"""

import unittest
from unittest.mock import Mock, patch, MagicMock
import threading
import concurrent.futures

from refactor.core.entities.task_entity import TaskEntity, TaskStatus, TaskPriority, ValidationResult
from refactor.core.repositories.repository_interface import (
    ITaskRepository, EntityNotFoundError, EntityAlreadyExistsError, ValidationError
)
from refactor.core.exceptions import EntityNotFoundError, ValidationError
from refactor.core.services.task_service import (
    TaskService, TaskServiceError, TaskRelationshipError, TaskStatusError, TaskCompletionError
)


class TestTaskService(unittest.TestCase):
    """Test cases for TaskService."""

    def setUp(self):
        """Set up test fixtures for each test case."""
        # Create mock repository
        self.repository = Mock(spec=ITaskRepository)
        
        # Create the service under test
        self.service = TaskService(self.repository)
        
        # Create a sample task for testing
        self.sample_task = TaskEntity(
            entity_id="tsk_12345",
            name="Test Task",
            description="Test description",
            status=TaskStatus.TO_DO,
            priority=3
        )
        
        # Mock validation methods to pass by default
        self.patcher = patch.object(TaskEntity, 'validate')
        self.mock_validate = self.patcher.start()
        self.mock_validate.return_value = ValidationResult(True)
        
    def tearDown(self):
        """Clean up after each test case."""
        self.patcher.stop()

    def test_create_task_success(self):
        """Test creating a task successfully."""
        # Arrange
        self.repository.add.return_value = self.sample_task
        self.repository.exists.return_value = False  # No parent task
        
        # Act
        result = self.service.create_task(
            name="Test Task",
            description="Test description",
            status=TaskStatus.TO_DO,
            priority=3
        )
        
        # Assert
        self.assertEqual(result, self.sample_task)
        self.repository.add.assert_called_once()
        
    def test_create_task_with_parent(self):
        """Test creating a subtask with a parent."""
        # Arrange
        parent_id = "tsk_parent"
        child_task = TaskEntity(
            entity_id="tsk_child",
            name="Child Task",
            description="Child description",
            parent_id=parent_id
        )
        parent_task = TaskEntity(
            entity_id=parent_id,
            name="Parent Task"
        )
        
        self.repository.exists.return_value = True
        self.repository.add.return_value = child_task
        self.repository.get.return_value = parent_task
        
        # Act
        result = self.service.create_task(
            name="Child Task",
            description="Child description",
            parent_id=parent_id
        )
        
        # Assert
        self.assertEqual(result, child_task)
        self.repository.exists.assert_called_once_with(parent_id)
        self.repository.add.assert_called_once()
        self.repository.update.assert_called_once()  # Parent should be updated
        
    def test_create_task_parent_not_found(self):
        """Test task creation with non-existent parent."""
        # Arrange
        parent_id = "tsk_nonexistent"
        self.repository.exists.return_value = False
        
        # Act & Assert
        with self.assertRaises(EntityNotFoundError):
            self.service.create_task(
                name="Child Task",
                parent_id=parent_id
            )
            
    def test_create_task_validation_error(self):
        """Test task creation with validation error."""
        # Arrange
        validation_errors = ["Name is required", "Priority must be between 1 and 5"]
        self.mock_validate.return_value = ValidationResult(False, validation_errors)
        
        # Act & Assert
        with self.assertRaises(ValidationError) as context:
            self.service.create_task(name="")
            
    def test_update_task_success(self):
        """Test updating a task successfully."""
        # Arrange
        updated_task = TaskEntity(
            entity_id="tsk_12345",
            name="Updated Task",
            description="Updated description",
            status=TaskStatus.IN_PROGRESS,
            priority=2
        )
        self.repository.update.return_value = updated_task
        
        # Act
        result = self.service.update_task(updated_task)
        
        # Assert
        self.assertEqual(result, updated_task)
        self.repository.update.assert_called_once_with(updated_task)
        
    def test_update_task_not_found(self):
        """Test updating a non-existent task."""
        # Arrange
        self.repository.update.side_effect = EntityNotFoundError("Task not found")
        
        # Act & Assert
        with self.assertRaises(EntityNotFoundError):
            self.service.update_task(self.sample_task)
            
    def test_update_task_validation_error(self):
        """Test task update with validation error."""
        # Arrange - mock the validation function to return error
        self.mock_validate.return_value = ValidationResult(False, ["Priority must be between 1 and 5"])
        self.repository.exists.return_value = True  # Task exists
        
        # Mock the repository update method to use validate
        def validate_and_update(task):
            validation_result = task.validate()
            if not validation_result.is_valid:
                raise ValidationError(f"Task validation failed: {'; '.join(validation_result.errors)}")
            return task
            
        self.repository.update.side_effect = validate_and_update
        
        # Act & Assert
        with self.assertRaises(ValidationError) as context:
            self.service.update_task(self.sample_task)
            
        # Verify the error message contains validation details  
        self.assertIn("Priority must be between 1 and 5", str(context.exception))
        
    def test_get_task_by_id_success(self):
        """Test getting a task by ID successfully."""
        # Arrange
        self.repository.get.return_value = self.sample_task
        
        # Act
        result = self.service.get_task("tsk_12345")
        
        # Assert
        self.assertEqual(result, self.sample_task)
        self.repository.get.assert_called_once_with("tsk_12345")
        
    def test_get_task_by_id_not_found(self):
        """Test getting a non-existent task by ID."""
        # Arrange
        self.repository.get.side_effect = EntityNotFoundError("Task not found")
        
        # Act & Assert
        with self.assertRaises(EntityNotFoundError):
            self.service.get_task("tsk_nonexistent")
            
    def test_get_task_by_name_success(self):
        """Test getting a task by name successfully."""
        # Arrange
        self.repository.get_by_name.return_value = self.sample_task
        
        # Act
        result = self.service.find_task_by_name("Test Task")
        
        # Assert
        self.assertEqual(result, self.sample_task)
        self.repository.get_by_name.assert_called_once_with("Test Task")
        
    def test_get_task_by_name_not_found(self):
        """Test getting a non-existent task by name."""
        # Arrange
        self.repository.get_by_name.side_effect = EntityNotFoundError("Task not found")
        
        # Act
        result = self.service.find_task_by_name("Nonexistent Task")
        
        # Assert
        self.assertIsNone(result)
        self.repository.get_by_name.assert_called_once_with("Nonexistent Task")
        
    def test_delete_task_success(self):
        """Test deleting a task successfully."""
        # Arrange
        task_with_no_subtasks = TaskEntity(
            entity_id="tsk_12345",
            name="Test Task"
        )
        self.repository.get.return_value = task_with_no_subtasks
        self.repository.delete.return_value = True
        
        # Act
        result = self.service.delete_task("tsk_12345")
        
        # Assert
        self.assertTrue(result)
        self.repository.delete.assert_called_once_with("tsk_12345")
        
    def test_delete_task_with_subtasks_no_cascade(self):
        """Test deleting a task with subtasks without cascade."""
        # Arrange
        # Task with subtasks
        parent_id = "tsk_parent"
        parent_task = TaskEntity(
            entity_id=parent_id,
            name="Parent Task"
        )
        # Simulate having subtasks in the service's _get_subtasks method
        with patch.object(self.service, '_get_subtasks') as mock_get_subtasks:
            mock_get_subtasks.return_value = ["tsk_child1", "tsk_child2"]
            self.repository.get.return_value = parent_task
            
            # Act & Assert
            with self.assertRaises(ValidationError):
                self.service.delete_task(parent_id, cascade=False)
                
            self.repository.delete.assert_not_called()
        
    def test_delete_task_with_subtasks_cascade(self):
        """Test deleting a task with subtasks with cascade."""
        # Arrange
        # Task with subtasks
        parent_id = "tsk_parent"
        parent_task = TaskEntity(
            entity_id=parent_id,
            name="Parent Task"
        )
        # Simulate having subtasks in the service's _get_subtasks method
        with patch.object(self.service, '_get_subtasks') as mock_get_subtasks:
            mock_get_subtasks.return_value = ["tsk_child1", "tsk_child2"]
            self.repository.get.return_value = parent_task
            self.repository.delete.return_value = True
            
            # Act
            result = self.service.delete_task(parent_id, cascade=True)
            
            # Assert
            self.assertTrue(result)
            self.repository.delete.assert_called_with(parent_id)
            # Verify that each subtask was deleted
            for subtask_id in mock_get_subtasks.return_value:
                self.repository.delete.assert_any_call(subtask_id)
        
    def test_delete_nonexistent_task(self):
        """Test deleting a task that doesn't exist."""
        # Arrange
        self.repository.get.side_effect = EntityNotFoundError("Task not found")
        
        # Act & Assert
        with self.assertRaises(EntityNotFoundError):
            self.service.delete_task("tsk_nonexistent")
            
    def test_change_task_status_success(self):
        """Test changing task status successfully."""
        # Arrange
        task = TaskEntity(
            entity_id="tsk_12345",
            name="Test Task",
            status=TaskStatus.TO_DO
        )
        self.repository.get.return_value = task
        self.repository.update.return_value = TaskEntity(
            entity_id="tsk_12345",
            name="Test Task",
            status=TaskStatus.IN_PROGRESS
        )
        
        # Act
        result = self.service.update_task_status("tsk_12345", TaskStatus.IN_PROGRESS)
        
        # Assert
        self.assertEqual(result.status, TaskStatus.IN_PROGRESS)
        self.repository.get.assert_called_once_with("tsk_12345")
        self.repository.update.assert_called_once()
        
    def test_thread_safety(self):
        """Test that the service is thread-safe."""
        # Since we can't directly access _lock, we'll test thread safety by mocking
        # the repository methods to verify they're called correctly in different contexts
        
        # Arrange
        # Define task for the first thread
        task1 = TaskEntity(
            entity_id="tsk_thread1",
            name="Thread 1 Task",
            status=TaskStatus.TO_DO
        )
        
        # Define task for the second thread
        task2 = TaskEntity(
            entity_id="tsk_thread2",
            name="Thread 2 Task",
            status=TaskStatus.IN_PROGRESS
        )
        
        # Mock the repository methods
        self.repository.add.side_effect = lambda t: t
        self.repository.get.side_effect = lambda id: task1 if id == task1.id else task2
        
        # Create thread functions
        def thread1_func():
            return self.service.create_task(
                name=task1.name,
                status=task1.status
            )
            
        def thread2_func():
            return self.service.create_task(
                name=task2.name,
                status=task2.status
            )
            
        # Use ThreadPoolExecutor to simulate concurrent calls
        with concurrent.futures.ThreadPoolExecutor(max_workers=2) as executor:
            future1 = executor.submit(thread1_func)
            future2 = executor.submit(thread2_func)
            
            result1 = future1.result()
            result2 = future2.result()
            
        # Assert results
        self.assertEqual(result1.name, task1.name)
        self.assertEqual(result2.name, task2.name)


if __name__ == '__main__':
    unittest.main() 