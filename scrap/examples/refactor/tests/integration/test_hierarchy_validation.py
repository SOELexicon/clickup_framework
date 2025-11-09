#!/usr/bin/env python3
"""
Integration tests for hierarchical task validation.

These tests verify that the task completion rules correctly enforce constraints
related to hierarchical task relationships (parent-child-grandchild),
including proper error messages and validation logic.
"""
import unittest
import tempfile
import json
import os
from pathlib import Path

# Import core entities and services
from refactor.core.entities.task_entity import TaskEntity
from refactor.core.services.task_service import TaskService
from refactor.core.repositories.task_repository import TaskRepository
from refactor.core.exceptions import ValidationError, TaskCompletionError
from refactor.core.entities.task_entity import TaskStatus

# Import storage components
from refactor.storage.providers.json_storage_provider import JsonStorageProvider
from refactor.storage.serialization.json_serializer import JsonSerializer


class HierarchicalTaskValidationTests(unittest.TestCase):
    """Integration tests for hierarchical task validation rules."""

    def setUp(self):
        """Set up test environment with hierarchical test fixtures."""
        # Create a temporary directory for test files
        self.temp_dir = tempfile.TemporaryDirectory()
        self.temp_path = Path(self.temp_dir.name)
        
        # Create a test file path
        self.test_file_path = self.temp_path / "test_hierarchy_validation.json"
        
        # Create initial empty file for repository
        self.test_file_path.touch()
        with open(self.test_file_path, 'w') as f:
            json.dump({"tasks": {}}, f)
        
        # Initialize storage provider correctly
        self.storage_provider = JsonStorageProvider()
        self.serializer = JsonSerializer()
        
        # Initialize TaskRepository with the file path
        self.task_repository = TaskRepository(self.test_file_path)
        self.task_service = TaskService(self.task_repository)
        
        # Load hierarchical test fixtures
        fixtures_path = Path(__file__).parent.parent / "fixtures" / "hierarchy_validation_fixtures.json"
        with open(fixtures_path, 'r') as f:
            self.fixtures = json.load(f)
            
        # Create initial empty template structure
        template_data = {
            "spaces": [
                {
                    "id": "spc_test001",
                    "name": "Test Space"
                }
            ],
            "folders": [
                {
                    "id": "fld_test001",
                    "name": "Test Folder",
                    "space_id": "spc_test001"
                }
            ],
            "lists": [
                {
                    "id": "lst_test001",
                    "name": "Test List",
                    "folder_id": "fld_test001"
                }
            ],
            "tasks": []
        }
        
        with open(self.test_file_path, 'w') as f:
            json.dump(template_data, f, indent=2)

    def tearDown(self):
        """Clean up temporary files."""
        self.temp_dir.cleanup()
    
    def _reset_test_file(self):
        """Reset the test file to a predefined state for hierarchy tests."""
        # Explicitly re-initialize the repository to clear in-memory state
        self.task_repository = TaskRepository(self.test_file_path)
        # Also re-initialize the service to use the new repository instance
        self.task_service = TaskService(self.task_repository)

        if self.test_file_path.exists():
            self.test_file_path.unlink()
        self.test_file_path.touch()
        # Create initial empty structure
        with open(self.test_file_path, 'w') as f:
            json.dump({"tasks": {}}, f)

        # REMOVED THE SAMPLE DATA LOADING LOOP
        # The fixture data should be the only data loaded for each test.
    
    def _load_fixture(self, fixture_name):
        """Load a specific fixture into the test file."""
        # Reset to clean state (now re-initializes repo)
        self._reset_test_file()
        
        # Get fixture data
        fixture_data = self.fixtures["fixtures"][fixture_name]
        
        # Add tasks to repository
        for task in fixture_data["tasks"]:
            # Convert dictionary to TaskEntity (recursively handle subtasks)
            self._add_task_recursive(task)
    
    def _add_task_recursive(self, task_dict):
        """Recursively add task and its subtasks to repository."""
        # Extract subtasks if they exist
        subtasks = task_dict.pop("subtasks", [])
        checklists_data = task_dict.pop("checklists", []) # Extract checklists

        # Map keys before creating entity
        entity_args = task_dict.copy()
        if 'id' in entity_args:
            entity_args['entity_id'] = entity_args.pop('id')
        if 'assignees' in entity_args:
            entity_args['assigned_to'] = entity_args.pop('assignees')
        
        # Remove unexpected 'type' key if it exists from fixture data
        entity_args.pop('type', None)

        # Add the first checklist dictionary to the args if it exists and is a dict
        if checklists_data and isinstance(checklists_data[0], dict):
            entity_args['checklist'] = checklists_data[0]
        else:
            # Optionally handle cases where checklists_data exists but isn't in the expected format
            pass # Or log a warning

        # Create task entity
        task = TaskEntity(**entity_args)
        # task.list_id = "lst_test001"  # Add list_id if not present - Handle carefully
        
        # Save to repository - Use add() for new entities
        self.task_repository.add(task)
        
        # Add subtasks recursively
        for subtask_dict in subtasks:
            self._add_task_recursive(subtask_dict)
            
        # Restore subtasks to original dictionary (and checklists if extracted)
        if subtasks:
            task_dict["subtasks"] = subtasks
        if checklists_data:
            task_dict["checklists"] = checklists_data # Put it back if extracted
    
    def test_simple_hierarchy_completion(self):
        """Test completion rules for simple parent-child hierarchy."""
        # Load the simple hierarchy fixture
        self._load_fixture("simple_hierarchy")
        
        # Attempt to complete parent task (should fail)
        with self.assertRaises(TaskCompletionError) as context:
            self.task_service.update_task_status("tsk_parent_001", "complete")
        
        # Verify error message mentions incomplete subtasks
        error_msg = str(context.exception)
        self.assertIn("subtask", error_msg.lower())
        self.assertIn("2", error_msg)  # Should mention 2 incomplete subtasks
        
        # Complete first child task
        self.task_service.update_task_status("stk_child_001", "complete")
        
        # Attempt to complete parent again (should still fail)
        with self.assertRaises(TaskCompletionError) as context:
            self.task_service.update_task_status("tsk_parent_001", "complete")
        
        # Verify error message mentions 1 incomplete subtask
        error_msg = str(context.exception)
        self.assertIn("1", error_msg)  # Should mention 1 incomplete subtask
        
        # Complete second child task
        self.task_service.update_task_status("stk_child_002", "complete")
        
        # Now parent task should be completable
        self.task_service.update_task_status("tsk_parent_001", "complete")
        
        # Verify parent task status
        updated_parent = self.task_repository.get("tsk_parent_001")
        self.assertEqual(updated_parent.status, TaskStatus.COMPLETE)
    
    def test_multi_level_hierarchy_completion(self):
        """Test completion rules for multi-level hierarchy (parent-child-grandchild)."""
        # Load the multi-level hierarchy fixture
        self._load_fixture("multi_level_hierarchy")
        
        # Attempt to complete grandparent task (should fail)
        with self.assertRaises(TaskCompletionError) as context:
            self.task_service.update_task_status("tsk_grandparent_001", "complete")
        
        # Verify error message mentions incomplete subtasks
        error_msg = str(context.exception)
        self.assertIn("subtask", error_msg.lower())
        
        # Try to complete parent task 1 (should fail)
        with self.assertRaises(TaskCompletionError) as context:
            self.task_service.update_task_status("stk_parent_001", "complete")
        
        # Complete child tasks for parent 1
        self.task_service.update_task_status("stk_child_101", "complete")
        self.task_service.update_task_status("stk_child_102", "complete")
        
        # Now parent task 1 should be completable
        self.task_service.update_task_status("stk_parent_001", "complete")
        
        # Try to complete parent task 2 (should fail)
        with self.assertRaises(TaskCompletionError) as context:
            self.task_service.update_task_status("stk_parent_002", "complete")
        
        # Complete child task for parent 2
        self.task_service.update_task_status("stk_child_201", "complete")
        
        # Now parent task 2 should be completable
        self.task_service.update_task_status("stk_parent_002", "complete")
        
        # Now grandparent task should be completable
        self.task_service.update_task_status("tsk_grandparent_001", "complete")
        
        # Verify all tasks are complete
        updated_grandparent = self.task_repository.get("tsk_grandparent_001")
        self.assertEqual(updated_grandparent.status, TaskStatus.COMPLETE)
    
    def test_mixed_status_hierarchy(self):
        """Test completion rules for hierarchy with mixed completion statuses."""
        # Load the mixed status hierarchy fixture
        self._load_fixture("mixed_status_hierarchy")
        
        # Attempt to complete parent task (should fail)
        with self.assertRaises(TaskCompletionError) as context:
            self.task_service.update_task_status("tsk_mixed_parent", "complete")
        
        # Verify error message mentions incomplete subtasks
        error_msg = str(context.exception)
        self.assertIn("subtask", error_msg.lower())
        
        # Complete the in-progress child
        self.task_service.update_task_status("stk_mixed_child_002", "complete")
        
        # Try to complete "to do" child (should fail due to grandchild)
        with self.assertRaises(TaskCompletionError) as context:
            self.task_service.update_task_status("stk_mixed_child_003", "complete")
        
        # Verify error message mentions incomplete subtasks
        error_msg = str(context.exception)
        self.assertIn("subtask", error_msg.lower())
        
        # Complete the grandchild task
        self.task_service.update_task_status("stk_mixed_grandchild", "complete")
        
        # Now the "to do" child should be completable
        self.task_service.update_task_status("stk_mixed_child_003", "complete")
        
        # Now parent task should be completable
        self.task_service.update_task_status("tsk_mixed_parent", "complete")
        
        # Verify parent task status
        updated_parent = self.task_repository.get("tsk_mixed_parent")
        self.assertEqual(updated_parent.status, TaskStatus.COMPLETE)
    
    def test_wide_hierarchy_completion(self):
        """Test completion rules for wide hierarchy with many children."""
        # Load the wide hierarchy fixture
        self._load_fixture("wide_hierarchy")
        
        # Attempt to complete parent task (should fail)
        with self.assertRaises(TaskCompletionError) as context:
            self.task_service.update_task_status("tsk_wide_parent", "complete")
        
        # Verify error message mentions 5 incomplete subtasks
        error_msg = str(context.exception)
        self.assertIn("5", error_msg)
        self.assertIn("subtask", error_msg.lower())
        
        # Complete tasks one by one
        for i in range(1, 6):
            child_id = f"stk_wide_child_{i:03d}"
            self.task_service.update_task_status(child_id, "complete")
            
            # If not the last child, parent completion should still fail
            if i < 5:
                with self.assertRaises(TaskCompletionError) as context:
                    self.task_service.update_task_status("tsk_wide_parent", "complete")
                # Verify error message mentions correct number of remaining subtasks
                error_msg = str(context.exception)
                self.assertIn(f"{5-i}", error_msg)
        
        # Now parent task should be completable
        self.task_service.update_task_status("tsk_wide_parent", "complete")
        
        # Verify parent task status
        updated_parent = self.task_repository.get("tsk_wide_parent")
        self.assertEqual(updated_parent.status, TaskStatus.COMPLETE)
    
    def test_specific_error_messages(self):
        """Test that error messages include specific information about what's blocking completion."""
        # Load the multi-level hierarchy fixture
        self._load_fixture("multi_level_hierarchy")
        
        # Attempt to complete grandparent task
        with self.assertRaises(TaskCompletionError) as context:
            self.task_service.update_task_status("tsk_grandparent_001", "complete")
        
        # Verify error message provides specific details
        error_msg = str(context.exception)
        self.assertIn("2", error_msg)  # Should specify 2 incomplete subtasks
        
        # Complete child tasks for parent 1
        self.task_service.update_task_status("stk_child_101", "complete")
        self.task_service.update_task_status("stk_child_102", "complete")
        
        # Complete parent 1
        self.task_service.update_task_status("stk_parent_001", "complete")
        
        # Try to complete grandparent with only 1 incomplete child
        with self.assertRaises(TaskCompletionError) as context:
            self.task_service.update_task_status("tsk_grandparent_001", "complete")
        
        # Verify error message specifies 1 incomplete subtask
        error_msg = str(context.exception)
        self.assertIn("1", error_msg)  # Should specify 1 incomplete subtask
        
        # Verify error message includes task name
        self.assertIn("Parent Task 2", error_msg)  # Should include name of incomplete subtask


if __name__ == "__main__":
    unittest.main() 