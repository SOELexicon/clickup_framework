import unittest
import json
from pathlib import Path

class TaskCollectionTests(unittest.TestCase):
    def setUp(self):
        # Set up the test environment with test data
        repo_root = Path('/home/lexicon/source/repos/clickup_json_manager')
        self.test_template_path = repo_root / 'refactor' / 'tests' / 'fixtures' / 'test_collection.json'
        print(f"Collection template path: {self.test_template_path}")
        
        # Create fixtures directory if it doesn't exist
        fixtures_dir = repo_root / 'refactor' / 'tests' / 'fixtures'
        fixtures_dir.mkdir(parents=True, exist_ok=True)
        
        # Create a test collection with various tasks for testing
        test_collection = {
            "tasks": [
                {
                    "id": "tsk_col001",
                    "name": "High Priority Task",
                    "description": "This is a high priority task",
                    "status": "to do",
                    "priority": 1,
                    "tags": ["important", "urgent"],
                    "due_date": "2023-12-20"
                },
                {
                    "id": "tsk_col002",
                    "name": "Medium Priority Task",
                    "description": "This is a medium priority task",
                    "status": "in progress",
                    "priority": 2,
                    "tags": ["important"],
                    "due_date": "2023-12-25"
                },
                {
                    "id": "tsk_col003",
                    "name": "Low Priority Task",
                    "description": "This is a low priority task",
                    "status": "in progress",
                    "priority": 3,
                    "tags": ["documentation"],
                    "due_date": "2024-01-05"
                },
                {
                    "id": "tsk_col004",
                    "name": "Completed Task",
                    "description": "This task is already completed",
                    "status": "complete",
                    "priority": 2,
                    "tags": ["documentation", "complete"],
                    "completion_date": "2023-12-15"
                },
                {
                    "id": "tsk_col005",
                    "name": "Blocked Task",
                    "description": "This task is blocked",
                    "status": "blocked",
                    "priority": 1,
                    "tags": ["blocked", "important"],
                    "relationships": {
                        "blocked_by": ["tsk_col003"]
                    }
                }
            ]
        }
        
        # Write test data to file
        with open(self.test_template_path, 'w') as f:
            json.dump(test_collection, f, indent=2)
        
        # Load the test data
        with open(self.test_template_path, 'r') as f:
            self.test_data = json.load(f)
        
        # Extract the task collection
        self.task_collection = self.test_data.get('tasks', [])
    
    def test_collection_basic_access(self):
        """Test basic collection access."""
        self.assertEqual(len(self.task_collection), 5)
        
        # Test accessing a specific task by ID
        task_col001 = next((t for t in self.task_collection if t['id'] == 'tsk_col001'), None)
        self.assertIsNotNone(task_col001)
        self.assertEqual(task_col001['name'], 'High Priority Task')
        
        # Test accessing a task that doesn't exist
        task_not_exist = next((t for t in self.task_collection if t['id'] == 'tsk_not_exist'), None)
        self.assertIsNone(task_not_exist)
    
    def test_collection_filtering(self):
        """Test filtering task collection."""
        # Filter by status
        in_progress_tasks = [t for t in self.task_collection if t['status'] == 'in progress']
        self.assertEqual(len(in_progress_tasks), 2)
        
        # Filter by priority
        high_priority_tasks = [t for t in self.task_collection if t['priority'] == 1]
        self.assertEqual(len(high_priority_tasks), 2)
        
        # Filter by tag
        important_tasks = [t for t in self.task_collection if 'important' in t.get('tags', [])]
        self.assertEqual(len(important_tasks), 3)
        
        # Complex filter (high priority and not complete)
        high_priority_not_complete = [
            t for t in self.task_collection 
            if t['priority'] == 1 and t['status'] != 'complete'
        ]
        self.assertEqual(len(high_priority_not_complete), 2)
    
    def test_collection_sorting(self):
        """Test sorting task collection."""
        # Sort by priority (ascending - highest priority is 1)
        priority_sorted = sorted(self.task_collection, key=lambda t: t['priority'])
        self.assertEqual(priority_sorted[0]['id'], 'tsk_col001')  # High priority (1)
        self.assertEqual(priority_sorted[-1]['id'], 'tsk_col003')  # Low priority (3)
        
        # Sort by due date (those with no due date come last)
        def due_date_key(task):
            return task.get('due_date', '9999-12-31')
        
        date_sorted = sorted(self.task_collection, key=due_date_key)
        self.assertEqual(date_sorted[0]['id'], 'tsk_col001')  # Due 2023-12-20
        
        # Sort by status (alphabetical)
        status_sorted = sorted(self.task_collection, key=lambda t: t['status'])
        self.assertEqual(status_sorted[0]['status'], 'blocked')
        self.assertEqual(status_sorted[-1]['status'], 'to do')

if __name__ == '__main__':
    unittest.main() 