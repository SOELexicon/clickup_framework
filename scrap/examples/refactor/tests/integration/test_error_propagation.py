#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
Integration tests for error propagation across module boundaries.

This test suite verifies that errors are correctly propagated and 
handled when crossing different layers of the application.
"""

import unittest
import json
import io
import sys
from pathlib import Path
import tempfile
import os
from unittest.mock import patch, MagicMock

# Import from different modules to test cross-boundary error handling
from refactor.cli.error_handling import CLIError, handle_cli_error, map_exception_to_error_code
from refactor.cli.command import CommandContext
from refactor.core.exceptions import (
    ErrorCode, ValidationError, EntityNotFoundError, 
    ErrorContextBuilder
)
from refactor.common.exceptions import TaskNotFoundError
from refactor.storage.exceptions import RepositoryError, FileAccessError


class ErrorPropagationTests(unittest.TestCase):
    """Integration tests for error propagation across module boundaries."""

    def setUp(self):
        """Set up test fixtures."""
        self.test_dir = tempfile.TemporaryDirectory()
        self.test_file_path = Path(self.test_dir.name) / "test.json"
        
        # Create a test file
        with open(self.test_file_path, "w") as f:
            json.dump({"test": "data"}, f)
        
        # Capture stdout for testing error messages
        self.stdout_capture = io.StringIO()
        self.stdout_backup = sys.stdout
        sys.stdout = self.stdout_capture
    
    def tearDown(self):
        """Tear down test fixtures."""
        # Clean up temporary files
        self.test_dir.cleanup()
        
        # Restore stdout
        sys.stdout = self.stdout_backup
    
    def test_repository_error_propagation_to_cli(self):
        """Test propagation of repository errors to CLI layer."""
        # Define a mock repository that raises an error
        class MockRepository:
            def get_task(self, task_id):
                raise RepositoryError(f"Task '{task_id}' could not be loaded", "REPO_ERROR_001")
        
        # Define a service that uses the repository
        class TaskService:
            def __init__(self, repository):
                self.repository = repository
            
            def get_task(self, task_id):
                return self.repository.get_task(task_id)
        
        # Define a CLI command function that uses the service
        @handle_cli_error
        def get_task_command(task_id):
            repository = MockRepository()
            service = TaskService(repository)
            try:
                task = service.get_task(task_id)
                return 0  # Success
            except Exception as e:
                # The error should propagate to handle_cli_error decorator
                raise e
        
        # Execute the command
        exit_code = get_task_command("task-123")
        
        # Verify error propagation
        self.assertEqual(exit_code, 1)  # Should indicate error
        output = self.stdout_capture.getvalue().strip()
        self.assertIn("Error [", output)  # Should have error code
        self.assertIn("task-123", output)  # Should contain the task ID
        self.assertIn("could not be loaded", output)  # Should contain error message
    
    def test_validation_error_propagation_to_cli(self):
        """Test propagation of validation errors to CLI layer."""
        # Define a validator function
        def validate_task_status(status):
            valid_statuses = ["to do", "in progress", "complete"]
            if status not in valid_statuses:
                raise ValidationError(f"Invalid status: {status}")
        
        # Define a service that uses validation
        class TaskService:
            def update_task_status(self, task_id, status):
                # Validate the status
                validate_task_status(status)
                # If valid, would update the task
                return {"id": task_id, "status": status}
        
        # Define a CLI command function that uses the service
        @handle_cli_error
        def update_status_command(task_id, status):
            service = TaskService()
            try:
                task = service.update_task_status(task_id, status)
                print(f"Task {task_id} updated to {status}")
                return 0  # Success
            except Exception as e:
                # The error should propagate to handle_cli_error decorator
                raise e
        
        # Execute the command with invalid status
        exit_code = update_status_command("task-123", "invalid")
        
        # Verify error propagation
        self.assertEqual(exit_code, 1)  # Should indicate error
        output = self.stdout_capture.getvalue().strip()
        self.assertIn("Error [", output)  # Should have error code
        self.assertIn("Invalid status", output)  # Should contain error message
        self.assertIn("invalid", output)  # Should contain the invalid value
    
    def test_command_context_propagation(self):
        """Test error propagation using CommandContext across layers."""
        # Create command context
        mock_command = MagicMock()
        mock_command.name = "test_command"
        context = CommandContext(mock_command)
        
        # Define repository layer (lowest level)
        class Repository:
            def get_task(self, task_id, context):
                if not task_id:
                    error = RepositoryError("Task ID cannot be empty", "REPO_ERROR_002")
                    context.abort(error)
                    return None
                return {"id": task_id, "name": "Test Task"}
        
        # Define service layer (middle level)
        class Service:
            def __init__(self, repository):
                self.repository = repository
            
            def get_task(self, task_id, context):
                if not task_id:
                    error = ValidationError("Task ID is required")
                    context.abort(error)
                    return None
                
                task = self.repository.get_task(task_id, context)
                if context.aborted:
                    # Error was already set in context, just propagate
                    return None
                
                return task
        
        # Define command layer (top level)
        class Command:
            def __init__(self, service):
                self.service = service
            
            def execute(self, task_id, context):
                task = self.service.get_task(task_id, context)
                if context.aborted:
                    # Error was already set in context, just return result
                    return 1
                
                print(f"Task found: {task['name']}")
                return 0
        
        # Create the layers
        repository = Repository()
        service = Service(repository)
        command = Command(service)
        
        # Execute with error (empty task ID)
        result = command.execute("", context)
        
        # Verify error propagation
        self.assertEqual(result, 1)  # Should indicate error
        self.assertTrue(context.aborted)
        self.assertIsNotNone(context.error)
        output = self.stdout_capture.getvalue().strip()
        self.assertIn("Error [", output)  # Should have error code
        
        # Verify the error came from validation layer
        self.assertIsInstance(context.error, ValidationError)
        self.assertIn("Task ID is required", str(context.error))
    
    def test_storage_error_propagation(self):
        """Test propagation of storage errors through multiple layers."""
        # Create a non-existent file path
        nonexistent_path = Path(self.test_dir.name) / "nonexistent.json"
        
        # Define file storage layer
        class FileStorage:
            def read_file(self, file_path):
                try:
                    with open(file_path, 'r') as f:
                        return json.load(f)
                except FileNotFoundError:
                    raise FileAccessError(f"File not found: {file_path}")
                except json.JSONDecodeError:
                    raise FileAccessError(f"Invalid JSON in file: {file_path}")
        
        # Define repository layer
        class Repository:
            def __init__(self, storage):
                self.storage = storage
            
            def load_task_template(self, template_path):
                try:
                    data = self.storage.read_file(template_path)
                    return data
                except FileAccessError:
                    # Propagate the original error
                    raise
        
        # Define service layer
        class Service:
            def __init__(self, repository):
                self.repository = repository
            
            def get_tasks(self, template_path):
                try:
                    template = self.repository.load_task_template(template_path)
                    return template.get('tasks', [])
                except Exception as e:
                    # Add more context but preserve original error
                    raise type(e)(f"{str(e)} (during task listing)")
        
        # Define CLI command
        @handle_cli_error
        def list_tasks_command(template_path):
            storage = FileStorage()
            repository = Repository(storage)
            service = Service(repository)
            
            try:
                tasks = service.get_tasks(template_path)
                print(f"Found {len(tasks)} tasks")
                return 0
            except Exception as e:
                # Let the decorator handle the error
                raise
        
        # Execute the command with nonexistent file
        exit_code = list_tasks_command(nonexistent_path)
        
        # Verify error propagation
        self.assertEqual(exit_code, 1)  # Should indicate error
        output = self.stdout_capture.getvalue().strip()
        self.assertIn("Error [", output)  # Should have error code
        self.assertIn("File not found", output)  # Should contain storage error
        self.assertIn("nonexistent.json", output)  # Should contain the file path
        self.assertIn("during task listing", output)  # Should contain the added context


if __name__ == '__main__':
    unittest.main() 