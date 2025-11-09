#!/usr/bin/env python3
"""
Integration tests for task relationship validation.

These tests verify that the task completion rules correctly enforce constraints
related to task dependencies and relationship constraints, including proper
error messages and validation logic.
"""
import unittest
import tempfile
import json
import os
from pathlib import Path

# Import core entities and services
from refactor.core.entities.task_entity import TaskEntity
from refactor.core.services.task_service import TaskService
from refactor.core.repositories.task_repository import TaskRepository
from refactor.core.exceptions import ValidationError, TaskCompletionError, CircularDependencyError

# Import storage components
from refactor.storage.providers.json_storage_provider import JsonStorageProvider
from refactor.storage.serialization.json_serializer import JsonSerializer


class RelationshipValidationTests(unittest.TestCase):
    """Integration tests for relationship validation rules."""

    def setUp(self):
        """Set up test environment with relationship test fixtures."""
        # Create a temporary directory for test files
        self.temp_dir = tempfile.TemporaryDirectory()
        self.temp_path = Path(self.temp_dir.name)
        
        # Create a test file path
        self.test_file_path = self.temp_path / "test_relationship_validation.json"
        
        # Create initial empty file for repository
        self.test_file_path.touch()
        with open(self.test_file_path, 'w') as f:
            json.dump({"tasks": {}}, f)
        
        # Initialize storage provider correctly
        self.storage_provider = JsonStorageProvider()
        self.serializer = JsonSerializer()
        
        # Initialize TaskRepository with the file path
        self.task_repository = TaskRepository(self.test_file_path)
        self.task_service = TaskService(self.task_repository)
        
        # Load relationship test fixtures
        fixtures_path = Path(__file__).parent.parent / "fixtures" / "relationship_validation_fixtures.json"
        with open(fixtures_path, 'r') as f:
            self.fixtures = json.load(f)
            
        # Create initial empty template structure
        template_data = {
            "spaces": [
                {
                    "id": "spc_test001",
                    "name": "Test Space"
                }
            ],
            "folders": [
                {
                    "id": "fld_test001",
                    "name": "Test Folder",
                    "space_id": "spc_test001"
                }
            ],
            "lists": [
                {
                    "id": "lst_test001",
                    "name": "Test List",
                    "folder_id": "fld_test001"
                }
            ],
            "tasks": [],
            "relationships": []
        }
        
        with open(self.test_file_path, 'w') as f:
            json.dump(template_data, f, indent=2)

    def tearDown(self):
        """Clean up temporary files."""
        self.temp_dir.cleanup()
    
    def _reset_test_file(self):
        """Reset the test file to an empty template with tasks for relationship tests."""
        if self.test_file_path.exists():
            self.test_file_path.unlink()

        # Define sample data with tasks suitable for relationship testing
        sample_data = {
            "tasks": [
                {
                    "id": "task_a",
                    "name": "Task A",
                    "status": "to do",
                    "priority": 1
                },
                {
                    "id": "task_b",
                    "name": "Task B",
                    "status": "to do",
                    "priority": 2
                },
                {
                    "id": "task_c",
                    "name": "Task C",
                    "status": "in progress",
                    "priority": 1
                }
                # Relationships will be added in _load_fixture based on test case
            ]
        }

        # Create TaskEntity instances and save them
        for task_data in sample_data.get("tasks", []):
            checklists_list = task_data.get('checklists', []) # Extract checklist list
            task_entity_data = {
                'entity_id': task_data.get('id'), # Use entity_id
                'name': task_data.get('name', 'Default Task Name'),
                'description': task_data.get('description', ''),
                'status': task_data.get('status', 'to do'),
                'priority': task_data.get('priority', 3),
                'created_at': task_data.get('created_at'),
                'updated_at': task_data.get('updated_at'),
                'due_date': task_data.get('due_date'),
                'tags': task_data.get('tags', []),
                'assigned_to': task_data.get('assignees', []), # Use assigned_to
                'parent_id': task_data.get('parent_id'),
                'container_id': task_data.get('list_id'), # Changed from list_id to container_id
                'task_type': task_data.get('task_type', 'Task'),
                'checklist': checklists_list[0] if checklists_list and isinstance(checklists_list[0], dict) else None, # Use checklist, take first if exists and is dict
                'relationships': task_data.get('relationships', {}), # Pass relationships dict
            }
            # Filter out None values before passing to constructor
            task_entity_data = {k: v for k, v in task_entity_data.items() if v is not None}
            task = TaskEntity(**task_entity_data)
            # Use add() for new entities
            self.task_repository.add(task)

        # No need to re-initialize repository here as it's done in setUp
    
    def _load_fixture(self, fixture_name):
        """Load a specific fixture into the test file."""
        # Reset to clean state
        self._reset_test_file()
        
        # Get fixture data
        fixture_data = self.fixtures["fixtures"][fixture_name]
        
        # Add tasks to repository
        for task_dict in fixture_data["tasks"]:
            # Extract checklists before modifying task_dict
            checklists_data = task_dict.pop("checklists", [])

            # Map keys before creating entity
            entity_args = task_dict.copy()
            if 'id' in entity_args:
                entity_args['entity_id'] = entity_args.pop('id')
            if 'assignees' in entity_args:
                entity_args['assigned_to'] = entity_args.pop('assignees')
            
            # Add the first checklist dictionary to the args if it exists and is a dict
            if checklists_data and isinstance(checklists_data[0], dict):
                entity_args['checklist'] = checklists_data[0]

            # Create task entity and save to repository
            task_entity = TaskEntity(**entity_args)
            # task_entity.list_id = "lst_test001"  # Add list_id if not present - Handle carefully
            # Use add() for new entities
            self.task_repository.add(task_entity)
        
        # Add relationships
        if "relationships" in fixture_data:
            for relationship in fixture_data["relationships"]:
                source_id = relationship["source_id"]
                target_id = relationship["target_id"]
                rel_type = relationship["type"]
                self.task_service.add_relationship(source_id, target_id, rel_type)
    
    def test_single_dependency_validation(self):
        """Test completion rules for task with a single dependency."""
        # Load the single dependency fixture
        self._load_fixture("single_dependency")
        
        # Attempt to complete dependent task (should fail)
        with self.assertRaises(TaskCompletionError) as context:
            self.task_service.update_task_status("tsk_dependency_001", "complete")
        
        # Verify error message mentions the dependency
        error_msg = str(context.exception)
        self.assertIn("depends", error_msg.lower())
        self.assertIn("Dependency Task", error_msg)  # Should mention dependency task name
        
        # Complete the dependency task
        self.task_service.update_task_status("tsk_dependency_002", "complete")
        
        # Now dependent task should be completable
        self.task_service.update_task_status("tsk_dependency_001", "complete")
        
        # Verify task status
        updated_task = self.task_repository.get_by_id("tsk_dependency_001")
        self.assertEqual(updated_task.status, "complete")
    
    def test_multiple_dependencies_validation(self):
        """Test completion rules for task with multiple dependencies."""
        # Load the multiple dependencies fixture
        self._load_fixture("multiple_dependencies")
        
        # Attempt to complete dependent task (should fail)
        with self.assertRaises(TaskCompletionError) as context:
            self.task_service.update_task_status("tsk_multi_dep_001", "complete")
        
        # Verify error message mentions multiple dependencies
        error_msg = str(context.exception)
        self.assertIn("depends", error_msg.lower())
        self.assertIn("3", error_msg)  # Should mention 3 dependencies
        
        # Complete first dependency task
        self.task_service.update_task_status("tsk_multi_dep_002", "complete")
        
        # Attempt to complete dependent task again (should still fail)
        with self.assertRaises(TaskCompletionError) as context:
            self.task_service.update_task_status("tsk_multi_dep_001", "complete")
        
        # Verify error message now mentions 2 dependencies
        error_msg = str(context.exception)
        self.assertIn("depends", error_msg.lower())
        self.assertIn("2", error_msg)  # Should mention 2 dependencies
        
        # Complete remaining dependencies
        self.task_service.update_task_status("tsk_multi_dep_003", "complete")
        self.task_service.update_task_status("tsk_multi_dep_004", "complete")
        
        # Now dependent task should be completable
        self.task_service.update_task_status("tsk_multi_dep_001", "complete")
        
        # Verify task status
        updated_task = self.task_repository.get_by_id("tsk_multi_dep_001")
        self.assertEqual(updated_task.status, "complete")
    
    def test_mixed_completion_dependencies(self):
        """Test completion rules for task with some complete and some incomplete dependencies."""
        # Load the mixed completion dependencies fixture
        self._load_fixture("mixed_completion_dependencies")
        
        # Attempt to complete dependent task (should fail)
        with self.assertRaises(TaskCompletionError) as context:
            self.task_service.update_task_status("tsk_mixed_dep_001", "complete")
        
        # Verify error message mentions incomplete dependencies but not completed ones
        error_msg = str(context.exception)
        self.assertIn("depends", error_msg.lower())
        self.assertIn("2", error_msg)  # Should mention 2 dependencies (excluding the completed one)
        self.assertIn("In Progress Dependency", error_msg)  # Should mention incomplete dependency
        self.assertIn("To Do Dependency", error_msg)  # Should mention incomplete dependency
        self.assertNotIn("Completed Dependency", error_msg)  # Should NOT mention completed dependency
        
        # Complete the in-progress dependency
        self.task_service.update_task_status("tsk_mixed_dep_003", "complete")
        
        # Attempt to complete dependent task again (should still fail)
        with self.assertRaises(TaskCompletionError) as context:
            self.task_service.update_task_status("tsk_mixed_dep_001", "complete")
        
        # Verify error message now mentions only 1 dependency
        error_msg = str(context.exception)
        self.assertIn("depends", error_msg.lower())
        self.assertIn("1", error_msg)  # Should mention 1 dependency
        self.assertIn("To Do Dependency", error_msg)  # Should mention the remaining incomplete dependency
        
        # Complete the last dependency
        self.task_service.update_task_status("tsk_mixed_dep_004", "complete")
        
        # Now dependent task should be completable
        self.task_service.update_task_status("tsk_mixed_dep_001", "complete")
        
        # Verify task status
        updated_task = self.task_repository.get_by_id("tsk_mixed_dep_001")
        self.assertEqual(updated_task.status, "complete")
    
    def test_circular_dependencies(self):
        """Test detection of circular dependencies."""
        # This is more of a validation test than completion test
        # Depending on implementation, this might fail at fixture loading time
        try:
            # Try to load the circular dependencies fixture
            self._load_fixture("circular_dependencies")
            
            # If loading succeeded, trying to complete any task should detect circular dependency
            with self.assertRaises((CircularDependencyError, TaskCompletionError)) as context:
                self.task_service.update_task_status("tsk_circular_001", "complete")
            
            # Verify error message mentions circular dependency
            error_msg = str(context.exception)
            self.assertIn("circular", error_msg.lower(), "Error should mention circular dependency")
            
        except CircularDependencyError:
            # If circular dependency was detected during fixture loading, that's also acceptable
            pass
    
    def test_complex_dependency_chain(self):
        """Test completion in a complex dependency chain."""
        # Load the complex dependency chain fixture
        self._load_fixture("complex_dependency_chain")
        
        # Tasks must be completed in reverse order of the chain
        
        # Start with the last task in the chain
        self.task_service.update_task_status("tsk_chain_005", "complete")
        
        # Continue up the chain
        self.task_service.update_task_status("tsk_chain_004", "complete")
        self.task_service.update_task_status("tsk_chain_003", "complete")
        self.task_service.update_task_status("tsk_chain_002", "complete")
        
        # Finally, the first task should be completable
        self.task_service.update_task_status("tsk_chain_001", "complete")
        
        # Verify all tasks are complete
        for i in range(1, 6):
            task_id = f"tsk_chain_{i:03d}"
            task = self.task_repository.get_by_id(task_id)
            self.assertEqual(task.status, "complete")
    
    def test_blocking_relationship(self):
        """Test completion rules for 'blocks' relationship type."""
        # Load the blocks relationship fixture
        self._load_fixture("blocks_relationship")
        
        # The blocked task should not be completable until the blocking task is complete
        with self.assertRaises(TaskCompletionError) as context:
            self.task_service.update_task_status("tsk_blocks_002", "complete")
        
        # Verify error message mentions the blocking task
        error_msg = str(context.exception)
        self.assertIn("block", error_msg.lower())
        self.assertIn("Blocking Task", error_msg)  # Should mention blocking task name
        
        # Complete the blocking task
        self.task_service.update_task_status("tsk_blocks_001", "complete")
        
        # Now blocked task should be completable
        self.task_service.update_task_status("tsk_blocks_002", "complete")
        
        # Verify task status
        updated_task = self.task_repository.get_by_id("tsk_blocks_002")
        self.assertEqual(updated_task.status, "complete")
    
    def test_specific_error_messages(self):
        """Test that error messages provide specific details about relationship validation failures."""
        # Load the multiple dependencies fixture
        self._load_fixture("multiple_dependencies")
        
        # Attempt to complete dependent task
        with self.assertRaises(TaskCompletionError) as context:
            self.task_service.update_task_status("tsk_multi_dep_001", "complete")
        
        # Verify error message includes specific details
        error_msg = str(context.exception)
        self.assertIn("depends", error_msg.lower())
        self.assertIn("3", error_msg)  # Number of dependencies
        
        # Check if the message includes dependency task names
        dependency_names = [
            "Dependency Task 1",
            "Dependency Task 2",
            "Dependency Task 3"
        ]
        for name in dependency_names:
            self.assertIn(name, error_msg, f"Error should mention dependency '{name}'")

    def _create_sample_task(self, name, status="to do", priority=3, parent=None, tags=None, relationships=None, checklist=None):
        """Helper to create a task entity for tests."""
        task_data = {
            'name': name,
            'description': f"Description for {name}",
            'status': status,
            'priority': priority,
            'container_id': self.container_id, # Use class attribute
            'parent_id': parent.id if parent else None,
            'tags': tags or [],
            'relationships': relationships or {},
            'checklist': checklist or None
        }
        task = TaskEntity(**task_data)
        return self.task_repository.add(task)


if __name__ == "__main__":
    unittest.main() 