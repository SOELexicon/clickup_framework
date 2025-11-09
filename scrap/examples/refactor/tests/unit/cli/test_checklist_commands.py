#!/usr/bin/env python3
"""
Unit tests for the Checklist CLI commands in the refactored ClickUp JSON Manager.
Tests include both successful execution paths and error handling.
"""
import unittest
import os
import subprocess
import json
import tempfile
from pathlib import Path
from unittest.mock import patch, MagicMock
from argparse import Namespace

from refactor.cli.commands.checklist import (
    CreateChecklistCommand,
    CheckChecklistItemCommand,
    ListChecklistItemsCommand,
    ChecklistCommand
)
from refactor.core.exceptions import EntityNotFoundError, ValidationError


class ChecklistCommandTests(unittest.TestCase):
    """Test cases for checklist commands using direct command execution with mocks."""

    def setUp(self):
        """Set up test environment."""
        # Create mock core manager
        self.mock_core_manager = MagicMock()
        
        # Create a test file path
        self.temp_dir = tempfile.TemporaryDirectory()
        self.temp_path = Path(self.temp_dir.name)
        self.test_file = self.temp_path / "test_checklists.json"
        
        # Create mock tasks and checklists
        self.task_with_checklists = {
            "id": "tsk_test1001",
            "name": "Test Task With Checklists",
            "description": "Task with checklists for testing",
            "status": "in progress",
            "priority": 1,
            "tags": ["test", "checklist"],
            "checklists": {
                "chk_test1001": {
                    "id": "chk_test1001",
                    "name": "Test Checklist",
                    "items": [
                        {
                            "id": "itm_test1001",
                            "text": "Test Item 1",
                            "checked": False
                        },
                        {
                            "id": "itm_test1002",
                            "text": "Test Item 2",
                            "checked": True
                        }
                    ]
                }
            }
        }
        
        self.task_without_checklists = {
            "id": "tsk_test1002",
            "name": "Test Task Without Checklists",
            "description": "Task without checklists for testing",
            "status": "to do",
            "priority": 2,
            "tags": ["test"],
            "checklists": {}
        }
        
        # Setup default mock behavior
        self.mock_core_manager.get_task.side_effect = self._mock_get_task
        self.mock_core_manager.get_task_by_name.side_effect = self._mock_get_task_by_name
        self.mock_core_manager.create_checklist.return_value = {
            "id": "chk_new1001",
            "name": "New Checklist", 
            "items": []
        }
        self.mock_core_manager.check_checklist_item.return_value = {
            "id": "itm_test1001",
            "text": "Test Item 1",
            "checked": True
        }

    def tearDown(self):
        """Clean up test environment."""
        self.temp_dir.cleanup()
        
    def _mock_get_task(self, task_id):
        """Mock implementation of get_task."""
        if task_id == "tsk_test1001" or task_id == "Test Task With Checklists":
            return self.task_with_checklists
        elif task_id == "tsk_test1002" or task_id == "Test Task Without Checklists":
            return self.task_without_checklists
        else:
            raise EntityNotFoundError(f"Task not found: {task_id}")
            
    def _mock_get_task_by_name(self, name):
        """Mock implementation of get_task_by_name."""
        if name == "Test Task With Checklists":
            return self.task_with_checklists
        elif name == "Test Task Without Checklists":
            return self.task_without_checklists
        else:
            raise EntityNotFoundError(f"Task not found: {name}")
    
    def test_list_checklists(self):
        """Test listing checklists in a task."""
        # Create the command
        command = ListChecklistItemsCommand(self.mock_core_manager)
        
        # Execute the command for task with checklists
        args = Namespace(
            template=str(self.test_file),
            task="Test Task With Checklists",
            checklist=None,
            unchecked_only=False,
            checked_only=False
        )
        # TODO: Failing test. Error: AttributeError: type object 'DefaultTheme' has no attribute 'CHECKLIST_UNCHECKED'.
        # Investigate ListChecklistItemsCommand execute method and DefaultTheme in refactor/utils/colors.py.
        # The command attempts to use DefaultTheme.CHECKLIST_UNCHECKED which doesn't seem to exist.
        result = command.execute(args)
        
        # Verify success
        self.assertEqual(result, 0, "Listing checklists should succeed")
        
        # Execute the command for task without checklists
        args = Namespace(
            template=str(self.test_file),
            task="Test Task Without Checklists",
            checklist=None,
            unchecked_only=False,
            checked_only=False
        )
        result = command.execute(args)
        
        # Verify success
        self.assertEqual(result, 0, "Listing empty checklists should succeed")
    
    def test_list_nonexistent_task(self):
        """Test listing checklists for a nonexistent task."""
        # Create the command
        command = ListChecklistItemsCommand(self.mock_core_manager)
        
        # Make get_task and get_task_by_name raise EntityNotFoundError for nonexistent task
        def mock_get_task_side_effect(task_id):
            if task_id == "Nonexistent Task":
                raise EntityNotFoundError(f"Task not found: {task_id}")
            return self._mock_get_task(task_id)
            
        def mock_get_task_by_name_side_effect(name):
            if name == "Nonexistent Task":
                raise EntityNotFoundError(f"Task not found: {name}")
            return self._mock_get_task_by_name(name)
            
        self.mock_core_manager.get_task.side_effect = mock_get_task_side_effect
        self.mock_core_manager.get_task_by_name.side_effect = mock_get_task_by_name_side_effect
        
        # Execute the command
        args = Namespace(
            template=str(self.test_file),
            task="Nonexistent Task",
            checklist=None,
            unchecked_only=False,
            checked_only=False
        )
        result = command.execute(args)
        
        # Verify failure
        self.assertNotEqual(result, 0, "Listing checklists for nonexistent task should fail")
    
    def test_create_checklist(self):
        """Test creating a new checklist."""
        # Create the command
        command = CreateChecklistCommand(self.mock_core_manager)
        
        # Execute the command
        args = Namespace(
            template=str(self.test_file),
            task="Test Task Without Checklists",
            name="New Checklist",
            items="Item 1,Item 2,Item 3"
        )
        result = command.execute(args)
        
        # Verify success
        self.assertEqual(result, 0, "Creating checklist should succeed")
        
        # Verify that create_checklist was called with the correct arguments
        self.mock_core_manager.create_checklist.assert_called_with(
            self.task_without_checklists["id"], "New Checklist"
        )
        
        # Verify that add_checklist_item was called for each item
        self.assertEqual(self.mock_core_manager.add_checklist_item.call_count, 3,
                         "Should add 3 checklist items")
    
    def test_create_duplicate_checklist(self):
        """Test creating a checklist with a duplicate name."""
        # Create the command
        command = CreateChecklistCommand(self.mock_core_manager)
        
        # Execute the command twice with the same name
        args = Namespace(
            template=str(self.test_file),
            task="Test Task Without Checklists",
            name="Duplicate Checklist",
            items="Item 1"
        )
        command.execute(args)
        
        # Second creation should succeed (duplicate names are allowed)
        args.items = "Item 2"
        result = command.execute(args)
        
        # Verify success
        self.assertEqual(result, 0, "Creating duplicate checklist should succeed")
    
    def test_check_item(self):
        """Test checking a checklist item."""
        # Create the command
        command = CheckChecklistItemCommand(self.mock_core_manager)
        
        # Execute the command
        args = Namespace(
            template_file=str(self.test_file),
            task_name="Test Task With Checklists",
            item_ids=["itm_test1001", "itm_test1002"],
            unchecked=False,
            checked=True
        )
        result = command.execute(args)
        
        # Verify success
        self.assertEqual(result, 0, "Checking items should succeed")
        
        # Verify the method was called with the correct arguments
        self.mock_core_manager.check_checklist_item.assert_any_call(
            "Test Task With Checklists", "itm_test1001", True
        )
        self.mock_core_manager.check_checklist_item.assert_any_call(
            "Test Task With Checklists", "itm_test1002", True
        )
        self.assertEqual(self.mock_core_manager.check_checklist_item.call_count, 2)
    
    def test_check_nonexistent_item(self):
        """Test checking a nonexistent checklist item."""
        # Create the command
        command = CheckChecklistItemCommand(self.mock_core_manager)
        
        # Make check_checklist_item raise EntityNotFoundError for nonexistent item
        self.mock_core_manager.check_checklist_item.side_effect = EntityNotFoundError(
            "Checklist item not found: itm_nonexistent"
        )
        
        # Execute the command
        args = Namespace(
            template_file=str(self.test_file),
            task_name="Test Task With Checklists",
            item_ids=["itm_nonexistent"],
            unchecked=False,
            checked=True
        )
        result = command.execute(args)
        
        # Verify failure
        self.assertNotEqual(result, 0, "Checking nonexistent item should fail")
    
    def test_uncheck_item(self):
        """Test unchecking a checklist item."""
        # Create the command
        command = CheckChecklistItemCommand(self.mock_core_manager)
        
        # Setup item to be unchecked
        self.mock_core_manager.check_checklist_item.return_value = {
            "id": "itm_test1002",
            "text": "Test Item 2",
            "checked": False
        }
        
        # Execute the command
        args = Namespace(
            template_file=str(self.test_file),
            task_name="Test Task With Checklists",
            item_ids=["itm_test1002"],
            unchecked=True,
            checked=False
        )
        result = command.execute(args)
        
        # Verify success
        self.assertEqual(result, 0, "Unchecking item should succeed")
        
        # Verify the method was called with the correct arguments
        self.mock_core_manager.check_checklist_item.assert_called_once_with(
            "Test Task With Checklists", "itm_test1002", False
        )


