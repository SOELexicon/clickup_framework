#!/usr/bin/env python3
"""
Standalone test runner for entity tests.

This script runs unit tests for the entity classes without relying on the 
project's test infrastructure that may have import dependencies.
"""

import pytest
import sys
import os

# Add the parent directory to the sys.path so imports work correctly
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "../../../../../")))

if __name__ == "__main__":
    # Run all entity tests with verbose output
    test_files = [
        "test_base_entity.py",
        "test_task_entity.py"
    ]
    
    # Convert filenames to absolute paths
    current_dir = os.path.dirname(os.path.abspath(__file__))
    test_paths = [os.path.join(current_dir, file) for file in test_files]
    
    # Run the tests
    exit_code = pytest.main(["-v"] + test_paths)
    sys.exit(exit_code) 