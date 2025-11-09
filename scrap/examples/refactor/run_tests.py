#!/usr/bin/env python3
"""
Test runner script that adds the refactor directory to the Python path.
Includes features to track test result history and show improvements/regressions.
"""
import os
import sys
import json
import unittest
from pathlib import Path
from datetime import datetime
import re

# ANSI color codes
GREEN = '\033[92m'
RED = '\033[91m'
YELLOW = '\033[93m'
BLUE = '\033[94m'
BOLD = '\033[1m'
RESET = '\033[0m'

# Add the parent directory to the Python path
current_dir = Path(__file__).resolve().parent
parent_dir = current_dir.parent
sys.path.insert(0, str(parent_dir))

TEST_HISTORY_FILE = parent_dir / '.test_history.json'
MAX_HISTORY_ENTRIES = 10

class TestResultTracker:
    def __init__(self, history_file=TEST_HISTORY_FILE):
        self.history_file = history_file
        self.history = self._load_history()
        
    def _load_history(self):
        """Load test history from file."""
        if self.history_file.exists():
            try:
                with open(self.history_file, 'r') as f:
                    return json.load(f)
            except json.JSONDecodeError:
                print(f"{YELLOW}Warning: History file is corrupted. Creating new history.{RESET}")
                return []
        return []
    
    def save_history(self):
        """Save test history to file."""
        with open(self.history_file, 'w') as f:
            json.dump(self.history, f, indent=2)
            
    def add_result(self, result):
        """Add a test result to history."""
        new_entry = {
            "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "total": result.testsRun,
            "passed": result.testsRun - (len(result.failures) + len(result.errors) + len(result.skipped)),
            "failed": len(result.failures),
            "errors": len(result.errors),
            "skipped": len(result.skipped)
        }
        
        self.history.append(new_entry)
        
        # Keep only the last MAX_HISTORY_ENTRIES entries
        if len(self.history) > MAX_HISTORY_ENTRIES:
            self.history = self.history[-MAX_HISTORY_ENTRIES:]
            
        self.save_history()
        return new_entry
    
    def get_last_result(self):
        """Get the previous test result for comparison."""
        if len(self.history) > 1:
            return self.history[-2]
        return None
    
    def print_comparison(self, current_result):
        """Print a comparison between current and previous runs."""
        last_result = self.get_last_result()
        if not last_result:
            print(f"\n{BLUE}{BOLD}First run recorded in history.{RESET}")
            return
            
        print(f"\n{BLUE}{BOLD}Comparison with previous run:{RESET}")
        
        # Calculate changes
        passed_diff = current_result["passed"] - last_result["passed"]
        failed_diff = current_result["failed"] - last_result["failed"]
        error_diff = current_result["errors"] - last_result["errors"]
        
        # Print changes with appropriate colors
        if passed_diff > 0:
            print(f"  Passed: {current_result['passed']} ({GREEN}+{passed_diff}{RESET})")
        elif passed_diff < 0:
            print(f"  Passed: {current_result['passed']} ({RED}{passed_diff}{RESET})")
        else:
            print(f"  Passed: {current_result['passed']} (no change)")
            
        if failed_diff < 0:
            print(f"  Failed: {current_result['failed']} ({GREEN}{failed_diff}{RESET})")
        elif failed_diff > 0:
            print(f"  Failed: {current_result['failed']} ({RED}+{failed_diff}{RESET})")
        else:
            print(f"  Failed: {current_result['failed']} (no change)")
            
        if error_diff < 0:
            print(f"  Errors: {current_result['errors']} ({GREEN}{error_diff}{RESET})")
        elif error_diff > 0:
            print(f"  Errors: {current_result['errors']} ({RED}+{error_diff}{RESET})")
        else:
            print(f"  Errors: {current_result['errors']} (no change)")
    
    def print_history(self):
        """Print a table of historical test results."""
        if not self.history:
            print(f"\n{YELLOW}No test history available.{RESET}")
            return
            
        print(f"\n{BLUE}{BOLD}Test Run History (last {min(len(self.history), MAX_HISTORY_ENTRIES)} runs):{RESET}")
        
        # Print header
        print(f"\n{BOLD}{'Timestamp':<20} {'Total':<8} {'Passed':<8} {'Failed':<8} {'Errors':<8} {'Skipped':<8}{RESET}")
        print("-" * 60)
        
        # Print each history entry
        for entry in self.history:
            print(f"{entry['timestamp']:<20} {entry['total']:<8} {entry['passed']:<8} {entry['failed']:<8} {entry['errors']:<8} {entry['skipped']:<8}")

if __name__ == '__main__':
    tracker = TestResultTracker()
    
    # Run all tests by default
    if len(sys.argv) == 1:
        test_suite = unittest.defaultTestLoader.discover('tests')
        result = unittest.TextTestRunner(verbosity=2).run(test_suite)
        
        # Record and display results
        current_result = tracker.add_result(result)
        tracker.print_comparison(current_result)
        tracker.print_history()
        
        # Return appropriate exit code based on test results
        sys.exit(0 if result.wasSuccessful() else 1)
    # Run specific test category or file if provided
    elif len(sys.argv) >= 2:
        test_path = sys.argv[1]
        
        # Check if the path is a file or directory
        path = Path(test_path)
        if path.is_file():
            # If it's a file, load the test module directly
            import importlib.util
            module_name = test_path.replace('/', '.').replace('.py', '')
            spec = importlib.util.spec_from_file_location(module_name, test_path)
            module = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(module)
            
            # Run the tests from the module
            test_suite = unittest.defaultTestLoader.loadTestsFromModule(module)
            result = unittest.TextTestRunner(verbosity=2).run(test_suite)
            
            # Record and display results
            current_result = tracker.add_result(result)
            tracker.print_comparison(current_result)
            tracker.print_history()
            
            # Return appropriate exit code based on test results
            sys.exit(0 if result.wasSuccessful() else 1)
        else:
            # If it's a directory, discover tests in that directory
            test_suite = unittest.defaultTestLoader.discover(test_path)
            result = unittest.TextTestRunner(verbosity=2).run(test_suite)
            
            # Record and display results
            current_result = tracker.add_result(result)
            tracker.print_comparison(current_result)
            tracker.print_history()
            
            # Return appropriate exit code based on test results
            sys.exit(0 if result.wasSuccessful() else 1) 