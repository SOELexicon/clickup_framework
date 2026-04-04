"""Regression tests for detail command help formatting."""

import unittest

from clickup_framework.cli import build_parser


class TestDetailHelpOutput(unittest.TestCase):
    """Verify detail help preserves epilog line breaks."""

    def test_detail_help_preserves_usage_bullets(self):
        parser = build_parser()
        subparsers = next(
            action for action in parser._actions
            if action.__class__.__name__ == "_SubParsersAction"
        )
        detail_parser = subparsers._name_parser_map["detail"]

        help_text = detail_parser.format_help()

        self.assertIn("Usage:\n  • View task details: cum detail <task_id>", help_text)
        self.assertIn("  • Use shorter alias: cum d <task_id>", help_text)
        self.assertIn("Tips:\n  • The detail view now shows full descriptions", help_text)


if __name__ == "__main__":
    unittest.main(verbosity=2)
