"""
Unit tests for task-related CLI commands.

This module contains tests for all task-related commands including:
- CreateTaskCommand
- ShowTaskCommand
- ListTasksCommand
- UpdateTaskCommand
- DeleteTaskCommand
- CommentTaskCommand
"""
import unittest
from unittest.mock import Mock, patch, MagicMock, call
from argparse import Namespace
import json
from typing import Dict, List, Optional
from dataclasses import dataclass
from io import StringIO
from datetime import datetime
from unittest import mock

from refactor.cli.commands.task import (
    CreateTaskCommand,
    ShowTaskCommand,
    ListTasksCommand,
    UpdateTaskCommand,
    DeleteTaskCommand,
    CommentTaskCommand,
    TaskCommand
)
from refactor.core.entities.task_entity import TaskStatus, TaskPriority
from refactor.core.interfaces.core_manager import CoreManager
from refactor.cli.error_handling import CLIError, ErrorCode

@dataclass
class TaskEntity:
    """Mock task entity for testing."""
    id: str
    name: str
    description: str = ""
    status: str = TaskStatus.TO_DO.value
    priority: str = TaskPriority.NORMAL.value
    tags: list = None
    parent_id: str = None
    list_id: str = None
    comments: list = None
    type: str = "Task"
    created_at: str = None
    updated_at: str = None
    checklists: list = None
    depends_on: list = None
    blocks: list = None
    linked_to: list = None

    def __post_init__(self):
        self.tags = self.tags or []
        self.comments = self.comments or []
        self.checklists = self.checklists or []
        self.depends_on = self.depends_on or []
        self.blocks = self.blocks or []
        self.linked_to = self.linked_to or []
        if not self.created_at:
            self.created_at = datetime.now().isoformat()
        if not self.updated_at:
            self.updated_at = datetime.now().isoformat()

    def to_dict(self):
        """Convert task to dictionary."""
        return {
            "id": self.id,
            "name": self.name,
            "description": self.description,
            "status": self.status,
            "priority": self.priority,
            "tags": self.tags,
            "parent_id": self.parent_id,
            "list_id": self.list_id,
            "comments": self.comments,
            "type": self.type,
            "created_at": self.created_at,
            "updated_at": self.updated_at,
            "checklists": self.checklists,
            "depends_on": self.depends_on,
            "blocks": self.blocks,
            "linked_to": self.linked_to
        }

class TaskStatusEncoder(json.JSONEncoder):
    """Custom JSON encoder for TaskStatus and TaskPriority enums."""
    def default(self, obj):
        if isinstance(obj, (TaskStatus, TaskPriority)):
            return str(obj.value)
        elif isinstance(obj, TaskEntity):
            return obj.to_dict()
        return super().default(obj)

class CommandResult:
    """Wrapper for command execution results."""
    def __init__(self, exit_code, output=""):
        self.exit_code = exit_code
        self.output = output

    @classmethod
    def success(cls, output=""):
        return cls(0, output)

    @classmethod
    def error(cls, output=""):
        return cls(1, output)

