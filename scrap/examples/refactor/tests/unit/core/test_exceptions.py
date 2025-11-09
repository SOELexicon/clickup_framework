#!/usr/bin/env python3
"""
Unit tests for the Core exceptions module.

This module tests the exception hierarchy, especially the new repository 
and service exceptions to ensure proper inheritance and behavior.
"""
import unittest
import sys
import os

# Add the project root to the Python path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../../../../')))

from refactor.core.exceptions import (
    ClickUpError,
    ValidationError,
    EntityError,
    EntityNotFoundError,
    EntityAlreadyExistsError,
    TaskCompletionError,
    CircularDependencyError,
    ConfigurationError,
    StorageError,
    FileOperationError,
    SerializationError,
    RepositoryError,
    RepositoryConnectionError,
    RepositoryDataError,
    RepositoryOperationError,
    ServiceError,
    BusinessRuleViolationError,
    ServiceOperationError,
    ServiceDependencyError,
    CommandError,
    PermissionError,
    DependencyError,
    QueryError,
    PluginError
)


class TestExceptionHierarchy(unittest.TestCase):
    """Test cases for the exception hierarchy."""
    
    def test_base_exception_inheritance(self):
        """Test that all base exceptions inherit from ClickUpError."""
        self.assertTrue(issubclass(ClickUpError, Exception))
        self.assertTrue(issubclass(ValidationError, ClickUpError))
        self.assertTrue(issubclass(EntityError, ClickUpError))
        self.assertTrue(issubclass(StorageError, ClickUpError))
        self.assertTrue(issubclass(RepositoryError, ClickUpError))
        self.assertTrue(issubclass(ServiceError, ClickUpError))
        self.assertTrue(issubclass(CommandError, ClickUpError))
        self.assertTrue(issubclass(PermissionError, ClickUpError))
        self.assertTrue(issubclass(DependencyError, ClickUpError))
        self.assertTrue(issubclass(QueryError, ClickUpError))
        self.assertTrue(issubclass(PluginError, ClickUpError))
    
    def test_entity_exception_inheritance(self):
        """Test that entity-specific exceptions inherit from EntityError."""
        self.assertTrue(issubclass(EntityNotFoundError, EntityError))
        self.assertTrue(issubclass(EntityAlreadyExistsError, EntityError))
    
    def test_storage_exception_inheritance(self):
        """Test that storage-specific exceptions inherit from StorageError."""
        self.assertTrue(issubclass(FileOperationError, StorageError))
        self.assertTrue(issubclass(SerializationError, StorageError))
    
    def test_repository_exception_inheritance(self):
        """Test that repository-specific exceptions inherit from RepositoryError."""
        self.assertTrue(issubclass(RepositoryConnectionError, RepositoryError))
        self.assertTrue(issubclass(RepositoryDataError, RepositoryError))
        self.assertTrue(issubclass(RepositoryOperationError, RepositoryError))
    
    def test_service_exception_inheritance(self):
        """Test that service-specific exceptions inherit from ServiceError."""
        self.assertTrue(issubclass(BusinessRuleViolationError, ServiceError))
        self.assertTrue(issubclass(ServiceOperationError, ServiceError))
        self.assertTrue(issubclass(ServiceDependencyError, ServiceError))


