#!/usr/bin/env python3
"""
Unit tests for the Error Context System.

This module tests the error context system components, including ErrorContext, 
ErrorCode, ErrorCodeRegistry, and related utilities.
"""
import unittest
import sys
import os
import json
from datetime import datetime
from unittest.mock import patch, MagicMock

# Add the project root to the Python path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../../../../')))

from refactor.core.exceptions import (
    ClickUpError,
    ValidationError,
    ErrorSeverity,
    ErrorCode,
    ErrorContext,
    ErrorContextBuilder,
    ErrorCodeRegistry,
    error_code_registry,
    with_error_context
)


class TestErrorCode(unittest.TestCase):
    """Test cases for the ErrorCode class."""
    
    def test_error_code_creation(self):
        """Test creating an ErrorCode instance."""
        error_code = ErrorCode("CORE", "REPO", "TASK", "001")
        self.assertEqual(error_code.component, "CORE")
        self.assertEqual(error_code.category, "REPO")
        self.assertEqual(error_code.subcategory, "TASK")
        self.assertEqual(error_code.code, "001")
    
    def test_error_code_string_representation(self):
        """Test the string representation of an ErrorCode."""
        error_code = ErrorCode("CORE", "REPO", "TASK", "001")
        self.assertEqual(str(error_code), "CORE-REPO-TASK-001")
    
    def test_error_code_from_string(self):
        """Test creating an ErrorCode from a string."""
        error_code = ErrorCode.from_string("CORE-REPO-TASK-001")
        self.assertEqual(error_code.component, "CORE")
        self.assertEqual(error_code.category, "REPO")
        self.assertEqual(error_code.subcategory, "TASK")
        self.assertEqual(error_code.code, "001")
    
    def test_error_code_from_string_invalid_format(self):
        """Test creating an ErrorCode from an invalid string format."""
        with self.assertRaises(ValueError) as context:
            ErrorCode.from_string("CORE-REPO-001")
        self.assertIn("Invalid error code format", str(context.exception))


class TestErrorContext(unittest.TestCase):
    """Test cases for the ErrorContext class."""
    
    def test_error_context_creation(self):
        """Test creating an ErrorContext instance."""
        context = ErrorContext("Test error message")
        self.assertEqual(context.message, "Test error message")
        self.assertEqual(context.severity, ErrorSeverity.ERROR)
        self.assertIsNone(context.error_code)
        self.assertIsNone(context.exception)
        self.assertEqual(context._context_data, {})
    
    def test_error_context_with_error_code_string(self):
        """Test creating an ErrorContext with an error code string."""
        context = ErrorContext("Test error message", error_code="CORE-REPO-TASK-001")
        self.assertEqual(str(context.error_code), "CORE-REPO-TASK-001")
    
    def test_error_context_with_invalid_error_code_string(self):
        """Test creating an ErrorContext with an invalid error code string."""
        context = ErrorContext("Test error message", error_code="INVALID")
        # Should create a generic error code
        self.assertEqual(str(context.error_code), "CORE-GENERAL-UNKNOWN-000")
    
    def test_error_context_with_exception(self):
        """Test creating an ErrorContext with an exception."""
        exception = ValueError("Test exception")
        context = ErrorContext("Test error message", exception=exception)
        self.assertEqual(context.exception, exception)
        self.assertIsNotNone(context.stack_trace)
        self.assertIn("ValueError: Test exception", context.stack_trace)
    
    def test_error_context_add_context_data(self):
        """Test adding context data to an ErrorContext."""
        context = ErrorContext("Test error message")
        context.add_context_data("key1", "value1")
        context.add_context_data("key2", 123)
        
        self.assertEqual(context.get_context_data("key1"), "value1")
        self.assertEqual(context.get_context_data("key2"), 123)
        self.assertIsNone(context.get_context_data("nonexistent"))
        self.assertEqual(context.get_context_data("nonexistent", "default"), "default")
    
    def test_error_context_merge_context_data(self):
        """Test merging context data into an ErrorContext."""
        context = ErrorContext("Test error message")
        context.add_context_data("key1", "value1")
        
        context.merge_context_data({"key2": 123, "key3": True})
        
        self.assertEqual(context.get_context_data("key1"), "value1")
        self.assertEqual(context.get_context_data("key2"), 123)
        self.assertEqual(context.get_context_data("key3"), True)
    
    def test_error_context_with_parent(self):
        """Test setting a parent ErrorContext."""
        parent = ErrorContext("Parent error")
        child = ErrorContext("Child error")
        
        child.with_parent(parent)
        
        self.assertEqual(child.parent_context, parent)
    
    def test_error_context_add_cause(self):
        """Test adding cause ErrorContexts."""
        result = ErrorContext("Result error")
        cause1 = ErrorContext("Cause 1")
        cause2 = ErrorContext("Cause 2")
        
        result.add_cause(cause1).add_cause(cause2)
        
        self.assertEqual(len(result.cause_contexts), 2)
        self.assertEqual(result.cause_contexts[0], cause1)
        self.assertEqual(result.cause_contexts[1], cause2)
    
    def test_error_context_to_dict(self):
        """Test converting an ErrorContext to a dictionary."""
        context = ErrorContext(
            message="Test error",
            error_code=ErrorCode("CORE", "REPO", "TASK", "001"),
            severity=ErrorSeverity.ERROR,
            context_data={"key1": "value1", "key2": 123}
        )
        
        context_dict = context.to_dict(include_stack_trace=False)
        
        self.assertEqual(context_dict["message"], "Test error")
        self.assertEqual(context_dict["error_code"], "CORE-REPO-TASK-001")
        self.assertEqual(context_dict["severity"], "ERROR")
        self.assertEqual(context_dict["context_data"], {"key1": "value1", "key2": 123})
        self.assertNotIn("stack_trace", context_dict)
    
    def test_error_context_to_json(self):
        """Test converting an ErrorContext to a JSON string."""
        context = ErrorContext(
            message="Test error",
            error_code=ErrorCode("CORE", "REPO", "TASK", "001"),
            severity=ErrorSeverity.ERROR,
            context_data={"key1": "value1", "key2": 123}
        )
        
        context_json = context.to_json(include_stack_trace=False)
        context_dict = json.loads(context_json)
        
        self.assertEqual(context_dict["message"], "Test error")
        self.assertEqual(context_dict["error_code"], "CORE-REPO-TASK-001")
        self.assertEqual(context_dict["severity"], "ERROR")
        self.assertEqual(context_dict["context_data"], {"key1": "value1", "key2": 123})
    
    def test_error_context_format_message(self):
        """Test formatting the error message."""
        context = ErrorContext(
            message="Test error",
            error_code=ErrorCode("CORE", "REPO", "TASK", "001"),
            severity=ErrorSeverity.ERROR
        )
        
        formatted_message = context.format_message()
        self.assertEqual(formatted_message, "ERROR: [CORE-REPO-TASK-001] Test error")
        
        # Without error code
        formatted_message = context.format_message(include_error_code=False)
        self.assertEqual(formatted_message, "ERROR: Test error")
        
        # With different severity
        context = ErrorContext(
            message="Test error",
            error_code=ErrorCode("CORE", "REPO", "TASK", "001"),
            severity=ErrorSeverity.WARNING
        )
        
        formatted_message = context.format_message()
        self.assertEqual(formatted_message, "[CORE-REPO-TASK-001] Test error")
    
    def test_error_context_str(self):
        """Test the string representation of an ErrorContext."""
        context = ErrorContext(
            message="Test error",
            error_code=ErrorCode("CORE", "REPO", "TASK", "001"),
            severity=ErrorSeverity.ERROR
        )
        
        self.assertEqual(str(context), "ERROR: [CORE-REPO-TASK-001] Test error")


