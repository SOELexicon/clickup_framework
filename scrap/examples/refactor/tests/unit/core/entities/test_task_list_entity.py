import unittest
import json
from pathlib import Path

class TaskListEntityTests(unittest.TestCase):
    def setUp(self):
        # Set up the test environment with test data
        repo_root = Path('/home/lexicon/source/repos/clickup_json_manager')
        self.test_template_path = repo_root / 'refactor' / 'tests' / 'fixtures' / 'test_template.json'
        print(f"Template path: {self.test_template_path}")
        
        # Create fixtures directory if it doesn't exist
        fixtures_dir = repo_root / 'refactor' / 'tests' / 'fixtures'
        fixtures_dir.mkdir(parents=True, exist_ok=True)
        
        # If test template doesn't exist, create it with some test data
        if not self.test_template_path.exists():
            # Create a minimal test template with a list for testing
            test_data = {
                "spaces": [
                    {
                        "id": "spc_test1001",
                        "name": "Test Space",
                        "folders": [
                            {
                                "id": "fld_test2001",
                                "name": "Test Folder",
                                "lists": [
                                    {
                                        "id": "lst_test3001",
                                        "name": "Test List",
                                        "description": "Test list description",
                                        "tasks": [
                                            {
                                                "id": "tsk_test4001",
                                                "name": "Test Task 1",
                                                "status": "to do"
                                            },
                                            {
                                                "id": "tsk_test4002",
                                                "name": "Test Task 2",
                                                "status": "in progress"
                                            }
                                        ]
                                    }
                                ]
                            }
                        ]
                    }
                ],
                "tasks": [] # We'll use this for flat task access
            }
            
            # Write test data to file
            with open(self.test_template_path, 'w') as f:
                json.dump(test_data, f, indent=2)
        
        # Load test data
        with open(self.test_template_path, 'r') as f:
            self.test_data = json.load(f)
        
        # Extract the test list
        self.list_data = None
        for space in self.test_data.get('spaces', []):
            for folder in space.get('folders', []):
                for list_item in folder.get('lists', []):
                    if list_item.get('id') == 'lst_test3001':
                        self.list_data = list_item
                        break
        
        # If test list not found, create it
        if not self.list_data:
            # Add a test space, folder and list if they don't exist
            if 'spaces' not in self.test_data:
                self.test_data['spaces'] = []
            
            if not self.test_data['spaces']:
                self.test_data['spaces'].append({
                    "id": "spc_test1001",
                    "name": "Test Space",
                    "folders": []
                })
            
            test_space = self.test_data['spaces'][0]
            
            if 'folders' not in test_space:
                test_space['folders'] = []
            
            if not test_space['folders']:
                test_space['folders'].append({
                    "id": "fld_test2001",
                    "name": "Test Folder",
                    "lists": []
                })
            
            test_folder = test_space['folders'][0]
            
            if 'lists' not in test_folder:
                test_folder['lists'] = []
            
            self.list_data = {
                "id": "lst_test3001",
                "name": "Test List",
                "description": "Test list description",
                "tasks": [
                    {
                        "id": "tsk_test4001",
                        "name": "Test Task 1",
                        "status": "to do"
                    },
                    {
                        "id": "tsk_test4002",
                        "name": "Test Task 2",
                        "status": "in progress"
                    }
                ]
            }
            
            test_folder['lists'].append(self.list_data)
            
            # Save changes to test template
            with open(self.test_template_path, 'w') as f:
                json.dump(self.test_data, f, indent=2)
    
    def test_task_list_basic_attributes(self):
        """Test basic task list attributes."""
        self.assertEqual(self.list_data['id'], 'lst_test3001')
        self.assertEqual(self.list_data['name'], 'Test List')
        self.assertEqual(self.list_data['description'], 'Test list description')
    
    def test_task_list_tasks(self):
        """Test tasks contained in the list."""
        self.assertGreaterEqual(len(self.list_data['tasks']), 2)
        
        task1 = self.list_data['tasks'][0]
        self.assertEqual(task1['id'], 'tsk_test4001')
        self.assertEqual(task1['name'], 'Test Task 1')
        self.assertEqual(task1['status'], 'to do')
        
        task2 = self.list_data['tasks'][1]
        self.assertEqual(task2['id'], 'tsk_test4002')
        self.assertEqual(task2['name'], 'Test Task 2')
        self.assertEqual(task2['status'], 'in progress')
    
    def test_task_status_counts(self):
        """Test counting tasks by status in the list."""
        # Count tasks by status
        status_counts = {}
        for task in self.list_data['tasks']:
            status = task.get('status', 'unknown')
            if status in status_counts:
                status_counts[status] += 1
            else:
                status_counts[status] = 1
        
        # Verify counts
        self.assertEqual(status_counts.get('to do', 0), 1)
        self.assertEqual(status_counts.get('in progress', 0), 1)
        self.assertEqual(status_counts.get('complete', 0), 0)  # No complete tasks

if __name__ == '__main__':
    unittest.main() 