#!/usr/bin/env python3
"""
Unit tests for the Common Exceptions module.

This module tests the exception hierarchy and error handling functionality
provided by the common.exceptions module.
"""
import unittest
import sys
import os
from typing import Dict, Any

# Add the project root to the Python path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../../../../../')))

from refactor.common.exceptions import (
    ClickUpManagerError,
    ValidationError,
    RequiredFieldError,
    InvalidValueError,
    InvalidQueryError,
    DataAccessError,
    EntityNotFoundError,
    TaskNotFoundError,
    ListNotFoundError,
    DuplicateEntityError,
    FileOperationError,
    FileReadError,
    FileWriteError,
    JsonParseError,
    RelationshipError,
    CircularDependencyError,
    InvalidRelationshipTypeError,
    ConfigurationError,
    MissingConfigurationError,
    InvalidConfigurationError
)


class TestBaseExceptions(unittest.TestCase):
    """Test cases for the base exception classes."""
    
    def test_clickup_manager_error_basic(self):
        """Test basic initialization of ClickUpManagerError."""
        error = ClickUpManagerError("Test error message")
        self.assertEqual(str(error), "Test error message")
        self.assertIsNone(error.error_code)
        self.assertEqual(error.context, {})
    
    def test_clickup_manager_error_with_code(self):
        """Test ClickUpManagerError with error code."""
        error = ClickUpManagerError("Test error message", error_code="TEST001")
        self.assertEqual(str(error), "Test error message")
        self.assertEqual(error.error_code, "TEST001")
        self.assertEqual(error.context, {})
    
    def test_clickup_manager_error_with_context(self):
        """Test ClickUpManagerError with context."""
        context = {"file": "test.json", "line": 42}
        error = ClickUpManagerError("Test error message", context=context)
        self.assertEqual(str(error), "Test error message")
        self.assertEqual(error.context, context)
    
    def test_clickup_manager_error_add_context(self):
        """Test adding context to ClickUpManagerError."""
        error = ClickUpManagerError("Test error message")
        error.add_context("file", "test.json")
        error.add_context("line", 42)
        
        self.assertEqual(error.context["file"], "test.json")
        self.assertEqual(error.context["line"], 42)
    
    def test_clickup_manager_error_add_context_chaining(self):
        """Test method chaining when adding context."""
        error = ClickUpManagerError("Test error message")
        result = error.add_context("file", "test.json").add_context("line", 42)
        
        self.assertEqual(result, error)  # Should return self
        self.assertEqual(error.context["file"], "test.json")
        self.assertEqual(error.context["line"], 42)


class TestValidationExceptions(unittest.TestCase):
    """Test cases for validation exception classes."""
    
    def test_validation_error(self):
        """Test ValidationError class."""
        error = ValidationError("Invalid data")
        self.assertEqual(str(error), "Invalid data")
        self.assertIsInstance(error, ClickUpManagerError)
    
    def test_required_field_error(self):
        """Test RequiredFieldError class."""
        error = RequiredFieldError("name")
        self.assertEqual(str(error), "Required field 'name' is missing")
        self.assertEqual(error.error_code, "ERR1001")
        self.assertEqual(error.field_name, "name")
        self.assertIsInstance(error, ValidationError)
    
    def test_required_field_error_with_context(self):
        """Test RequiredFieldError with context."""
        context = {"entity_type": "task", "entity_id": "tsk_123"}
        error = RequiredFieldError("name", context=context)
        self.assertEqual(str(error), "Required field 'name' is missing")
        self.assertEqual(error.context, context)
    
    def test_invalid_value_error(self):
        """Test InvalidValueError class."""
        error = InvalidValueError(
            "status", "pending", "Status must be one of: to do, in progress, complete"
        )
        self.assertEqual(
            str(error),
            "Invalid value for field 'status': Status must be one of: to do, in progress, complete"
        )
        self.assertEqual(error.error_code, "ERR1002")
        self.assertEqual(error.field_name, "status")
        self.assertEqual(error.value, "pending")
        self.assertEqual(error.reason, "Status must be one of: to do, in progress, complete")
        self.assertIsInstance(error, ValidationError)
    
    def test_invalid_query_error(self):
        """Test InvalidQueryError class."""
        error = InvalidQueryError("status = 'pending'", "Unknown status value: pending")
        self.assertEqual(str(error), "Invalid query: Unknown status value: pending")
        self.assertEqual(error.error_code, "ERR1003")
        self.assertEqual(error.query, "status = 'pending'")
        self.assertEqual(error.reason, "Unknown status value: pending")
        self.assertIsInstance(error, ValidationError)


