import argparse
import io
import sys
import unittest
from unittest.mock import Mock, patch

from clickup_framework.commands import command_sync


def _make_command_parser(name: str, description: str) -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog=f"cum {name}", description=description)
    parser.add_argument("--example", action="store_true")
    return parser


class TestCommandSyncIntrospection(unittest.TestCase):
    def test_discover_cli_commands_uses_registered_parsers(self):
        command_parsers = {
            "detail": _make_command_parser("detail", "Show detailed task output."),
            "search": _make_command_parser("search", "Search task content."),
            "list-mgmt": _make_command_parser("list-mgmt", "Manage lists."),
        }

        with patch.object(command_sync, "_get_registered_command_parsers", return_value=command_parsers):
            with patch.object(command_sync.subprocess, "run", side_effect=AssertionError("unexpected subprocess")):
                commands = command_sync.discover_cli_commands()

        self.assertIn("detail", commands)
        self.assertIn("search", commands)
        self.assertIn("list_mgmt", commands)
        self.assertNotIn("list-mgmt", commands)

    def test_get_command_help_uses_internal_parser(self):
        parser = argparse.ArgumentParser(
            prog="cum detail",
            description="Render the full detail view for a task.",
        )
        parser.add_argument("task_id")

        help_output, error_output = command_sync.get_command_help(
            "detail",
            {"detail": parser},
        )

        self.assertEqual(error_output, "")
        self.assertIn("usage: cum detail", help_output)
        self.assertIn("Render the full detail view for a task.", help_output)

    def test_execute_command_on_test_task_uses_python_module_invocation(self):
        completed = Mock(stdout="detail output", stderr="")

        with patch.object(command_sync.subprocess, "run", return_value=completed) as mock_run:
            stdout, stderr = command_sync.execute_command_on_test_task("detail", "86abc123")

        self.assertEqual(stdout, "detail output")
        self.assertEqual(stderr, "")
        self.assertEqual(
            mock_run.call_args.args[0][:3],
            [sys.executable, "-m", "clickup_framework"],
        )
        self.assertEqual(
            mock_run.call_args.args[0][3:],
            ["detail", "86abc123"],
        )

    def test_list_missing_commands_reports_mapping_and_catalog_gaps(self):
        command_parsers = {
            "detail": _make_command_parser("detail", "Show detailed task output."),
            "search": _make_command_parser("search", "Search task content."),
            "map": _make_command_parser("map", "Map tasks."),
        }
        mock_client = Mock()
        mock_client.get_list_tasks.return_value = {
            "tasks": [
                {
                    "id": "86detail123",
                    "name": "(ClickUp Display) CUM detail",
                }
            ],
            "last_page": True,
        }
        stdout = io.StringIO()

        with patch.object(command_sync, "_get_registered_command_parsers", return_value=command_parsers):
            with patch.dict(
                command_sync.COMMAND_CATEGORIES,
                {
                    "detail": "ClickUp Display",
                    "search": "ClickUp Display",
                },
                clear=True,
            ):
                with patch.dict(
                    command_sync.COMMAND_TASK_IDS,
                    {"detail": "86detail123"},
                    clear=True,
                ):
                    with patch("clickup_framework.commands.command_sync.ClickUpClient", return_value=mock_client):
                        with patch("sys.stdout", stdout):
                            command_sync.list_missing_commands("901517567020")

        output = stdout.getvalue()
        self.assertIn("Registered commands missing from COMMAND_CATEGORIES (1):", output)
        self.assertIn("  - map", output)
        self.assertIn("Syncable commands missing from CLI_COMMAND_TASK_IDS (1):", output)
        self.assertIn("  - search", output)
        self.assertIn("Syncable commands with no matching CLI Commands task by name (1):", output)
        self.assertIn("search -> (ClickUp Display) CUM search", output)