class ChecklistCommandUnitTests(unittest.TestCase):
    """Unit tests for checklist command classes."""

    def setUp(self):
        """Set up mocks for unit tests."""
        self.mock_core_manager = MagicMock()
        # Define a dummy test_file path for unit tests, as the manager is mocked anyway
        self.test_file = Path("/tmp/dummy_checklist_test.json") 

    def test_create_checklist_command(self):
        """Test CreateChecklistCommand execution."""
        # Set up command with mock context
        command = CreateChecklistCommand(self.mock_core_manager)
        
        # Mock task result
        task_id = "tsk_test1001"
        mock_task = {"id": task_id, "name": "Test Task"}
        
        # Setup mocks for task retrieval
        self.mock_core_manager.get_task.side_effect = Exception("Not found by ID")
        self.mock_core_manager.get_task_by_name.return_value = mock_task
        
        # Mock checklist creation
        mock_checklist = {"id": "chk_test1001", "name": "Test Checklist"}
        self.mock_core_manager.create_checklist.return_value = mock_checklist
        
        # Define args for this specific test
        args = Namespace(
            template=str(self.test_file),
            task="Test Task",
            name="New Test Checklist",
            items="Item A, Item B"
        )
        
        # Execute command
        result = command.execute(args)
        self.assertEqual(result, 0) # Expect success
        
        # Verify service methods were called with correct arguments
        self.mock_core_manager.get_task_by_name.assert_called_once_with(args.task)
        self.mock_core_manager.create_checklist.assert_called_once_with(task_id, args.name)
        self.mock_core_manager.add_checklist_item.assert_any_call(task_id, mock_checklist['id'], "Item A")
        self.mock_core_manager.add_checklist_item.assert_any_call(task_id, mock_checklist['id'], "Item B")
        
    def test_create_checklist_error_handling(self):
        """Test CreateChecklistCommand error handling."""
        # Set up command with mock context
        command = CreateChecklistCommand(self.mock_core_manager)
        
        # Make service throw an error (e.g., task not found)
        self.mock_core_manager.get_task.side_effect = EntityNotFoundError("Task not found")
        self.mock_core_manager.get_task_by_name.return_value = None
        
        # Define args for this specific test
        args = Namespace(
            template=str(self.test_file),
            task="NonExistent Task",
            name="Error Checklist",
            items="Item 1"
        )
        
        # Execute command should print error and return non-zero exit code
        result = command.execute(args)
        
        # Verify result is error code
        self.assertEqual(result, 1)
        self.mock_core_manager.create_checklist.assert_not_called()
    
    def test_check_item_command(self):
        """Test CheckItemCommand execution."""
        # Set up command with mock context
        command = CheckChecklistItemCommand(self.mock_core_manager)
        args = {
            "template_file": "test_template.json",
            "task_name": "Test Task",
            "item_ids": ["itm_test1001", "itm_test1002"],
            "checked": True,
            "unchecked": False
        }
        
        # Execute command
        command.execute(Namespace(**args))
        
        # Verify service method was called with correct arguments
        self.mock_core_manager.check_checklist_item.assert_any_call(
            args["task_name"], args["item_ids"][0], True
        )
        self.mock_core_manager.check_checklist_item.assert_any_call(
            args["task_name"], args["item_ids"][1], True
        )
        self.assertEqual(self.mock_core_manager.check_checklist_item.call_count, 2)
    
    def test_list_checklists_command(self):
        """Test ListChecklistItemsCommand execution."""
        command = ListChecklistItemsCommand(self.mock_core_manager)
        args = Namespace(
            template=str(self.test_file),
            task="Test Task",
            checklist=None,
            unchecked_only=False,
            checked_only=False
        )
        # TODO: Failing test. Error: AttributeError: type object 'DefaultTheme' has no attribute 'CHECKLIST_UNCHECKED'.
        # Same root cause as test_list_checklists in ChecklistCommandTests. Investigate ListChecklistItemsCommand
        # execute method and DefaultTheme in refactor/utils/colors.py.
        result = command.execute(args)
        self.assertEqual(result, 0)
        self.mock_core_manager.get_task.assert_called_once_with("Test Task")


if __name__ == "__main__":
    unittest.main() 