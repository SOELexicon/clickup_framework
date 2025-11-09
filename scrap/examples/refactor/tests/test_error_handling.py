#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
Tests for error handling functionality across the CLI.
"""

import unittest
from unittest.mock import patch, MagicMock
import sys
import io
import json

from refactor.cli.command import CommandContext
from refactor.cli.error_handling import CLIError, map_exception_to_error_code, validate_args, handle_cli_error
from refactor.core.exceptions import (
    ErrorCode, ErrorContextBuilder, get_command_error_code,
    ValidationError, EntityNotFoundError
)
from refactor.common.exceptions import TaskNotFoundError


class TestErrorHandling(unittest.TestCase):
    """Test error handling functionality."""

    def setUp(self):
        """Set up test fixtures."""
        self.mock_command = MagicMock()
        self.mock_command.name = "test_command"
        
        # Capture stdout for testing printed messages
        self.stdout_capture = io.StringIO()
        self.stdout_backup = sys.stdout
        sys.stdout = self.stdout_capture
    
    def tearDown(self):
        """Tear down test fixtures."""
        # Restore stdout
        sys.stdout = self.stdout_backup
    
    def test_command_context_abort_with_cli_error(self):
        """Test CommandContext abort with CLIError."""
        # Create a CLI error
        error_code = ErrorCode("CLI", "TEST", "ABORT", "001")
        context_data = {"test_key": "test_value"}
        cli_error = CLIError("Test CLIError", error_code, context_data)
        
        # Create context and abort
        context = CommandContext(self.mock_command)
        context.abort(cli_error)
        
        # Verify state
        self.assertTrue(context.aborted)
        self.assertEqual(context.error, cli_error)
        self.assertEqual(context.error_context, cli_error.error_context)
        self.assertEqual(context.get_error_code(), str(error_code))
        
        # Verify error message was printed
        output = self.stdout_capture.getvalue().strip()
        self.assertEqual(output, f"Error [{error_code}]: Test CLIError")
    
    def test_command_context_abort_with_exception(self):
        """Test CommandContext abort with standard exception."""
        # Create a standard exception
        exception = ValueError("Test exception")
        
        # Create context and abort
        context = CommandContext(self.mock_command)
        context.abort(exception)
        
        # Verify state
        self.assertTrue(context.aborted)
        self.assertEqual(context.error, exception)
        self.assertIsNotNone(context.error_context)
        self.assertTrue(context.get_error_code().startswith("CLI-COMMAND-ABORT-001"))
        
        # Verify error message was printed
        output = self.stdout_capture.getvalue().strip()
        self.assertTrue("Error [CLI-COMMAND-ABORT-001]: Test exception" in output)
    
    def test_command_context_abort_with_context_data(self):
        """Test CommandContext abort with additional context data."""
        # Create an exception with context data
        exception = ValueError("Test with context")
        context_data = {"file_path": "test.json", "line_number": 42}
        
        # Create context and abort
        context = CommandContext(self.mock_command)
        context.abort(exception, context_data)
        
        # Verify state
        self.assertTrue(context.aborted)
        self.assertEqual(context.error, exception)
        
        # Verify context data was added
        self.assertEqual(context.error_context.get_context_data("file_path"), "test.json")
        self.assertEqual(context.error_context.get_context_data("line_number"), 42)
    
    def test_has_error_and_get_error_code(self):
        """Test has_error and get_error_code methods."""
        context = CommandContext(self.mock_command)
        
        # Initially no error
        self.assertFalse(context.has_error())
        self.assertEqual(context.get_error_code(), "")
        
        # After error
        context.abort(ValueError("Test error"))
        self.assertTrue(context.has_error())
        self.assertTrue(context.get_error_code().startswith("CLI-COMMAND-ABORT-001"))
    
    def test_error_formatting(self):
        """Test error message formatting."""
        # Create a custom error code
        error_code = ErrorCode("CLI", "FORMAT", "TEST", "002")
        
        # Create a context and abort with formatted message
        context = CommandContext(self.mock_command)
        context.abort(CLIError("Error with formatting: value=42", error_code))
        
        # Verify formatted message
        output = self.stdout_capture.getvalue().strip()
        self.assertEqual(output, f"Error [{error_code}]: Error with formatting: value=42")
    
    def test_map_exception_to_error_code(self):
        """Test mapping different exceptions to appropriate error codes."""
        # Create different types of exceptions
        cli_error = CLIError("CLI error", ErrorCode("CLI", "TEST", "MAP", "001"))
        entity_not_found = EntityNotFoundError("entity-123", "Entity")
        task_not_found = TaskNotFoundError("task-123")
        validation_error = ValidationError("Invalid data")
        file_not_found = FileNotFoundError("test.json")
        generic_error = Exception("Generic error")
        
        # Map exceptions to error codes
        cli_error_code = map_exception_to_error_code(cli_error)
        entity_not_found_code = map_exception_to_error_code(entity_not_found)
        task_not_found_code = map_exception_to_error_code(task_not_found)
        validation_error_code = map_exception_to_error_code(validation_error)
        file_not_found_code = map_exception_to_error_code(file_not_found)
        generic_error_code = map_exception_to_error_code(generic_error)
        
        # Verify mappings
        self.assertEqual(str(cli_error_code), "CLI-TEST-MAP-001")
        self.assertTrue(str(entity_not_found_code).endswith("ENTITY-001"))
        self.assertTrue(str(task_not_found_code).endswith("TASK-001"))
        self.assertTrue(str(validation_error_code).endswith("GENERAL-001"))
        self.assertTrue("STORAGE-FILE" in str(file_not_found_code))
        self.assertTrue(str(generic_error_code).endswith("GENERAL-000"))
    
    def test_error_context_serialization(self):
        """Test error context serialization to JSON."""
        # Create an error with context data
        error_code = ErrorCode("CLI", "JSON", "TEST", "003")
        context_data = {
            "file_path": "test.json",
            "line_number": 42,
            "command": "update"
        }
        cli_error = CLIError("Test error for JSON", error_code, context_data)
        
        # Verify context can be serialized to JSON
        json_str = cli_error.error_context.to_json()
        self.assertIsInstance(json_str, str)
        
        # Verify JSON contains expected data
        json_data = json.loads(json_str)
        self.assertEqual(json_data["message"], "Test error for JSON")
        self.assertEqual(json_data["error_code"], str(error_code))
        self.assertEqual(json_data["context_data"]["file_path"], "test.json")
        self.assertEqual(json_data["context_data"]["line_number"], 42)
        self.assertEqual(json_data["context_data"]["command"], "update")
    
    def test_command_context_values(self):
        """Test get_value and set_value methods."""
        context = CommandContext(self.mock_command)
        
        # Initially value not set
        self.assertIsNone(context.get_value("test_key"))
        self.assertEqual(context.get_value("test_key", "default"), "default")
        
        # Set and get value
        context.set_value("test_key", "test_value")
        self.assertEqual(context.get_value("test_key"), "test_value")
        
        # Override value
        context.set_value("test_key", "new_value")
        self.assertEqual(context.get_value("test_key"), "new_value")
    
    def test_validate_args(self):
        """Test argument validation."""
        # Create args namespace
        args = type('Args', (), {
            'required_arg': 'value',
            'optional_arg': 'optional'
        })()
        
        # Validate with all required args present
        valid, error = validate_args(args, ['required_arg'])
        self.assertTrue(valid)
        self.assertIsNone(error)
        
        # Validate with missing required arg
        valid, error = validate_args(args, ['required_arg', 'missing_arg'])
        self.assertFalse(valid)
        self.assertTrue("Missing required argument: missing_arg" in error)
    
    def test_handle_cli_error_decorator_success(self):
        """Test handle_cli_error decorator with successful execution."""
        # Define a test function
        @handle_cli_error
        def successful_function():
            return 0  # Success
        
        # Call the decorated function
        exit_code = successful_function()
        
        # Verify success
        self.assertEqual(exit_code, 0)
    
    def test_handle_cli_error_decorator_string_error(self):
        """Test handle_cli_error decorator with string error code."""
        # Define a test function
        @handle_cli_error
        def error_function():
            return "CLI-TEST-ERROR-001"  # Return error code
        
        # Call the decorated function
        exit_code = error_function()
        
        # Verify error
        self.assertEqual(exit_code, 1)
        output = self.stdout_capture.getvalue().strip()
        self.assertTrue("Error [CLI-TEST-ERROR-001]: Command failed" in output)
    
    def test_handle_cli_error_decorator_cli_error(self):
        """Test handle_cli_error decorator with CLIError exception."""
        # Define a test function
        @handle_cli_error
        def cli_error_function():
            error_code = ErrorCode("CLI", "DECORATOR", "TEST", "002")
            raise CLIError("Decorator test error", error_code)
        
        # Call the decorated function
        exit_code = cli_error_function()
        
        # Verify error
        self.assertEqual(exit_code, 1)
        output = self.stdout_capture.getvalue().strip()
        self.assertTrue("Error [CLI-DECORATOR-TEST-002]: Decorator test error" in output)
    
    def test_handle_cli_error_decorator_standard_exception(self):
        """Test handle_cli_error decorator with standard exception."""
        # Define a test function
        @handle_cli_error
        def exception_function():
            raise ValueError("Standard exception test")
        
        # Call the decorated function
        exit_code = exception_function()
        
        # Verify error
        self.assertEqual(exit_code, 1)
        output = self.stdout_capture.getvalue().strip()
        self.assertTrue("Standard exception test" in output)


if __name__ == "__main__":
    unittest.main() 