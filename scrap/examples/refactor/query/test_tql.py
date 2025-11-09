"""
Task: tsk_62630e24 - Update Utilities and Support Modules Comments
Document: refactor/query/test_tql.py
dohcount: 1

Related Tasks:
    - tsk_0a733101 - Code Comments Enhancement (parent)
    - tsk_7e3a4709 - Update Common Module Comments (sibling)
    - tsk_bf28d342 - Update CLI Module Comments (sibling)
    - tsk_4c899138 - Update Storage Module Comments (sibling)
    - tsk_3f55d115 - Update Plugins Module Comments (sibling)

Used By:
    - Testing Framework: Runs as part of test suite
    - TQL Development: Used for regression testing during development
    - Documentation Generation: Provides example queries
    - Query Validator: Uses test cases to validate implementation
    - CI/CD Pipeline: Automatically runs to verify TQL functionality
    - New Feature Development: Reference for query syntax and behavior

Purpose:
    Provides a comprehensive test suite for the Task Query Language (TQL) system.
    Contains a collection of test queries that validate core TQL functionality
    including field access, comparison operators, logical operators, and edge cases.
    Serves as both a testing tool and a demonstration of TQL capabilities with
    practical examples.

Requirements:
    - CRITICAL: Must test all supported operators and combinations
    - CRITICAL: Must validate against realistic task data structures
    - Must include regression tests for fixed bugs
    - Must print clear results with pass/fail status
    - Should verify both positive and negative cases
    - Should include examples of complex, nested queries
    - Must be runnable as a standalone script and by test frameworks

Task Query Language (TQL) Test

This script tests the Task Query Language with various example queries.
"""

import json
import sys
import os
from typing import Any, Dict, List

# Add the parent directory to the Python path so we can import modules properly
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../..')))

from refactor.query import TQL

def create_sample_tasks() -> List[Dict[str, Any]]:
    """Create a list of sample tasks for testing"""
    return [
        {
            "id": "tsk_123",
            "name": "Fix login bug",
            "description": "The login page shows errors on mobile devices",
            "status": "in progress",
            "priority": 3,
            "task_type": "bug",
            "tags": ["frontend", "bug", "mobile"],
            "assignee": "alice",
            "created_at": "2023-08-15",
            "updated_at": "2023-08-17",
            "due_date": "2023-08-20",
            "list_name": "Sprint 23",
            "folder_name": "Development",
            "space_name": "Product",
            "comments": [
                {"Author": "bob", "Text": "I can't reproduce this on iPhone 12"},
                {"Author": "alice", "Text": "Confirmed on Android devices"}
            ]
        },
        {
            "id": "tsk_456",
            "name": "Add export feature",
            "description": "Users need to export their data in CSV format",
            "status": "to do",
            "priority": 2,
            "task_type": "feature",
            "tags": ["backend", "feature", "csv"],
            "assignee": "bob",
            "created_at": "2023-08-16",
            "updated_at": "2023-08-16",
            "due_date": "2023-08-25",
            "list_name": "Sprint 24",
            "folder_name": "Development",
            "space_name": "Product",
            "comments": []
        },
        {
            "id": "tsk_789",
            "name": "Update documentation",
            "description": "Update API documentation with the new endpoints",
            "status": "complete",
            "priority": 1,
            "task_type": "documentation",
            "tags": ["docs", "api"],
            "assignee": "charlie",
            "created_at": "2023-08-10",
            "updated_at": "2023-08-14",
            "due_date": "2023-08-15",
            "list_name": "Sprint 23",
            "folder_name": "Documentation",
            "space_name": "Product",
            "comments": [
                {"Author": "dave", "Text": "Looks good to me!"}
            ]
        },
        {
            "id": "tsk_101",
            "name": "Migrate database",
            "description": "Migrate from MySQL to PostgreSQL",
            "status": "to do",
            "priority": 4,
            "task_type": "infrastructure",
            "tags": ["database", "migration", "backend", "critical"],
            "assignee": "dave",
            "created_at": "2023-08-01",
            "updated_at": "2023-08-05",
            "due_date": "2023-09-01",
            "list_name": "Sprint 25",
            "folder_name": "Infrastructure",
            "space_name": "Operations",
            "comments": [
                {"Author": "dave", "Text": "We need to plan the maintenance window"},
                {"Author": "alice", "Text": "I can help with the migration script"}
            ]
        },
        {
            "id": "stk_102",
            "name": "Design database schema",
            "description": "Design the new database schema for PostgreSQL",
            "status": "in progress",
            "priority": 3,
            "task_type": "design",
            "tags": ["database", "design"],
            "assignee": "alice",
            "created_at": "2023-08-02",
            "updated_at": "2023-08-10",
            "due_date": "2023-08-20",
            "list_name": "Sprint 25",
            "folder_name": "Infrastructure",
            "space_name": "Operations",
            "parent_id": "tsk_101",
            "comments": []
        }
    ]

