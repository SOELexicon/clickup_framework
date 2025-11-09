#!/usr/bin/env python3
"""
Task: tsk_62630e24 - Update Utilities and Support Modules Comments
Document: refactor/tools/test_failure_tasks.py
dohcount: 1

Related Tasks:
    - tsk_0a733101 - Code Comments Enhancement (parent)
    - tsk_7e3a4709 - Update Common Module Comments (sibling)
    - tsk_bf28d342 - Update CLI Module Comments (sibling)
    - tsk_4c899138 - Update Storage Module Comments (sibling)
    - tsk_3f55d115 - Update Plugins Module Comments (sibling)

Used By:
    - CI/CD Pipeline: Automatically creates tasks for test failures
    - QA Process: Tracks test failures and enables progress monitoring
    - Development Workflow: Creates actionable tasks from test output
    - Unit Test Runner: Integrated with run_unit_tests.sh script

Purpose:
    Automates the creation of task tracking items in ClickUp for test failures.
    This tool parses test failure output, creates parent tasks for each test file
    with failures, and subtasks for individual test failures. It streamlines the
    process of documenting and tracking test issues, providing detailed error
    information, stack traces, and test metadata to assist developers in resolving
    the failures efficiently.

Requirements:
    - CRITICAL: Must parse both ERROR and FAIL test outcomes correctly
    - CRITICAL: Must maintain hierarchy (task per file, subtask per failure)
    - CRITICAL: Must include full error details and stack traces
    - Must include timestamps in task names for tracking
    - Must properly handle shell command execution and errors
    - Should group related failures by test file
    - Should provide detailed summary statistics

Test Failure Task Creator

This script parses test failure output and creates ClickUp tasks to track failures.
It is designed to be called from the run_unit_tests.sh script with the --create-tasks flag.
"""

import os
import sys
import re
import argparse
import subprocess
import json
from datetime import datetime

