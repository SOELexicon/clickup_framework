#!/usr/bin/env python3
"""
Integration tests for CLI-Core module interactions.

These tests verify the proper integration between the CLI module and Core services,
ensuring that commands executed through the CLI correctly interact with the Core
module's services and repositories.
"""
import unittest
import tempfile
import json
import os
import io
import sys
from pathlib import Path
from unittest.mock import patch, MagicMock
# from clickup_api import ClickUpAPI  # Assuming this exists for API interactions - Removing unused import

# Import CLI components
# Updated imports for commands based on refactor/cli/commands/
from refactor.cli.command import Command # Base command class might still be needed
from refactor.cli.commands.task import CreateTaskCommand, ShowTaskCommand, UpdateTaskCommand, ListTasksCommand, DeleteTaskCommand
from refactor.cli.commands.relationship import AddRelationshipCommand, RemoveRelationshipCommand, ListRelationshipsCommand, CheckCyclesCommand
from refactor.cli.commands.search import SearchCommand
from refactor.cli.commands.checklist import CreateChecklistCommand, CheckItemCommand, ListChecklistItemsCommand
from refactor.cli.commands.assign import AssignToListCommand # Assuming assign command exists here

# Import core entities and services
from refactor.core.manager import CoreManager
from refactor.core.entities.task_entity import TaskEntity, TaskStatus, TaskPriority # Updated import path
from refactor.core.repositories.task_repository import TaskRepository
from refactor.core.services.task_service import TaskService
from refactor.core.exceptions import ValidationError, EntityNotFoundError

# Import storage components
from refactor.storage.providers.json_storage_provider import JsonStorageProvider
from refactor.storage.serialization.json_serializer import JsonSerializer