def run_test():
    """Run TQL tests with various queries"""
    tasks = create_sample_tasks()
    tql = TQL()
    
    # Define test queries and their expected results
    test_queries = [
        {
            "name": "Basic status filter",
            "query": "status == 'to do'",
            "expected_count": 2
        },
        {
            "name": "Task by name contains",
            "query": "name contains 'database'",
            "expected_count": 2
        },
        {
            "name": "Tasks with high priority",
            "query": "priority >= 3",
            "expected_count": 3
        },
        {
            "name": "Tasks in Development folder",
            "query": "folder == 'Development'",
            "expected_count": 2
        },
        {
            "name": "Tasks with specific tag",
            "query": "tags in 'backend'",
            "expected_count": 2
        },
        {
            "name": "Tasks assigned to Alice",
            "query": "assignee == 'alice'",
            "expected_count": 2
        },
        {
            "name": "Tasks with comments from Dave",
            "query": "author in 'dave'",
            "expected_count": 2
        },
        {
            "name": "Complex query with AND",
            "query": "status == 'to do' AND priority > 2",
            "expected_count": 1
        },
        {
            "name": "Complex query with OR",
            "query": "status == 'complete' OR priority == 1",
            "expected_count": 1
        },
        {
            "name": "Complex query with parentheses",
            "query": "(status == 'to do' OR status == 'in progress') AND priority >= 3",
            "expected_count": 3
        },
        {
            "name": "Subtasks of specific task",
            "query": "parent == 'tsk_101'",
            "expected_count": 1
        },
        {
            "name": "Tasks with due date before specific date",
            "query": "due_date < '2023-08-21'",
            "expected_count": 3
        },
        {
            "name": "Tasks with due date after specific date",
            "query": "due_date > '2023-08-20'",
            "expected_count": 2
        },
        {
            "name": "Tasks with specific list and status",
            "query": "list == 'Sprint 25' AND status == 'to do'",
            "expected_count": 1
        }
    ]
    
    # Run all test queries
    failed_tests = []
    
    print(f"Running {len(test_queries)} TQL test queries...")
    print("=" * 80)
    
    for i, test in enumerate(test_queries, 1):
        print(f"{i}. Testing: {test['name']}")
        print(f"   Query: {test['query']}")
        
        try:
            # Filter tasks with the query
            filtered = tql.filter_tasks(tasks, test['query'])
            
            # Get parsed query explanation
            explanation = tql.explain(test['query'])
            
            # Check results
            result_count = len(filtered)
            expected_count = test['expected_count']
            
            # Print results
            print(f"   Result: {result_count} tasks")
            print(f"   Expected: {expected_count} tasks")
            
            # Print query explanation
            print(f"   Explanation:\n{explanation}")
            
            # Mark as passed or failed
            if result_count == expected_count:
                print(f"   ✅ PASSED")
            else:
                print(f"   ❌ FAILED")
                failed_tests.append(test['name'])
                
                # Print matching tasks for debugging
                print(f"   Matching tasks:")
                for task in filtered:
                    print(f"   - {task['id']}: {task['name']} ({task['status']})")
        except Exception as e:
            print(f"   ❌ ERROR: {e}")
            failed_tests.append(test['name'])
        
        print("-" * 80)
    
    # Print summary
    print("=" * 80)
    print(f"Test Summary: {len(test_queries) - len(failed_tests)}/{len(test_queries)} passed")
    
    if failed_tests:
        print(f"Failed tests:")
        for name in failed_tests:
            print(f"- {name}")
        return 1
    else:
        print("All tests passed!")
        return 0

if __name__ == "__main__":
    sys.exit(run_test()) 