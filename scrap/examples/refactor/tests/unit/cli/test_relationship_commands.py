#!/usr/bin/env python3
"""
Unit tests for the Relationship CLI commands in the refactored ClickUp JSON Manager.
Tests include both successful execution paths and error handling.
"""
import unittest
import os
import subprocess
import json
import tempfile
from pathlib import Path
from unittest.mock import patch, MagicMock
from argparse import Namespace
import shutil

from refactor.cli.commands.relationship import (
    AddRelationshipCommand,
    RemoveRelationshipCommand,
    ListRelationshipsCommand,
    CheckCyclesCommand,
    ValidateRelationshipsCommand,
    RelationshipCommand
)
from refactor.core.exceptions import EntityNotFoundError, ValidationError, CircularDependencyError


class RelationshipCommandTests(unittest.TestCase):
    """Test cases for relationship commands using direct command execution with mocks."""

    def setUp(self):
        """Set up test environment."""
        # Create mock core manager
        self.mock_core_manager = MagicMock()
        
        # Create a test file path
        self.temp_dir = tempfile.TemporaryDirectory()
        self.temp_path = Path(self.temp_dir.name)
        self.test_file = self.temp_path / "test_relationships.json"
        
        # Create mock tasks
        self.task_a = {
            "id": "tsk_test2001",
            "name": "Task A",
            "description": "Task A for testing relationships",
            "status": "in progress",
            "priority": 1,
            "tags": ["test", "relationship"],
            "blocks": [],
            "depends_on": []
        }
        
        self.task_b = {
            "id": "tsk_test2002",
            "name": "Task B",
            "description": "Task B for testing relationships",
            "status": "to do",
            "priority": 2,
            "tags": ["test"],
            "blocks": [],
            "depends_on": []
        }
        
        self.task_c = {
            "id": "tsk_test2003",
            "name": "Task C",
            "description": "Task C for testing relationships",
            "status": "to do",
            "priority": 3,
            "tags": ["test"],
            "blocks": [],
            "depends_on": []
        }
        
        # Setup default mock behavior
        self.mock_core_manager.get_task.side_effect = self._mock_get_task
        self.mock_core_manager.get_task_by_name.side_effect = self._mock_get_task_by_name
        self.mock_core_manager.add_relationship.return_value = True
        self.mock_core_manager.remove_relationship.return_value = True

    def tearDown(self):
        """Clean up test environment."""
        self.temp_dir.cleanup()
        
    def _mock_get_task(self, task_id):
        """Mock implementation of get_task."""
        if task_id == "tsk_test2001" or task_id == "Task A":
            return self.task_a
        elif task_id == "tsk_test2002" or task_id == "Task B":
            return self.task_b
        elif task_id == "tsk_test2003" or task_id == "Task C":
            return self.task_c
        else:
            raise EntityNotFoundError(f"Task not found: {task_id}")
            
    def _mock_get_task_by_name(self, name):
        """Mock implementation of get_task_by_name."""
        if name == "Task A":
            return self.task_a
        elif name == "Task B":
            return self.task_b
        elif name == "Task C":
            return self.task_c
        else:
            raise EntityNotFoundError(f"Task not found: {name}")
    
    def test_add_blocks_relationship(self):
        """Test adding a blocks relationship."""
        # Create the command
        command = AddRelationshipCommand(self.mock_core_manager)
        
        # Execute the command
        args = Namespace(
            template=str(self.test_file),
            source_task="Task A",
            relationship_type="blocks",
            target_task="Task B"
        )
        result = command.execute(args)
        
        # Verify success
        self.assertEqual(result, 0, "Adding blocks relationship should succeed")
        
        # Verify the method was called with the correct arguments
        self.mock_core_manager.add_relationship.assert_called_once_with(
            self.task_a["id"], "blocks", self.task_b["id"]
        )
    
    def test_add_depends_on_relationship(self):
        """Test adding a depends_on relationship."""
        # Create the command
        command = AddRelationshipCommand(self.mock_core_manager)
        
        # Execute the command
        args = Namespace(
            template=str(self.test_file),
            source_task="Task A",
            relationship_type="depends_on",
            target_task="Task C"
        )
        result = command.execute(args)
        
        # Verify success
        self.assertEqual(result, 0, "Adding depends_on relationship should succeed")
        
        # Verify the method was called with the correct arguments
        self.mock_core_manager.add_relationship.assert_called_once_with(
            self.task_a["id"], "depends_on", self.task_c["id"]
        )
    
    def test_circular_dependency_prevention(self):
        """Test that circular dependencies are prevented."""
        # Create the command
        command = AddRelationshipCommand(self.mock_core_manager)
        
        # Make add_relationship raise CircularDependencyError
        self.mock_core_manager.add_relationship.side_effect = CircularDependencyError(
            "Adding this relationship would create a circular dependency"
        )
        
        # Execute the command
        args = Namespace(
            template=str(self.test_file),
            source_task="Task C",
            relationship_type="depends_on",
            target_task="Task A"
        )
        result = command.execute(args)
        
        # Verify failure
        self.assertNotEqual(result, 0, "Circular dependency should be rejected")
    
    def test_remove_blocks_relationship(self):
        """Test removing a blocks relationship."""
        # Create the command
        command = RemoveRelationshipCommand(self.mock_core_manager)
        
        # Execute the command
        args = Namespace(
            template=str(self.test_file),
            source_task="Task A",
            relationship_type="blocks",
            target_task="Task B"
        )
        result = command.execute(args)
        
        # Verify success
        self.assertEqual(result, 0, "Removing blocks relationship should succeed")
        
        # Verify the method was called with the correct arguments
        self.mock_core_manager.remove_relationship.assert_called_once_with(
            self.task_a["id"], "blocks", self.task_b["id"]
        )
    
    def test_remove_depends_on_relationship(self):
        """Test removing a depends_on relationship."""
        # Create the command
        command = RemoveRelationshipCommand(self.mock_core_manager)
        
        # Execute the command
        args = Namespace(
            template=str(self.test_file),
            source_task="Task A",
            relationship_type="depends_on",
            target_task="Task C"
        )
        result = command.execute(args)
        
        # Verify success
        self.assertEqual(result, 0, "Removing depends_on relationship should succeed")
        
        # Verify the method was called with the correct arguments
        self.mock_core_manager.remove_relationship.assert_called_once_with(
            self.task_a["id"], "depends_on", self.task_c["id"]
        )
    
    def test_list_relationships(self):
        """Test listing relationships for a task."""
        # Create the command
        command = ListRelationshipsCommand(self.mock_core_manager)
        
        # Setup task relationships
        self.task_a["blocks"] = [self.task_b["id"]]
        self.task_a["depends_on"] = [self.task_c["id"]]
        
        # Setup find_tasks_blocked_by to return an empty list
        self.mock_core_manager.find_tasks_blocked_by.return_value = []
        
        # Execute the command
        args = Namespace(
            template=str(self.test_file),
            task="Task A",
            type="all"
        )
        result = command.execute(args)
        
        # Verify success
        self.assertEqual(result, 0, "Listing relationships should succeed")
    
    def test_add_nonexistent_task(self):
        """Test adding a relationship with a nonexistent task."""
        # Create the command
        command = AddRelationshipCommand(self.mock_core_manager)
        
        # Make get_task and get_task_by_name raise EntityNotFoundError for nonexistent task
        def mock_get_task_side_effect(task_id):
            if task_id == "Nonexistent Task":
                raise EntityNotFoundError(f"Task not found: {task_id}")
            return self._mock_get_task(task_id)
            
        def mock_get_task_by_name_side_effect(name):
            if name == "Nonexistent Task":
                raise EntityNotFoundError(f"Task not found: {name}")
            return self._mock_get_task_by_name(name)
            
        self.mock_core_manager.get_task.side_effect = mock_get_task_side_effect
        self.mock_core_manager.get_task_by_name.side_effect = mock_get_task_by_name_side_effect
        
        # Execute the command
        args = Namespace(
            template=str(self.test_file),
            source_task="Nonexistent Task",
            relationship_type="blocks",
            target_task="Task B"
        )
        result = command.execute(args)
        
        # Verify failure
        self.assertNotEqual(result, 0, "Adding relationship with nonexistent task should fail")
    
    def test_add_self_relationship(self):
        """Test adding a relationship to self."""
        # Create the command
        command = AddRelationshipCommand(self.mock_core_manager)
        
        # Make add_relationship raise ValidationError for self-relationship
        self.mock_core_manager.add_relationship.side_effect = ValidationError(
            "Cannot create relationship with the same task"
        )
        
        # Execute the command
        args = Namespace(
            template=str(self.test_file),
            source_task="Task A",
            relationship_type="blocks",
            target_task="Task A"
        )
        result = command.execute(args)
        
        # Verify failure
        self.assertNotEqual(result, 0, "Adding self-relationship should fail")


