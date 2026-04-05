"""Regression tests for the time tracking CLI commands."""

import io
import unittest
from argparse import Namespace
from unittest.mock import Mock, patch

from clickup_framework.commands.base_command import BaseCommand
from clickup_framework.commands.time_commands import (
    TimeAddCommand,
    TimeCommandBase,
    TimeListCommand,
    TimeStartCommand,
    TimeStatusCommand,
    time_add_command,
)
from clickup_framework.utils.duration import parse_duration_to_ms


class TestTimeCommands(unittest.TestCase):
    """Verify duration parsing and time command wiring."""

    def _mock_context(self):
        context = Mock()
        context.get_ansi_output.return_value = False
        return context

    def test_parse_duration_to_ms_supports_common_formats(self):
        self.assertEqual(parse_duration_to_ms("2h30m"), 9_000_000)
        self.assertEqual(parse_duration_to_ms("90m"), 5_400_000)
        self.assertEqual(parse_duration_to_ms("1.5h"), 5_400_000)
        self.assertEqual(parse_duration_to_ms("45"), 2_700_000)

    def test_parse_duration_to_ms_rejects_invalid_text(self):
        with self.assertRaises(ValueError):
            parse_duration_to_ms("two hours")

        with self.assertRaises(ValueError):
            parse_duration_to_ms("0m")

    def test_time_command_classes_inherit_base_command(self):
        self.assertTrue(issubclass(TimeCommandBase, BaseCommand))
        self.assertTrue(issubclass(TimeStartCommand, TimeCommandBase))
        self.assertTrue(issubclass(TimeListCommand, TimeCommandBase))
        self.assertTrue(issubclass(TimeAddCommand, TimeCommandBase))
        self.assertTrue(issubclass(TimeStatusCommand, TimeCommandBase))

    @patch("clickup_framework.commands.base_command.ClickUpClient")
    @patch("clickup_framework.commands.base_command.get_context_manager")
    def test_time_start_resolves_team_and_task_then_starts_timer(
        self,
        mock_get_context_manager,
        mock_client_cls,
    ):
        mock_get_context_manager.return_value = self._mock_context()
        mock_client = Mock()
        mock_client.get_task.return_value = {"id": "task-123", "name": "CLI Command Implementation"}
        mock_client.start_time_entry.return_value = {"data": {"start": 1_712_581_200_000, "tid": "task-123"}}
        mock_client_cls.return_value = mock_client
        args = Namespace(
            task_id="current",
            team_id="current",
            description="Working on implementation",
            colorize=None,
        )
        stdout = io.StringIO()

        command = TimeStartCommand(args, command_name="time")
        with patch.object(command, "resolve_id", side_effect=["team-123", "task-123"]) as mock_resolve:
            with patch("sys.stdout", stdout):
                command.execute()

        self.assertEqual(mock_resolve.call_args_list[0].args, ("workspace", "current"))
        self.assertEqual(mock_resolve.call_args_list[1].args, ("task", "current"))
        mock_client.start_time_entry.assert_called_once_with(
            "team-123",
            tid="task-123",
            description="Working on implementation",
        )
        self.assertIn("Timer started on task: CLI Command Implementation", stdout.getvalue())

    @patch("clickup_framework.commands.base_command.ClickUpClient")
    @patch("clickup_framework.commands.base_command.get_context_manager")
    def test_time_list_prints_table_and_total(
        self,
        mock_get_context_manager,
        mock_client_cls,
    ):
        mock_get_context_manager.return_value = self._mock_context()
        mock_client = Mock()
        mock_client.get_time_entries.return_value = {
            "data": [
                {
                    "id": "timer-1",
                    "start": 1_712_581_200_000,
                    "end": 1_712_588_400_000,
                    "duration": 7_200_000,
                    "description": "Working on implementation",
                    "user": {"username": "Craig Wright"},
                    "task": {"id": "task-123", "name": "CLI Command Implementation"},
                },
                {
                    "id": "timer-2",
                    "start": 1_712_667_600_000,
                    "end": 1_712_671_200_000,
                    "duration": 3_600_000,
                    "description": "Code review",
                    "user": {"username": "Lexicon Code"},
                    "task": {"id": "task-123", "name": "CLI Command Implementation"},
                },
            ]
        }
        mock_client.get_task.return_value = {"id": "task-123", "name": "CLI Command Implementation"}
        mock_client_cls.return_value = mock_client
        args = Namespace(
            task_id="current",
            team_id="current",
            assignee=None,
            start_date=None,
            end_date=None,
            colorize=None,
        )
        stdout = io.StringIO()

        command = TimeListCommand(args, command_name="time")
        with patch.object(command, "resolve_id", side_effect=["team-123", "task-123"]):
            with patch("sys.stdout", stdout):
                command.execute()

        output = stdout.getvalue()
        self.assertIn("⏱️  Time Entries", output)
        self.assertIn("Craig Wright", output)
        self.assertIn("Code review", output)
        self.assertIn("Total: 3h", output)

    @patch("clickup_framework.commands.base_command.ClickUpClient")
    @patch("clickup_framework.commands.base_command.get_context_manager")
    def test_time_status_shows_running_timer_details(
        self,
        mock_get_context_manager,
        mock_client_cls,
    ):
        mock_get_context_manager.return_value = self._mock_context()
        mock_client = Mock()
        mock_client.get_current_time_entry.return_value = {
            "data": {
                "id": "timer-1",
                "start": 1_712_581_200_000,
                "duration": -1,
                "description": "Working on implementation",
                "task": {"id": "task-123", "name": "CLI Command Implementation"},
            }
        }
        mock_client_cls.return_value = mock_client
        args = Namespace(team_id="current", colorize=None)
        stdout = io.StringIO()

        command = TimeStatusCommand(args, command_name="time")
        with patch.object(command, "resolve_id", return_value="team-123"):
            with patch("sys.stdout", stdout):
                command.execute()

        output = stdout.getvalue()
        self.assertIn("Current Timer", output)
        self.assertIn("CLI Command Implementation", output)
        self.assertIn("Use 'cum time stop' to stop the timer", output)

    @patch("clickup_framework.commands.base_command.ClickUpClient")
    @patch("clickup_framework.commands.base_command.get_context_manager")
    @patch("clickup_framework.commands.time_commands.TimeAddCommand.execute")
    def test_time_add_wrapper_uses_command_class(
        self,
        mock_execute,
        mock_get_context_manager,
        mock_client_cls,
    ):
        mock_get_context_manager.return_value = self._mock_context()
        mock_client_cls.return_value = Mock()
        args = Namespace(
            task_id="current",
            duration="90m",
            team_id="current",
            description=None,
            date=None,
            colorize=None,
        )

        time_add_command(args)

        mock_execute.assert_called_once()


if __name__ == "__main__":
    unittest.main(verbosity=2)
