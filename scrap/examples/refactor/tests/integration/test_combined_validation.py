#!/usr/bin/env python3
"""
Integration tests for combined workflow validation.

These tests verify that the task completion rules correctly enforce constraints
when multiple types of constraints (hierarchy, checklist, relationships) are combined,
including proper error messages and validation priorities.
"""
import unittest
import tempfile
import json
import os
from pathlib import Path

# Import core entities and services
from refactor.core.entities.task_entity import TaskEntity
from refactor.core.entities.checklist_entity import ChecklistEntity, ChecklistItemEntity
from refactor.core.services.task_service import TaskService
from refactor.core.repositories.task_repository import TaskRepository
from refactor.core.exceptions import ValidationError, TaskCompletionError, CircularDependencyError

# Import storage components
from refactor.storage.providers.json_storage_provider import JsonStorageProvider
from refactor.storage.serialization.json_serializer import JsonSerializer


class CombinedWorkflowValidationTests(unittest.TestCase):
    """Integration tests for combined workflow validation rules."""

    def setUp(self):
        """Set up test environment with combined test fixtures."""
        # Create a temporary directory for test files
        self.temp_dir = tempfile.TemporaryDirectory()
        self.temp_path = Path(self.temp_dir.name)
        
        # Create a test file path
        self.test_file_path = Path(self.temp_dir.name) / "test_combined_validation.json"
        
        # Initialize storage components
        self.serializer = JsonSerializer()
        self.storage_provider = JsonStorageProvider()
        
        # Initialize repository and service
        self.task_repository = TaskRepository(self.test_file_path)
        self.task_service = TaskService(self.task_repository)
        
        # Load combined test fixtures
        fixtures_path = Path(__file__).parent.parent / "fixtures" / "combined_validation_fixtures.json"
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
            "tasks": [],
            "relationships": []
        }
        
        with open(self.test_file_path, 'w') as f:
            json.dump(template_data, f, indent=2)

    def tearDown(self):
        """Clean up temporary files."""
        self.temp_dir.cleanup()
    
    def _reset_test_file(self):
        """Reset the test file to an empty template."""
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
            "tasks": [],
            "relationships": []
        }
        
        with open(self.test_file_path, 'w') as f:
            json.dump(template_data, f, indent=2)
        
        # Re-initialize repository with fresh data
        self.storage_provider = JsonStorageProvider()
        self.task_repository = TaskRepository(self.test_file_path)
        self.task_service = TaskService(self.task_repository)
    
    def _load_fixture(self, fixture_name):
        """Load a specific fixture into the test file."""
        # Reset to clean state
        self._reset_test_file()
        
        # Get fixture data
        fixture_data = self.fixtures["fixtures"][fixture_name]
        
        # Add tasks to repository
        for task in fixture_data["tasks"]:
            # Convert dictionary to TaskEntity (recursively handle subtasks)
            self._add_task_recursive(task)
        
        # Add relationships
        if "relationships" in fixture_data:
            for relationship in fixture_data["relationships"]:
                source_id = relationship["source_id"]
                target_id = relationship["target_id"]
                rel_type = relationship["type"]
                self.task_service.add_relationship(source_id, target_id, rel_type)
    
    def _add_task_recursive(self, task_dict):
        """Recursively add task and its subtasks to repository."""
        # Extract subtasks and checklists if they exist
        subtasks = task_dict.pop("subtasks", [])
        checklists_data = task_dict.pop("checklists", [])
        
        # Prepare data for TaskEntity, mapping 'id' to 'entity_id'
        task_entity_data = {
            'entity_id': task_dict.get('id'),
            'name': task_dict.get('name', 'Default Task Name'),
            'description': task_dict.get('description', ''),
            'status': task_dict.get('status', 'to do'),
            'priority': task_dict.get('priority', 3),
            'parent_id': task_dict.get('parent_id'),
        }
        # Filter out None values
        task_entity_data = {k: v for k, v in task_entity_data.items() if v is not None}
        task = TaskEntity(**task_entity_data)
        task.list_id = "lst_test001"  # Add list_id if not present
        
        # Add checklists
        if checklists_data:
            checklists = []
            for checklist_data in checklists_data:
                items_data = checklist_data.pop("items", [])
                checklist = ChecklistEntity(**checklist_data)
                
                # Add checklist items
                items = []
                for item_data in items_data:
                    item = ChecklistItemEntity(**item_data)
                    items.append(item)
                
                checklist.items = items
                checklists.append(checklist)
            
            task.checklists = checklists
        
        # Save to repository
        self.task_repository.save(task)
        
        # Add subtasks recursively
        for subtask_dict in subtasks:
            self._add_task_recursive(subtask_dict)
            
        # Restore subtasks and checklists to original dictionary
        if subtasks:
            task_dict["subtasks"] = subtasks
        if checklists_data:
            task_dict["checklists"] = checklists_data

    def test_hierarchy_with_relationships(self):
        """Test task with hierarchical structure and relationship dependencies."""
        # Load hierarchy with relationships fixture
        self._load_fixture("hierarchy_with_relationships")
        
        # Attempt to complete parent task (should fail due to incomplete subtasks)
        with self.assertRaises(TaskCompletionError) as context:
            self.task_service.update_task_status("tsk_combined_001", "complete")
        
        # Verify error message mentions subtasks
        error_msg = str(context.exception)
        self.assertIn("subtask", error_msg.lower())
        
        # Try to complete first child task (should fail due to dependency)
        with self.assertRaises(TaskCompletionError) as context:
            self.task_service.update_task_status("stk_combined_101", "complete")
        
        # Verify error message mentions dependency
        error_msg = str(context.exception)
        self.assertIn("depends", error_msg.lower())
        self.assertIn("Dependent Task", error_msg)
        
        # Complete the dependency task first
        self.task_service.update_task_status("tsk_combined_002", "complete")
        
        # Now complete the first child task
        self.task_service.update_task_status("stk_combined_101", "complete")
        
        # Try to complete parent task (should still fail due to second child)
        with self.assertRaises(TaskCompletionError) as context:
            self.task_service.update_task_status("tsk_combined_001", "complete")
        
        # Verify error message mentions remaining subtask
        error_msg = str(context.exception)
        self.assertIn("subtask", error_msg.lower())
        self.assertIn("Child Task 2", error_msg)
        
        # Complete the second child task
        self.task_service.update_task_status("stk_combined_102", "complete")
        
        # Now parent task should be completable
        self.task_service.update_task_status("tsk_combined_001", "complete")
        
        # Verify parent task status
        updated_parent = self.task_repository.get_by_id("tsk_combined_001")
        self.assertEqual(updated_parent.status, "complete")
    
    def test_hierarchy_with_checklists(self):
        """Test task with hierarchical structure and checklists."""
        # Load hierarchy with checklists fixture
        self._load_fixture("hierarchy_with_checklists")
        
        # Attempt to complete parent task (should fail due to subtask and checklist)
        with self.assertRaises(TaskCompletionError) as context:
            self.task_service.update_task_status("tsk_combined_003", "complete")
        
        # First error should be about subtasks (implementation-dependent, but generally
        # hierarchical constraints are checked first)
        error_msg = str(context.exception)
        self.assertIn("subtask", error_msg.lower())
        
        # Try to complete child task (should fail due to checklist)
        with self.assertRaises(TaskCompletionError) as context:
            self.task_service.update_task_status("stk_combined_201", "complete")
        
        # Verify error message mentions checklist items
        error_msg = str(context.exception)
        self.assertIn("checklist", error_msg.lower())
        
        # Complete the child's checklist items
        child = self.task_repository.get_by_id("stk_combined_201")
        for item in child.checklists[0].items:
            item.checked = True
        self.task_repository.save(child)
        
        # Now complete the child task
        self.task_service.update_task_status("stk_combined_201", "complete")
        
        # Try to complete parent task (should fail due to its own checklist)
        with self.assertRaises(TaskCompletionError) as context:
            self.task_service.update_task_status("tsk_combined_003", "complete")
        
        # Verify error message now mentions only checklist items
        error_msg = str(context.exception)
        self.assertIn("checklist", error_msg.lower())
        self.assertNotIn("subtask", error_msg.lower())
        
        # Complete the parent's checklist items
        parent = self.task_repository.get_by_id("tsk_combined_003")
        for item in parent.checklists[0].items:
            item.checked = True
        self.task_repository.save(parent)
        
        # Now parent task should be completable
        self.task_service.update_task_status("tsk_combined_003", "complete")
        
        # Verify parent task status
        updated_parent = self.task_repository.get_by_id("tsk_combined_003")
        self.assertEqual(updated_parent.status, "complete")
    
    def test_checklist_with_relationships(self):
        """Test task with both checklist and relationship constraints."""
        # Load checklist with relationships fixture
        self._load_fixture("checklist_with_relationships")
        
        # Attempt to complete task (should fail)
        with self.assertRaises(TaskCompletionError) as context:
            self.task_service.update_task_status("tsk_combined_004", "complete")
        
        # The error could be about either dependency or checklist, depending on validation order
        error_msg = str(context.exception)
        constraint_mentioned = "depends" in error_msg.lower() or "checklist" in error_msg.lower()
        self.assertTrue(constraint_mentioned, 
                        "Error should mention either dependency or checklist constraint")
        
        # Complete dependency task
        self.task_service.update_task_status("tsk_combined_005", "complete")
        
        # Try to complete task again (should still fail due to checklist)
        with self.assertRaises(TaskCompletionError) as context:
            self.task_service.update_task_status("tsk_combined_004", "complete")
        
        # Now error should specifically mention checklist
        error_msg = str(context.exception)
        self.assertIn("checklist", error_msg.lower())
        
        # Complete checklist items
        task = self.task_repository.get_by_id("tsk_combined_004")
        for item in task.checklists[0].items:
            item.checked = True
        self.task_repository.save(task)
        
        # Now task should be completable
        self.task_service.update_task_status("tsk_combined_004", "complete")
        
        # Verify task status
        updated_task = self.task_repository.get_by_id("tsk_combined_004")
        self.assertEqual(updated_task.status, "complete")
    
    def test_complex_combined_constraints(self):
        """Test complex combination of all constraint types."""
        # Load complex combined constraints fixture
        self._load_fixture("complex_combined_constraints")
        
        # Attempt to complete parent task (should fail)
        with self.assertRaises(TaskCompletionError) as context:
            self.task_service.update_task_status("tsk_complex_001", "complete")
        
        # Verify error message mentions subtasks
        error_msg = str(context.exception)
        self.assertIn("subtask", error_msg.lower())
        
        # Try to complete child task 1 (should fail due to dependency)
        with self.assertRaises(TaskCompletionError) as context:
            self.task_service.update_task_status("stk_complex_101", "complete")
        
        # Verify error message mentions dependency
        error_msg = str(context.exception)
        self.assertIn("depends", error_msg.lower())
        
        # Try to complete child task 2 (should fail due to subtask)
        with self.assertRaises(TaskCompletionError) as context:
            self.task_service.update_task_status("stk_complex_102", "complete")
        
        # Verify error message mentions subtask
        error_msg = str(context.exception)
        self.assertIn("subtask", error_msg.lower())
        
        # Try to complete grandchild task (should fail due to dependency and checklist)
        with self.assertRaises(TaskCompletionError) as context:
            self.task_service.update_task_status("stk_complex_201", "complete")
        
        # Complete the dependency task's checklist
        dependency_task = self.task_repository.get_by_id("tsk_complex_002")
        for item in dependency_task.checklists[0].items:
            item.checked = True
        self.task_repository.save(dependency_task)
        
        # Complete the dependency task
        self.task_service.update_task_status("tsk_complex_002", "complete")
        
        # Complete the grandchild's checklist
        grandchild = self.task_repository.get_by_id("stk_complex_201")
        for item in grandchild.checklists[0].items:
            item.checked = True
        self.task_repository.save(grandchild)
        
        # Now complete the grandchild task
        self.task_service.update_task_status("stk_complex_201", "complete")
        
        # Complete child task 2's checklist
        child2 = self.task_repository.get_by_id("stk_complex_102")
        for item in child2.checklists[0].items:
            item.checked = True
        self.task_repository.save(child2)
        
        # Now complete child task 2
        self.task_service.update_task_status("stk_complex_102", "complete")
        
        # Now complete child task 1
        self.task_service.update_task_status("stk_complex_101", "complete")
        
        # Complete parent's checklist
        parent = self.task_repository.get_by_id("tsk_complex_001")
        for item in parent.checklists[0].items:
            item.checked = True
        self.task_repository.save(parent)
        
        # Finally complete parent task
        self.task_service.update_task_status("tsk_complex_001", "complete")
        
        # Verify parent task status
        updated_parent = self.task_repository.get_by_id("tsk_complex_001")
        self.assertEqual(updated_parent.status, "complete")
    
    def test_blocking_with_hierarchy(self):
        """Test blocking relationships within a hierarchical structure."""
        # Load blocking with hierarchy fixture
        self._load_fixture("blocking_with_hierarchy")
        
        # Attempt to complete parent task (should fail due to incomplete subtasks)
        with self.assertRaises(TaskCompletionError) as context:
            self.task_service.update_task_status("tsk_blocking_001", "complete")
        
        # Verify error message mentions subtasks
        error_msg = str(context.exception)
        self.assertIn("subtask", error_msg.lower())
        
        # Try to complete blocked child (should fail due to blocking task)
        with self.assertRaises(TaskCompletionError) as context:
            self.task_service.update_task_status("stk_blocking_101", "complete")
        
        # Verify error message mentions blocking task
        error_msg = str(context.exception)
        self.assertIn("block", error_msg.lower())
        
        # Complete regular child first
        self.task_service.update_task_status("stk_blocking_102", "complete")
        
        # Try to complete parent (should still fail due to blocked child)
        with self.assertRaises(TaskCompletionError) as context:
            self.task_service.update_task_status("tsk_blocking_001", "complete")
        
        # Complete the blocking task
        self.task_service.update_task_status("tsk_blocking_002", "complete")
        
        # Now complete the previously blocked child
        self.task_service.update_task_status("stk_blocking_101", "complete")
        
        # Now parent task should be completable
        self.task_service.update_task_status("tsk_blocking_001", "complete")
        
        # Verify parent task status
        updated_parent = self.task_repository.get_by_id("tsk_blocking_001")
        self.assertEqual(updated_parent.status, "complete")
    
    def test_mixed_validation_priorities(self):
        """Test validation priorities when multiple constraint types exist."""
        # Load mixed validation priorities fixture
        self._load_fixture("mixed_validation_priorities")
        
        # Attempt to complete multi-constraint task (should fail)
        with self.assertRaises(TaskCompletionError) as context:
            self.task_service.update_task_status("tsk_priority_001", "complete")
        
        # Capture first error message - should reflect validation priority
        first_error_msg = str(context.exception)
        
        # We'll check which constraint was validated first (implementation dependent)
        has_subtask_first = "subtask" in first_error_msg.lower()
        has_dependency_first = "depends" in first_error_msg.lower()
        has_checklist_first = "checklist" in first_error_msg.lower()
        
        # Complete dependency
        self.task_service.update_task_status("tsk_priority_002", "complete")
        
        # Complete child task
        self.task_service.update_task_status("stk_priority_101", "complete")
        
        # Complete checklist
        task = self.task_repository.get_by_id("tsk_priority_001")
        for item in task.checklists[0].items:
            item.checked = True
        self.task_repository.save(task)
        
        # Now task should be completable
        self.task_service.update_task_status("tsk_priority_001", "complete")
        
        # Verify task status
        updated_task = self.task_repository.get_by_id("tsk_priority_001")
        self.assertEqual(updated_task.status, "complete")
        
        # Note on validation priority (informational):
        # This test doesn't assert which validation occurs first, as that's implementation-specific.
        # It only verifies that all validations eventually occur.
        # The typical priority order would be:
        # 1. Hierarchical constraints (subtasks)
        # 2. Relationship constraints (dependencies/blocking)
        # 3. Checklist constraints
        # But any order is valid as long as all constraints are enforced.
    
    def test_error_message_detail(self):
        """Test that error messages provide detailed information about all constraints."""
        # Load complex combined constraints fixture
        self._load_fixture("complex_combined_constraints")
        
        # Attempt to complete parent task (should fail)
        with self.assertRaises(TaskCompletionError) as context:
            self.task_service.update_task_status("tsk_complex_001", "complete")
        
        # Verify error message contains detailed information
        error_msg = str(context.exception)
        
        # Error should mention subtasks
        self.assertIn("subtask", error_msg.lower())
        
        # Error should ideally include subtask count or names
        self.assertTrue(
            any(name in error_msg for name in ["Complex Child Task 1", "Complex Child Task 2"]),
            "Error should mention at least one subtask name"
        )


if __name__ == "__main__":
    unittest.main() 