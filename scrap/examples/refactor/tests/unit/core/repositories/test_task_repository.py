#!/usr/bin/env python3
"""
Unit tests for the Task Repository in the Core module.
"""
import unittest
import json
import tempfile
from pathlib import Path
from unittest.mock import patch, MagicMock

from refactor.core.repositories.task_repository import TaskRepository
from refactor.core.repositories.repository_interface import (
    EntityNotFoundError,
    EntityAlreadyExistsError,
    ValidationError
)
from refactor.core.entities.task_entity import TaskEntity, TaskStatus, TaskPriority


class MockTaskEntity:
    """Mock task entity for testing the repository."""
    
    @classmethod
    def from_dict(cls, data):
        """Create a mock task entity from a dictionary."""
        mock_task = MagicMock(spec=TaskEntity)
        mock_task.id = data.get('id', '')
        mock_task.name = data.get('name', '')
        
        # Convert status from string to enum if it's a string
        status = data.get('status', '')
        if isinstance(status, str):
            mock_task.status = TaskStatus.from_string(status)
        else:
            mock_task.status = status
            
        # Convert priority from int to enum if it's an int
        priority = data.get('priority', 1)
        if isinstance(priority, int):
            mock_task.priority = TaskPriority.from_int(priority)
        else:
            mock_task.priority = priority
            
        mock_task.tags = data.get('tags', [])
        mock_task.description = data.get('description', '')
        
        # Add parent_id if it exists
        if 'parent_id' in data:
            mock_task.parent_id = data['parent_id']
            
        # Implement methods needed by tests
        mock_task.set_status = MagicMock(return_value=None)
        mock_task.set_priority = MagicMock(return_value=None)
            
        return mock_task