class MockCoreManager:
    """Mock core manager for testing."""

    def __init__(self):
        """Initialize the mock core manager."""
        self.tasks = {}
        self.comments = {}
        self.next_task_id = 1
        self.data = {"tasks": []} 
        # Add sort configuration
        self.sort_options = {
            "sort_by": "priority",
            "sort_reverse": True
        }
    
    def initialize(self, template_file):
        """Initialize with a template file (mock implementation)."""
        # This method is called by commands but doesn't need to do anything in tests
        # as the mock data is set up directly in the test methods
        return True

    def create_task(self, name: str, description: str = None, status: str = "to do",
                   priority: int = 3, tags: List[str] = None, parent_id: str = None, task_type: str = "task") -> Dict:
        """Create a new task."""
        task_id = f"tsk_{self.next_task_id:08d}"
        self.next_task_id += 1

        task = {
            'id': task_id,
            'name': name,
            'description': description,
            'status': status,
            'priority': priority,
            'tags': tags or [],
            'parent_id': parent_id,
            'task_type': task_type
        }
        self.tasks[task_id] = task
        return task

    def get_task(self, task_id: str) -> Dict:
        """Get a task by ID."""
        if task_id not in self.tasks:
            raise CLIError(f"Task not found: {task_id}", ErrorCode.TASK_NOT_FOUND)
        return self.tasks[task_id]

    def get_task_by_name(self, name: str) -> Dict:
        """Get a task by name."""
        for task in self.tasks.values():
            if task['name'] == name:
                return task
        raise CLIError(f"Task not found: {name}", ErrorCode.TASK_NOT_FOUND)

    def find_task_by_id_or_name(self, id_or_name: str) -> Dict:
        """Find a task by ID or name."""
        try:
            # First try to get by ID
            return self.get_task(id_or_name)
        except CLIError:
            try:
                # If that fails, try to get by name
                return self.get_task_by_name(id_or_name)
            except CLIError:
                return None  # Return None instead of raising to match implementation in commands

    def update_task(self, task_id: str, task_data: Dict = None, **kwargs) -> Dict:
        """Update a task with dictionary or keyword arguments."""
        if task_id not in self.tasks:
            raise CLIError(f"Task not found: {task_id}", ErrorCode.TASK_NOT_FOUND)
        
        # If task_data is provided, update with it
        if task_data:
            self.tasks[task_id].update(task_data)
        
        # Update with any keyword arguments
        if kwargs:
            self.tasks[task_id].update(kwargs)
            
        return self.tasks[task_id]
    
    def update_task_status(self, task_id: str, status: str, comment: str = None, force: bool = False) -> Dict:
        """Update task status with optional comment."""
        if task_id not in self.tasks:
            raise CLIError(f"Task not found: {task_id}", ErrorCode.TASK_NOT_FOUND)
        
        task = self.tasks[task_id]
        task['status'] = status
        
        # Add comment if provided
        if comment:
            self.add_comment(task_id, comment)
            
        return task

    def delete_task(self, task_id: str, cascade: bool = False, force: bool = False) -> bool:
        """Delete a task with optional cascade."""
        if task_id not in self.tasks:
            raise CLIError(f"Task not found: {task_id}", ErrorCode.TASK_NOT_FOUND)
        
        # Handle cascade deletion (delete any subtasks)
        if cascade:
            subtasks = self.get_subtasks(task_id)
            for subtask in subtasks:
                del self.tasks[subtask['id']]
        
        del self.tasks[task_id]
        return True

    def get_subtasks(self, task_id: str) -> List[Dict]:
        """Get subtasks for a task."""
        return [task for task in self.tasks.values() if task.get('parent_id') == task_id]
    
    def add_tag(self, task_id: str, tag: str) -> Dict:
        """Add a tag to a task."""
        if task_id not in self.tasks:
            raise CLIError(f"Task not found: {task_id}", ErrorCode.TASK_NOT_FOUND)
        
        if 'tags' not in self.tasks[task_id]:
            self.tasks[task_id]['tags'] = []
        
        if tag not in self.tasks[task_id]['tags']:
            self.tasks[task_id]['tags'].append(tag)
        
        return self.tasks[task_id]
    
    def remove_tag(self, task_id: str, tag: str) -> Dict:
        """Remove a tag from a task."""
        if task_id not in self.tasks:
            raise CLIError(f"Task not found: {task_id}", ErrorCode.TASK_NOT_FOUND)
        
        if 'tags' in self.tasks[task_id] and tag in self.tasks[task_id]['tags']:
            self.tasks[task_id]['tags'].remove(tag)
        
        return self.tasks[task_id]

    def get_task_relationships(self, task_id: str) -> Dict:
        """Get relationships for a task."""
        if task_id not in self.tasks:
            raise CLIError(f"Task not found: {task_id}", ErrorCode.TASK_NOT_FOUND)
            
        # Return empty relationship objects by default
        relationships = {
            "depends_on": [],
            "blocks": [],
            "linked_to": []
        }
        
        # If the task has relationship data, use it
        task = self.tasks[task_id]
        if "depends_on" in task and task["depends_on"]:
            relationships["depends_on"] = task["depends_on"]
        if "blocks" in task and task["blocks"]:
            relationships["blocks"] = task["blocks"]
        if "linked_to" in task and task["linked_to"]:
            relationships["linked_to"] = task["linked_to"]
            
        return relationships

    def get_all_tasks(self) -> List[Dict]:
        """Get all tasks."""
        return list(self.tasks.values())

    def get_tasks_by_filter(self, status=None, priority=None, tags=None, parent_id=None):
        """Filter tasks by given criteria."""
        tasks = self.get_all_tasks()
        
        # Apply filters if specified
        if status:
            tasks = [t for t in tasks if t.get('status') == status]
        if priority:
            tasks = [t for t in tasks if t.get('priority') == int(priority)]
        if tags:
            tag_list = [tag.strip() for tag in tags.split(',')]
            tasks = [t for t in tasks if any(tag in t.get('tags', []) for tag in tag_list)]
        if parent_id:
            tasks = [t for t in tasks if t.get('parent_id') == parent_id]
            
        return tasks

    def add_comment(self, task_id: str, comment: Dict) -> Dict:
        """Add a comment to a task."""
        if task_id not in self.tasks:
            raise CLIError(f"Task not found: {task_id}", ErrorCode.TASK_NOT_FOUND)
        if task_id not in self.comments:
            self.comments[task_id] = []
        self.comments[task_id].append(comment)
        return comment
        
    def add_comment_to_task(self, task_id: str, text: str, author: str = None) -> Dict:
        """Add a comment to a task with text and author."""
        if task_id not in self.tasks:
            raise CLIError(f"Task not found: {task_id}", ErrorCode.TASK_NOT_FOUND)
        
        comment = {
            "text": text,
            "author": author or "Anonymous",
            "date": datetime.now().isoformat()
        }
        
        if task_id not in self.comments:
            self.comments[task_id] = []
        
        self.comments[task_id].append(comment)
        return comment

    def save(self):
        """Mock save method."""
        # We need to update our mock data structure to match what's expected
        self.data = {"tasks": list(self.tasks.values())}
        # Call json.dump to ensure it's recorded in the test
        with open("test.json", "w") as f:
            json.dump(self.data, f, indent=2)
        return True

    def find_task(self, id_or_name: str) -> Optional[Dict]:
        """Mock find_task method."""
        try:
            return self.get_task(id_or_name)
        except CLIError:
            try:
                return self.get_task_by_name(id_or_name)
            except CLIError:
                return None

    def get_task_by_id_or_name(self, id_or_name: str) -> Dict:
        """Get a task by ID or name."""
        try:
            return self.get_task(id_or_name)
        except CLIError:
            try:
                return self.get_task_by_name(id_or_name)
            except CLIError:
                return None

