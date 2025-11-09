#!/usr/bin/env python3
"""
Unit tests for the Error Codes module.

This module tests the error code registry and utility functions for
managing error codes in the ClickUp JSON Manager.
"""
import unittest
import sys
import os

# Add the project root to the Python path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../../../../')))

from refactor.core.exceptions import (
    ErrorCode,
    ErrorCodeRegistry,
    error_code_registry,
    get_repo_error_code,
    get_service_error_code,
    get_storage_error_code,
    get_command_error_code,
    get_validation_error_code
)


class TestErrorCodeUtilities(unittest.TestCase):
    """Test cases for the error code utility functions."""
    
    def test_get_repo_error_code(self):
        """Test the get_repo_error_code utility function."""
        error_code = get_repo_error_code("TASK", "001")
        self.assertEqual(error_code.component, "CORE")
        self.assertEqual(error_code.category, "REPO")
        self.assertEqual(error_code.subcategory, "TASK")
        self.assertEqual(error_code.code, "001")
        self.assertEqual(str(error_code), "CORE-REPO-TASK-001")
    
    def test_get_service_error_code(self):
        """Test the get_service_error_code utility function."""
        error_code = get_service_error_code("SPACE", "002")
        self.assertEqual(error_code.component, "CORE")
        self.assertEqual(error_code.category, "SERVICE")
        self.assertEqual(error_code.subcategory, "SPACE")
        self.assertEqual(error_code.code, "002")
        self.assertEqual(str(error_code), "CORE-SERVICE-SPACE-002")
    
    def test_get_storage_error_code(self):
        """Test the get_storage_error_code utility function."""
        error_code = get_storage_error_code("JSON", "003")
        self.assertEqual(error_code.component, "STORAGE")
        self.assertEqual(error_code.category, "FILE")
        self.assertEqual(error_code.subcategory, "JSON")
        self.assertEqual(error_code.code, "003")
        self.assertEqual(str(error_code), "STORAGE-FILE-JSON-003")
    
    def test_get_command_error_code(self):
        """Test the get_command_error_code utility function."""
        error_code = get_command_error_code("ARGS", "001")
        self.assertEqual(error_code.component, "CLI")
        self.assertEqual(error_code.category, "COMMAND")
        self.assertEqual(error_code.subcategory, "ARGS")
        self.assertEqual(error_code.code, "001")
        self.assertEqual(str(error_code), "CLI-COMMAND-ARGS-001")
    
    def test_get_validation_error_code(self):
        """Test the get_validation_error_code utility function."""
        error_code = get_validation_error_code("002")
        self.assertEqual(error_code.component, "CORE")
        self.assertEqual(error_code.category, "VALID")
        self.assertEqual(error_code.subcategory, "ENTITY")
        self.assertEqual(error_code.code, "002")
        self.assertEqual(str(error_code), "CORE-VALID-ENTITY-002")


class TestErrorCodeRegistryUsage(unittest.TestCase):
    """Test cases for the global error code registry."""
    
    def test_predefined_error_codes(self):
        """Test that predefined error codes are registered."""
        # Test a few common error codes
        self.assertTrue(error_code_registry.is_registered("CORE-REPO-TASK-001"))
        self.assertTrue(error_code_registry.is_registered("CORE-SERVICE-TASK-001"))
        self.assertTrue(error_code_registry.is_registered("STORAGE-FILE-JSON-001"))
        self.assertTrue(error_code_registry.is_registered("CLI-COMMAND-ARGS-001"))
        self.assertTrue(error_code_registry.is_registered("CORE-VALID-ENTITY-001"))
        
        # Verify descriptions
        self.assertEqual(
            error_code_registry.get_description("CORE-REPO-TASK-001"),
            "Task not found with the specified ID"
        )
        self.assertEqual(
            error_code_registry.get_description("STORAGE-FILE-JSON-001"),
            "Failed to read JSON file"
        )
    
    def test_error_code_filtering(self):
        """Test filtering error codes by component, category, and subcategory."""
        # Get all repo error codes for tasks
        task_repo_codes = error_code_registry.list_codes(
            component="CORE", category="REPO", subcategory="TASK"
        )
        # Should have at least 4 codes (001-004)
        self.assertGreaterEqual(len(task_repo_codes), 4)
        
        # Get all service error codes
        service_codes = error_code_registry.list_codes(category="SERVICE")
        self.assertGreaterEqual(len(service_codes), 7)  # At least 7 service error codes
        
        # Get all storage error codes for JSON operations
        json_codes = error_code_registry.list_codes(
            component="STORAGE", subcategory="JSON"
        )
        self.assertGreaterEqual(len(json_codes), 5)  # At least 5 JSON error codes
    
    def test_error_code_utility_with_registry(self):
        """Test that utility functions generate codes that match the registry."""
        # Generate a code with the utility function
        task_not_found = get_repo_error_code("TASK", "001")
        
        # Verify it's in the registry with the expected description
        self.assertTrue(error_code_registry.is_registered(str(task_not_found)))
        self.assertEqual(
            error_code_registry.get_description(task_not_found),
            "Task not found with the specified ID"
        )
        
        # Test another code
        service_validation_error = get_service_error_code("TASK", "001")
        self.assertTrue(error_code_registry.is_registered(str(service_validation_error)))
        self.assertEqual(
            error_code_registry.get_description(service_validation_error),
            "Task operation failed due to validation error"
        )
    
    def test_code_format_standardization(self):
        """Test that error codes follow the standardized format."""
        for code_pair in error_code_registry.list_codes():
            code_str = code_pair[0]
            # Verify format: COMP-CAT-SUB-CODE
            parts = code_str.split('-')
            self.assertEqual(len(parts), 4, f"Error code {code_str} is not in standard format")
            
            # Component should be uppercase
            self.assertEqual(parts[0], parts[0].upper())
            
            # Category should be uppercase
            self.assertEqual(parts[1], parts[1].upper())
            
            # Subcategory should be uppercase
            self.assertEqual(parts[2], parts[2].upper())
            
            # Code should be 3 digits for most codes
            # (except special cases like "000" for unknown)
            if parts[0] != "CORE" or parts[1] != "GENERAL" or parts[2] != "UNKNOWN":
                self.assertEqual(len(parts[3]), 3)
                self.assertTrue(parts[3].isdigit())


if __name__ == "__main__":
    unittest.main() 