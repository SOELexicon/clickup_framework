"""Focused tests for shared command issue-reporting support."""

import io
import unittest
from unittest.mock import Mock, patch

from clickup_framework.cli import build_parser, main
from clickup_framework.commands.base_command import BaseCommand


class TestIssueReportingParser(unittest.TestCase):
    """Verify shared report arguments are added to executable command parsers."""

    def test_leaf_command_help_includes_issue_reporting(self):
        parser = build_parser()
        subparsers = next(
            action for action in parser._actions
            if action.__class__.__name__ == "_SubParsersAction"
        )
        detail_parser = subparsers._name_parser_map["detail"]

        help_text = detail_parser.format_help()

        self.assertIn("Issue Reporting", help_text)
        self.assertIn("--report-issue", help_text)
        self.assertIn("--report-list", help_text)
        self.assertIn("--report-details", help_text)
        self.assertIn("--report-details-file", help_text)
        self.assertIn("expected behaviour", help_text)

    def test_nested_leaf_command_help_includes_issue_reporting(self):
        parser = build_parser()
        subparsers = next(
            action for action in parser._actions
            if action.__class__.__name__ == "_SubParsersAction"
        )
        dump_parser = subparsers._name_parser_map["dump"]
        dump_subparsers = next(
            action for action in dump_parser._actions
            if action.__class__.__name__ == "_SubParsersAction"
        )
        dump_task_parser = dump_subparsers._name_parser_map["task"]

        help_text = dump_task_parser.format_help()

        self.assertIn("--report-issue", help_text)
        self.assertIn("--report-list", help_text)

    def test_parent_command_help_includes_issue_reporting(self):
        parser = build_parser()
        subparsers = next(
            action for action in parser._actions
            if action.__class__.__name__ == "_SubParsersAction"
        )
        dump_parser = subparsers._name_parser_map["dump"]

        help_text = dump_parser.format_help()

        self.assertIn("--report-issue", help_text)
        self.assertIn("--report-list", help_text)


class TestIssueReportingFlow(unittest.TestCase):
    """Verify report-mode validation and short-circuit dispatch."""

    @patch("clickup_framework.cli.ARGCOMPLETE_AVAILABLE", False)
    def test_report_list_requires_report_issue(self):
        stderr = io.StringIO()
        with patch("sys.stderr", stderr):
            with patch("sys.argv", ["cum", "detail", "current", "--report-list", "901"]):
                with self.assertRaises(SystemExit) as cm:
                    main()

        self.assertEqual(cm.exception.code, 2)
        self.assertIn("require --report-issue", stderr.getvalue())

    @patch("clickup_framework.cli.ARGCOMPLETE_AVAILABLE", False)
    @patch("clickup_framework.commands.detail.detail_command")
    @patch("clickup_framework.cli.BaseCommand.create_command_issue_report")
    def test_main_creates_issue_instead_of_executing_command(
        self,
        mock_create_issue_report,
        mock_detail_command,
    ):
        mock_create_issue_report.return_value = {
            "task": {
                "id": "86test123",
                "name": "Detail command bug",
                "url": "https://app.clickup.com/t/86test123",
            },
            "linked_command_task": {
                "id": "86cmd123",
                "name": "(ClickUp Display) CUM detail",
            },
            "link_created": True,
            "link_error": None,
        }

        stdout = io.StringIO()
        with patch("sys.stdout", stdout):
            with patch(
                "sys.argv",
                [
                    "cum",
                    "detail",
                    "current",
                    "--report-issue",
                    "Detail command bug",
                    "--report-list",
                    "901517404276",
                    "--report-details",
                    "Expected a full detail view. Actual: linked tasks were omitted.",
                ],
            ):
                with self.assertRaises(SystemExit) as cm:
                    main()

        self.assertEqual(cm.exception.code, 0)
        mock_detail_command.assert_not_called()
        mock_create_issue_report.assert_called_once()
        call_kwargs = mock_create_issue_report.call_args.kwargs
        self.assertEqual(call_kwargs["root_command"], "detail")
        self.assertEqual(call_kwargs["command_path"], "detail")
        self.assertEqual(call_kwargs["report_list_id"], "901517404276")
        self.assertEqual(call_kwargs["command_line"], "cum detail current")
        self.assertIn("Issue task created", stdout.getvalue())


class TestBaseCommandIssueReporting(unittest.TestCase):
    """Verify BaseCommand report helpers create and link tasks correctly."""

    def test_create_command_issue_report_links_catalog_task(self):
        mock_client = Mock()
        mock_client.get_list.return_value = {"id": "901517404276", "name": "Bug Fixes"}
        mock_client.create_task.return_value = {
            "id": "86issue123",
            "name": "Search command fails",
            "url": "https://app.clickup.com/t/86issue123",
        }
        mock_client.get_list_tasks.return_value = {
            "tasks": [
                {
                    "id": "86cmd999",
                    "name": "(ClickUp Display) CUM search",
                }
            ]
        }

        mock_context = Mock()
        mock_context.resolve_id.return_value = "901517404276"
        mock_context.get_default_assignee.return_value = "user-123"

        result = BaseCommand.create_command_issue_report(
            report_title="Search command fails",
            report_list_id="901517404276",
            report_details="Expected search results. Actual: dependency failure.",
            root_command="search",
            command_path="search",
            command_line="cum search foo",
            cwd="E:\\Projects\\clickup_framework",
            client=mock_client,
            context=mock_context,
        )

        self.assertEqual(result["task"]["id"], "86issue123")
        self.assertTrue(result["link_created"])
        self.assertEqual(result["linked_command_task"]["id"], "86cmd999")
        mock_client.create_task.assert_called_once()
        create_kwargs = mock_client.create_task.call_args.kwargs
        self.assertEqual(create_kwargs["name"], "Search command fails")
        self.assertIn("cum search foo", create_kwargs["markdown_description"])
        self.assertIn("Expected search results", create_kwargs["markdown_description"])
        self.assertEqual(create_kwargs["assignees"], [{"id": "user-123"}])
        mock_client.add_task_link.assert_called_once_with("86issue123", "86cmd999")


if __name__ == "__main__":
    unittest.main(verbosity=2)
