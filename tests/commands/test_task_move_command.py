"""Regression tests for task_move cross-list behavior."""

import io
import unittest
from argparse import Namespace
from unittest.mock import Mock, patch

from clickup_framework.commands.task_commands import task_move_command


class TestTaskMoveCommand(unittest.TestCase):
    """Verify task_move uses the dedicated home-list API and preserves parent moves."""

    @patch("clickup_framework.commands.task_commands.ClickUpClient")
    @patch("clickup_framework.commands.task_commands.get_context_manager")
    def test_task_move_uses_home_list_move_for_list_changes(
        self,
        mock_get_context_manager,
        mock_client_cls,
    ):
        context = Mock()
        context.resolve_id.side_effect = lambda resource_type, value: value
        mock_get_context_manager.return_value = context

        client = mock_client_cls.return_value
        client.get_list.return_value = {"id": "dest-list", "name": "Destination"}
        client.get_task.side_effect = [
            {
                "id": "task-123",
                "name": "Task One",
                "list": {"id": "source-list", "name": "Source"},
                "parent": None,
                "team_id": "workspace-1",
            },
            {
                "id": "task-123",
                "name": "Task One",
                "list": {"id": "dest-list", "name": "Destination"},
                "parent": None,
            },
        ]

        args = Namespace(
            task_ids=["task-123"],
            list_id="dest-list",
            parent=None,
            force=True,
        )

        stdout = io.StringIO()
        with patch("sys.stdout", stdout):
            task_move_command(args)

        client.move_task_to_home_list.assert_called_once_with(
            "workspace-1",
            "task-123",
            "dest-list",
        )
        client.update_task.assert_not_called()
        self.assertIn("Moved: Task One -> list 'Destination'", stdout.getvalue())

    @patch("clickup_framework.commands.task_commands.ClickUpClient")
    @patch("clickup_framework.commands.task_commands.get_context_manager")
    def test_task_move_parent_only_updates_parent_and_home_list(
        self,
        mock_get_context_manager,
        mock_client_cls,
    ):
        context = Mock()
        context.resolve_id.side_effect = lambda resource_type, value: value
        mock_get_context_manager.return_value = context

        client = mock_client_cls.return_value
        client.get_task.side_effect = [
            {
                "id": "parent-456",
                "name": "Parent Task",
                "list": {"id": "dest-list", "name": "Destination"},
                "parent": None,
            },
            {
                "id": "task-123",
                "name": "Task One",
                "list": {"id": "source-list", "name": "Source"},
                "parent": None,
                "team_id": "workspace-1",
            },
            {
                "id": "task-123",
                "name": "Task One",
                "list": {"id": "dest-list", "name": "Destination"},
                "parent": "parent-456",
            },
        ]

        args = Namespace(
            task_ids=["task-123"],
            list_id=None,
            parent="parent-456",
            force=True,
        )

        stdout = io.StringIO()
        with patch("sys.stdout", stdout):
            task_move_command(args)

        client.move_task_to_home_list.assert_called_once_with(
            "workspace-1",
            "task-123",
            "dest-list",
        )
        client.update_task.assert_called_once_with("task-123", parent="parent-456")
        self.assertIn("Moved: Task One -> parent 'Parent Task'", stdout.getvalue())


if __name__ == "__main__":
    unittest.main(verbosity=2)
