"""Regression tests for bulk task_set_tags behavior."""

import io
import unittest
from argparse import Namespace
from unittest.mock import Mock, patch

from clickup_framework.commands.task_commands import task_set_tags_command


class TestTaskSetTagsCommand(unittest.TestCase):
    """Verify task_set_tags supports multiple task IDs in one invocation."""

    @patch("clickup_framework.commands.task_commands.ClickUpClient")
    @patch("clickup_framework.commands.task_commands.get_context_manager")
    def test_task_set_tags_adds_tags_to_multiple_tasks(
        self,
        mock_get_context_manager,
        mock_client_cls,
    ):
        context = Mock()
        context.resolve_id.side_effect = lambda resource_type, value: value
        mock_get_context_manager.return_value = context

        client = mock_client_cls.return_value
        client.get_task.side_effect = [
            {"id": "task-1", "name": "First Task", "tags": [{"name": "existing"}]},
            {"id": "task-2", "name": "Second Task", "tags": [{"name": "existing"}, {"name": "keep"}]},
        ]
        client.update_task.side_effect = [
            {"id": "task-1", "name": "First Task"},
            {"id": "task-2", "name": "Second Task"},
        ]

        args = Namespace(
            task_id=["task-1", "task-2"],
            add=["bug", "existing"],
            remove=None,
            set=None,
        )

        stdout = io.StringIO()
        with patch("sys.stdout", stdout):
            task_set_tags_command(args)

        self.assertEqual(client.get_task.call_count, 2)
        client.update_task.assert_any_call("task-1", tags=["existing", "bug"])
        client.update_task.assert_any_call("task-2", tags=["existing", "keep", "bug"])
        output = stdout.getvalue()
        self.assertIn("Task: First Task [task-1]", output)
        self.assertIn("Task: Second Task [task-2]", output)
        self.assertIn("Updated: 2/2 tasks", output)

    @patch("clickup_framework.commands.task_commands.ClickUpClient")
    @patch("clickup_framework.commands.task_commands.get_context_manager")
    def test_task_set_tags_reports_partial_failure_after_processing_all_tasks(
        self,
        mock_get_context_manager,
        mock_client_cls,
    ):
        context = Mock()
        context.resolve_id.side_effect = lambda resource_type, value: value
        mock_get_context_manager.return_value = context

        client = mock_client_cls.return_value
        client.get_task.side_effect = [
            {"id": "task-1", "name": "First Task", "tags": [{"name": "existing"}]},
            {"id": "task-2", "name": "Second Task", "tags": [{"name": "stale"}]},
        ]
        client.update_task.side_effect = [
            {"id": "task-1", "name": "First Task"},
            RuntimeError("boom"),
        ]

        args = Namespace(
            task_id=["task-1", "task-2"],
            add=None,
            remove=["stale"],
            set=None,
        )

        stdout = io.StringIO()
        stderr = io.StringIO()
        with patch("sys.stdout", stdout), patch("sys.stderr", stderr):
            with self.assertRaises(SystemExit) as cm:
                task_set_tags_command(args)

        self.assertEqual(cm.exception.code, 1)
        self.assertEqual(client.get_task.call_count, 2)
        client.update_task.assert_any_call("task-1", tags=["existing"])
        client.update_task.assert_any_call("task-2", tags=[])
        self.assertIn("Updated: 1/2 tasks", stdout.getvalue())
        self.assertIn("Failed: 1/2 tasks", stdout.getvalue())
        self.assertIn("Error setting tags for task-2: boom", stderr.getvalue())


if __name__ == "__main__":
    unittest.main(verbosity=2)