class TestFailureTaskCreator:
    """Parses test failures and creates corresponding ClickUp tasks."""
    
    def __init__(self, template_file, folder_name, list_name, parent_task_name=None):
        """
        Initialize the task creator.
        
        Args:
            template_file (str): Path to the ClickUp JSON template file
            folder_name (str): Name of the folder to create tasks in
            list_name (str): Name of the list to create tasks in
            parent_task_name (str, optional): Name of the parent task to create subtasks under
        """
        self.template_file = template_file
        self.folder_name = folder_name
        self.list_name = list_name
        self.parent_task_name = parent_task_name
        self.cujm_path = self._find_cujm_executable()
    
    def _find_cujm_executable(self):
        """Find the path to the CUJM executable."""
        # Try the current directory first
        if os.path.isfile("./cujm"):
            return "./cujm"
        
        # Try searching in PATH
        try:
            result = subprocess.run(
                ["which", "cujm"], 
                capture_output=True, 
                text=True, 
                check=True
            )
            return result.stdout.strip()
        except (subprocess.CalledProcessError, FileNotFoundError):
            # Default to relative path from this script
            return os.path.join(os.path.dirname(__file__), "../..", "cujm")
    
    def parse_failed_tests_file(self, failed_tests_file):
        """
        Parse the file containing failed test output.
        
        Args:
            failed_tests_file (str): Path to the file containing failed test output
            
        Returns:
            dict: A dictionary mapping test files to their failures
        """
        if not os.path.isfile(failed_tests_file):
            print(f"Error: Failed tests file not found: {failed_tests_file}")
            return {}
        
        with open(failed_tests_file, "r") as f:
            content = f.read()
        
        # Group failures by test file
        test_failures = {}
        
        # Regular expression to match test failures
        # Format: ERROR: test_some_test (path.to.test_file.TestClass)
        # or: FAIL: test_some_test (path.to.test_file.TestClass)
        pattern = r"(ERROR|FAIL): (test_\w+) \(([\w\.]+)\)"
        matches = re.finditer(pattern, content)
        
        for match in matches:
            error_type = match.group(1)
            test_name = match.group(2)
            test_path = match.group(3)
            
            # Extract the test file name from the path
            test_file = test_path.split(".")[-2]
            if not test_file.startswith("test_"):
                test_file = "test_" + test_file
            
            # Find the error message and traceback
            start_pos = match.end()
            next_match = re.search(pattern, content[start_pos:])
            end_pos = start_pos + next_match.start() if next_match else len(content)
            
            error_details = content[start_pos:end_pos].strip()
            
            # Store the failure information
            if test_file not in test_failures:
                test_failures[test_file] = []
            
            test_failures[test_file].append({
                "error_type": error_type,
                "test_name": test_name,
                "test_path": test_path,
                "error_details": error_details
            })
        
        return test_failures
    
    def create_task_for_test_file(self, test_file, failures):
        """
        Create a task for a test file with failures.
        
        Args:
            test_file (str): Name of the test file
            failures (list): List of failure dictionaries
            
        Returns:
            str: ID of the created task
        """
        # Format the task name
        date_str = datetime.now().strftime("%Y-%m-%d")
        task_name = f"Fix test failures in {test_file} ({date_str})"
        
        # Format the task description
        description = f"""## Test Failures in {test_file}

This task tracks {len(failures)} test failures found on {date_str}.

### Summary
{test_file} contains the following failing tests:
"""
        for i, failure in enumerate(failures, 1):
            description += f"- {i}. {failure['test_name']} ({failure['error_type']})\n"
        
        description += "\nPlease fix these failing tests and mark this task as complete when done."
        
        # Create the task
        try:
            cmd = [
                self.cujm_path,
                "create-task",
                self.template_file,
                task_name,
                "--description", description,
                "--status", "to do",
                "--priority", "2",
                "--folder", self.folder_name,
                "--list", self.list_name,
                "--tags", "test-failure,automated"
            ]
            result = subprocess.run(cmd, capture_output=True, text=True, check=True)
            
            # Extract the task ID using regex
            match = re.search(r"ID: (\w+)", result.stdout)
            if match:
                return match.group(1)
            else:
                print(f"Warning: Could not extract task ID from output: {result.stdout}")
                return None
                
        except subprocess.CalledProcessError as e:
            print(f"Error creating task for {test_file}: {e}")
            print(f"Command output: {e.stdout}")
            print(f"Command error: {e.stderr}")
            return None
    
    def create_subtask_for_test_failure(self, parent_task_id, failure, index):
        """
        Create a subtask for an individual test failure.
        
        Args:
            parent_task_id (str): ID of the parent task
            failure (dict): Failure information
            index (int): Index of this failure for numbering
            
        Returns:
            str: ID of the created subtask
        """
        # Format the subtask name
        subtask_name = f"Fix {index}: {failure['test_name']} ({failure['error_type']})"
        
        # Format the subtask description
        description = f"""## Test Failure Details

### Test Information
- **Test Name**: {failure['test_name']}
- **Test Path**: {failure['test_path']}
- **Failure Type**: {failure['error_type']}

### Error Details
```
{failure['error_details']}
```

Please fix this test and mark this subtask as complete when done.
"""
        
        # Create the subtask
        try:
            cmd = [
                self.cujm_path,
                "create-subtask",
                self.template_file,
                parent_task_id,
                subtask_name,
                "--description", description,
                "--status", "to do",
                "--priority", "2",
                "--tags", "test-failure"
            ]
            result = subprocess.run(cmd, capture_output=True, text=True, check=True)
            
            # Extract the subtask ID
            match = re.search(r"ID: '(\w+)'", result.stdout)
            if match:
                return match.group(1)
            else:
                print(f"Warning: Could not extract subtask ID from output: {result.stdout}")
                return None
                
        except subprocess.CalledProcessError as e:
            print(f"Error creating subtask for {failure['test_name']}: {e}")
            print(f"Command output: {e.stdout}")
            print(f"Command error: {e.stderr}")
            return None
    
    def create_tasks_for_failures(self, failed_tests_file):
        """
        Create tasks for all test failures.
        
        Args:
            failed_tests_file (str): Path to the file containing failed test output
            
        Returns:
            dict: A dictionary with statistics about created tasks
        """
        test_failures = self.parse_failed_tests_file(failed_tests_file)
        
        if not test_failures:
            print("No test failures found.")
            return {"test_files": 0, "total_failures": 0, "tasks_created": 0, "subtasks_created": 0}
        
        stats = {
            "test_files": len(test_failures),
            "total_failures": sum(len(failures) for failures in test_failures.values()),
            "tasks_created": 0,
            "subtasks_created": 0
        }
        
        # Create parent task if needed and if a name is provided
        parent_task_id = None
        if self.parent_task_name:
            # Check if the parent task exists
            try:
                cmd = [
                    self.cujm_path,
                    "show",
                    self.template_file,
                    self.parent_task_name
                ]
                result = subprocess.run(cmd, capture_output=True, text=True, check=True)
                # Extract the task ID
                match = re.search(r"ID: (\w+)", result.stdout)
                if match:
                    parent_task_id = match.group(1)
            except subprocess.CalledProcessError as e:
                print(f"Error checking parent task: {e}")
                print("Creating tasks without a parent task.")
        
        # Process each test file
        for test_file, failures in test_failures.items():
            # Create a task for the test file
            task_id = self.create_task_for_test_file(test_file, failures)
            
            if task_id:
                stats["tasks_created"] += 1
                
                # Create subtasks for each failure
                for i, failure in enumerate(failures, 1):
                    subtask_id = self.create_subtask_for_test_failure(task_id, failure, i)
                    if subtask_id:
                        stats["subtasks_created"] += 1
        
        return stats

def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(description="Create ClickUp tasks for test failures")
    parser.add_argument("failed_tests_file", help="Path to the file containing failed test output")
    parser.add_argument("--template", default="000_clickup_tasks_template.json", 
                      help="Path to the ClickUp JSON template file")
    parser.add_argument("--folder", default="Testing", 
                      help="Name of the folder to create tasks in")
    parser.add_argument("--list", default="Refactor Testing", 
                      help="Name of the list to create tasks in")
    parser.add_argument("--parent", 
                      help="Name of the parent task to create subtasks under")
    
    args = parser.parse_args()
    
    creator = TestFailureTaskCreator(
        args.template, 
        args.folder, 
        args.list, 
        args.parent
    )
    
    stats = creator.create_tasks_for_failures(args.failed_tests_file)
    
    print("\n--- Task Creation Summary ---")
    print(f"Test files with failures: {stats['test_files']}")
    print(f"Total failures: {stats['total_failures']}")
    print(f"Tasks created: {stats['tasks_created']}")
    print(f"Subtasks created: {stats['subtasks_created']}")
    print("-----------------------------")

if __name__ == "__main__":
    main() 