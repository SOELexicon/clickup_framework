#!/usr/bin/env python3
"""
Run tests for the TaskService class.
"""
import os
import sys
import unittest

# Add the parent directory to the path so that imports work
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Import the TaskService test class
from refactor.tests.unit.test_task_service import TestTaskService

if __name__ == "__main__":
    # Create a test suite
    suite = unittest.TestLoader().loadTestsFromTestCase(TestTaskService)
    
    # Run the tests
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)
    
    # Exit with non-zero code if tests failed
    sys.exit(not result.wasSuccessful()) 