class TestErrorContextBuilder(unittest.TestCase):
    """Test cases for the ErrorContextBuilder class."""
    
    def test_builder_basic_construction(self):
        """Test building a basic ErrorContext."""
        context = ErrorContextBuilder("Test error").build()
        
        self.assertEqual(context.message, "Test error")
        self.assertEqual(context.severity, ErrorSeverity.ERROR)
        self.assertIsNone(context.error_code)
        self.assertIsNone(context.exception)
        self.assertEqual(context._context_data, {})
    
    def test_builder_with_all_options(self):
        """Test building an ErrorContext with all options."""
        exception = ValueError("Test exception")
        error_code = ErrorCode("CORE", "REPO", "TASK", "001")
        
        context = ErrorContextBuilder("Test error") \
            .with_code(error_code) \
            .with_severity(ErrorSeverity.CRITICAL) \
            .with_exception(exception) \
            .with_data("key1", "value1") \
            .with_data_dict({"key2": 123, "key3": True}) \
            .build()
        
        self.assertEqual(context.message, "Test error")
        self.assertEqual(context.error_code, error_code)
        self.assertEqual(context.severity, ErrorSeverity.CRITICAL)
        self.assertEqual(context.exception, exception)
        self.assertEqual(context.get_context_data("key1"), "value1")
        self.assertEqual(context.get_context_data("key2"), 123)
        self.assertEqual(context.get_context_data("key3"), True)
    
    def test_builder_with_parent_and_causes(self):
        """Test building an ErrorContext with parent and causes."""
        parent = ErrorContext("Parent error")
        cause1 = ErrorContext("Cause 1")
        cause2 = ErrorContext("Cause 2")
        
        context = ErrorContextBuilder("Test error") \
            .with_parent(parent) \
            .with_cause(cause1) \
            .with_cause(cause2) \
            .build()
        
        self.assertEqual(context.parent_context, parent)
        self.assertEqual(len(context.cause_contexts), 2)
        self.assertEqual(context.cause_contexts[0], cause1)
        self.assertEqual(context.cause_contexts[1], cause2)