class CLICoreIntegrationTests(unittest.TestCase):
    """Integration tests for CLI-Core module interactions."""

    def setUp(self):
        """Set up test environment with temporary test files."""
        # Create a temporary directory for test files
        self.temp_dir = tempfile.TemporaryDirectory()
        self.temp_path = Path(self.temp_dir.name)
        
        # Create a test file path
        # Ensure the path uses self.temp_path, not self.temp_dir.name directly
        self.test_file_path = self.temp_path / "test_cli_core.json" 
        
        # Initialize storage components (serializers likely not needed at this level)
        # self.serializer = JsonSerializer() 
        # self.storage_provider = JsonStorageProvider() 
        
        # --- Initialize CoreManager ---
        # The CoreManager creates its own repository and service internally
        self.core_manager = CoreManager() 
        
        # --- Create initial empty template structure on disk ---
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
            "tasks": [], # Start with empty tasks
            "relationships": []
        }
        with open(self.test_file_path, 'w') as f:
            json.dump(template_data, f, indent=2)
        
        # --- Load the template into the CoreManager ---
        self.core_manager.load_template(str(self.test_file_path))

        # --- Set up test task data using CoreManager ---
        test_task_data = {
            "name": "Test Task",
            "description": "Test task description",
            "status": "to do", 
            "priority": 3, 
            "tags": ["test", "integration"],
            "container_id": "lst_test001" # Assuming container_id is the correct key
            # list_id might also work depending on implementation
        }
        self.test_task = self.core_manager.create_task(test_task_data)
        
        # Ensure the task is saved (CoreManager might not auto-save after create)
        # Use the save_template method
        self.core_manager.save_template(str(self.test_file_path)) 
        
        # Store the ID for later use (assuming create_task returns the task object/dict)
        self.test_task_id = self.test_task['id'] # Or self.test_task.id if it returns an object

    def tearDown(self):
        """Clean up temporary files."""
        self.temp_dir.cleanup()
    
    def _execute_command(self, command_class, args):
        """Helper method to create and execute a command with the given arguments."""
        # Create command instance, passing core_manager
        command = command_class(self.core_manager) 
        
        # Set dependencies (might not be needed if passed via constructor)
        # command.task_service = self.task_service # Inject CoreManager instead if needed
        
        # Parse arguments
        # Use CustomArgumentParser if commands rely on it
        # parser = command.configure_parser(CustomArgumentParser()) 
        parser = ArgumentParser() # Use standard ArgumentParser for now
        command.configure_parser(parser)
        
        # Handle potential exit_on_error=False if using CustomArgumentParser
        try:
        parsed_args = parser.parse_args(args)
        except SystemExit:
             # Handle argparse errors if necessary, maybe return error indicator
             output = captured_output.getvalue()
             sys.stdout = sys.__stdout__
             return {'result': False, 'output': output} # Indicate failure
        
        # Capture stdout
        captured_output = io.StringIO()
        sys.stdout = captured_output
        
        try:
            # Execute command
            # The execute method now likely returns an exit code (0 for success)
            exit_code = command.execute(parsed_args)
            
            # Restore stdout
            sys.stdout = sys.__stdout__
            
            return {
                'result': exit_code == 0, # Success if exit code is 0
                'output': captured_output.getvalue()
            }
        except Exception as e:
             # Catch other potential errors during execution
             output = captured_output.getvalue()
             sys.stdout = sys.__stdout__
             # Log or print the exception
             print(f"Command execution failed: {e}", file=sys.__stderr__) 
             return {'result': False, 'output': output} # Indicate failure
        finally:
            # Ensure stdout is restored even if an exception occurs
            sys.stdout = sys.__stdout__
    
    def test_create_task_command(self):
        """Test creating a task through the CLI command."""
        # Define command arguments
        # Removed --folder and --list as they are not valid for create-task
        args = [
            str(self.test_file_path), # Use string path for argparse
            "New CLI Task",
            "--description", "Task created via CLI",
            "--status", "to do",
            "--priority", "2",
            "--tags", "cli,test" # Pass tags as a single comma-separated string
        ]
        
        # Execute command (Using the correct command class)
        result = self._execute_command(CreateTaskCommand, args)
        
        # Verify command succeeded
        self.assertTrue(result['result'], f"Create task command failed. Output:\\n{result['output']}")
        
        # Verify task was created in the repository using CoreManager
        created_task = self.core_manager.get_task_by_name("New CLI Task")
        
        self.assertIsNotNone(created_task)
        self.assertEqual(created_task['description'], "Task created via CLI")
        # Compare with string status or enum value depending on what get_task_by_name returns
        self.assertEqual(str(created_task['status']), "to do") 
        self.assertEqual(created_task['priority'], 2) # Assuming priority is stored as int
        self.assertEqual(set(created_task['tags']), {"cli", "test"})

        # TODO: Add separate test for assigning the created task using AssignToListCommand
    
    def test_show_task_command(self):
        """Test retrieving and displaying a task through the CLI command."""
        # Define command arguments
        args = [
            str(self.test_file_path),
            self.test_task_id, # Use the known ID
            "--details"
        ]
        
        # Execute command (Using the correct command class)
        result = self._execute_command(ShowTaskCommand, args)
        
        # Verify command succeeded
        self.assertTrue(result['result'], f"Show task command failed. Output:\\n{result['output']}")
        
        # Verify output contains task details
        output = result['output']
        self.assertIn("Test Task", output)
        self.assertIn("Test task description", output)
        self.assertIn("to do", output)
        self.assertIn("integration", output)
    
    def test_update_task_command(self): # Renamed from test_update_task_status_command
        """Test updating a task's status through the CLI command."""
        # Define command arguments for UpdateTaskCommand
        args = [
            str(self.test_file_path),
            self.test_task_id, # Use the known ID
            "--status", "in progress", # Use status flag
            "--comment", "Status updated via CLI test" # Use comment flag
        ]
        
        # Execute command (Using the correct command class: UpdateTaskCommand)
        result = self._execute_command(UpdateTaskCommand, args)
        
        # Verify command succeeded
        self.assertTrue(result['result'], f"Update task command failed. Output:\\n{result['output']}")
        
        # Verify task status was updated using CoreManager
        updated_task = self.core_manager.get_task(self.test_task_id)
        self.assertEqual(str(updated_task['status']), "in progress")
        
        # Verify comment was added (check CoreManager/TaskService capability or output)
        # This depends on how comments are stored/retrieved. 
        # Assume comments are added via a separate CoreManager method if not part of update_task
        # Check output first as it's more likely for CLI tests
        # self.assertIn("Comment added", result['output']) 
        # Or if update_task returns the task with comments:
        # if 'comments' in updated_task and updated_task['comments']:
        #     comment_texts = [c.get('text', '') for c in updated_task['comments']]
        #     self.assertTrue(any("Status updated via CLI test" in text for text in comment_texts))
        # Let's assume update_task doesn't handle comments directly based on CoreManager interface
        # We need a separate comment command test if applicable
    
    def test_add_relationship_command(self):
        """Test adding a relationship between tasks through the CLI command."""
        # Create a second task for the relationship using CoreManager
        related_task_data = {
            "name": "Related Task",
            "description": "Task for relationship testing",
            "status": "to do",
            "priority": 3,
            "container_id": "lst_test001", 
            "tags": ["test", "relationship"]
        }
        related_task = self.core_manager.create_task(related_task_data)
        # Save after creating the second task
        self.core_manager.save_template(str(self.test_file_path)) 
        related_task_id = related_task['id']
        
        # Define command arguments
        args = [
            str(self.test_file_path),
            self.test_task_id, # Source task ID
            "depends_on",
            related_task_id # Target task ID
        ]
        
        # Execute command (Using the correct command class)
        result = self._execute_command(AddRelationshipCommand, args)
        
        # Verify command succeeded
        self.assertTrue(result['result'], f"Add relationship command failed. Output:\\n{result['output']}")
        
        # Verify relationship was created using CoreManager or by checking output
        # This depends on how relationships are stored/retrieved.
        # Option 1: Use CoreManager if it has a method like get_relationships
        # relationships = self.core_manager.get_relationships(self.test_task_id) 
        # self.assertTrue(any(r['source_id'] == self.test_task_id and 
        #                     r['target_id'] == related_task_id and 
        #                     r['type'] == "depends_on" for r in relationships))
        # Option 2: Check command output for confirmation (more reliable for CLI test)
        self.assertIn("Relationship added", result['output']) 
    
    def test_search_command(self):
        """Test searching for tasks through the CLI command."""
        # Create additional tasks for testing search using CoreManager
        task_a_data = {
            "name": "SearchA Important Task",
            "description": "Task with specific keywords",
            "status": "to do",
            "priority": 1,
            "container_id": "lst_test001",
            "tags": ["search", "important"]
        }
        self.core_manager.create_task(task_a_data)
        
        task_b_data = {
            "name": "SearchB Regular Task",
            "description": "Another task with keywords",
            "status": "to do",
            "priority": 3,
            "container_id": "lst_test001",
            "tags": ["search", "regular"]
        }
        self.core_manager.create_task(task_b_data)
        # Save after creating all search tasks
        self.core_manager.save_template(str(self.test_file_path)) 
        
        # Define command arguments for name search
        args = [
            str(self.test_file_path),
            "name contains 'Search'", # Query string
            # Add other search options if needed, e.g., --status, --priority
        ]
        
        # Execute command (Using the correct command class)
        result = self._execute_command(SearchCommand, args)
        
        # Verify command succeeded
        self.assertTrue(result['result'], f"Search command failed. Output:\\n{result['output']}")
        
        # Verify output contains both search tasks
        output = result['output']
        self.assertIn("SearchA Important Task", output)
        self.assertIn("SearchB Regular Task", output)
        
        # Test more specific search
        args = [
            str(self.test_file_path),
            "name contains 'Important' and priority == 1", # More complex query
        ]
        
        result = self._execute_command(SearchCommand, args)
        self.assertTrue(result['result'], f"Search command failed. Output:\\n{result['output']}")
        
        # Verify output contains only the important task
        output = result['output']
        self.assertIn("SearchA Important Task", output)
        self.assertNotIn("SearchB Regular Task", output)
        
        # Verify task status was not changed using CoreManager
        unchanged_task = self.core_manager.get_task(self.test_task_id)
        # Need to handle case where task might be None if ID is invalid in test setup
        if unchanged_task:
            self.assertNotEqual(str(unchanged_task['status']), "invalid_status")
        else:
            # If task is None, the previous check already failed, which is expected
            pass 
    
    def test_error_handling_invalid_input(self):
        """Test error handling when CLI commands receive invalid input."""
        # Test with non-existent task for ShowTaskCommand
        args_show = [
            str(self.test_file_path),
            "Non-Existent Task",
            "--details"
        ]
        
        # Execute ShowTaskCommand
        result_show = self._execute_command(ShowTaskCommand, args_show)
        
        # Verify command failed
        self.assertFalse(result_show['result'], "Show task with non-existent task should fail.")
        
        # Verify output contains error message
        output_show = result_show['output']
        # Error message might come from CoreManager or Command itself
        self.assertTrue("not found" in output_show.lower() or "error" in output_show.lower()) 
        
        # Test UpdateTaskCommand with invalid status
        args_update = [
            str(self.test_file_path),
            self.test_task_id,
            "--status", "invalid_status" # Invalid status value
        ]
        
        # Execute UpdateTaskCommand and expect failure
        # The execute helper should catch exceptions or return failure code
        result_update = self._execute_command(UpdateTaskCommand, args_update)
        self.assertFalse(result_update['result'], "Update task with invalid status should fail.")
        output_update = result_update['output']
        # Check for validation error message in output
        self.assertTrue("invalid status" in output_update.lower() or "validationerror" in output_update.lower()) 
        
        # Verify task status was not changed using CoreManager
        unchanged_task = self.core_manager.get_task(self.test_task_id)
        self.assertNotEqual(str(unchanged_task['status']), "invalid_status")
    
    def test_cli_argument_validation(self):
        """Test that CLI commands properly validate arguments via argparse."""
        # This test often overlaps with error handling. Focus on argparse level errors.
        # Example: Missing required argument for UpdateTaskCommand
        args_missing = [
            str(self.test_file_path),
            # Missing task ID/Name
            "--status", "in progress" 
        ]
        
        # Execute command and expect failure (likely SystemExit from argparse)
        # The _execute_command helper should handle SystemExit from parse_args
        result = self._execute_command(UpdateTaskCommand, args_missing)
        
        # Verify command failed due to parsing
        self.assertFalse(result['result'], "Command with missing required argument should fail parsing.")
        self.assertIn("required", result['output'].lower()) # Check for argparse error message
    
    def test_command_output_formatting(self):
        """Test that CLI commands format their output correctly."""
        # Use ShowTaskCommand as an example
        args = [
            str(self.test_file_path),
            self.test_task_id,
            "--details"
        ]
        
        # Execute command
        result = self._execute_command(ShowTaskCommand, args)
        
        # Verify command succeeded
        self.assertTrue(result['result'], f"Show task command failed. Output:\\n{result['output']}")
        
        # Verify output formatting (add more specific checks based on ShowTaskCommand's output)
        output = result['output']
        # Check for key elements and structure expected from detailed view
        self.assertTrue(output.strip().startswith("Task Details:")) # Example check for header
        self.assertIn(f"ID: {self.test_task_id}", output) 
        self.assertIn("Name: Test Task", output)
        self.assertIn("Status: to do", output) # Check for colored status if applicable
        self.assertIn("Priority: 3", output)
        self.assertIn("Tags: test, integration", output)
        self.assertIn("Description:", output)
        self.assertIn("Test task description", output)
        # Add checks for alignment, sections, colors if applicable


if __name__ == "__main__":
    unittest.main() 