class TaskCommandTests(unittest.TestCase):
    """Test cases for task-related CLI commands."""
    
    def setUp(self):
        """Set up test environment."""
        self.core_manager = MockCoreManager()
        self.args = Namespace()
        self.printed_output = []
        
        # Mock print function to capture output - handle empty print() calls
        self.mock_print_patcher = mock.patch('builtins.print')
        self.mock_print = self.mock_print_patcher.start()
        # Use this approach to handle both print() and print(arg1, arg2, ...)
        self.mock_print.side_effect = lambda *args, **kwargs: self.printed_output.append(' '.join(str(arg) for arg in args) if args else '')
        
        # Mock file operations
        self.mock_file = mock.patch('builtins.open', mock.mock_open(read_data='{"tasks": []}')).start()
        self.mock_json = mock.patch('json.load').start()
        self.mock_json_dump = mock.patch('json.dump').start()
        self.mock_json.return_value = {"tasks": []}
    
    def tearDown(self):
        """Clean up test environment."""
        self.mock_print_patcher.stop()
        mock.patch.stopall()
    
    def test_create_task_basic(self):
        """Test basic task creation."""
        self.args.name = "Test Task"
        self.args.description = "Test Description"
        self.args.status = "to do"
        self.args.priority = 4  # Changed to match command's mapping (4=Low)
        self.args.tags = "test,tag"
        self.args.parent = None
        self.args.list = None
        self.args.template = "test.json"  # This should match the expected parameter name
        self.args.task_type = "task"
        
        # Mock file operations for template
        self.mock_json.return_value = {"tasks": []}
        
        cmd = CreateTaskCommand(self.core_manager)
        result = cmd.execute(self.args)
        output = '\n'.join(self.printed_output)
        print(f"\nCreate task output: {output}")  # Debug output
        
        # Verify command succeeded
        self.assertEqual(result, 0, f"Command failed with output: {output}")
        
        # Verify task was created correctly
        task = next(iter(self.core_manager.tasks.values()))
        self.assertEqual(task['name'], "Test Task")
        self.assertEqual(task['description'], "Test Description")
        self.assertEqual(task['status'], "to do")
        self.assertEqual(task['priority'], 4)
        self.assertEqual(task['tags'], ["test", "tag"])
        
        # Verify template file was updated
        self.mock_json_dump.assert_called_once()
        saved_data = self.mock_json_dump.call_args[0][0]
        self.assertEqual(len(saved_data['tasks']), 1)
        saved_task = saved_data['tasks'][0]
        self.assertEqual(saved_task['name'], "Test Task")
        self.assertEqual(saved_task['description'], "Test Description")
        self.assertEqual(saved_task['status'], "to do")
        self.assertEqual(saved_task['priority'], 4)
        self.assertEqual(saved_task['tags'], ["test", "tag"])
        self.assertEqual(saved_task['task_type'], "task")
    
    def test_create_task_with_parent(self):
        """Test task creation with parent task."""
        parent = self.core_manager.create_task("Parent Task")
        
        self.args.name = "Child Task"
        self.args.parent = parent['id']
        self.args.status = "in progress"
        self.args.description = None
        self.args.priority = None
        self.args.tags = None
        self.args.list = None
        self.args.template = "test.json"  # This should match the expected parameter name
        self.args.task_type = "task"
        
        # Mock file operations for template
        self.mock_json.return_value = {"tasks": [parent]}
        
        cmd = CreateTaskCommand(self.core_manager)
        result = cmd.execute(self.args)
        output = '\n'.join(self.printed_output)
        print(f"\nCreate task with parent output: {output}")  # Debug output
        
        # Verify command succeeded
        self.assertEqual(result, 0, f"Command failed with output: {output}")
        
        # Verify child task was created correctly
        tasks = list(self.core_manager.tasks.values())
        child_task = next(t for t in tasks if t['id'] != parent['id'])
        self.assertEqual(child_task['name'], "Child Task")
        self.assertEqual(child_task['status'], "in progress")
        self.assertEqual(child_task['parent_id'], parent['id'])
        
        # Verify template file was updated
        self.mock_json_dump.assert_called_once()
        saved_data = self.mock_json_dump.call_args[0][0]
        self.assertEqual(len(saved_data['tasks']), 2)
        saved_child = next(t for t in saved_data['tasks'] if t['id'] != parent['id'])
        self.assertEqual(saved_child['name'], "Child Task")
        self.assertEqual(saved_child['status'], "in progress")
        self.assertEqual(saved_child['parent_id'], parent['id'])
        self.assertEqual(saved_child['task_type'], "task")
    
    def test_show_task(self):
        """Test showing task details."""
        task = self.core_manager.create_task(
            "Test Task",
            description="Test Description",
            status="in progress",
            priority=2  # High priority
        )
        
        # Mock file content with task data
        self.mock_file.return_value.__enter__.return_value = StringIO(
            json.dumps({"tasks": [task]}, cls=TaskStatusEncoder)
        )
        
        self.args.task_name = task['id']
        self.args.details = True
        self.args.template = "test.json"
        self.args.json = False
        
        cmd = ShowTaskCommand(self.core_manager)
        result = cmd.execute(self.args)
        output = '\n'.join(self.printed_output)
        
        self.assertEqual(result, 0, f"Command failed with output: {output}")
        self.assertIn(task['name'], output)
        self.assertIn(task['id'], output)
        self.assertIn(task['status'], output)
    
    def test_show_nonexistent_task(self):
        """Test showing a nonexistent task."""
        # Mock empty file content
        self.mock_file.return_value.__enter__.return_value = StringIO(
            json.dumps({"tasks": []})
        )
        
        self.args.task_name = "tsk_nonexistent"
        self.args.details = False
        self.args.template = "test.json"
        self.args.json = False
        
        cmd = ShowTaskCommand(self.core_manager)
        result = cmd.execute(self.args)
        
        self.assertNotEqual(result, 0, "Command should fail with nonexistent task")
    
    def test_update_task_status(self):
        """Test updating task status."""
        task = self.core_manager.create_task("Test Task", status="to do")
        
        self.args.task_name = task['id']
        self.args.name = None
        self.args.description = None
        self.args.status = "in progress"
        self.args.status_option = None
        self.args.priority = None
        self.args.tags = None
        self.args.comment = None
        self.args.template = "test.json"
        self.args.force = True  # Force update to skip confirmation
        self.args.task_type = "task"
        
        # Mock file operations for template
        self.mock_json.return_value = {"tasks": [task]}
        
        # TODO: UpdateTaskCommand seems to expect find_task or similar on CoreManager.
        # Error: AttributeError: 'MockCoreManager' object has no attribute 'find_task'
        # Update MockCoreManager or the command's logic.
        cmd = UpdateTaskCommand(self.core_manager)
        result = cmd.execute(self.args)
        output = '\n'.join(self.printed_output)
        print(f"\nUpdate task status output: {output}")  # Debug output
        
        # Verify command succeeded
        # TODO: Failing test. Likely due to AttributeError in command execution.
        self.assertEqual(result, 0, f"Command failed with output: {output}")
        
        # Verify status was updated
        updated_task = self.core_manager.get_task(task['id'])
        self.assertEqual(updated_task['status'], "in progress")
        self.assertEqual(updated_task['task_type'], "task")
    
    def test_update_task_priority(self):
        """Test updating task priority."""
        task = self.core_manager.create_task("Test Task", priority=3)  # Normal priority
        
        self.args.task_name = task['id']
        self.args.name = None
        self.args.description = None
        self.args.status = None
        self.args.status_option = None
        self.args.priority = 2  # High priority
        self.args.tags = None
        self.args.comment = None
        self.args.template = "test.json"
        self.args.force = True  # Force update to skip confirmation
        self.args.task_type = "task"
        
        # Mock file operations for template
        self.mock_json.return_value = {"tasks": [task]}
        
        # TODO: UpdateTaskCommand seems to expect find_task or similar on CoreManager.
        # Error: AttributeError: 'MockCoreManager' object has no attribute 'find_task'
        # Update MockCoreManager or the command's logic.
        cmd = UpdateTaskCommand(self.core_manager)
        result = cmd.execute(self.args)
        output = '\n'.join(self.printed_output)
        
        # TODO: Failing test. Likely due to AttributeError in command execution.
        self.assertEqual(result, 0, f"Command failed with output: {output}")
        
        # Verify priority was updated
        updated_task = self.core_manager.get_task(task['id'])
        self.assertEqual(updated_task['priority'], 2)
        self.assertEqual(updated_task['task_type'], "task")
    
    def test_delete_task(self):
        """Test task deletion."""
        task = self.core_manager.create_task("Test Task")
        
        self.args.task_name = task['id']
        self.args.cascade = False
        self.args.no_confirm = True
        self.args.force = False
        self.args.template = "test.json"  # Add template parameter
        self.args.task_type = "task"
        
        # Mock file operations for template
        self.mock_json.return_value = {"tasks": [task]}
        
        cmd = DeleteTaskCommand(self.core_manager)
        with patch('builtins.input', return_value='y'):
            result = cmd.execute(self.args)
        
        # Verify command succeeded
        self.assertEqual(result, 0, "Command should succeed with valid task")
        
        # Verify task was deleted from core manager
        with self.assertRaises(Exception):
            self.core_manager.get_task(task['id'])
    
    def test_delete_nonexistent_task(self):
        """Test deletion of nonexistent task."""
        self.args.task_name = "tsk_nonexistent"
        self.args.cascade = False
        self.args.no_confirm = True
        self.args.force = False
        self.args.template = "test.json"  # Add template parameter
        self.args.task_type = "task"
        
        # Mock file operations for template
        self.mock_json.return_value = {"tasks": []}
        
        cmd = DeleteTaskCommand(self.core_manager)
        result = cmd.execute(self.args)
        
        # Verify command failed
        self.assertNotEqual(result, 0, "Command should fail with nonexistent task")


