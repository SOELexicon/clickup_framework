"""Regression tests for the ProcMon stalker CLI wrapper."""

import io
import unittest
from argparse import Namespace
from pathlib import Path
from unittest.mock import Mock, patch

from clickup_framework.commands.base_command import BaseCommand
from clickup_framework.commands.stalker_command import StalkerCommand, stalker_command


class TestStalkerCommand(unittest.TestCase):
    """Verify stalker command wiring and launch behavior."""

    def _mock_context(self):
        context = Mock()
        context.get_ansi_output.return_value = False
        return context

    def test_stalker_command_class_inherits_base_command(self):
        self.assertTrue(issubclass(StalkerCommand, BaseCommand))

    @patch("clickup_framework.commands.stalker_command.get_context_manager")
    def test_stalker_wrapper_uses_command_class(self, mock_get_context_manager):
        mock_get_context_manager.return_value = self._mock_context()
        args = Namespace(
            path=None,
            browse=False,
            skip_procmon_download=False,
            buffer_size=1000,
            show_stack_trace=False,
            dry_run=False,
            colorize=None,
        )

        with patch.object(StalkerCommand, "execute", return_value=None) as mock_execute:
            stalker_command(args)

        mock_execute.assert_called_once()

    @patch("clickup_framework.commands.stalker_command.os.name", "nt")
    def test_dry_run_prints_launch_plan(self):
        args = Namespace(
            path=None,
            browse=False,
            skip_procmon_download=True,
            buffer_size=2048,
            show_stack_trace=True,
            dry_run=True,
            colorize=None,
        )
        stdout = io.StringIO()
        monitor_path = Path("E:/Projects/clickup_framework").resolve()
        script_path = monitor_path / "scripts" / "procmon_stalker.ps1"

        with patch("clickup_framework.commands.stalker_command.get_context_manager", return_value=self._mock_context()):
            with patch.object(StalkerCommand, "_script_path", return_value=script_path):
                with patch.object(StalkerCommand, "_find_powershell", return_value="powershell.exe"):
                    with patch.object(StalkerCommand, "_resolve_monitor_path", return_value=monitor_path):
                        with patch("sys.stdout", stdout):
                            StalkerCommand(args, command_name="stalker").execute()

        output = stdout.getvalue()
        self.assertIn("Dry run: stalker launch plan", output)
        self.assertIn("procmon_stalker.ps1", output)
        self.assertIn("-SkipProcMonDownload", output)
        self.assertIn("-BufferSize 2048", output)
        self.assertIn("-ShowStackTrace", output)

    @patch("clickup_framework.commands.stalker_command.os.name", "nt")
    @patch("clickup_framework.commands.stalker_command.subprocess.Popen")
    def test_launches_new_console_with_expected_arguments(
        self,
        mock_subprocess_popen,
    ):
        args = Namespace(
            path="scripts",
            browse=False,
            skip_procmon_download=False,
            buffer_size=1000,
            show_stack_trace=False,
            dry_run=False,
            colorize=None,
        )
        process = Mock()
        process.pid = 1234
        mock_subprocess_popen.return_value = process
        stdout = io.StringIO()
        repo_root = Path("E:/Projects/clickup_framework").resolve()
        script_path = repo_root / "scripts" / "procmon_stalker.ps1"
        monitor_path = repo_root / "scripts"

        with patch("clickup_framework.commands.stalker_command.get_context_manager", return_value=self._mock_context()):
            with patch.object(StalkerCommand, "_repo_root", return_value=repo_root):
                with patch.object(StalkerCommand, "_script_path", return_value=script_path):
                    with patch.object(StalkerCommand, "_find_powershell", return_value="powershell.exe"):
                        with patch.object(StalkerCommand, "_resolve_monitor_path", return_value=monitor_path):
                            with patch("sys.stdout", stdout):
                                StalkerCommand(args, command_name="stalker").execute()

        command = mock_subprocess_popen.call_args.args[0]
        kwargs = mock_subprocess_popen.call_args.kwargs
        self.assertEqual(command[:2], ["powershell.exe", "-NoLogo"])
        self.assertIn("procmon_stalker.ps1", " ".join(command))
        self.assertIn("-MonitorPath", command)
        self.assertEqual(Path(kwargs["cwd"]).resolve(), repo_root)
        self.assertIn("Started stalker in a new console window", stdout.getvalue())


if __name__ == "__main__":
    unittest.main(verbosity=2)
