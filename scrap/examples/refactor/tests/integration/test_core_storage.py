#!/usr/bin/env python3
"""
Integration tests for Core-Storage module interactions.

These tests verify the proper integration between core entities/repositories
and storage components, including serialization, transaction handling,
error recovery, and cross-platform compatibility.
"""
import unittest
import tempfile
import json
import os
import threading
import time
from pathlib import Path
from concurrent.futures import ThreadPoolExecutor

# Import core entities and services
from refactor.core.entities.task_entity import TaskEntity
from refactor.core.entities.space_entity import SpaceEntity
from refactor.core.entities.folder_entity import FolderEntity
from refactor.core.entities.list_entity import ListEntity
from refactor.core.repositories.task_repository import TaskRepository
from refactor.core.repositories.space_repository import SpaceRepository
from refactor.core.repositories.folder_repository import FolderRepository
from refactor.core.repositories.list_repository import ListRepository
from refactor.core.exceptions import ValidationError, EntityNotFoundError, StorageError

# Import storage components
from refactor.storage.providers.json_storage_provider import JsonStorageProvider
from refactor.storage.serialization.json_serializer import JsonSerializer


class CoreStorageIntegrationTests(unittest.TestCase):
    """Integration tests for Core-Storage module interactions."""

    def setUp(self):
        """Set up test environment with temporary test files."""
        # Create a temporary directory for test files
        self.temp_dir = tempfile.TemporaryDirectory()
        self.temp_path = Path(self.temp_dir.name)
        
        # Create a test file path
        self.test_file_path = Path(self.temp_dir.name) / "test_core_storage.json"
        
        # Initialize storage components
        self.serializer = JsonSerializer()
        self.storage_provider = JsonStorageProvider()
        
        # Initialize repositories
        self.task_repository = TaskRepository(self.test_file_path)
        self.space_repository = SpaceRepository(self.storage_provider)
        self.folder_repository = FolderRepository(self.storage_provider)
        self.list_repository = ListRepository(self.storage_provider)
        
        # Create initial empty template structure
        template_data = {
            "spaces": [],
            "folders": [],
            "lists": [],
            "tasks": [],
            "relationships": []
        }
        
        with open(self.test_file_path, 'w') as f:
            json.dump(template_data, f, indent=2)

    def tearDown(self):
        """Clean up temporary files."""
        self.temp_dir.cleanup()
    
    def test_entity_save_and_load(self):
        """Test saving and loading entities through repositories."""
        # Create test entities
        space = SpaceEntity(
            id="spc_test001",
            name="Test Space"
        )
        
        folder = FolderEntity(
            id="fld_test001",
            name="Test Folder",
            space_id="spc_test001"
        )
        
        list_entity = ListEntity(
            id="lst_test001",
            name="Test List",
            folder_id="fld_test001"
        )
        
        task = TaskEntity(
            id="tsk_test001",
            name="Test Task",
            description="Test task description",
            status="to do",
            priority=3,
            list_id="lst_test001",
            type="Task",
            tags=["test", "integration"]
        )
        
        # Save entities
        self.space_repository.save(space)
        self.folder_repository.save(folder)
        self.list_repository.save(list_entity)
        self.task_repository.save(task)
        
        # Load entities and verify they match
        loaded_space = self.space_repository.get_by_id("spc_test001")
        loaded_folder = self.folder_repository.get_by_id("fld_test001")
        loaded_list = self.list_repository.get_by_id("lst_test001")
        loaded_task = self.task_repository.get_by_id("tsk_test001")
        
        # Verify loaded entities match original entities
        self.assertEqual(space.id, loaded_space.id)
        self.assertEqual(space.name, loaded_space.name)
        
        self.assertEqual(folder.id, loaded_folder.id)
        self.assertEqual(folder.name, loaded_folder.name)
        self.assertEqual(folder.space_id, loaded_folder.space_id)
        
        self.assertEqual(list_entity.id, loaded_list.id)
        self.assertEqual(list_entity.name, loaded_list.name)
        self.assertEqual(list_entity.folder_id, loaded_list.folder_id)
        
        self.assertEqual(task.id, loaded_task.id)
        self.assertEqual(task.name, loaded_task.name)
        self.assertEqual(task.description, loaded_task.description)
        self.assertEqual(task.status, loaded_task.status)
        self.assertEqual(task.priority, loaded_task.priority)
        self.assertEqual(task.list_id, loaded_task.list_id)
        self.assertEqual(task.type, loaded_task.type)
        self.assertEqual(task.tags, loaded_task.tags)
    
    def test_entity_update(self):
        """Test updating existing entities."""
        # Create and save test task
        task = TaskEntity(
            id="tsk_update001",
            name="Initial Task Name",
            description="Initial description",
            status="to do",
            priority=3,
            list_id="lst_test001",
            type="Task",
            tags=["test"]
        )
        self.task_repository.save(task)
        
        # Load the task, modify it, and save it again
        loaded_task = self.task_repository.get_by_id("tsk_update001")
        loaded_task.name = "Updated Task Name"
        loaded_task.description = "Updated description"
        loaded_task.status = "in progress"
        loaded_task.priority = 2
        loaded_task.tags = ["test", "updated"]
        
        self.task_repository.save(loaded_task)
        
        # Load the task again and verify the updates
        updated_task = self.task_repository.get_by_id("tsk_update001")
        self.assertEqual(updated_task.name, "Updated Task Name")
        self.assertEqual(updated_task.description, "Updated description")
        self.assertEqual(updated_task.status, "in progress")
        self.assertEqual(updated_task.priority, 2)
        self.assertEqual(updated_task.tags, ["test", "updated"])
    
    def test_entity_deletion(self):
        """Test deleting entities through repositories."""
        # Create and save test entities
        task = TaskEntity(
            id="tsk_delete001",
            name="Task to Delete",
            description="This task will be deleted",
            status="to do",
            priority=3,
            list_id="lst_test001",
            type="Task",
            tags=["test", "delete"]
        )
        self.task_repository.save(task)
        
        # Verify the task exists
        self.assertIsNotNone(self.task_repository.get_by_id("tsk_delete001"))
        
        # Delete the task
        self.task_repository.delete("tsk_delete001")
        
        # Verify the task no longer exists
        with self.assertRaises(EntityNotFoundError):
            self.task_repository.get_by_id("tsk_delete001")
    
    def test_relationship_persistence(self):
        """Test persistence of relationships between entities."""
        # Create parent and child tasks
        parent_task = TaskEntity(
            id="tsk_parent001",
            name="Parent Task",
            description="Parent task with children",
            status="to do",
            priority=2,
            list_id="lst_test001",
            type="Task",
            tags=["test", "parent"]
        )
        
        child_task1 = TaskEntity(
            id="tsk_child001",
            name="Child Task 1",
            description="First child task",
            status="to do",
            priority=3,
            list_id="lst_test001",
            parent_id="tsk_parent001",
            type="Task",
            tags=["test", "child"]
        )
        
        child_task2 = TaskEntity(
            id="tsk_child002",
            name="Child Task 2",
            description="Second child task",
            status="to do",
            priority=3,
            list_id="lst_test001",
            parent_id="tsk_parent001",
            type="Task",
            tags=["test", "child"]
        )
        
        # Save tasks
        self.task_repository.save(parent_task)
        self.task_repository.save(child_task1)
        self.task_repository.save(child_task2)
        
        # Add relationship (dependency)
        self.task_repository.add_relationship("tsk_child001", "tsk_child002", "depends_on")
        
        # Read from a fresh provider to ensure data was persisted
        new_provider = JsonStorageProvider(self.test_file_path, self.serializer)
        new_task_repo = TaskRepository(new_provider)
        
        # Verify parent-child relationships
        loaded_parent = new_task_repo.get_by_id("tsk_parent001")
        children = new_task_repo.get_children("tsk_parent001")
        
        self.assertEqual(len(children), 2)
        child_ids = [child.id for child in children]
        self.assertIn("tsk_child001", child_ids)
        self.assertIn("tsk_child002", child_ids)
        
        # Verify dependency relationship
        relationships = new_task_repo.get_relationships("tsk_child001")
        self.assertEqual(len(relationships), 1)
        
        relationship = relationships[0]
        self.assertEqual(relationship["source_id"], "tsk_child001")
        self.assertEqual(relationship["target_id"], "tsk_child002")
        self.assertEqual(relationship["type"], "depends_on")
    
    def test_serialization_special_chars(self):
        """Test serialization and deserialization with special characters."""
        # Create task with special characters
        task = TaskEntity(
            id="tsk_special001",
            name="Task with special characters: éçñ大家好",
            description="Description with newlines:\nLine 1\nLine 2\nLine with quote: \"quoted text\"\\backslash",
            status="to do",
            priority=3,
            list_id="lst_test001",
            type="Task",
            tags=["test", "special-chars"]
        )
        
        # Save and reload the task
        self.task_repository.save(task)
        loaded_task = self.task_repository.get_by_id("tsk_special001")
        
        # Verify the special characters are preserved
        self.assertEqual(loaded_task.name, "Task with special characters: éçñ大家好")
        self.assertEqual(loaded_task.description, "Description with newlines:\nLine 1\nLine 2\nLine with quote: \"quoted text\"\\backslash")
    
    def test_transaction_rollback(self):
        """Test transaction rollback on validation error."""
        # Create a valid task
        valid_task = TaskEntity(
            id="tsk_valid001",
            name="Valid Task",
            description="This is a valid task",
            status="to do",
            priority=3,
            list_id="lst_test001",
            type="Task",
            tags=["test"]
        )
        
        # Create an invalid task (missing required field)
        invalid_task = TaskEntity(
            id="tsk_invalid001",
            description="This task is missing a name",
            status="invalid_status",  # Invalid status will cause validation error
            priority=3,
            list_id="lst_test001",
            type="Task",
            tags=["test"]
        )
        
        # Save the valid task
        self.task_repository.save(valid_task)
        
        # Try to save the invalid task, which should raise a validation error
        with self.assertRaises(ValidationError):
            self.task_repository.save(invalid_task)
        
        # Verify the valid task still exists
        self.assertIsNotNone(self.task_repository.get_by_id("tsk_valid001"))
        
        # Verify the invalid task was not saved
        with self.assertRaises(EntityNotFoundError):
            self.task_repository.get_by_id("tsk_invalid001")
    
    def test_concurrent_access(self):
        """Test concurrent access to repositories."""
        # Create base entities for the test
        self.list_repository.save(ListEntity(
            id="lst_concurrent",
            name="Concurrent List",
            folder_id="fld_test001"
        ))
        
        # Function to create tasks in parallel
        def create_task(task_id):
            task = TaskEntity(
                id=f"tsk_concurrent{task_id:03d}",
                name=f"Concurrent Task {task_id}",
                description=f"Task created by thread {task_id}",
                status="to do",
                priority=3,
                list_id="lst_concurrent",
                type="Task",
                tags=["test", "concurrent"]
            )
            
            # Create a new storage provider and repository for thread safety
            thread_provider = JsonStorageProvider(self.test_file_path, JsonSerializer())
            thread_repo = TaskRepository(thread_provider)
            
            thread_repo.save(task)
            return task_id
        
        # Execute task creation concurrently
        with ThreadPoolExecutor(max_workers=5) as executor:
            results = list(executor.map(create_task, range(10)))
        
        # Verify all tasks were created
        for task_id in range(10):
            task_id_str = f"tsk_concurrent{task_id:03d}"
            task = self.task_repository.get_by_id(task_id_str)
            self.assertEqual(task.name, f"Concurrent Task {task_id}")
    
    def test_error_recovery(self):
        """Test recovery from storage errors."""
        # Create initial task
        task = TaskEntity(
            id="tsk_recovery001",
            name="Task for recovery test",
            description="This task tests error recovery",
            status="to do",
            priority=3,
            list_id="lst_test001",
            type="Task",
            tags=["test", "recovery"]
        )
        self.task_repository.save(task)
        
        # Corrupt the storage file
        with open(self.test_file_path, 'w') as f:
            f.write("{This is not valid JSON")
        
        # Create a new provider that should fail to load data
        with self.assertRaises(Exception):
            corrupt_provider = JsonStorageProvider(self.test_file_path, self.serializer)
            corrupt_repo = TaskRepository(corrupt_provider)
            corrupt_repo.get_by_id("tsk_recovery001")
        
        # Fix the file with valid but empty JSON
        with open(self.test_file_path, 'w') as f:
            json.dump({"spaces": [], "folders": [], "lists": [], "tasks": [], "relationships": []}, f)
        
        # Now we should be able to load and work with the provider again
        recovered_provider = JsonStorageProvider(self.test_file_path, self.serializer)
        recovered_repo = TaskRepository(recovered_provider)
        
        # Create a new task after recovery
        new_task = TaskEntity(
            id="tsk_recovery002",
            name="Task created after recovery",
            description="This task was created after error recovery",
            status="to do",
            priority=3,
            list_id="lst_test001",
            type="Task",
            tags=["test", "recovery"]
        )
        recovered_repo.save(new_task)
        
        # Verify the new task exists
        loaded_task = recovered_repo.get_by_id("tsk_recovery002")
        self.assertEqual(loaded_task.name, "Task created after recovery")
    
    def test_cross_platform_newlines(self):
        """Test handling of different newline characters across platforms."""
        # Create tasks with different newline formats
        unix_newlines = TaskEntity(
            id="tsk_newline_unix",
            name="Unix Newlines",
            description="Line1\nLine2\nLine3",
            status="to do",
            priority=3,
            list_id="lst_test001",
            type="Task",
            tags=["test", "newlines"]
        )
        
        windows_newlines = TaskEntity(
            id="tsk_newline_windows",
            name="Windows Newlines",
            description="Line1\r\nLine2\r\nLine3",
            status="to do",
            priority=3,
            list_id="lst_test001",
            type="Task",
            tags=["test", "newlines"]
        )
        
        mixed_newlines = TaskEntity(
            id="tsk_newline_mixed",
            name="Mixed Newlines",
            description="Line1\nLine2\r\nLine3",
            status="to do",
            priority=3,
            list_id="lst_test001",
            type="Task",
            tags=["test", "newlines"]
        )
        
        # Save all tasks
        self.task_repository.save(unix_newlines)
        self.task_repository.save(windows_newlines)
        self.task_repository.save(mixed_newlines)
        
        # Read from a fresh provider to ensure serialization/deserialization happened
        new_provider = JsonStorageProvider(self.test_file_path, self.serializer)
        new_task_repo = TaskRepository(new_provider)
        
        # Load tasks and verify newlines are handled correctly
        loaded_unix = new_task_repo.get_by_id("tsk_newline_unix")
        loaded_windows = new_task_repo.get_by_id("tsk_newline_windows")
        loaded_mixed = new_task_repo.get_by_id("tsk_newline_mixed")
        
        # Count lines to verify newlines are preserved
        self.assertEqual(loaded_unix.description.count('\n'), 2)
        
        # For Windows and mixed newlines, the specific handling depends on the implementation
        # The important part is that we don't lose lines
        self.assertGreaterEqual(loaded_windows.description.count('\n') + loaded_windows.description.count('\r\n'), 2)
        self.assertGreaterEqual(loaded_mixed.description.count('\n') + loaded_mixed.description.count('\r\n'), 2)


if __name__ == "__main__":
    unittest.main() 