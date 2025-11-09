#!/usr/bin/env python3
"""
Integration tests for error handling in the repository interfaces.

These tests verify that errors are properly propagated and handled
when they occur in the repository layer.
"""
import unittest
import tempfile
import json
import os
from pathlib import Path
from unittest.mock import patch, MagicMock

from refactor.core.repositories.repository_interface import (
    RepositoryError,
    EntityNotFoundError,
    EntityAlreadyExistsError,
    ValidationError
)

from refactor.core.repositories.task_repository import TaskRepository
from refactor.core.entities.task_entity import TaskEntity


# Create a real TaskEntity class for testing to avoid MagicMock issues
class TestTaskEntity:
    """A simple implementation of TaskEntity for testing."""
    
    def __init__(self, entity_id, name):
        self.id = entity_id
        self.name = name
        self.status = "to do"
        self.priority = 1
        self.tags = []
        self.description = ""
        self.parent_id = None
    
    # Create a copy of this entity
    def copy(self):
        """Create a copy of this entity."""
        new_entity = TestTaskEntity(self.id, self.name)
        new_entity.status = self.status
        new_entity.priority = self.priority
        new_entity.tags = list(self.tags)
        new_entity.description = self.description
        new_entity.parent_id = self.parent_id
        return new_entity


class BasicErrorHandlingTests(unittest.TestCase):
    """Integration tests for error handling in repository interfaces."""
    
    def setUp(self):
        """Set up test environment."""
        # Create a temporary directory for test files
        self.temp_dir = tempfile.TemporaryDirectory()
        self.temp_path = Path(self.temp_dir.name)
        
        # Create a test file path
        self.test_file_path = self.temp_path / "test_error_handling.json"
        
        # Create initial template structure
        template_data = {
            "tasks": [
                {
                    "id": "tsk_test001",
                    "name": "Test Task 1",
                    "description": "Test task description",
                    "status": "to do",
                    "priority": 1,
                    "tags": ["test", "high-priority"],
                    "subtasks": []
                }
            ]
        }
        
        with open(self.test_file_path, 'w') as f:
            json.dump(template_data, f, indent=2)
            
        # Initialize repository
        self.task_repository = self._create_repository()
    
    def tearDown(self):
        """Clean up temporary files."""
        self.temp_dir.cleanup()
    
    def _create_repository(self):
        """Create and return a repository instance for testing."""
        return TaskRepository(json_path=self.test_file_path)
    
    def test_not_found_error(self):
        """Test that EntityNotFoundError is raised when entity doesn't exist."""
        # Attempt to get a non-existent task
        with self.assertRaises(EntityNotFoundError) as context:
            self.task_repository.get("non_existent_id")
        
        # Verify the error message contains useful information
        self.assertIn("not found", str(context.exception).lower())
        
        # Attempt to get by name
        with self.assertRaises(EntityNotFoundError) as context:
            self.task_repository.get_by_name("Non-Existent Task")
        
        # Verify the error message contains useful information
        self.assertIn("not found", str(context.exception).lower())
    
    def test_already_exists_error(self):
        """Test that EntityAlreadyExistsError is raised for duplicate entities."""
        # Create a task with the same ID as an existing one
        duplicate_task = self._create_task_mock("tsk_test001", "Duplicate Task")
        
        # Attempt to add a task with duplicate ID
        with self.assertRaises(EntityAlreadyExistsError) as context:
            self.task_repository.add(duplicate_task)
        
        # Verify the error message contains useful information
        self.assertIn("already exists", str(context.exception).lower())
        
        # Create a task with the same name but different ID
        same_name_task = self._create_task_mock("tsk_different", "Test Task 1")
        
        # Attempt to add a task with duplicate name
        with self.assertRaises(EntityAlreadyExistsError) as context:
            self.task_repository.add(same_name_task)
        
        # Verify the error message contains useful information
        self.assertIn("already exists", str(context.exception).lower())
    
    def test_validation_error(self):
        """Test that ValidationError is raised for invalid updates."""
        # Reset the repository to have a clean state
        self.task_repository = self._create_repository()
        
        # Create a first task with a unique name
        task1 = self._create_task_mock("tsk_test1", "Validation Test Task A")
        self.task_repository.add(task1)
        
        # Create a second task with a different name
        task2 = self._create_task_mock("tsk_test2", "Validation Test Task B")
        original_task2 = task2.copy()  # Keep a copy of the original
        self.task_repository.add(task2)
        
        # Now try to update task2 to have the same name as task1
        task2_update = original_task2.copy()  # Start with a fresh copy
        task2_update.name = "Validation Test Task A"  # Same name as the first task
        
        # Attempt the update, which should fail
        with self.assertRaises(ValidationError) as context:
            self.task_repository.update(task2_update)
        
        # Verify the error message contains useful information
        self.assertIn("already in use", str(context.exception).lower())
    
    def test_error_inheritance(self):
        """Test that all specific errors inherit from RepositoryError."""
        # Create instances of specific errors
        not_found_error = EntityNotFoundError("Entity not found")
        already_exists_error = EntityAlreadyExistsError("Entity already exists")
        validation_error = ValidationError("Invalid entity")
        
        # Verify they are all instances of RepositoryError
        self.assertIsInstance(not_found_error, RepositoryError)
        self.assertIsInstance(already_exists_error, RepositoryError)
        self.assertIsInstance(validation_error, RepositoryError)
        
        # Verify that catching RepositoryError catches all specific errors
        caught = False
        try:
            raise EntityNotFoundError("Test error")
        except RepositoryError as e:
            caught = True
        self.assertTrue(caught)
    
    def test_error_propagation(self):
        """Test that errors properly propagate through method calls."""
        # Create a mock repository with a method that raises an error
        mock_repo = MagicMock()
        mock_repo.get.side_effect = EntityNotFoundError("Entity not found")
        
        # Create a function that calls the repository method
        def get_entity_name(repo, entity_id):
            entity = repo.get(entity_id)
            return entity.name
        
        # Call the function and verify the error propagates
        with self.assertRaises(EntityNotFoundError) as context:
            get_entity_name(mock_repo, "test_id")
        
        # Verify the error message is preserved
        self.assertIn("not found", str(context.exception).lower())

    def test_update_nonexistent_entity(self):
        """Test that updating a non-existent entity raises EntityNotFoundError."""
        # Create an entity that doesn't exist in the repository
        nonexistent_task = self._create_task_mock("tsk_nonexistent", "Nonexistent Task")
        
        # Attempt to update the non-existent entity
        with self.assertRaises(EntityNotFoundError) as context:
            self.task_repository.update(nonexistent_task)
            
        # Verify the error message contains useful information
        self.assertIn("not found", str(context.exception).lower())
        self.assertIn("tsk_nonexistent", str(context.exception))
    
    def test_delete_nonexistent_entity(self):
        """Test that deleting a non-existent entity raises EntityNotFoundError."""
        # Attempt to delete a non-existent entity
        with self.assertRaises(EntityNotFoundError):
            self.task_repository.delete("tsk_nonexistent")
    
    def test_get_by_name_case_sensitivity(self):
        """Test that get_by_name is case sensitive."""
        # Attempt to get a task with different case
        with self.assertRaises(EntityNotFoundError) as context:
            self.task_repository.get_by_name("test task 1")  # lowercase vs. "Test Task 1"
            
        # Verify the error message contains useful information
        self.assertIn("not found", str(context.exception).lower())
        
    def test_error_message_details(self):
        """Test that error messages contain detailed information."""
        # Test EntityNotFoundError message details
        try:
            self.task_repository.get("tsk_nonexistent")
        except EntityNotFoundError as e:
            error_message = str(e)
            self.assertIn("tsk_nonexistent", error_message)
            
        # Test EntityAlreadyExistsError message details
        duplicate_task = self._create_task_mock("tsk_test001", "Duplicate Task")
        
        try:
            self.task_repository.add(duplicate_task)
        except EntityAlreadyExistsError as e:
            error_message = str(e)
            self.assertIn("tsk_test001", error_message)
            
    def test_multiple_operations_after_error(self):
        """Test that repository remains usable after an error."""
        # Create a task with duplicate ID (should fail)
        duplicate_task = self._create_task_mock("tsk_test001", "Duplicate Task")
        
        # This operation should fail
        with self.assertRaises(EntityAlreadyExistsError):
            self.task_repository.add(duplicate_task)
            
        # Repository should still be usable
        # Try to add a valid task
        valid_task = self._create_task_mock("tsk_valid", "Valid Task")
        
        # This should succeed
        self.task_repository.add(valid_task)
        
        # Verify task was added
        self.assertTrue(self.task_repository.exists("tsk_valid"))
        
        # Try to get the original task (should still work)
        task = self.task_repository.get("tsk_test001")
        self.assertEqual(task.id, "tsk_test001")

    def test_null_and_empty_values(self):
        """Test handling of null and empty values in the repository."""
        # Test get with empty ID
        with self.assertRaises(ValidationError) as context:
            self.task_repository.get("")
        self.assertIn("empty", str(context.exception).lower())
        
        # Test get_by_name with empty name
        with self.assertRaises(ValidationError) as context:
            self.task_repository.get_by_name("")
        self.assertIn("empty", str(context.exception).lower())
        
        # Test adding task with empty ID
        empty_id_task = self._create_task_mock("", "Empty ID Task")
        
        with self.assertRaises(ValidationError) as context:
            self.task_repository.add(empty_id_task)
        self.assertIn("empty", str(context.exception).lower())
        
        # Test adding task with empty name
        empty_name_task = self._create_task_mock("tsk_empty_name", "")
        
        with self.assertRaises(ValidationError) as context:
            self.task_repository.add(empty_name_task)
        self.assertIn("empty", str(context.exception).lower())
    
    def test_special_characters_in_ids(self):
        """Test handling of special characters in entity IDs."""
        # Create a task with special characters in ID
        special_id_task = self._create_task_mock("tsk_special!@#$%^&*()_id", "Special ID Task")
        
        # Add task with special characters in ID
        self.task_repository.add(special_id_task)
        
        # Verify we can retrieve it
        retrieved_task = self.task_repository.get("tsk_special!@#$%^&*()_id")
        self.assertEqual(retrieved_task.id, "tsk_special!@#$%^&*()_id")
        self.assertEqual(retrieved_task.name, "Special ID Task")
        
        # Verify deletion works correctly
        self.assertTrue(self.task_repository.delete("tsk_special!@#$%^&*()_id"))
        
        # Verify task no longer exists
        self.assertFalse(self.task_repository.exists("tsk_special!@#$%^&*()_id"))
    
    def test_special_characters_in_names(self):
        """Test handling of special characters in entity names."""
        # Create a task with special characters in name
        special_name_task = self._create_task_mock("tsk_special_name", "Special !@#$%^&*() Name")
        
        # Add task with special characters in name
        self.task_repository.add(special_name_task)
        
        # Verify we can retrieve it by ID
        retrieved_task = self.task_repository.get("tsk_special_name")
        self.assertEqual(retrieved_task.name, "Special !@#$%^&*() Name")
        
        # Verify we can retrieve it by name
        retrieved_task = self.task_repository.get_by_name("Special !@#$%^&*() Name")
        self.assertEqual(retrieved_task.id, "tsk_special_name")
    
    def test_unicode_characters(self):
        """Test handling of Unicode characters in entity IDs and names."""
        # Create a task with Unicode characters
        unicode_task = self._create_task_mock("tsk_unicode_☺_id", "Unicode 你好世界 Name")
        
        # Add the task
        self.task_repository.add(unicode_task)
        
        # Verify we can retrieve it by ID
        retrieved_task = self.task_repository.get("tsk_unicode_☺_id")
        self.assertEqual(retrieved_task.id, "tsk_unicode_☺_id")
        self.assertEqual(retrieved_task.name, "Unicode 你好世界 Name")
        
        # Verify we can retrieve it by name
        retrieved_task = self.task_repository.get_by_name("Unicode 你好世界 Name")
        self.assertEqual(retrieved_task.id, "tsk_unicode_☺_id")
        
        # Verify deletion works correctly
        self.assertTrue(self.task_repository.delete("tsk_unicode_☺_id"))
    
    def test_long_values(self):
        """Test handling of very long IDs and names."""
        # Create a task with a long ID
        long_id = "tsk_" + "a" * 1000  # 1003 characters
        long_id_task = self._create_task_mock(long_id, "Long ID Task")
        
        # Add task with long ID
        self.task_repository.add(long_id_task)
        
        # Verify we can retrieve it
        retrieved_task = self.task_repository.get(long_id)
        self.assertEqual(retrieved_task.id, long_id)
        
        # Create a task with a long name
        long_name = "Long Name Task " + "a" * 1000  # 1015 characters
        long_name_task = self._create_task_mock("tsk_long_name", long_name)
        
        # Add task with long name
        self.task_repository.add(long_name_task)
        
        # Verify we can retrieve it by ID
        retrieved_task = self.task_repository.get("tsk_long_name")
        self.assertEqual(retrieved_task.name, long_name)
        
        # Verify we can retrieve it by name
        retrieved_task = self.task_repository.get_by_name(long_name)
        self.assertEqual(retrieved_task.id, "tsk_long_name")
    
    def _create_task_mock(self, task_id, name):
        """Helper method to create task mocks for testing."""
        return TestTaskEntity(task_id, name)
    
    def test_bulk_add_with_error(self):
        """Test that errors during bulk add operations are handled properly."""
        # Create a list of tasks to add
        tasks = [
            self._create_task_mock("tsk_bulk1", "Bulk Task 1"),
            self._create_task_mock("tsk_bulk2", "Bulk Task 2"),
            self._create_task_mock("tsk_bulk1", "Duplicate ID Task"),  # Duplicate ID
            self._create_task_mock("tsk_bulk3", "Bulk Task 3"),
            self._create_task_mock("tsk_bulk4", "Bulk Task 4")
        ]
        
        # Add tasks one by one, catching errors
        added_count = 0
        for task in tasks:
            try:
                self.task_repository.add(task)
                added_count += 1
            except EntityAlreadyExistsError:
                pass  # Expected for duplicate ID
        
        # Verify correct number of tasks were added
        self.assertEqual(added_count, 4)  # 5 tasks, 1 duplicate
        
        # Verify tasks with unique IDs were added
        self.assertTrue(self.task_repository.exists("tsk_bulk1"))
        self.assertTrue(self.task_repository.exists("tsk_bulk2"))
        self.assertTrue(self.task_repository.exists("tsk_bulk3"))
        self.assertTrue(self.task_repository.exists("tsk_bulk4"))
    
    def test_add_and_update_sequence(self):
        """Test a sequence of add and update operations with error handling."""
        # Reset the repository to have a clean state
        self.task_repository = self._create_repository()
        
        # Create and add task1
        task1 = self._create_task_mock("tsk_seq1", "Sequence Test A")
        self.task_repository.add(task1)
        
        # Create and add task2
        task2 = self._create_task_mock("tsk_seq2", "Sequence Test B")
        original_task2 = task2.copy()  # Keep a copy of the original
        self.task_repository.add(task2)
        
        # Try to add task with same ID as task1 (should fail)
        duplicate_task = self._create_task_mock("tsk_seq1", "Duplicate Task")
        with self.assertRaises(EntityAlreadyExistsError):
            self.task_repository.add(duplicate_task)
        
        # Try to update task2 with same name as task1 (should fail)
        task2_update = original_task2.copy()  # Start with a fresh copy
        task2_update.name = "Sequence Test A"
        with self.assertRaises(ValidationError):
            self.task_repository.update(task2_update)
        
        # Verify task2 name was not updated
        retrieved_task = self.task_repository.get("tsk_seq2")
        self.assertEqual(retrieved_task.name, "Sequence Test B")
    
    def test_add_update_delete_sequence(self):
        """Test a complex sequence of operations to ensure state consistency."""
        # Reset the repository to have a clean state
        self.task_repository = self._create_repository()
        
        # Create and add task1
        task1 = self._create_task_mock("tsk_complex1", "Complex Test A")
        self.task_repository.add(task1)
        
        # Create and add task2
        task2 = self._create_task_mock("tsk_complex2", "Complex Test B")
        original_task2 = task2.copy()  # Make a copy
        self.task_repository.add(task2)
        
        # Delete task1
        self.task_repository.delete("tsk_complex1")
        
        # Try to update task1 (should fail)
        task1_update = task1.copy()  # Make a copy
        task1_update.name = "Updated Complex Test A"
        with self.assertRaises(EntityNotFoundError):
            self.task_repository.update(task1_update)
        
        # Add a new task with same ID as task1
        new_task1 = self._create_task_mock("tsk_complex1", "New Complex Test A")
        self.task_repository.add(new_task1)
        
        # Try to update task2 to have same name as new_task1 (should fail)
        task2_update = original_task2.copy()  # Create a new copy of task2
        task2_update.name = "New Complex Test A"
        with self.assertRaises(ValidationError):
            self.task_repository.update(task2_update)
        
        # Verify final state is consistent
        self.assertTrue(self.task_repository.exists("tsk_complex1"))
        self.assertTrue(self.task_repository.exists("tsk_complex2"))
        
        retrieved_task1 = self.task_repository.get("tsk_complex1")
        self.assertEqual(retrieved_task1.name, "New Complex Test A")
        
        retrieved_task2 = self.task_repository.get("tsk_complex2")
        self.assertEqual(retrieved_task2.name, "Complex Test B")
    
    def test_transaction_consistency(self):
        """Test that repository state remains consistent when errors occur during transactions."""
        # Initial state
        initial_task = self._create_task_mock("tsk_initial", "Initial Task")
        self.task_repository.add(initial_task)
        
        # Define a transaction function that will fail
        def failing_transaction(repo):
            # First step: add a valid task
            task1 = self._create_task_mock("tsk_trans1", "Transaction Task 1")
            repo.add(task1)
            
            # Second step: add a duplicate task (will fail)
            duplicate = self._create_task_mock("tsk_initial", "Duplicate Task")
            repo.add(duplicate)  # This will raise EntityAlreadyExistsError
            
            # Third step: won't be executed due to exception
            task2 = self._create_task_mock("tsk_trans2", "Transaction Task 2")
            repo.add(task2)
        
        # Execute the transaction and catch the expected error
        try:
            failing_transaction(self.task_repository)
        except EntityAlreadyExistsError:
            pass
        
        # Check repository state after failed transaction
        # Initial task should still exist
        self.assertTrue(self.task_repository.exists("tsk_initial"))
        
        # Task added before the error should exist
        self.assertTrue(self.task_repository.exists("tsk_trans1"))
        
        # Task after the error should not exist
        self.assertFalse(self.task_repository.exists("tsk_trans2"))
    
    def test_concurrent_operations_simulation(self):
        """Test simulated concurrent operations with error handling."""
        # Set up initial state
        task1 = self._create_task_mock("tsk_concurrent1", "Concurrent Task 1")
        self.task_repository.add(task1)
        
        # Simulate concurrent update attempts
        # 1. Get the task
        original_task = self.task_repository.get("tsk_concurrent1")
        
        # 2. Create a modified version (simulating another user's update)
        concurrent_update = self._create_task_mock("tsk_concurrent1", "Updated by User 2")
        self.task_repository.update(concurrent_update)
        
        # 3. Try to update with original task, modified differently
        # This simulates two users trying to update the same task
        original_task.name = "Updated by User 1"
        
        # In a real concurrent scenario, this might need optimistic locking
        # For our test, we're checking it doesn't corrupt state
        try:
            self.task_repository.update(original_task)
        except ValidationError:
            # Some implementations might detect this and raise an error
            pass
        
        # Verify final state - the task should have one of the updates, not both
        final_task = self.task_repository.get("tsk_concurrent1")
        self.assertIn(final_task.name, ["Updated by User 1", "Updated by User 2"])
        
        # Most importantly, repository should be in a consistent state
        self.assertTrue(self.task_repository.exists("tsk_concurrent1"))
        self.assertEqual(len(self.task_repository._tasks_by_name), len(self.task_repository._tasks))


if __name__ == '__main__':
    unittest.main() 