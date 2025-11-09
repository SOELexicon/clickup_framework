#!/usr/bin/env python3
"""
Integration tests for task validation logic.

These tests verify that the task validation rules properly enforce constraints
around task completion, including subtask hierarchy, checklists, and relationships.
"""
import unittest
import tempfile
import json
import os
from pathlib import Path

# Import core entities and services
from refactor.core.entities.task_entity import TaskEntity, TaskStatus
from refactor.core.entities.checklist_entity import ChecklistEntity, ChecklistItemEntity
from refactor.core.services.task_service import TaskService
from refactor.core.repositories.task_repository import TaskRepository

# Import storage components
from refactor.storage.providers.json_storage_provider import JsonStorageProvider
from refactor.storage.serialization.json_serializer import JsonSerializer


class TaskValidationTests(unittest.TestCase):
    """Integration tests for task validation logic."""

    def setUp(self):
        """Set up test environment with a test repository and service."""
        # Create a temporary directory for test files
        self.temp_dir = tempfile.TemporaryDirectory()
        self.temp_path = Path(self.temp_dir.name)
        
        # Create a test file path
        self.test_file_path = self.temp_path / "test_task_validation.json"
        
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
        
        # Create initial test template structure
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

    def test_validate_no_incomplete_subtasks(self):
        """Test that task validation fails when subtasks are incomplete."""
        # Create a parent task
        parent_task = TaskEntity(
            entity_id="tsk_parent",
            name="Parent Task",
            description="Task with subtasks",
            status="to do",
            priority=1,
            tags=["test"],
            container_id="lst_test001"
        )
        self.task_repository.add(parent_task)
        
        # Create child tasks
        subtasks = []
        for i in range(3):
            subtask = TaskEntity(
                entity_id=f"tsk_child{i}",
                name=f"Subtask {i}",
                description=f"This is subtask {i}",
                status="to do",
                priority=2,
                tags=["test"],
                parent_id="tsk_parent",
                container_id="lst_test001"
            )
            self.task_repository.add(subtask)
            subtasks.append(subtask)
        
        # Attempt to complete parent task
        with self.assertRaises(Exception) as context:
            self.task_service.update_task_status("tsk_parent", "complete")
            
        # Verify exception mentions incomplete subtasks
        self.assertIn("subtask", str(context.exception).lower())
        
        # Complete subtasks one by one
        for i, subtask in enumerate(subtasks):
            # Update status to complete
            self.task_service.update_task_status(subtask.id, "complete")
            
            # If not the last subtask, parent completion should still fail
            if i < len(subtasks) - 1:
                with self.assertRaises(Exception):
                    self.task_service.update_task_status("tsk_parent", "complete")
        
        # Now parent task should be completable
        result = self.task_service.update_task_status("tsk_parent", "complete")
        self.assertTrue(result)
        
        # Verify parent task status
        updated_parent = self.task_repository.get("tsk_parent")
        self.assertEqual(updated_parent.status, TaskStatus.COMPLETE)

    def test_validate_recursive_subtask_hierarchy(self):
        """Test that task validation checks multiple levels of subtask hierarchy."""
        # Create a hierarchy: parent -> child -> grandchild
        parent_task = TaskEntity(
            entity_id="tsk_grandparent",
            name="Grandparent Task",
            description="Top-level task",
            status="to do",
            priority=1,
            tags=["test"],
            container_id="lst_test001"
        )
        self.task_repository.add(parent_task)
        
        child_task = TaskEntity(
            entity_id="tsk_parent",
            name="Parent Task",
            description="Mid-level task",
            status="to do",
            priority=2,
            tags=["test"],
            parent_id="tsk_grandparent",
            container_id="lst_test001"
        )
        self.task_repository.add(child_task)
        
        grandchild_task = TaskEntity(
            entity_id="tsk_child",
            name="Child Task",
            description="Bottom-level task",
            status="to do",
            priority=3,
            tags=["test"],
            parent_id="tsk_parent",
            container_id="lst_test001"
        )
        self.task_repository.add(grandchild_task)
        
        # Attempt to complete grandparent task (should fail)
        with self.assertRaises(Exception) as context:
            self.task_service.update_task_status("tsk_grandparent", "complete")
        self.assertIn("subtask", str(context.exception).lower())
        
        # Attempt to complete parent task (should fail)
        with self.assertRaises(Exception) as context:
            self.task_service.update_task_status("tsk_parent", "complete")
        self.assertIn("subtask", str(context.exception).lower())
        
        # Complete child task
        self.task_service.update_task_status("tsk_child", "complete")
        
        # Now parent task should be completable
        self.task_service.update_task_status("tsk_parent", "complete")
        
        # Now grandparent task should be completable
        self.task_service.update_task_status("tsk_grandparent", "complete")
        
        # Verify all tasks are complete
        updated_grandparent = self.task_repository.get("tsk_grandparent")
        self.assertEqual(updated_grandparent.status, TaskStatus.COMPLETE)
        
        updated_parent = self.task_repository.get("tsk_parent")
        self.assertEqual(updated_parent.status, TaskStatus.COMPLETE)
        
        updated_child = self.task_repository.get("tsk_child")
        self.assertEqual(updated_child.status, TaskStatus.COMPLETE)

    def test_validate_checklist_completion(self):
        """Test that task validation fails when checklist items are incomplete."""
        # Define checklist data as a dictionary first
        checklist_data = {
            "id": "chk_test",
            "name": "Test Checklist",
            "items": [
                {"id": "itm_1", "name": "Item 1", "checked": False},
                {"id": "itm_2", "name": "Item 2", "checked": False},
                {"id": "itm_3", "name": "Item 3", "checked": False}
            ]
        }

        # Create a task with the checklist data
        task = TaskEntity(
            entity_id="tsk_checklist",
            name="Checklist Task",
            description="Task with checklist",
            status="to do",
            priority=1,
            tags=["test"],
            container_id="lst_test001",
            checklist=checklist_data # Pass checklist data here
        )
        self.task_repository.add(task)

        # Attempt to complete task with unchecked items
        with self.assertRaises(Exception) as context:
            self.task_service.update_task_status("tsk_checklist", "complete")
        self.assertIn("checklist", str(context.exception).lower())

        # Check first item (Need to fetch task and modify checklist dict)
        updated_task = self.task_repository.get("tsk_checklist")
        if updated_task._checklist and updated_task._checklist.get('items'):
            updated_task._checklist['items'][0]['checked'] = True
            self.task_repository.update(updated_task)
        else:
            self.fail("Task checklist or items not found after add")

        # Attempt to complete task with some unchecked items
        with self.assertRaises(Exception) as context:
            self.task_service.update_task_status("tsk_checklist", "complete")
        self.assertIn("checklist", str(context.exception).lower())

        # Check remaining items
        updated_task = self.task_repository.get("tsk_checklist")
        if updated_task._checklist and updated_task._checklist.get('items'):
            for item in updated_task._checklist['items']:
                item['checked'] = True
            self.task_repository.update(updated_task)
        else:
             self.fail("Task checklist or items not found before checking remaining")

        # Now task should be completable
        result = self.task_service.update_task_status("tsk_checklist", "complete")
        self.assertTrue(result)

        # Verify task status
        completed_task = self.task_repository.get("tsk_checklist")
        self.assertEqual(completed_task.status, TaskStatus.COMPLETE)

    def test_validate_task_relationships(self):
        """Test that task validation checks blocking relationships."""
        # Create tasks with relationships
        blocker_task = TaskEntity(
            entity_id="tsk_blocker",
            name="Blocker Task",
            description="Task that blocks another",
            status="to do",
            priority=1,
            tags=["test"],
            container_id="lst_test001",
            # Pass relationships as a dictionary
            relationships={"blocks": ["tsk_blocked"]}
        )
        self.task_repository.add(blocker_task)

        blocked_task = TaskEntity(
            entity_id="tsk_blocked",
            name="Blocked Task",
            description="Task that is blocked",
            status="to do",
            priority=2,
            tags=["test"],
            container_id="lst_test001",
            # Pass relationships as a dictionary
            relationships={"blocked_by": ["tsk_blocker"]}
        )
        self.task_repository.add(blocked_task)

        # Attempt to complete blocked task
        with self.assertRaises(Exception) as context:
            self.task_service.update_task_status("tsk_blocked", "complete")
        self.assertIn("blocked", str(context.exception).lower())
        self.assertIn("blocker task", str(context.exception).lower())

        # Complete blocker task
        self.task_service.update_task_status("tsk_blocker", "complete")

        # Now blocked task should be completable
        result = self.task_service.update_task_status("tsk_blocked", "complete")
        self.assertTrue(result)

        # Verify both tasks are complete
        updated_blocker = self.task_repository.get("tsk_blocker")
        self.assertEqual(updated_blocker.status, TaskStatus.COMPLETE)

        updated_blocked = self.task_repository.get("tsk_blocked")
        self.assertEqual(updated_blocked.status, TaskStatus.COMPLETE)

    def test_force_override_validation(self):
        """Test that force flag bypasses validation constraints."""
        # Define checklist data first
        checklist_data = {
            "id": "chk_force",
            "name": "Force Checklist",
            "items": [
                {"id": "itm_force_1", "name": "Force Item 1", "checked": False},
                {"id": "itm_force_2", "name": "Force Item 2", "checked": False}
            ]
        }

        # Create a task with checklist and other constraints
        parent_task = TaskEntity(
            entity_id="tsk_force_parent",
            name="Force Parent Task",
            description="Task to force complete",
            status="to do",
            priority=1,
            tags=["test"],
            container_id="lst_test001",
            checklist=checklist_data # Pass checklist data here
        )
        self.task_repository.add(parent_task)

        # Add subtask
        subtask = TaskEntity(
            entity_id="tsk_force_child",
            name="Force Child Task",
            description="Child task",
            status="to do",
            priority=2,
            tags=["test"],
            parent_id="tsk_force_parent",
            container_id="lst_test001"
        )
        self.task_repository.add(subtask)

        # Attempt normal completion (should fail)
        with self.assertRaises(Exception):
            self.task_service.update_task_status("tsk_force_parent", "complete")

        # Use force flag to override validation
        result = self.task_service.update_task_status("tsk_force_parent", "complete", force=True)
        self.assertTrue(result)

        # Verify task is complete
        completed_task = self.task_repository.get("tsk_force_parent")
        self.assertEqual(completed_task.status, TaskStatus.COMPLETE)

    def test_error_message_contains_specific_constraints(self):
        """Test that error messages include specific information about validation failures."""
        # Define checklist data first
        checklist_data = {
            "id": "chk_complex",
            "name": "Complex Checklist",
            "items": [
                {"id": "itm_doc", "name": "Documentation Review", "checked": False},
                {"id": "itm_test", "name": "Test Execution", "checked": False}
            ]
        }
        # Define relationships data first
        relationships_data = {"blocked_by": ["tsk_complex_blocker"]}

        # Create a task with multiple constraint types
        complex_task = TaskEntity(
            entity_id="tsk_complex",
            name="Complex Task",
            description="Task with multiple constraints",
            status="to do",
            priority=1,
            tags=["test"],
            container_id="lst_test001",
            checklist=checklist_data, # Pass checklist here
            relationships=relationships_data # Pass relationships here
        )
        self.task_repository.add(complex_task)

        # Add subtasks with specific names
        subtask_names = ["Critical Subtask", "Required Subtask"]
        for i, name in enumerate(subtask_names):
            subtask = TaskEntity(
                entity_id=f"tsk_complex_sub{i}",
                name=name,
                description=f"This is {name}",
                status="to do",
                priority=2,
                tags=["test"],
                parent_id="tsk_complex",
                container_id="lst_test001"
            )
            self.task_repository.add(subtask)

        # Add blocking task (also needs relationships dict)
        blocker_task = TaskEntity(
            entity_id="tsk_complex_blocker",
            name="Complex Blocker",
            description="Task that blocks the complex task",
            status="to do",
            priority=1,
            tags=["test"],
            container_id="lst_test001",
            relationships={"blocks": ["tsk_complex"]} # Pass relationships here
        )
        self.task_repository.add(blocker_task)

        # Attempt to complete task and capture exception message
        with self.assertRaises(Exception) as context:
            self.task_service.update_task_status("tsk_complex", "complete")

        error_message = str(context.exception).lower()

        # Verify error message includes specific subtask names
        for name in subtask_names:
            self.assertIn(name.lower(), error_message)

        # Verify error message includes specific checklist item names
        self.assertIn("documentation review", error_message)
        self.assertIn("test execution", error_message)

        # Verify error message includes blocker task name
        self.assertIn("complex blocker", error_message)

    def _reset_test_file(self):
        """Reset the test file to an empty template with tasks for basic validation."""
        if self.test_file_path.exists():
            self.test_file_path.unlink()

        # Define sample data with basic tasks
        sample_data = {
            "tasks": [
                {
                    "id": "task_basic_1",
                    "name": "Basic Task 1",
                    "status": "to do",
                    "priority": 1
                },
                {
                    "id": "task_basic_2",
                    "name": "Basic Task 2",
                    "status": "in progress",
                    "priority": 2
                },
                {
                    "id": "task_basic_3",
                    "name": "Basic Task 3",
                    "status": "complete",
                    "priority": 3
                }
                # Constraints (subtasks, checklists, relationships) will be added by specific tests
            ]
        }

        # Create TaskEntity instances and save them
        for task_data in sample_data.get("tasks", []):
            checklists_list = task_data.get('checklists', []) # Extract checklist list
            task_entity_data = {
                'entity_id': task_data.get('id'), # Use entity_id
                'name': task_data.get('name', 'Default Task Name'),
                'description': task_data.get('description', ''),
                'status': task_data.get('status', 'to do'),
                'priority': task_data.get('priority', 3),
                'created_at': task_data.get('created_at'),
                'updated_at': task_data.get('updated_at'),
                'due_date': task_data.get('due_date'),
                'tags': task_data.get('tags', []),
                'assigned_to': task_data.get('assignees', []), # Use assigned_to
                'parent_id': task_data.get('parent_id'),
                'container_id': task_data.get('container_id', 'lst_test001'), # Default container_id
                'task_type': task_data.get('task_type', 'Task'),
                'checklist': checklists_list[0] if checklists_list and isinstance(checklists_list[0], dict) else None, # Use checklist, take first if exists and is dict
                'relationships': task_data.get('relationships', {}), # Expect relationships as dict
            }
            # Filter out None values before passing to constructor
            task_entity_data = {k: v for k, v in task_entity_data.items() if v is not None}
            task = TaskEntity(**task_entity_data)
            self.task_repository.add(task)

        # No need to re-initialize repository here as it's done in setUp


if __name__ == "__main__":
    unittest.main() 