@patch('refactor.core.repositories.task_repository.TaskEntity', MockTaskEntity)
class TaskRepositoryTests(unittest.TestCase):
    """Test cases for the TaskRepository implementation."""

    def setUp(self):
        """Set up test environment."""
        # Create a temporary file with test data
        self.test_fd, self.test_path = tempfile.mkstemp(suffix='.json')
        self.test_path = Path(self.test_path)
        
        # Create test data
        self.test_data = {
            "tasks": [
                {
                    "id": "tsk_test1001",
                    "name": "Test Task 1",
                    "description": "Test task description",
                    "status": "to do",
                    "priority": 1,
                    "tags": ["test", "high-priority"],
                    "subtasks": [
                        {
                            "id": "stk_test2001",
                            "name": "Test Subtask 1",
                            "description": "Subtask description",
                            "status": "to do",
                            "priority": 2,
                            "parent_id": "tsk_test1001",
                            "tags": ["test"]
                        }
                    ],
                    "checklists": [
                        {
                            "name": "Test Checklist",
                            "items": [
                                {"name": "Test Item 1", "checked": False},
                                {"name": "Test Item 2", "checked": True}
                            ]
                        }
                    ],
                    "relationships": {
                        "blocks": ["tsk_test3001"],
                        "depends_on": []
                    }
                },
                {
                    "id": "tsk_test3001",
                    "name": "Test Task 2",
                    "description": "Another test task",
                    "status": "in progress",
                    "priority": 3,
                    "tags": ["test", "documentation"],
                    "subtasks": [],
                    "checklists": [],
                    "relationships": {
                        "depends_on": ["tsk_test1001"],
                        "blocks": []
                    }
                }
            ]
        }
        
        # Write test data to file
        with open(self.test_path, 'w') as f:
            json.dump(self.test_data, f, indent=2)
            
        # Create repository with test data
        self.repo = TaskRepository(self.test_path)
        
    def tearDown(self):
        """Clean up after tests."""
        import os
        try:
            os.close(self.test_fd)
            os.unlink(self.test_path)
        except:
            pass
    
    def test_repository_initialization(self):
        """Test repository initialization from JSON file."""
        self.assertEqual(self.repo.count(), 3)  # 2 tasks + 1 subtask
        
        # Check if tasks are loaded
        task1 = self.repo.get("tsk_test1001")
        self.assertEqual(task1.name, "Test Task 1")
        # Use string comparison for status enum
        self.assertEqual(task1.status.name, "TO_DO")
        
        task2 = self.repo.get("tsk_test3001")
        self.assertEqual(task2.name, "Test Task 2")
        self.assertEqual(task2.status.name, "IN_PROGRESS")
        
        # Check if subtasks are loaded
        subtask = self.repo.get("stk_test2001")
        self.assertEqual(subtask.name, "Test Subtask 1")
        
    def test_get_by_name(self):
        """Test getting tasks by name."""
        task = self.repo.get_by_name("Test Task 1")
        self.assertEqual(task.id, "tsk_test1001")
        
        with self.assertRaises(EntityNotFoundError):
            self.repo.get_by_name("Non-existent Task")
            
    @patch('refactor.core.repositories.task_repository.TaskEntity', MockTaskEntity)
    def test_add_task(self):
        """Test adding a new task."""
        # Create a mock task
        new_task = MagicMock(spec=TaskEntity)
        new_task.id = "tsk_test4001"
        new_task.name = "New Test Task"
        new_task.status = TaskStatus.TO_DO
        new_task.priority = TaskPriority.HIGH
        new_task.tags = ["test", "new"]
        
        # Add task
        added_task = self.repo.add(new_task)
        self.assertEqual(added_task.id, "tsk_test4001")
        self.assertEqual(self.repo.count(), 4)
        
        # Check if task is retrievable
        retrieved_task = self.repo.get("tsk_test4001")
        self.assertEqual(retrieved_task.name, "New Test Task")
        
        # Try adding a task with duplicate ID
        duplicate_task = MagicMock(spec=TaskEntity)
        duplicate_task.id = "tsk_test4001"  # Same ID
        duplicate_task.name = "Duplicate Task"
        
        with self.assertRaises(EntityAlreadyExistsError):
            self.repo.add(duplicate_task)
            
        # Try adding a task with duplicate name
        duplicate_name_task = MagicMock(spec=TaskEntity)
        duplicate_name_task.id = "tsk_test5001"
        duplicate_name_task.name = "New Test Task"  # Same name
        
        with self.assertRaises(EntityAlreadyExistsError):
            self.repo.add(duplicate_name_task)
            
    def test_update_task(self):
        """Test updating an existing task."""
        # Get existing task
        task = self.repo.get("tsk_test1001")
        
        # Update task using set methods instead of property assignment
        task.set_status(TaskStatus.IN_PROGRESS)
        task.set_priority(TaskPriority.HIGH)
        
        updated_task = self.repo.update(task)
        self.assertEqual(updated_task.status, TaskStatus.IN_PROGRESS)
        self.assertEqual(updated_task.priority, TaskPriority.HIGH)
        
        # Retrieve and check if updates persisted
        retrieved_task = self.repo.get("tsk_test1001")
        self.assertEqual(retrieved_task.status, TaskStatus.IN_PROGRESS)
        self.assertEqual(retrieved_task.priority, TaskPriority.HIGH)
        
        # Try updating non-existent task
        non_existent_task = MagicMock(spec=TaskEntity)
        non_existent_task.id = "tsk_nonexistent"
        non_existent_task.name = "Non-existent Task"
        
        with self.assertRaises(EntityNotFoundError):
            self.repo.update(non_existent_task)
            
    def test_delete_task(self):
        """Test deleting a task."""
        # Initial count
        initial_count = self.repo.count()
        
        # Delete task
        result = self.repo.delete("tsk_test1001")
        self.assertTrue(result)
        self.assertEqual(self.repo.count(), initial_count - 1)
        
        # Check if task is no longer retrievable
        with self.assertRaises(EntityNotFoundError):
            self.repo.get("tsk_test1001")
            
        # Try deleting non-existent task
        result = self.repo.delete("tsk_nonexistent")
        self.assertFalse(result)
        
    def test_find(self):
        """Test finding tasks with a predicate."""
        # Find all tasks with high priority
        high_priority_tasks = self.repo.find(lambda task: task.priority.value >= TaskPriority.NORMAL.value)
        self.assertEqual(len(high_priority_tasks), 1)
        self.assertEqual(high_priority_tasks[0].id, "tsk_test3001")
        
        # Find tasks with "documentation" tag
        doc_tasks = self.repo.find(lambda task: "documentation" in task.tags)
        self.assertEqual(len(doc_tasks), 1)
        self.assertEqual(doc_tasks[0].id, "tsk_test3001")
        
    def test_get_by_status(self):
        """Test getting tasks by status."""
        to_do_tasks = self.repo.get_by_status(TaskStatus.TO_DO)
        self.assertEqual(len(to_do_tasks), 2)  # Task 1 and Subtask
        
        in_progress_tasks = self.repo.get_by_status(TaskStatus.IN_PROGRESS)
        self.assertEqual(len(in_progress_tasks), 1)  # Task 2
        
    def test_get_by_tag(self):
        """Test getting tasks by tag."""
        high_priority_tasks = self.repo.get_by_tag("high-priority")
        self.assertEqual(len(high_priority_tasks), 1)
        self.assertEqual(high_priority_tasks[0].id, "tsk_test1001")
        
    def test_search(self):
        """Test searching for tasks."""
        # Search by name (using more specific query to match only one task)
        results = self.repo.search("Test Task 1")
        self.assertEqual(len(results), 1)
        self.assertEqual(results[0].id, "tsk_test1001")
        
        # Search by status
        results = self.repo.search("", statuses=[TaskStatus.TO_DO])
        self.assertEqual(len(results), 2)  # Task 1 and Subtask
        
        # Search by priority
        results = self.repo.search("", priorities=[TaskPriority.NORMAL])
        self.assertEqual(len(results), 1)
        self.assertEqual(results[0].id, "tsk_test3001")
        
        # Search by tag
        results = self.repo.search("", tags=["documentation"])
        self.assertEqual(len(results), 1)
        self.assertEqual(results[0].id, "tsk_test3001")
        
        # Search by parent ID
        results = self.repo.search("", parent_id="tsk_test1001")
        self.assertEqual(len(results), 1)
        self.assertEqual(results[0].id, "stk_test2001")
        
        # Combined search
        results = self.repo.search("test", statuses=[TaskStatus.TO_DO], tags=["test"])
        self.assertEqual(len(results), 2)  # Task 1 and Subtask


if __name__ == "__main__":
    unittest.main() 