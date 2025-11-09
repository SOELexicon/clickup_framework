#!/usr/bin/env python3
"""
Integration tests for Task Management Workflow.

These tests verify the complete task management lifecycle, including task creation,
updates, status changes, relationship management, and completion validation across
all integrated system components.
"""
import unittest
import tempfile
import json
import os
import shutil
from pathlib import Path
from unittest.mock import patch, MagicMock

# Import core components
from refactor.core.entities.task_entity import TaskEntity
from refactor.core.services.task_service import TaskService
from refactor.core.repositories.task_repository import TaskRepository
from refactor.core.exceptions import ValidationError, EntityNotFoundError

# Import storage components
from refactor.storage.providers.json_storage_provider import JsonStorageProvider
from refactor.storage.serialization.json_serializer import JsonSerializer

# Import CLI components if needed for end-to-end workflow testing
from refactor.cli.registry import CommandRegistry
from refactor.cli.commands.task import CreateTaskCommand, UpdateTaskCommand, DeleteTaskCommand, ListTasksCommand, ShowTaskCommand
from refactor.cli.commands.checklist import CreateChecklistCommand, CheckItemCommand, ListChecklistItemsCommand
from refactor.cli.commands.relationship import AddRelationshipCommand, RemoveRelationshipCommand, ListRelationshipsCommand


