import unittest
import json
import tempfile
from pathlib import Path

class ErrorHandlingTests(unittest.TestCase):
    def setUp(self):
        # Create a temporary file for testing
        self.temp_dir = tempfile.TemporaryDirectory()
        self.temp_file_path = Path(self.temp_dir.name) / "error_test.json"
    
    def tearDown(self):
        # Clean up the temporary directory
        self.temp_dir.cleanup()
    
    def test_handle_invalid_json(self):
        """Test handling of invalid JSON input."""
        # Create an invalid JSON file
        with open(self.temp_file_path, 'w') as f:
            f.write('{"this": "is", "invalid": json}')  # Missing quotes around 'json'
        
        # Try to load the invalid JSON
        with self.assertRaises(json.JSONDecodeError):
            with open(self.temp_file_path, 'r') as f:
                json.load(f)
    
    def test_handle_missing_required_fields(self):
        """Test handling of task data missing required fields."""
        # Define a function to validate a task
        def validate_task(task_data):
            required_fields = ['id', 'name', 'status']
            for field in required_fields:
                if field not in task_data:
                    raise ValueError(f"Missing required field: {field}")
            return True
        
        # Test a valid task
        valid_task = {
            "id": "tsk_err001",
            "name": "Valid Task",
            "status": "to do"
        }
        self.assertTrue(validate_task(valid_task))
        
        # Test tasks with missing fields
        invalid_tasks = [
            {"name": "No ID", "status": "to do"},
            {"id": "tsk_err002", "status": "to do"},
            {"id": "tsk_err003", "name": "No Status"}
        ]
        
        for task in invalid_tasks:
            with self.assertRaises(ValueError) as context:
                validate_task(task)
            
            # Check that the error message mentions the missing field
            error_msg = str(context.exception)
            missing_field = next((f for f in ['id', 'name', 'status'] if f not in task), None)
            self.assertIn(missing_field, error_msg)
    
    def test_handle_invalid_status_transition(self):
        """Test handling of invalid task status transitions."""
        # Define valid transitions
        valid_transitions = {
            "to do": ["in progress", "blocked"],
            "in progress": ["to do", "blocked", "complete"],
            "blocked": ["to do", "in progress"],
            "complete": []  # Cannot transition out of complete
        }
        
        # Define a function to validate a status transition
        def validate_transition(current_status, new_status):
            if new_status not in valid_transitions.get(current_status, []):
                raise ValueError(f"Invalid status transition: {current_status} -> {new_status}")
            return True
        
        # Test valid transitions
        self.assertTrue(validate_transition("to do", "in progress"))
        self.assertTrue(validate_transition("in progress", "complete"))
        
        # Test invalid transitions
        invalid_transitions = [
            ("to do", "complete"),  # Cannot go directly from to do to complete
            ("blocked", "complete"),  # Cannot go directly from blocked to complete
            ("complete", "to do"),  # Cannot transition out of complete
            ("complete", "in progress")  # Cannot transition out of complete
        ]
        
        for current, new in invalid_transitions:
            with self.assertRaises(ValueError) as context:
                validate_transition(current, new)
            
            # Check the error message
            error_msg = str(context.exception)
            self.assertIn("Invalid status transition", error_msg)
            self.assertIn(current, error_msg)
            self.assertIn(new, error_msg)
    
    def test_handle_circular_dependencies(self):
        """Test detection of circular dependencies between tasks."""
        # Define test tasks with dependencies
        tasks = {
            "tsk_circ001": {
                "id": "tsk_circ001",
                "name": "Task 1",
                "relationships": {"depends_on": ["tsk_circ002"]}
            },
            "tsk_circ002": {
                "id": "tsk_circ002",
                "name": "Task 2",
                "relationships": {"depends_on": ["tsk_circ003"]}
            },
            "tsk_circ003": {
                "id": "tsk_circ003",
                "name": "Task 3",
                "relationships": {"depends_on": ["tsk_circ001"]}  # Creates a cycle
            }
        }
        
        # Define a function to detect cycles
        def detect_cycles(task_id, visited=None, stack=None):
            if visited is None:
                visited = set()
            if stack is None:
                stack = set()
            
            visited.add(task_id)
            stack.add(task_id)
            
            # Check dependencies
            task = tasks.get(task_id)
            if task and 'relationships' in task:
                for dep_id in task['relationships'].get('depends_on', []):
                    if dep_id not in visited:
                        if detect_cycles(dep_id, visited, stack):
                            return True
                    elif dep_id in stack:
                        return True
            
            stack.remove(task_id)
            return False
        
        # Test cycle detection
        self.assertTrue(detect_cycles("tsk_circ001"))
        
        # Remove the cycle and test again
        tasks["tsk_circ003"]["relationships"]["depends_on"] = []
        visited = set()
        stack = set()
        self.assertFalse(detect_cycles("tsk_circ001", visited, stack))

if __name__ == '__main__':
    unittest.main() 