class TestExceptionInstantiation(unittest.TestCase):
    """Test cases for exception instantiation and message formatting."""
    
    def test_clickup_error_instantiation(self):
        """Test instantiation of ClickUpError."""
        error = ClickUpError("Test error")
        self.assertEqual(str(error), "Test error")
        
        # Test default message
        error = ClickUpError()
        self.assertEqual(str(error), "An error occurred")
    
    def test_validation_error_instantiation(self):
        """Test instantiation of ValidationError."""
        error = ValidationError("Invalid input")
        self.assertEqual(str(error), "Invalid input")
        
        # Test default message
        error = ValidationError()
        self.assertEqual(str(error), "Validation failed")
    
    def test_entity_error_instantiation(self):
        """Test instantiation of EntityError."""
        error = EntityError("Task", "Invalid task")
        self.assertEqual(str(error), "Task error: Invalid task")
        self.assertEqual(error.entity_type, "Task")
    
    def test_entity_not_found_error_instantiation(self):
        """Test instantiation of EntityNotFoundError."""
        error = EntityNotFoundError("tsk_12345", "Task")
        self.assertEqual(str(error), "Task error: Not found with ID: tsk_12345")
        self.assertEqual(error.entity_id, "tsk_12345")
        self.assertEqual(error.entity_type, "Task")
        
        # Test with default entity type
        error = EntityNotFoundError("tsk_12345")
        self.assertEqual(str(error), "Entity error: Not found with ID: tsk_12345")
    
    def test_entity_already_exists_error_instantiation(self):
        """Test instantiation of EntityAlreadyExistsError."""
        error = EntityAlreadyExistsError("tsk_12345", "Task")
        self.assertEqual(str(error), "Task error: Already exists with ID: tsk_12345")
        self.assertEqual(error.entity_id, "tsk_12345")
        self.assertEqual(error.entity_type, "Task")
    
    def test_repository_error_instantiation(self):
        """Test instantiation of RepositoryError."""
        error = RepositoryError("TaskRepository", "Failed to connect")
        self.assertEqual(str(error), "TaskRepository error: Failed to connect")
        self.assertEqual(error.repository_name, "TaskRepository")
        
        # Test default values
        error = RepositoryError()
        self.assertEqual(str(error), "Repository error: Repository operation failed")
    
    def test_repository_connection_error_instantiation(self):
        """Test instantiation of RepositoryConnectionError."""
        error = RepositoryConnectionError("TaskRepository", "Database unreachable")
        self.assertEqual(str(error), "TaskRepository error: Database unreachable")
        self.assertEqual(error.repository_name, "TaskRepository")
        
        # Test default values
        error = RepositoryConnectionError()
        self.assertEqual(str(error), "Repository error: Could not connect to data source")
    
    def test_repository_data_error_instantiation(self):
        """Test instantiation of RepositoryDataError."""
        error = RepositoryDataError("TaskRepository", "Corrupted data")
        self.assertEqual(str(error), "TaskRepository error: Corrupted data")
        self.assertEqual(error.repository_name, "TaskRepository")
    
    def test_repository_operation_error_instantiation(self):
        """Test instantiation of RepositoryOperationError."""
        error = RepositoryOperationError("TaskRepository", "update", "Invalid input")
        self.assertEqual(str(error), "TaskRepository error: Operation 'update' failed: Invalid input")
        self.assertEqual(error.repository_name, "TaskRepository")
        self.assertEqual(error.operation, "update")
    
    def test_service_error_instantiation(self):
        """Test instantiation of ServiceError."""
        error = ServiceError("TaskService", "Service unavailable")
        self.assertEqual(str(error), "TaskService error: Service unavailable")
        self.assertEqual(error.service_name, "TaskService")
        
        # Test default values
        error = ServiceError()
        self.assertEqual(str(error), "Service error: Service operation failed")
    
    def test_business_rule_violation_error_instantiation(self):
        """Test instantiation of BusinessRuleViolationError."""
        error = BusinessRuleViolationError("TaskService", "task_completion", "Cannot complete task with open subtasks")
        self.assertEqual(str(error), "TaskService error: Business rule 'task_completion' violated: Cannot complete task with open subtasks")
        self.assertEqual(error.service_name, "TaskService")
        self.assertEqual(error.rule, "task_completion")
    
    def test_service_operation_error_instantiation(self):
        """Test instantiation of ServiceOperationError."""
        error = ServiceOperationError("TaskService", "create_task", "Failed to create task")
        self.assertEqual(str(error), "TaskService error: Operation 'create_task' failed: Failed to create task")
        self.assertEqual(error.service_name, "TaskService")
        self.assertEqual(error.operation, "create_task")
    
    def test_service_dependency_error_instantiation(self):
        """Test instantiation of ServiceDependencyError."""
        error = ServiceDependencyError("TaskService", "TaskRepository", "Repository unavailable")
        self.assertEqual(str(error), "TaskService error: Dependency 'TaskRepository' issue: Repository unavailable")
        self.assertEqual(error.service_name, "TaskService")
        self.assertEqual(error.dependency, "TaskRepository")