class TestListTasksCommand(unittest.TestCase):
    """Test cases for listing tasks."""
    
    def setUp(self):
        """Set up test environment."""
        self.core_manager = MockCoreManager()
        self.command = ListTasksCommand(self.core_manager)
        
        # Mock file operations
        self.mock_file_patcher = patch("builtins.open")
        self.mock_file = self.mock_file_patcher.start()
        
        # Mock print function and capture output
        self.print_patcher = patch('builtins.print')
        self.mock_print = self.print_patcher.start()
        self.printed_output = []
        self.mock_print.side_effect = lambda *args, **kwargs: self.printed_output.append(' '.join(str(arg) for arg in args))
        
        # Create some test tasks
        self.tasks = [
            self.core_manager.create_task("Task 1", status=TaskStatus.TO_DO, priority=TaskPriority.HIGH, tags=["important"]),
            self.core_manager.create_task("Task 2", status=TaskStatus.IN_PROGRESS, priority=TaskPriority.NORMAL),
            self.core_manager.create_task("Task 3", status=TaskStatus.COMPLETE, priority=TaskPriority.LOW)
        ]
        
        # Mock file content with tasks
        self.mock_file.return_value.__enter__.return_value = StringIO(
            json.dumps({"tasks": self.tasks}, cls=TaskStatusEncoder)
        )
        
        # Initialize the core manager
        self.core_manager.initialize("test.json")
        
    def tearDown(self):
        """Clean up test environment."""
        self.print_patcher.stop()
        self.mock_file_patcher.stop()
    
    def test_list_all_tasks(self):
        """Test listing all tasks."""
        args = Namespace(
            template="test.json",
            status=None,
            priority=None,
            tags=None,
            parent=None,
            list=None,
            use_config=False,
            tree=False,
            show_relationships=False,
            json=False,
            sort_by=None,
            asc=False,
            show_id=False,
            complete=False,
            flat=True,
            colorize=True,
            show_descriptions=False,
            description_length=80,
            show_comments=0
        )
        
        result = CommandResult(self.command.execute(args), '\n'.join(self.printed_output))
        
        self.assertEqual(result.exit_code, 0)
        self.assertEqual(len(self.core_manager.tasks), 3)
    
    def test_list_tasks_by_status(self):
        """Test listing tasks filtered by status."""
        args = Namespace(
            template="test.json",
            status="in progress",
            priority=None,
            tags=None,
            parent=None,
            list=None,
            use_config=False,
            tree=False,
            show_relationships=False,
            json=False,
            sort_by=None,
            asc=False,
            show_id=False,
            complete=False,
            flat=True,
            colorize=True,
            show_descriptions=False,
            description_length=80,
            show_comments=0
        )
        
        result = CommandResult(self.command.execute(args), '\n'.join(self.printed_output))
        
        self.assertEqual(result.exit_code, 0)
        self.mock_print.assert_called()
    
    def test_list_tasks_by_priority(self):
        """Test listing tasks filtered by priority."""
        args = Namespace(
            template="test.json",
            status=None,
            priority="2",
            tags=None,
            parent=None,
            list=None,
            use_config=False,
            tree=False,
            show_relationships=False,
            json=False,
            sort_by=None,
            asc=False,
            show_id=False,
            complete=False,
            flat=True,
            colorize=True,
            show_descriptions=False,
            description_length=80,
            show_comments=0
        )
        
        result = CommandResult(self.command.execute(args), '\n'.join(self.printed_output))
        
        self.assertEqual(result.exit_code, 0)
        self.mock_print.assert_called()
    
    def test_list_tasks_by_tag(self):
        """Test listing tasks filtered by tag."""
        args = Namespace(
            template="test.json",
            status=None,
            priority=None,
            tags="important",
            parent=None,
            list=None,
            use_config=False,
            tree=False,
            show_relationships=False,
            json=False,
            sort_by=None,
            asc=False,
            show_id=False,
            complete=False,
            flat=True,
            colorize=True,
            show_descriptions=False,
            description_length=80,
            show_comments=0
        )
        
        result = CommandResult(self.command.execute(args), '\n'.join(self.printed_output))
        
        self.assertEqual(result.exit_code, 0)
        self.mock_print.assert_called()