class TestDataAccessExceptions(unittest.TestCase):
    """Test cases for data access exception classes."""
    
    def test_data_access_error(self):
        """Test DataAccessError class."""
        error = DataAccessError("Data access failed")
        self.assertEqual(str(error), "Data access failed")
        self.assertIsInstance(error, ClickUpManagerError)
    
    def test_entity_not_found_error(self):
        """Test EntityNotFoundError class."""
        error = EntityNotFoundError("task", "Task123")
        self.assertEqual(str(error), "Could not find task with identifier 'Task123'")
        self.assertEqual(error.error_code, "ERR2001")
        self.assertEqual(error.entity_type, "task")
        self.assertEqual(error.identifier, "Task123")
        self.assertIsInstance(error, DataAccessError)
    
    def test_task_not_found_error(self):
        """Test TaskNotFoundError class."""
        error = TaskNotFoundError("Task123")
        self.assertEqual(str(error), "Could not find task with identifier 'Task123'")
        self.assertEqual(error.entity_type, "task")
        self.assertEqual(error.identifier, "Task123")
        self.assertIsInstance(error, EntityNotFoundError)
    
    def test_list_not_found_error(self):
        """Test ListNotFoundError class."""
        error = ListNotFoundError("List123")
        self.assertEqual(str(error), "Could not find list with identifier 'List123'")
        self.assertEqual(error.entity_type, "list")
        self.assertEqual(error.identifier, "List123")
        self.assertIsInstance(error, EntityNotFoundError)
    
    def test_duplicate_entity_error(self):
        """Test DuplicateEntityError class."""
        error = DuplicateEntityError("task", "Task123")
        self.assertEqual(str(error), "task with identifier 'Task123' already exists")
        self.assertEqual(error.error_code, "ERR2002")
        self.assertEqual(error.entity_type, "task")
        self.assertEqual(error.identifier, "Task123")
        self.assertIsInstance(error, DataAccessError)


class TestFileOperationExceptions(unittest.TestCase):
    """Test cases for file operation exception classes."""
    
    def test_file_operation_error(self):
        """Test FileOperationError class."""
        error = FileOperationError("File operation failed")
        self.assertEqual(str(error), "File operation failed")
        self.assertIsInstance(error, ClickUpManagerError)
    
    def test_file_read_error(self):
        """Test FileReadError class."""
        error = FileReadError("/path/to/file.json", "Permission denied")
        self.assertEqual(str(error), "Could not read file '/path/to/file.json': Permission denied")
        self.assertEqual(error.error_code, "ERR3001")
        self.assertEqual(error.file_path, "/path/to/file.json")
        self.assertEqual(error.reason, "Permission denied")
        self.assertIsInstance(error, FileOperationError)
    
    def test_file_write_error(self):
        """Test FileWriteError class."""
        error = FileWriteError("/path/to/file.json", "Disk full")
        self.assertEqual(str(error), "Could not write to file '/path/to/file.json': Disk full")
        self.assertEqual(error.error_code, "ERR3002")
        self.assertEqual(error.file_path, "/path/to/file.json")
        self.assertEqual(error.reason, "Disk full")
        self.assertIsInstance(error, FileOperationError)
    
    def test_json_parse_error_basic(self):
        """Test JsonParseError class with basic information."""
        error = JsonParseError("/path/to/file.json", "Invalid JSON syntax")
        self.assertEqual(str(error), "Invalid JSON in file '/path/to/file.json': Invalid JSON syntax")
        self.assertEqual(error.error_code, "ERR3003")
        self.assertEqual(error.file_path, "/path/to/file.json")
        self.assertEqual(error.error_details, "Invalid JSON syntax")
        self.assertIsNone(error.line)
        self.assertIsNone(error.column)
        self.assertIsInstance(error, FileOperationError)
    
    def test_json_parse_error_with_location(self):
        """Test JsonParseError class with line and column information."""
        error = JsonParseError("/path/to/file.json", "Unexpected end of object", 42, 10)
        self.assertEqual(
            str(error),
            "Invalid JSON in file '/path/to/file.json' at line 42, column 10: Unexpected end of object"
        )
        self.assertEqual(error.line, 42)
        self.assertEqual(error.column, 10)