class RelationshipCommandUnitTests(unittest.TestCase):
    """Unit tests for relationship command classes."""
    
    def setUp(self):
        """Set up test environment."""
        # Create mock service and context
        self.mock_core_manager = MagicMock()
        
        # Create test data
        self.test_args = {
            "template": "test_template.json",
            "source_task": "Task A",
            "relationship_type": "blocks",
            "target_task": "Task B"
        }
    
    def test_add_relationship_command(self):
        """Test AddRelationshipCommand execution."""
        # Set up command with mock context
        command = AddRelationshipCommand(self.mock_core_manager)
        
        # Mock task entities
        source_task = {"id": "tsk_test2001", "name": "Task A"}
        target_task = {"id": "tsk_test2002", "name": "Task B"}
        
        # Setup mocks for task retrieval
        self.mock_core_manager.get_task.side_effect = Exception("Not found by ID")
        self.mock_core_manager.get_task_by_name.side_effect = [source_task, target_task]
        
        # Execute command
        result = command.execute(Namespace(**self.test_args))
        
        # Verify success and service method call
        self.assertEqual(result, 0, "Command should return zero for success")
        self.mock_core_manager.add_relationship.assert_called_once_with(
            source_task["id"], self.test_args["relationship_type"], target_task["id"]
        )
    
    def test_add_relationship_error_handling(self):
        """Test AddRelationshipCommand error handling."""
        # Set up command with mock context
        command = AddRelationshipCommand(self.mock_core_manager)
        
        # Make task retrieval fail
        self.mock_core_manager.get_task.side_effect = Exception("Not found by ID")
        self.mock_core_manager.get_task_by_name.side_effect = Exception("Task not found")
        
        # Execute command should print error
        result = command.execute(Namespace(**self.test_args))
        
        # Verify result is error code
        self.assertEqual(result, 1, "Command should return non-zero for errors")
    
    def test_remove_relationship_command(self):
        """Test RemoveRelationshipCommand execution."""
        # Set up command with mock context
        command = RemoveRelationshipCommand(self.mock_core_manager)
        args = {
            "template": "test_template.json",
            "source_task": "Task A",
            "relationship_type": "blocks",
            "target_task": "Task B"
        }
        
        # Mock task entities
        source_task = {"id": "tsk_test2001", "name": "Task A"}
        target_task = {"id": "tsk_test2002", "name": "Task B"}
        
        # Setup mocks for task retrieval
        self.mock_core_manager.get_task.side_effect = Exception("Not found by ID")
        self.mock_core_manager.get_task_by_name.side_effect = [source_task, target_task]
        
        # Execute command
        result = command.execute(Namespace(**args))
        
        # Verify success and service method call
        self.assertEqual(result, 0, "Command should return zero for success")
        self.mock_core_manager.remove_relationship.assert_called_once_with(
            source_task["id"], args["relationship_type"], target_task["id"]
        )
    
    def test_list_relationships_command(self):
        """Test ListRelationshipsCommand execution."""
        # Set up command with mock context
        command = ListRelationshipsCommand(self.mock_core_manager)
        args = {
            "template": "test_template.json",
            "task": "Task A",
            "type": "all"
        }
        
        # Mock task entity
        task = {"id": "tsk_test2001", "name": "Task A"}
        
        # Setup mock for task retrieval
        self.mock_core_manager.get_task.side_effect = Exception("Not found by ID")
        self.mock_core_manager.get_task_by_name.return_value = task
        
        # Execute command
        result = command.execute(Namespace(**args))
        
        # Verify success
        self.assertEqual(result, 0, "Command should return zero for success")
    
    def test_list_specific_relationship_type(self):
        """Test ListRelationshipsCommand with specific relationship type."""
        # Set up command with mock context
        command = ListRelationshipsCommand(self.mock_core_manager)
        args = {
            "template": "test_template.json",
            "task": "Task A",
            "type": "blocks"
        }
        
        # Mock task entity
        task = {"id": "tsk_test2001", "name": "Task A"}
        
        # Setup mock for task retrieval
        self.mock_core_manager.get_task.side_effect = Exception("Not found by ID")
        self.mock_core_manager.get_task_by_name.return_value = task
        
        # Execute command
        result = command.execute(Namespace(**args))
        
        # Verify success
        self.assertEqual(result, 0, "Command should return zero for success")


if __name__ == "__main__":
    unittest.main() 