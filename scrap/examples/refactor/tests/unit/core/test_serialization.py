import unittest
import json
import tempfile
from pathlib import Path

class SerializationTests(unittest.TestCase):
    def setUp(self):
        # Create test data for serialization tests
        self.task_data = {
            "id": "tsk_ser001",
            "name": "Test Serialization Task",
            "description": "This is a task for testing serialization",
            "status": "to do",
            "priority": 1,
            "tags": ["test", "serialization"],
            "subtasks": [
                {
                    "id": "stk_ser002",
                    "name": "Test Subtask",
                    "status": "to do"
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
                "blocks": ["tsk_ser003"],
                "depends_on": []
            }
        }
        
        # Create a temporary file for testing
        self.temp_dir = tempfile.TemporaryDirectory()
        self.temp_file_path = Path(self.temp_dir.name) / "serialization_test.json"
    
    def tearDown(self):
        # Clean up the temporary directory
        self.temp_dir.cleanup()
    
    def test_serialize_deserialize_task(self):
        """Test serialization and deserialization of a task."""
        # Serialize the task to JSON
        serialized_task = json.dumps(self.task_data, indent=2)
        
        # Write to a file
        with open(self.temp_file_path, 'w') as f:
            f.write(serialized_task)
        
        # Read from the file
        with open(self.temp_file_path, 'r') as f:
            loaded_json = f.read()
        
        # Deserialize back to a Python object
        deserialized_task = json.loads(loaded_json)
        
        # Verify the data is preserved
        self.assertEqual(deserialized_task['id'], self.task_data['id'])
        self.assertEqual(deserialized_task['name'], self.task_data['name'])
        self.assertEqual(deserialized_task['status'], self.task_data['status'])
        self.assertEqual(deserialized_task['priority'], self.task_data['priority'])
        
        # Verify nested structures
        self.assertEqual(len(deserialized_task['subtasks']), len(self.task_data['subtasks']))
        self.assertEqual(deserialized_task['subtasks'][0]['id'], self.task_data['subtasks'][0]['id'])
        
        self.assertEqual(len(deserialized_task['checklists']), len(self.task_data['checklists']))
        self.assertEqual(len(deserialized_task['checklists'][0]['items']), 
                        len(self.task_data['checklists'][0]['items']))
        
        self.assertEqual(deserialized_task['relationships']['blocks'], 
                        self.task_data['relationships']['blocks'])
    
    def test_serialize_deserialize_collection(self):
        """Test serialization and deserialization of a task collection."""
        # Create a collection with multiple tasks
        task_collection = {
            "tasks": [
                self.task_data,
                {
                    "id": "tsk_ser004",
                    "name": "Another Task",
                    "status": "in progress",
                    "priority": 2
                }
            ]
        }
        
        # Serialize the collection
        serialized_collection = json.dumps(task_collection, indent=2)
        
        # Write to a file
        with open(self.temp_file_path, 'w') as f:
            f.write(serialized_collection)
        
        # Read from the file
        with open(self.temp_file_path, 'r') as f:
            loaded_json = f.read()
        
        # Deserialize back to a Python object
        deserialized_collection = json.loads(loaded_json)
        
        # Verify the collection
        self.assertEqual(len(deserialized_collection['tasks']), 2)
        self.assertEqual(deserialized_collection['tasks'][0]['id'], 'tsk_ser001')
        self.assertEqual(deserialized_collection['tasks'][1]['id'], 'tsk_ser004')
    
    def test_handle_unicode_and_special_chars(self):
        """Test serialization with Unicode and special characters."""
        # Create a task with special characters
        special_task = {
            "id": "tsk_ser005",
            "name": "Unicode Test ñáéíóú",
            "description": "Special chars: \u00A9 \u2022 \u2713",
            "tags": ["émojis", "symbols"]
        }
        
        # Serialize and deserialize
        serialized = json.dumps(special_task, ensure_ascii=False)
        deserialized = json.loads(serialized)
        
        # Verify the data
        self.assertEqual(deserialized['name'], "Unicode Test ñáéíóú")
        self.assertEqual(deserialized['description'], "Special chars: \u00A9 \u2022 \u2713")
        self.assertIn("émojis", deserialized['tags'])

if __name__ == '__main__':
    unittest.main() 