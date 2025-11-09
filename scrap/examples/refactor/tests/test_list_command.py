"""
Task: tsk_019e4306 - Update Container Hierarchy Display
Document: refactor/tests/test_list_command.py
dohcount: 1

Purpose:
    Tests for the list command with updated parent flag display.
"""

import pytest
from unittest.mock import Mock, patch
from argparse import Namespace

from refactor.cli.commands.list import ListTasksCommand
from refactor.core.manager import CoreManager

@pytest.fixture
def mock_core_manager():
    return Mock(spec=CoreManager)

@pytest.fixture
def list_command(mock_core_manager):
    return ListTasksCommand(mock_core_manager)

def test_list_command_name(list_command):
    """Test that the command name is correct."""
    assert list_command.name == "list"

def test_list_command_description(list_command):
    """Test that the command description is correct."""
    assert "List tasks" in list_command.description

def test_list_tasks_with_parent_flag(list_command, mock_core_manager):
    """Test listing tasks with parent flag display."""
    # Mock tasks with parent flags
    mock_tasks = [
        {
            "id": "task1",
            "name": "Parent Task",
            "status": "in progress",
            "priority": 1,
            "tags": ["important"],
            "is_parent": True
        },
        {
            "id": "task2",
            "name": "Child Task",
            "status": "to do",
            "priority": 2,
            "tags": [],
            "is_parent": False
        }
    ]
    mock_core_manager.get_tasks.return_value = mock_tasks
    
    args = Namespace(
        status=None,
        priority=None,
        tag=None,
        parent_only=False,
        no_truncate=True,
        no_color=True
    )
    
    with patch('builtins.print') as mock_print:
        list_command.execute(args)
        
    # Verify parent indicator is present for parent task
    mock_print.assert_called_once()
    output = mock_print.call_args[0][0]
    assert "📁 Parent Task" in output
    assert "Child Task" in output
    assert "📁" not in output.split("\n")[1]  # Second line should not have folder icon

def test_list_tasks_parent_only_filter(list_command, mock_core_manager):
    """Test filtering to show only parent tasks."""
    mock_tasks = [
        {
            "id": "task1",
            "name": "Parent Task 1",
            "status": "in progress",
            "is_parent": True
        },
        {
            "id": "task2",
            "name": "Child Task",
            "status": "to do",
            "is_parent": False
        },
        {
            "id": "task3",
            "name": "Parent Task 2",
            "status": "complete",
            "is_parent": True
        }
    ]
    mock_core_manager.get_tasks.return_value = mock_tasks
    
    args = Namespace(
        status=None,
        priority=None,
        tag=None,
        parent_only=True,
        no_truncate=True,
        no_color=True
    )
    
    with patch('builtins.print') as mock_print:
        list_command.execute(args)
        
    # Verify only parent tasks are shown
    mock_print.assert_called_once()
    output = mock_print.call_args[0][0]
    assert "Parent Task 1" in output
    assert "Parent Task 2" in output
    assert "Child Task" not in output
    assert output.count("📁") == 2  # Should have two folder icons

def test_list_tasks_with_filters(list_command, mock_core_manager):
    """Test task listing with multiple filters including parent status."""
    mock_tasks = [
        {
            "id": "task1",
            "name": "Important Parent",
            "status": "in progress",
            "priority": 1,
            "tags": ["important"],
            "is_parent": True
        },
        {
            "id": "task2",
            "name": "Regular Task",
            "status": "in progress",
            "priority": 2,
            "tags": ["important"],
            "is_parent": False
        },
        {
            "id": "task3",
            "name": "Another Parent",
            "status": "complete",
            "priority": 1,
            "tags": ["important"],
            "is_parent": True
        }
    ]
    mock_core_manager.get_tasks.return_value = mock_tasks
    
    args = Namespace(
        status="in progress",
        priority=1,
        tag="important",
        parent_only=False,
        no_truncate=True,
        no_color=True
    )
    
    with patch('builtins.print') as mock_print:
        list_command.execute(args)
        
    # Verify filtered output
    mock_print.assert_called_once()
    output = mock_print.call_args[0][0]
    assert "Important Parent" in output
    assert "📁" in output
    assert "Regular Task" not in output
    assert "Another Parent" not in output

def test_list_tasks_error_handling(list_command, mock_core_manager):
    """Test error handling in list command."""
    mock_core_manager.get_tasks.side_effect = Exception("Test error")
    
    args = Namespace(
        status=None,
        priority=None,
        tag=None,
        parent_only=False,
        no_truncate=True,
        no_color=True
    )
    
    with pytest.raises(Exception) as exc_info:
        list_command.execute(args)
    
    assert "Test error" in str(exc_info.value)

def test_list_tasks_empty_result(list_command, mock_core_manager):
    """Test displaying empty task list."""
    mock_core_manager.get_tasks.return_value = []
    
    args = Namespace(
        status=None,
        priority=None,
        tag=None,
        parent_only=False,
        no_truncate=True,
        no_color=True
    )
    
    with patch('builtins.print') as mock_print:
        list_command.execute(args)
        
    mock_print.assert_called_once_with("No tasks found") 