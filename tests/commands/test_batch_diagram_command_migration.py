"""Regression tests for BaseCommand migration inside batch_diagram_command.py."""

import io
import unittest
from argparse import Namespace
from unittest.mock import Mock, patch

from clickup_framework.commands.base_command import BaseCommand
from clickup_framework.commands.batch_diagram_command import (
    BatchDiagramCommand,
    batch_diagram_command,
)


class TestBatchDiagramCommandMigration(unittest.TestCase):
    """Verify the batch-diagram wrapper and optional watchdog handling."""

    def _mock_context(self):
        context = Mock()
        context.get_ansi_output.return_value = False
        return context

    def test_batch_diagram_command_class_inherits_base_command(self):
        self.assertTrue(issubclass(BatchDiagramCommand, BaseCommand))

    @patch("clickup_framework.commands.batch_diagram_command.get_context_manager")
    def test_batch_diagram_wrapper_uses_command_class(self, mock_get_context_manager):
        mock_get_context_manager.return_value = self._mock_context()
        args = Namespace(
            config=".diagram-pipeline.yaml",
            init=False,
            dry_run=False,
            watch=False,
            stop_on_error=False,
            colorize=None,
        )

        with patch.object(BatchDiagramCommand, "execute", return_value=None) as mock_execute:
            batch_diagram_command(args)

        mock_execute.assert_called_once()

    @patch("clickup_framework.commands.batch_diagram_command.WATCHDOG_AVAILABLE", False)
    @patch("clickup_framework.commands.batch_diagram_command.Path.exists", return_value=True)
    @patch("clickup_framework.commands.batch_diagram_command.PipelineConfig")
    @patch("clickup_framework.commands.batch_diagram_command.BatchGenerator")
    def test_watch_mode_without_watchdog_exits_cleanly(
        self,
        mock_batch_generator,
        mock_pipeline_config,
        mock_exists,
    ):
        mock_context = self._mock_context()
        args = Namespace(
            config=".diagram-pipeline.yaml",
            init=False,
            dry_run=False,
            watch=True,
            stop_on_error=False,
        )
        stderr = io.StringIO()

        with patch("sys.stderr", stderr), self.assertRaises(SystemExit) as exc:
            BatchDiagramCommand(args, command_name="batch-diagram").execute()

        self.assertEqual(exc.exception.code, 1)
        self.assertIn("requires the optional 'watchdog' dependency", stderr.getvalue())
        mock_pipeline_config.assert_called_once_with(".diagram-pipeline.yaml")
        mock_batch_generator.assert_called_once()


if __name__ == "__main__":
    unittest.main(verbosity=2)