class TestErrorCodeRegistry(unittest.TestCase):
    """Test cases for the ErrorCodeRegistry class."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.registry = ErrorCodeRegistry()
    
    def test_register_error_code(self):
        """Test registering an error code."""
        self.registry.register("CORE-REPO-TASK-001", "Task not found")
        self.assertTrue(self.registry.is_registered("CORE-REPO-TASK-001"))
        self.assertEqual(self.registry.get_description("CORE-REPO-TASK-001"), "Task not found")
    
    def test_register_error_code_object(self):
        """Test registering an ErrorCode object."""
        error_code = ErrorCode("CORE", "REPO", "TASK", "002")
        self.registry.register(error_code, "Task already exists")
        
        self.assertTrue(self.registry.is_registered(error_code))
        self.assertTrue(self.registry.is_registered("CORE-REPO-TASK-002"))
        self.assertEqual(self.registry.get_description(error_code), "Task already exists")
        self.assertEqual(self.registry.get_description("CORE-REPO-TASK-002"), "Task already exists")
    
    def test_register_duplicate_error_code(self):
        """Test registering a duplicate error code."""
        self.registry.register("CORE-REPO-TASK-001", "Task not found")
        
        with self.assertRaises(ValueError) as context:
            self.registry.register("CORE-REPO-TASK-001", "Another description")
        
        self.assertIn("already registered", str(context.exception))
    
    def test_get_description_nonexistent(self):
        """Test getting the description of a non-existent error code."""
        self.assertIsNone(self.registry.get_description("NONEXISTENT"))
    
    def test_list_codes(self):
        """Test listing registered error codes."""
        self.registry.register("CORE-REPO-TASK-001", "Task not found")
        self.registry.register("CORE-REPO-TASK-002", "Task already exists")
        self.registry.register("CORE-SERVICE-TASK-001", "Invalid task data")
        self.registry.register("CLI-COMMAND-TASK-001", "Invalid task command")
        
        # List all codes
        all_codes = self.registry.list_codes()
        self.assertEqual(len(all_codes), 4)
        
        # Filter by component
        core_codes = self.registry.list_codes(component="CORE")
        self.assertEqual(len(core_codes), 3)
        self.assertIn(("CORE-REPO-TASK-001", "Task not found"), core_codes)
        self.assertIn(("CORE-REPO-TASK-002", "Task already exists"), core_codes)
        self.assertIn(("CORE-SERVICE-TASK-001", "Invalid task data"), core_codes)
        
        # Filter by category
        repo_codes = self.registry.list_codes(category="REPO")
        self.assertEqual(len(repo_codes), 2)
        self.assertIn(("CORE-REPO-TASK-001", "Task not found"), repo_codes)
        self.assertIn(("CORE-REPO-TASK-002", "Task already exists"), repo_codes)
        
        # Filter by subcategory
        task_codes = self.registry.list_codes(subcategory="TASK")
        self.assertEqual(len(task_codes), 4)
        
        # Combined filters
        core_repo_codes = self.registry.list_codes(component="CORE", category="REPO")
        self.assertEqual(len(core_repo_codes), 2)
        self.assertIn(("CORE-REPO-TASK-001", "Task not found"), core_repo_codes)
        self.assertIn(("CORE-REPO-TASK-002", "Task already exists"), core_repo_codes)


class TestWithErrorContextDecorator(unittest.TestCase):
    """Test cases for the with_error_context decorator."""
    
    def test_successful_function_execution(self):
        """Test that the decorator doesn't interfere with successful execution."""
        @with_error_context
        def successful_function(x, y):
            return x + y
        
        result = successful_function(2, 3)
        self.assertEqual(result, 5)
    
    def test_exception_handling(self):
        """Test that the decorator adds error context to exceptions."""
        @with_error_context
        def failing_function():
            raise ValueError("Test error")
        
        try:
            failing_function()
            self.fail("Expected ValueError")
        except ValueError as e:
            self.assertTrue(hasattr(e, 'error_context'))
            self.assertEqual(e.error_context.message, "Error in failing_function: Test error")
            self.assertEqual(e.error_context.severity, ErrorSeverity.ERROR)
            self.assertEqual(e.error_context.exception, e)
    
    def test_exception_with_existing_context(self):
        """Test that the decorator doesn't override existing error context."""
        @with_error_context
        def wrapper_function():
            exception = ValueError("Test error")
            context = ErrorContext("Custom error message", severity=ErrorSeverity.CRITICAL)
            exception.error_context = context
            raise exception
        
        try:
            wrapper_function()
            self.fail("Expected ValueError")
        except ValueError as e:
            self.assertTrue(hasattr(e, 'error_context'))
            self.assertEqual(e.error_context.message, "Custom error message")
            self.assertEqual(e.error_context.severity, ErrorSeverity.CRITICAL)


if __name__ == "__main__":
    unittest.main() 