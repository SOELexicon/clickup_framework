"""
Tests for saved search command registration.

This test verifies that the saved search command is properly registered
in the main.py file.
"""

import ast
import os
import sys
import pytest


class TestSavedSearchRegistration:
    """Tests for saved search command registration."""
    
    def test_saved_search_command_imported_and_registered(self):
        """
        Test that the SavedSearchCommand is imported and registered in main.py.
        
        This test parses the AST of main.py to verify:
        1. The SavedSearchCommand is imported
        2. There's a call to register the SavedSearchCommand
        """
        # Get the path to main.py in the refactor directory
        main_path = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), 'main.py')
        
        # Ensure the file exists
        assert os.path.exists(main_path), f"main.py not found at {main_path}"
        
        # Read the file
        with open(main_path, 'r') as f:
            main_content = f.read()
        
        # Parse the AST
        tree = ast.parse(main_content)
        
        # Check for SavedSearchCommand import
        saved_search_import_found = False
        for node in ast.walk(tree):
            if isinstance(node, ast.ImportFrom) and node.module and 'saved_search' in node.module:
                for name in node.names:
                    if name.name == 'SavedSearchCommand':
                        saved_search_import_found = True
                        break
        
        assert saved_search_import_found, "SavedSearchCommand is not imported in main.py"
        
        # Check for register_command call with SavedSearchCommand
        saved_search_registration_found = False
        for node in ast.walk(tree):
            if isinstance(node, ast.Call) and hasattr(node, 'func') and isinstance(node.func, ast.Attribute):
                if node.func.attr == 'register_command':
                    for arg in node.args:
                        if isinstance(arg, ast.Call) and hasattr(arg, 'func') and isinstance(arg.func, ast.Name):
                            if arg.func.id == 'SavedSearchCommand':
                                saved_search_registration_found = True
                                break
        
        assert saved_search_registration_found, "SavedSearchCommand is not registered in main.py" 