class TestCommentTaskCommand(unittest.TestCase):
    """Test cases for task comments."""
    
    def setUp(self):
        """Set up test environment."""
        self.core_manager = MockCoreManager()
        self.command = CommentTaskCommand(self.core_manager)
        self.test_task = self.core_manager.create_task("Test Task")
        
        # Mock print function and capture output
        self.print_patcher = patch('builtins.print')
        self.mock_print = self.print_patcher.start()
        self.printed_output = []
        # Use a lambda that accepts **kwargs to handle any keyword arguments like 'file'
        self.mock_print.side_effect = lambda *args, **kwargs: self.printed_output.append(' '.join(str(arg) for arg in args))
        
        # Initialize the core manager
        self.core_manager.initialize("test.json")
        
        # Patch add_comment method to match expected interface
        original_add_comment = self.core_manager.add_comment
        
        def patched_add_comment(task_id, text, author=None):
            # Create a comment dictionary manually
            comment = {"text": text, "author": author or "Unknown", "timestamp": datetime.now().isoformat()}
            # Add to comments collection
            if task_id not in self.core_manager.comments:
                self.core_manager.comments[task_id] = []
            self.core_manager.comments[task_id].append(comment)
            return comment
            
        # Replace the method
        self.core_manager.add_comment = patched_add_comment
    
    def tearDown(self):
        """Clean up test environment."""
        self.print_patcher.stop()
    
    def test_add_comment(self):
        """Test adding a comment to a task."""
        args = Namespace(
            task_name=self.test_task['id'],
            text="Test comment",
            author="Test User",
            template="test.json",  # Add the template file parameter
            task_type="task"
        )
        
        result = CommandResult(self.command.execute(args), '\n'.join(self.printed_output))
        
        self.assertEqual(result.exit_code, 0)
        task = self.core_manager.get_task(self.test_task['id'])
        self.assertEqual(len(self.core_manager.comments[task['id']]), 1)
        comment = self.core_manager.comments[task['id']][0]
        self.assertEqual(comment['text'], "Test comment")
        self.assertEqual(comment['author'], "Test User")
    
    def test_add_comment_nonexistent_task(self):
        """Test adding a comment to a nonexistent task."""
        args = Namespace(
            task_name="tsk_nonexistent",
            text="Test comment",
            author="Test User",
            template="test.json"  # Add the template file parameter
        )
        
        # Mock logger to capture the error
        with patch('refactor.cli.commands.task.logger') as mock_logger:
            result = CommandResult(self.command.execute(args), '\n'.join(self.printed_output))
        
        self.assertNotEqual(result.exit_code, 0)
        # Verify the logger was called with the expected error message
        mock_logger.error.assert_called_with("Task 'tsk_nonexistent' not found")


if __name__ == "__main__":
    unittest.main() 