class TestExceptionHandling(unittest.TestCase):
    """Test cases for exception handling patterns."""
    
    def test_catch_by_base_exception(self):
        """Test that catching the base exception catches all derived exceptions."""
        # Create a list of exceptions to test
        exceptions = [
            ValidationError("Validation failed"),
            EntityNotFoundError("tsk_12345", "Task"),
            EntityAlreadyExistsError("tsk_12345", "Task"),
            StorageError("Storage failed"),
            FileOperationError("test.json", "read", "File not found"),
            RepositoryError("TaskRepository", "Operation failed"),
            RepositoryConnectionError("TaskRepository", "Connection failed"),
            ServiceError("TaskService", "Service failed"),
            BusinessRuleViolationError("TaskService", "task_completion", "Rule violation"),
            CommandError("create_task", "Command failed")
        ]
        
        # Try to catch each exception with ClickUpError
        for exception in exceptions:
            try:
                raise exception
            except ClickUpError as e:
                # Should catch all exceptions
                self.assertEqual(str(e), str(exception))
            except Exception:
                # Should not reach here
                self.fail(f"Failed to catch {type(exception).__name__} with ClickUpError")
    
    def test_catch_by_specific_exception(self):
        """Test catching by specific exception types."""
        # Test repository exceptions
        repo_exceptions = [
            RepositoryConnectionError("TaskRepository", "Connection failed"),
            RepositoryDataError("TaskRepository", "Data corrupted"),
            RepositoryOperationError("TaskRepository", "update", "Operation failed")
        ]
        
        for exception in repo_exceptions:
            try:
                raise exception
            except RepositoryError as e:
                # Should catch all repository exceptions
                self.assertEqual(str(e), str(exception))
            except Exception:
                # Should not reach here
                self.fail(f"Failed to catch {type(exception).__name__} with RepositoryError")
        
        # Test service exceptions
        service_exceptions = [
            BusinessRuleViolationError("TaskService", "task_completion", "Rule violation"),
            ServiceOperationError("TaskService", "create_task", "Operation failed"),
            ServiceDependencyError("TaskService", "TaskRepository", "Dependency failed")
        ]
        
        for exception in service_exceptions:
            try:
                raise exception
            except ServiceError as e:
                # Should catch all service exceptions
                self.assertEqual(str(e), str(exception))
            except Exception:
                # Should not reach here
                self.fail(f"Failed to catch {type(exception).__name__} with ServiceError")
    
    def test_exception_attributes(self):
        """Test that exception attributes are properly set and accessible."""
        # Test repository exception attributes
        repo_exception = RepositoryOperationError("TaskRepository", "update", "Operation failed")
        self.assertEqual(repo_exception.repository_name, "TaskRepository")
        self.assertEqual(repo_exception.operation, "update")
        
        # Test service exception attributes
        service_exception = BusinessRuleViolationError("TaskService", "task_completion", "Rule violation")
        self.assertEqual(service_exception.service_name, "TaskService")
        self.assertEqual(service_exception.rule, "task_completion")
        
        # Test entity exception attributes
        entity_exception = EntityNotFoundError("tsk_12345", "Task")
        self.assertEqual(entity_exception.entity_id, "tsk_12345")
        self.assertEqual(entity_exception.entity_type, "Task")


if __name__ == "__main__":
    unittest.main() 