class TestRelationshipExceptions(unittest.TestCase):
    """Test cases for relationship exception classes."""
    
    def test_relationship_error(self):
        """Test RelationshipError class."""
        error = RelationshipError("Relationship operation failed")
        self.assertEqual(str(error), "Relationship operation failed")
        self.assertIsInstance(error, ClickUpManagerError)
    
    def test_circular_dependency_error(self):
        """Test CircularDependencyError class."""
        dependency_chain = ["Task1", "Task2", "Task3", "Task1"]
        error = CircularDependencyError("Task1", dependency_chain)
        
        self.assertIn("Circular dependency detected", str(error))
        self.assertIn("Task1 -> Task2 -> Task3 -> Task1", str(error))
        self.assertEqual(error.task_id, "Task1")
        self.assertEqual(error.dependency_chain, dependency_chain)
        self.assertIsInstance(error, RelationshipError)
    
    def test_invalid_relationship_type_error(self):
        """Test InvalidRelationshipTypeError class."""
        valid_types = ["depends_on", "blocks", "parent_of"]
        error = InvalidRelationshipTypeError("connects_to", valid_types)
        
        self.assertIn("Invalid relationship type: 'connects_to'", str(error))
        self.assertIn("depends_on, blocks, parent_of", str(error))
        self.assertEqual(error.relationship_type, "connects_to")
        self.assertEqual(error.valid_types, valid_types)
        self.assertIsInstance(error, RelationshipError)


class TestConfigurationExceptions(unittest.TestCase):
    """Test cases for configuration exception classes."""
    
    def test_configuration_error(self):
        """Test ConfigurationError class."""
        error = ConfigurationError("Configuration error occurred")
        self.assertEqual(str(error), "Configuration error occurred")
        self.assertIsInstance(error, ClickUpManagerError)
    
    def test_missing_configuration_error(self):
        """Test MissingConfigurationError class."""
        error = MissingConfigurationError("database.host")
        self.assertEqual(str(error), "Required configuration 'database.host' is missing")
        self.assertEqual(error.config_key, "database.host")
        self.assertIsInstance(error, ConfigurationError)
    
    def test_invalid_configuration_error(self):
        """Test InvalidConfigurationError class."""
        error = InvalidConfigurationError(
            "max_tasks", "unlimited", "Value must be a positive integer or -1"
        )
        self.assertEqual(
            str(error),
            "Invalid configuration value for 'max_tasks': Value must be a positive integer or -1"
        )
        self.assertEqual(error.config_key, "max_tasks")
        self.assertEqual(error.value, "unlimited")
        self.assertEqual(error.reason, "Value must be a positive integer or -1")
        self.assertIsInstance(error, ConfigurationError)


class TestExceptionContextInteraction(unittest.TestCase):
    """Test how exception context works with different exception types."""
    
    def test_exception_context_propagation(self):
        """Test that context is properly propagated through exception handling."""
        try:
            try:
                # Start with a base exception
                raise TaskNotFoundError("Task123", {"user_id": "user456"})
            except TaskNotFoundError as e:
                # Add more context and re-raise as a different type
                e.add_context("operation", "task_completion")
                new_error = FileOperationError("Could not update task status")
                new_error.add_context("original_error", str(e))
                for key, value in e.context.items():
                    new_error.add_context(key, value)
                raise new_error
        except FileOperationError as e:
            # Check that all context is present
            self.assertEqual(e.context["user_id"], "user456")
            self.assertEqual(e.context["operation"], "task_completion")
            self.assertIn("Could not find task", e.context["original_error"])


if __name__ == "__main__":
    unittest.main() 