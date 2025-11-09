#!/usr/bin/env python3
"""
Unit tests for the Repository interfaces in the Core module.
"""
import unittest
from unittest.mock import MagicMock

from refactor.core.repositories.repository_interface import (
    IRepository,
    ITaskRepository,
    RepositoryError,
    EntityNotFoundError,
    EntityAlreadyExistsError,
    ValidationError
)


class RepositoryInterfaceTests(unittest.TestCase):
    """Test cases for Repository interfaces."""

    def test_repository_error_inheritance(self):
        """Test repository error inheritance."""
        self.assertTrue(issubclass(RepositoryError, Exception))
        self.assertTrue(issubclass(EntityNotFoundError, RepositoryError))
        self.assertTrue(issubclass(EntityAlreadyExistsError, RepositoryError))
        self.assertTrue(issubclass(ValidationError, RepositoryError))
        
    def test_repository_abstract_methods(self):
        """Test that repository interfaces define required abstract methods."""
        # Get all abstract methods from IRepository
        abstract_methods = [
            method_name for method_name in dir(IRepository) 
            if method_name.startswith('_') is False and 
            callable(getattr(IRepository, method_name))
        ]
        
        # Check for essential methods
        essential_methods = ['add', 'update', 'get', 'get_by_name', 'exists', 
                           'delete', 'list_all', 'count', 'find']
                           
        for method in essential_methods:
            self.assertIn(method, abstract_methods, 
                        f"Essential method {method} not found in IRepository")
            
    def test_task_repository_specific_methods(self):
        """Test ITaskRepository has task-specific methods."""
        # Check for task-specific methods
        task_methods = ['get_by_status', 'get_by_priority', 'get_by_tag', 
                      'get_subtasks', 'get_related_tasks', 'search']
                      
        for method in task_methods:
            self.assertTrue(hasattr(ITaskRepository, method), 
                         f"Task-specific method {method} not found in ITaskRepository")


if __name__ == "__main__":
    unittest.main() 