class TaskManagementWorkflowTests(unittest.TestCase):
    """Integration tests for the complete task management workflow."""

    def setUp(self):
        """Set up test environment with temporary test files and necessary components."""
        # Create a temporary directory for test files
        self.temp_dir = tempfile.TemporaryDirectory()
        self.temp_path = Path(self.temp_dir.name)
        
        # Create a test file path
        self.test_file_path = self.temp_path / "test_task_workflow.json"
        
        # Initialize storage components
        self.serializer = JsonSerializer()
        # self.storage_provider = JsonStorageProvider(self.test_file_path, self.serializer) # Removed - Repository handles path now
        
        # Initialize repository and service
        # TaskRepository now takes the file path directly
        self.task_repository = TaskRepository(self.test_file_path)
        self.task_service = TaskService(self.task_repository)
        
        # Initialize CLI components for end-to-end testing if needed
        # TODO: Re-enable or update CLI component usage if full end-to-end tests are desired.
        # self.command_registry = CommandRegistry()
        # self.command_executor = CommandExecutor(self.command_registry)
        
        # Create initial template structure with spaces, folders, and lists
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
    
    def test_task_creation_and_validation(self):
        """Test task creation with validation of required fields."""
        # Test valid task creation
        valid_task = self.task_service.create_task({
            "name": "Valid Task",
            "description": "This is a valid task",
            "status": "to do",
            "priority": 2,
            "list_id": "lst_test001",
            "tags": ["test", "integration"]
        })
        
        # Verify task was created correctly
        self.assertIsNotNone(valid_task)
        self.assertEqual(valid_task.name, "Valid Task")
        self.assertEqual(valid_task.status, "to do")
        
        # Verify task can be retrieved
        retrieved_task = self.task_service.get_task(valid_task.id)
        self.assertEqual(retrieved_task.name, "Valid Task")
        
        # Test task creation with missing required fields
        with self.assertRaises(ValidationError):
            invalid_task = self.task_service.create_task({
                "description": "Missing name field",
                "status": "to do",
                "list_id": "lst_test001"
            })
        
        # Test task creation with invalid status
        with self.assertRaises(ValidationError):
            invalid_status_task = self.task_service.create_task({
                "name": "Invalid Status Task",
                "description": "This task has an invalid status",
                "status": "not_a_valid_status",
                "list_id": "lst_test001"
            })
        
        # Test task creation with invalid list ID
        with self.assertRaises(ValidationError):
            invalid_list_task = self.task_service.create_task({
                "name": "Invalid List Task",
                "description": "This task has an invalid list ID",
                "status": "to do",
                "list_id": "nonexistent_list"
            })
    
    def test_subtask_creation_and_parent_child_relationships(self):
        """Test creating subtasks and managing parent-child relationships."""
        # Create a parent task
        parent_task = self.task_service.create_task({
            "name": "Parent Task",
            "description": "This is a parent task",
            "status": "to do",
            "list_id": "lst_test001",
            "tags": ["parent", "test"]
        })
        
        # Create subtasks linked to the parent
        subtask1 = self.task_service.create_task({
            "name": "Subtask 1",
            "description": "This is subtask 1",
            "status": "to do",
            "list_id": "lst_test001",
            "parent_id": parent_task.id,
            "tags": ["subtask", "test"]
        })
        
        subtask2 = self.task_service.create_task({
            "name": "Subtask 2",
            "description": "This is subtask 2",
            "status": "to do",
            "list_id": "lst_test001",
            "parent_id": parent_task.id,
            "tags": ["subtask", "test"]
        })
        
        # Verify the parent-child relationship
        parent_with_children = self.task_service.get_task_with_subtasks(parent_task.id)
        self.assertEqual(len(parent_with_children.subtasks), 2)
        
        # Verify subtask parent references
        retrieved_subtask1 = self.task_service.get_task(subtask1.id)
        self.assertEqual(retrieved_subtask1.parent_id, parent_task.id)
        
        # Test nested subtasks (subtask of a subtask)
        sub_subtask = self.task_service.create_task({
            "name": "Sub-Subtask",
            "description": "This is a subtask of a subtask",
            "status": "to do",
            "list_id": "lst_test001",
            "parent_id": subtask1.id,
            "tags": ["sub-subtask", "test"]
        })
        
        # Verify nested subtask relationship
        subtask_with_children = self.task_service.get_task_with_subtasks(subtask1.id)
        self.assertEqual(len(subtask_with_children.subtasks), 1)
        
        # Test getting all descendants of parent task
        all_descendants = self.task_service.get_all_descendants(parent_task.id)
        self.assertEqual(len(all_descendants), 3)  # 2 direct subtasks + 1 sub-subtask
    
    def test_task_status_transitions_with_validation(self):
        """Test task status transitions with validation rules."""
        # Create a task to test status transitions
        task = self.task_service.create_task({
            "name": "Status Test Task",
            "description": "Testing status transitions",
            "status": "to do",
            "list_id": "lst_test001"
        })
        
        # Valid status transition: to do -> in progress
        task = self.task_service.update_task_status(task.id, "in progress")
        self.assertEqual(task.status, "in progress")
        
        # Valid status transition: in progress -> in review
        task = self.task_service.update_task_status(task.id, "in review")
        self.assertEqual(task.status, "in review")
        
        # Valid status transition: in review -> complete
        task = self.task_service.update_task_status(task.id, "complete")
        self.assertEqual(task.status, "complete")
        
        # Test invalid status value
        with self.assertRaises(ValidationError):
            task = self.task_service.update_task_status(task.id, "invalid_status")
        
        # Create parent task with subtasks to test completion validation
        parent = self.task_service.create_task({
            "name": "Parent with Subtasks",
            "description": "Parent task with subtasks for status testing",
            "status": "to do",
            "list_id": "lst_test001"
        })
        
        subtask1 = self.task_service.create_task({
            "name": "Status Subtask 1",
            "description": "Subtask 1 for status testing",
            "status": "to do",
            "list_id": "lst_test001",
            "parent_id": parent.id
        })
        
        subtask2 = self.task_service.create_task({
            "name": "Status Subtask 2",
            "description": "Subtask 2 for status testing",
            "status": "to do",
            "list_id": "lst_test001",
            "parent_id": parent.id
        })
        
        # Test: Cannot complete parent if subtasks are not complete
        with self.assertRaises(ValidationError):
            parent = self.task_service.update_task_status(parent.id, "complete")
        
        # Complete subtasks one by one
        subtask1 = self.task_service.update_task_status(subtask1.id, "in progress")
        subtask1 = self.task_service.update_task_status(subtask1.id, "complete")
        
        # Still can't complete parent with one incomplete subtask
        with self.assertRaises(ValidationError):
            parent = self.task_service.update_task_status(parent.id, "complete")
        
        # Complete the second subtask
        subtask2 = self.task_service.update_task_status(subtask2.id, "in progress")
        subtask2 = self.task_service.update_task_status(subtask2.id, "complete")
        
        # Now parent can be completed
        parent = self.task_service.update_task_status(parent.id, "complete")
        self.assertEqual(parent.status, "complete")
    
    def test_relationship_enforcement(self):
        """Test enforcement of task relationships (blocks/depends_on)."""
        # Create tasks for relationship testing
        task_a = self.task_service.create_task({
            "name": "Task A",
            "description": "Task that blocks other tasks",
            "status": "to do",
            "list_id": "lst_test001"
        })
        
        task_b = self.task_service.create_task({
            "name": "Task B",
            "description": "Task that depends on task A",
            "status": "to do",
            "list_id": "lst_test001"
        })
        
        task_c = self.task_service.create_task({
            "name": "Task C",
            "description": "Another dependent task",
            "status": "to do",
            "list_id": "lst_test001"
        })
        
        # Create "blocks" relationship: A blocks B and C
        self.task_service.add_relationship(task_a.id, task_b.id, "blocks")
        self.task_service.add_relationship(task_a.id, task_c.id, "blocks")
        
        # Create "depends_on" relationship: B and C depend on A
        self.task_service.add_relationship(task_b.id, task_a.id, "depends_on")
        self.task_service.add_relationship(task_c.id, task_a.id, "depends_on")
        
        # Verify relationships were created
        relationships = self.task_service.get_all_relationships()
        self.assertEqual(len(relationships), 4)
        
        # Test: Cannot complete tasks B and C while A is not complete
        with self.assertRaises(ValidationError):
            task_b = self.task_service.update_task_status(task_b.id, "complete")
        
        with self.assertRaises(ValidationError):
            task_c = self.task_service.update_task_status(task_c.id, "complete")
        
        # Complete task A
        task_a = self.task_service.update_task_status(task_a.id, "in progress")
        task_a = self.task_service.update_task_status(task_a.id, "complete")
        
        # Now tasks B and C can be completed
        task_b = self.task_service.update_task_status(task_b.id, "in progress")
        task_b = self.task_service.update_task_status(task_b.id, "complete")
        self.assertEqual(task_b.status, "complete")
        
        task_c = self.task_service.update_task_status(task_c.id, "in progress")
        task_c = self.task_service.update_task_status(task_c.id, "complete")
        self.assertEqual(task_c.status, "complete")
        
        # Test circular dependency detection
        task_d = self.task_service.create_task({
            "name": "Task D",
            "description": "Task for circular dependency testing",
            "status": "to do",
            "list_id": "lst_test001"
        })
        
        task_e = self.task_service.create_task({
            "name": "Task E",
            "description": "Another task for circular dependency testing",
            "status": "to do",
            "list_id": "lst_test001"
        })
        
        # Create relationships: D depends on E, E depends on D (circular)
        self.task_service.add_relationship(task_d.id, task_e.id, "depends_on")
        
        # Adding the second relationship should fail due to circular dependency
        with self.assertRaises(ValidationError):
            self.task_service.add_relationship(task_e.id, task_d.id, "depends_on")
    
    def test_checklist_creation_and_completion_workflow(self):
        """Test checklist creation and completion within tasks."""
        # Create a task with a checklist
        task = self.task_service.create_task({
            "name": "Checklist Task",
            "description": "Task with a checklist",
            "status": "to do",
            "list_id": "lst_test001"
        })
        
        # Create a checklist
        checklist = self.task_service.create_checklist(task.id, "Implementation Steps")
        
        # Add checklist items
        item1_id = self.task_service.add_checklist_item(task.id, checklist.id, "Design the interface")
        item2_id = self.task_service.add_checklist_item(task.id, checklist.id, "Implement core functionality")
        item3_id = self.task_service.add_checklist_item(task.id, checklist.id, "Write tests")
        
        # Verify checklist was created with items
        updated_task = self.task_service.get_task(task.id)
        self.assertEqual(len(updated_task.checklists), 1)
        self.assertEqual(len(updated_task.checklists[0].items), 3)
        
        # Test: Cannot complete task with incomplete checklist items
        with self.assertRaises(ValidationError):
            self.task_service.update_task_status(task.id, "complete")
        
        # Complete checklist items one by one
        self.task_service.update_checklist_item(task.id, checklist.id, item1_id, True)
        
        # Check that item was marked complete
        updated_task = self.task_service.get_task(task.id)
        self.assertTrue(updated_task.checklists[0].items[0].checked)
        
        # Still can't complete task with incomplete checklist items
        with self.assertRaises(ValidationError):
            self.task_service.update_task_status(task.id, "complete")
        
        # Complete remaining items
        self.task_service.update_checklist_item(task.id, checklist.id, item2_id, True)
        self.task_service.update_checklist_item(task.id, checklist.id, item3_id, True)
        
        # Now task can be completed
        task = self.task_service.update_task_status(task.id, "in progress")
        task = self.task_service.update_task_status(task.id, "complete")
        self.assertEqual(task.status, "complete")
        
        # Test unchecking items and re-checking them
        self.task_service.update_checklist_item(task.id, checklist.id, item1_id, False)
        updated_task = self.task_service.get_task(task.id)
        self.assertFalse(updated_task.checklists[0].items[0].checked)
        
        self.task_service.update_checklist_item(task.id, checklist.id, item1_id, True)
        updated_task = self.task_service.get_task(task.id)
        self.assertTrue(updated_task.checklists[0].items[0].checked)
    
    def test_task_completion_validation(self):
        """Test comprehensive task completion validation with all dependencies."""
        # Create tasks with multiple dependency types for validation
        parent_task = self.task_service.create_task({
            "name": "Main Project Task",
            "description": "Parent task with dependencies and subtasks",
            "status": "to do",
            "list_id": "lst_test001"
        })
        
        # Create a checklist on the parent task
        checklist = self.task_service.create_checklist(parent_task.id, "Project Checklist")
        checklist_item1 = self.task_service.add_checklist_item(parent_task.id, checklist.id, "Plan project")
        checklist_item2 = self.task_service.add_checklist_item(parent_task.id, checklist.id, "Review documentation")
        
        # Create subtasks
        subtask1 = self.task_service.create_task({
            "name": "Implementation Subtask",
            "description": "First implementation step",
            "status": "to do",
            "list_id": "lst_test001",
            "parent_id": parent_task.id
        })
        
        subtask2 = self.task_service.create_task({
            "name": "Documentation Subtask",
            "description": "Documentation step",
            "status": "to do",
            "list_id": "lst_test001",
            "parent_id": parent_task.id
        })
        
        # Create dependent tasks
        dependency_task = self.task_service.create_task({
            "name": "Dependency Task",
            "description": "Task that the main task depends on",
            "status": "to do",
            "list_id": "lst_test001"
        })
        
        # Create the dependency relationship
        self.task_service.add_relationship(parent_task.id, dependency_task.id, "depends_on")
        
        # Test: Cannot complete parent task with:
        # 1. Incomplete checklist items
        # 2. Incomplete subtasks
        # 3. Incomplete dependencies
        with self.assertRaises(ValidationError):
            self.task_service.update_task_status(parent_task.id, "complete")
        
        # Step 1: Complete the dependency task
        dependency_task = self.task_service.update_task_status(dependency_task.id, "in progress")
        dependency_task = self.task_service.update_task_status(dependency_task.id, "complete")
        
        # Still cannot complete due to checklist and subtasks
        with self.assertRaises(ValidationError):
            self.task_service.update_task_status(parent_task.id, "complete")
        
        # Step 2: Complete all checklist items
        self.task_service.update_checklist_item(parent_task.id, checklist.id, checklist_item1, True)
        self.task_service.update_checklist_item(parent_task.id, checklist.id, checklist_item2, True)
        
        # Still cannot complete due to subtasks
        with self.assertRaises(ValidationError):
            self.task_service.update_task_status(parent_task.id, "complete")
        
        # Step 3: Complete all subtasks
        subtask1 = self.task_service.update_task_status(subtask1.id, "in progress")
        subtask1 = self.task_service.update_task_status(subtask1.id, "complete")
        
        subtask2 = self.task_service.update_task_status(subtask2.id, "in progress")
        subtask2 = self.task_service.update_task_status(subtask2.id, "complete")
        
        # Now parent task can be completed
        parent_task = self.task_service.update_task_status(parent_task.id, "in progress")
        parent_task = self.task_service.update_task_status(parent_task.id, "complete")
        self.assertEqual(parent_task.status, "complete")
    
    def test_task_comment_and_history_tracking(self):
        """Test task comment functionality and history tracking."""
        # Create a task
        task = self.task_service.create_task({
            "name": "Comment Test Task",
            "description": "Task for testing comments",
            "status": "to do",
            "list_id": "lst_test001"
        })
        
        # Add comments to the task
        comment1_id = self.task_service.add_comment(task.id, "Initial planning comment")
        comment2_id = self.task_service.add_comment(task.id, "Progress update: Started implementation")
        
        # Verify comments were added
        updated_task = self.task_service.get_task(task.id)
        self.assertEqual(len(updated_task.comments), 2)
        self.assertEqual(updated_task.comments[0].text, "Initial planning comment")
        
        # Update task status and verify automatic history comment
        task = self.task_service.update_task_status(task.id, "in progress", "Starting work on this task")
        
        # Check that status update comment was added
        updated_task = self.task_service.get_task(task.id)
        self.assertEqual(len(updated_task.comments), 3)
        self.assertIn("Starting work on this task", updated_task.comments[2].text)
        
        # Test editing a comment
        self.task_service.update_comment(task.id, comment1_id, "Updated initial planning comment")
        
        # Verify comment was updated
        updated_task = self.task_service.get_task(task.id)
        self.assertEqual(updated_task.comments[0].text, "Updated initial planning comment")
        
        # Test deleting a comment
        self.task_service.delete_comment(task.id, comment2_id)
        
        # Verify comment was deleted
        updated_task = self.task_service.get_task(task.id)
        self.assertEqual(len(updated_task.comments), 2)
        
        # Complete task with comment
        task = self.task_service.update_task_status(task.id, "complete", "Task completed successfully")
        
        # Verify completion comment was added
        final_task = self.task_service.get_task(task.id)
        self.assertEqual(len(final_task.comments), 3)
        self.assertIn("Task completed successfully", final_task.comments[2].text)
    
    def test_task_tag_management(self):
        """Test task tag management functionality."""
        # Create a task with initial tags
        task = self.task_service.create_task({
            "name": "Tag Test Task",
            "description": "Task for testing tag management",
            "status": "to do",
            "list_id": "lst_test001",
            "tags": ["initial", "testing"]
        })
        
        # Verify initial tags
        self.assertEqual(len(task.tags), 2)
        self.assertIn("initial", task.tags)
        self.assertIn("testing", task.tags)
        
        # Add new tags
        task = self.task_service.update_tags(task.id, ["initial", "testing", "important", "bug"])
        
        # Verify tags were added
        self.assertEqual(len(task.tags), 4)
        self.assertIn("important", task.tags)
        self.assertIn("bug", task.tags)
        
        # Remove tags
        task = self.task_service.update_tags(task.id, ["important", "bug"])
        
        # Verify tags were removed
        self.assertEqual(len(task.tags), 2)
        self.assertNotIn("initial", task.tags)
        self.assertNotIn("testing", task.tags)
        self.assertIn("important", task.tags)
        self.assertIn("bug", task.tags)
        
        # Replace all tags
        task = self.task_service.update_tags(task.id, ["completed", "verified"])
        
        # Verify tags were replaced
        self.assertEqual(len(task.tags), 2)
        self.assertIn("completed", task.tags)
        self.assertIn("verified", task.tags)
        self.assertNotIn("important", task.tags)
        self.assertNotIn("bug", task.tags)
        
        # Clear all tags
        task = self.task_service.update_tags(task.id, [])
        
        # Verify tags were cleared
        self.assertEqual(len(task.tags), 0)


if __name__ == "__main__":
    unittest.main() 