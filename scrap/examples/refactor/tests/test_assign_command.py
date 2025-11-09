"""
Task: tsk_a3f74d5d - Implement List Assignment Command
Document: refactor/tests/test_assign_command.py
dohcount: 1

Purpose:
    Tests for the task assignment command functionality.
"""
import pytest
from argparse import Namespace
from unittest.mock import Mock, patch

from refactor.cli.commands.assign import AssignToListCommand
from refactor.core.entities.task_entity import TaskEntity
from refactor.core.entities.list_entity import ListEntity
from refactor.cli.error_handling import CLIError, ErrorCode


def test_assign_command_creation():
    """Test basic command creation."""
    core_manager = Mock()
    command = AssignToListCommand(core_manager)
    assert command.name == "assign"
    assert command.description == "Assign a task to a list"


def test_assign_command_parser_configuration():
    """Test command parser configuration."""
    core_manager = Mock()
    command = AssignToListCommand(core_manager)
    parser = Mock()
    command.configure_parser(parser)
    
    # Verify arguments were added
    parser.add_argument.assert_any_call("task_id", help="ID of the task to assign")
    parser.add_argument.assert_any_call("list_id", help="ID of the list to assign the task to")
    parser.add_argument.assert_any_call(
        "--force",
        action="store_true",
        help="Force assignment even if task has existing container"
    )


def test_assign_task_to_list_success():
    """Test successful task assignment to list."""
    # Setup mocks
    core_manager = Mock()
    task = TaskEntity(name="Test Task", entity_id="tsk_123")
    target_list = ListEntity(name="Target List", entity_id="lst_456", space="Space", folder="Folder")
    
    core_manager.task_service.get_task.return_value = task
    core_manager.list_service.get_list.return_value = target_list
    
    # Create command and execute
    command = AssignToListCommand(core_manager)
    args = Namespace(task_id="tsk_123", list_id="lst_456", force=False)
    result = command.execute(args)
    
    # Verify results
    assert result == 0
    assert task.space == target_list.space
    assert task.folder == target_list.folder
    assert task.list_name == target_list.name
    core_manager.task_service.update_task.assert_called_once_with(task)


def test_assign_task_not_found():
    """Test error when task is not found."""
    # Setup mocks
    core_manager = Mock()
    core_manager.task_service.get_task.return_value = None
    
    # Create command and execute
    command = AssignToListCommand(core_manager)
    args = Namespace(task_id="tsk_123", list_id="lst_456", force=False)
    result = command.execute(args)
    
    # Verify results
    assert result == 1
    core_manager.task_service.update_task.assert_not_called()


def test_assign_list_not_found():
    """Test error when list is not found."""
    # Setup mocks
    core_manager = Mock()
    task = TaskEntity(name="Test Task", entity_id="tsk_123")
    core_manager.task_service.get_task.return_value = task
    core_manager.list_service.get_list.return_value = None
    
    # Create command and execute
    command = AssignToListCommand(core_manager)
    args = Namespace(task_id="tsk_123", list_id="lst_456", force=False)
    result = command.execute(args)
    
    # Verify results
    assert result == 1
    core_manager.task_service.update_task.assert_not_called()


def test_assign_task_already_assigned():
    """Test error when task is already assigned without force flag."""
    # Setup mocks
    core_manager = Mock()
    task = TaskEntity(name="Test Task", entity_id="tsk_123", list_name="Current List")
    target_list = ListEntity(name="Target List", entity_id="lst_456", space="Space", folder="Folder")
    
    core_manager.task_service.get_task.return_value = task
    core_manager.list_service.get_list.return_value = target_list
    
    # Create command and execute
    command = AssignToListCommand(core_manager)
    args = Namespace(task_id="tsk_123", list_id="lst_456", force=False)
    result = command.execute(args)
    
    # Verify results
    assert result == 1
    core_manager.task_service.update_task.assert_not_called()


def test_assign_task_force_reassignment():
    """Test successful task reassignment with force flag."""
    # Setup mocks
    core_manager = Mock()
    task = TaskEntity(
        name="Test Task",
        entity_id="tsk_123",
        space="Old Space",
        folder="Old Folder",
        list_name="Old List"
    )
    target_list = ListEntity(name="Target List", entity_id="lst_456", space="Space", folder="Folder")
    
    core_manager.task_service.get_task.return_value = task
    core_manager.list_service.get_list.return_value = target_list
    
    # Create command and execute
    command = AssignToListCommand(core_manager)
    args = Namespace(task_id="tsk_123", list_id="lst_456", force=True)
    result = command.execute(args)
    
    # Verify results
    assert result == 0
    assert task.space == target_list.space
    assert task.folder == target_list.folder
    assert task.list_name == target_list.name
    core_manager.task_service.update_task.assert_called_once_with(task)


def test_assign_task_unexpected_error():
    """Test handling of unexpected errors during assignment."""
    # Setup mocks
    core_manager = Mock()
    task = TaskEntity(name="Test Task", entity_id="tsk_123")
    target_list = ListEntity(name="Target List", entity_id="lst_456", space="Space", folder="Folder")
    
    core_manager.task_service.get_task.return_value = task
    core_manager.list_service.get_list.return_value = target_list
    core_manager.task_service.update_task.side_effect = Exception("Unexpected error")
    
    # Create command and execute
    command = AssignToListCommand(core_manager)
    args = Namespace(task_id="tsk_123", list_id="lst_456", force=False)
    result = command.execute(args)
    
    # Verify results
    assert result == 1 