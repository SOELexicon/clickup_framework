"""Launch the ProcMon-backed file system stalker utility."""

import os
import shutil
import subprocess
from pathlib import Path

from clickup_framework import get_context_manager
from clickup_framework.commands.base_command import BaseCommand
from clickup_framework.utils.argparse_helpers import raw_text_formatter


COMMAND_METADATA = {
    "category": "🛠️  Utility Commands",
    "commands": [
        {
            "name": "stalker",
            "args": "[path] [--browse] [--skip-procmon-download] [--buffer-size N] [--show-stack-trace] [--dry-run]",
            "description": "Launch the ProcMon-backed file system stalker in a new console window",
        }
    ],
}


class StalkerCommand(BaseCommand):
    """CLI wrapper around scripts/procmon_stalker.ps1."""

    def _get_context_manager(self):
        """Return the active context manager instance."""
        return get_context_manager()

    def _create_client(self):
        """This utility command does not need the ClickUp API client."""
        return None

    def _repo_root(self) -> Path:
        return Path(__file__).resolve().parents[2]

    def _script_path(self) -> Path:
        return self._repo_root() / "scripts" / "procmon_stalker.ps1"

    def _find_powershell(self) -> str | None:
        return shutil.which("powershell.exe") or shutil.which("pwsh.exe")

    def _resolve_monitor_path(self):
        if getattr(self.args, "browse", False):
            return None

        if getattr(self.args, "path", None):
            target = Path(self.args.path).expanduser().resolve()
            if not target.exists():
                self.error(f"Path does not exist: {target}")
            if not target.is_dir():
                self.error(f"Path must be a directory: {target}")
            return target

        current = Path.cwd().resolve()
        return current if current.exists() and current.is_dir() else None

    def _build_command(self, powershell_exe: str, monitor_path):
        cmd = [
            powershell_exe,
            "-NoLogo",
            "-NoProfile",
            "-ExecutionPolicy",
            "Bypass",
            "-File",
            str(self._script_path()),
        ]

        if monitor_path is not None:
            cmd.extend(["-MonitorPath", str(monitor_path)])
        if getattr(self.args, "skip_procmon_download", False):
            cmd.append("-SkipProcMonDownload")
        if getattr(self.args, "buffer_size", None):
            cmd.extend(["-BufferSize", str(self.args.buffer_size)])
        if getattr(self.args, "show_stack_trace", False):
            cmd.append("-ShowStackTrace")

        return cmd

    def execute(self):
        if os.name != "nt":
            self.error("stalker is only available on Windows hosts")

        script_path = self._script_path()
        if not script_path.exists():
            self.error(f"Missing ProcMon stalker script: {script_path}")

        powershell_exe = self._find_powershell()
        if not powershell_exe:
            self.error("Could not find powershell.exe or pwsh.exe on PATH")

        monitor_path = self._resolve_monitor_path()
        cmd = self._build_command(powershell_exe, monitor_path)

        if getattr(self.args, "dry_run", False):
            self.print("Dry run: stalker launch plan")
            self.print(f"  executable: {powershell_exe}")
            self.print(f"  script: {script_path}")
            self.print(f"  monitor_path: {monitor_path if monitor_path else '[folder picker]'}")
            self.print(f"  command: {' '.join(cmd)}")
            return

        creationflags = getattr(subprocess, "CREATE_NEW_CONSOLE", 0)
        process = subprocess.Popen(
            cmd,
            cwd=str(self._repo_root()),
            creationflags=creationflags,
        )

        self.print_success(f"Started stalker in a new console window (pid {process.pid})")
        if monitor_path is None:
            self.print("Select a folder in the PowerShell window to begin monitoring.")
        else:
            self.print(f"Monitoring path: {monitor_path}")


def stalker_command(args):
    """Backward-compatible wrapper for the stalker command."""
    StalkerCommand(args, command_name="stalker").execute()


def register_command(subparsers, add_common_args=None):
    """Register the stalker command."""
    parser = subparsers.add_parser(
        "stalker",
        help="Launch the ProcMon-backed file system stalker",
        formatter_class=raw_text_formatter(),
        description=(
            "Open the ProcMon-backed file system stalker in a new PowerShell console. "
            "If no path is supplied, the current directory is used when possible; "
            "otherwise the script opens a folder picker."
        ),
        epilog=(
            "Examples:\n"
            "  cum stalker\n"
            "  cum stalker E:\\Projects\\clickup_framework\n"
            "  cum stalker --browse\n"
            "  cum stalker . --skip-procmon-download --buffer-size 2000 --show-stack-trace\n"
            "  cum stalker --dry-run\n"
        ),
    )
    parser.add_argument(
        "path",
        nargs="?",
        help="Directory to monitor. Defaults to the current working directory when valid.",
    )
    parser.add_argument(
        "--browse",
        action="store_true",
        help="Open the folder picker instead of using the current directory.",
    )
    parser.add_argument(
        "--skip-procmon-download",
        action="store_true",
        help="Do not auto-download ProcMon if it is not already available.",
    )
    parser.add_argument(
        "--buffer-size",
        type=int,
        default=1000,
        help="ProcMon event buffer size. Default: 1000.",
    )
    parser.add_argument(
        "--show-stack-trace",
        action="store_true",
        help="Capture stack traces in ProcMon for deeper file activity inspection.",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Print the launch plan without opening a new console window.",
    )
    parser.set_defaults(func=stalker_command)
