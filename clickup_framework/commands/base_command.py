"""
Base command class for ClickUp Framework CLI commands.

This base class provides common functionality that all commands need:
- Context and client initialization
- Common argument handling
- ID resolution utilities
- Error handling
- Colorization utilities
- Command metadata storage
"""

import logging
import sys
from datetime import datetime
from pathlib import Path
from typing import Optional, Dict, Any
from clickup_framework import ClickUpClient, get_context_manager
from clickup_framework.clickup_constants import (
    CLICKUP_FRAMEWORK_LIST_IDS,
    CLI_COMMAND_TASK_IDS,
)
from clickup_framework.utils.colors import colorize, TextColor, TextStyle
from clickup_framework.utils.animations import ANSIAnimations
from clickup_framework.cli_error_handler import handle_cli_error
from clickup_framework.commands.utils import (
    resolve_container_id,
    resolve_list_id,
    create_format_options,
)
from clickup_framework.utils.image_export import console_to_jpg, capture_command_output_to_jpg


class BaseCommand:
    """
    Base class for all ClickUp Framework CLI commands.
    
    This class provides common functionality and attributes that all commands
    can use, reducing code duplication and ensuring consistency.
    
    Attributes:
        args: Parsed command-line arguments
        context: Context manager instance
        client: ClickUpClient instance
        use_color: Whether to use ANSI color codes
        format_options: FormatOptions instance (if applicable)
        command_name: Name of the command
        command_metadata: Optional metadata about the command
    """
    
    def __init__(self, args, command_name: Optional[str] = None):
        """
        Initialize the base command.
        
        Args:
            args: Parsed command-line arguments from argparse
            command_name: Optional name of the command (auto-detected if not provided)
        """
        self.args = args
        self.context = self._get_context_manager()
        self.client = self._create_client()
        self.command_name = command_name or self._detect_command_name()
        self.command_metadata: Optional[Dict[str, Any]] = None
        
        # Determine color usage from args or context
        if hasattr(args, 'colorize') and args.colorize is not None:
            self.use_color = args.colorize
        else:
            self.use_color = self.context.get_ansi_output()
        
        # Create format options if command uses formatting
        if self._uses_formatting():
            self.format_options = create_format_options(args)
        else:
            self.format_options = None

    def _get_context_manager(self):
        """Return the active context manager instance."""
        return get_context_manager()

    def _create_client(self):
        """Create the ClickUp client used by this command."""
        return ClickUpClient()
    
    def _detect_command_name(self) -> str:
        """Detect command name from args or class name."""
        if hasattr(self.args, 'command'):
            return self.args.command
        return self.__class__.__name__.replace('Command', '').lower()
    
    def _uses_formatting(self) -> bool:
        """Check if command uses format options."""
        # Commands that use formatting typically have preset or format-related args
        return (hasattr(self.args, 'preset') or 
                hasattr(self.args, 'colorize') or
                hasattr(self.args, 'show_ids'))
    
    # ==================== ID Resolution Methods ====================
    
    def resolve_id(self, id_type: str, id_or_current: str) -> str:
        """
        Resolve an ID from context or use provided ID.
        
        Args:
            id_type: Type of ID ('task', 'list', 'workspace', 'folder', 'space')
            id_or_current: ID string or 'current' to resolve from context
            
        Returns:
            Resolved ID string
            
        Raises:
            ValueError: If ID cannot be resolved
        """
        try:
            return self.context.resolve_id(id_type, id_or_current)
        except ValueError as e:
            self.error(str(e))
            sys.exit(1)
    
    def resolve_container(self, id_or_current: str) -> Dict[str, Any]:
        """
        Resolve a container ID (space, folder, list, or task).
        
        Args:
            id_or_current: Container ID or 'current' keyword
            
        Returns:
            Dictionary with 'type' and 'id' keys, optionally 'data' and 'list_id'
            
        Raises:
            ValueError: If container cannot be resolved
        """
        try:
            return resolve_container_id(self.client, id_or_current, self.context)
        except ValueError as e:
            self.error(str(e))
            sys.exit(1)
    
    def resolve_list(self, id_or_current: str) -> str:
        """
        Resolve a list ID from list ID, task ID, or 'current'.
        
        Args:
            id_or_current: List ID, task ID, or 'current' keyword
            
        Returns:
            Resolved list ID string
            
        Raises:
            ValueError: If list ID cannot be resolved
        """
        try:
            return resolve_list_id(self.client, id_or_current, self.context)
        except ValueError as e:
            self.error(str(e))
            sys.exit(1)
    
    # ==================== Output Methods ====================
    
    def print(self, *args, **kwargs):
        """Print with optional colorization."""
        print(*args, **kwargs)
    
    def print_color(self, text: str, color: TextColor = TextColor.BRIGHT_WHITE,
                   style: TextStyle = None):
        """Print colorized text."""
        if self.use_color:
            print(colorize(text, color, style))
        else:
            print(text)
    
    def print_error(self, message: str, **kwargs):
        """Print error message."""
        kwargs.setdefault('file', sys.stderr)
        if self.use_color:
            print(ANSIAnimations.error_message(message), **kwargs)
        else:
            print(f"Error: {message}", **kwargs)
    
    def print_success(self, message: str):
        """Print success message."""
        if self.use_color:
            print(ANSIAnimations.success_message(message))
        else:
            print(f"Success: {message}")
    
    def print_warning(self, message: str):
        """Print warning message."""
        if self.use_color:
            print(ANSIAnimations.warning_message(message))
        else:
            print(f"Warning: {message}")
    
    def error(self, message: str, exit_code: int = 1):
        """
        Print error and exit.
        
        Args:
            message: Error message
            exit_code: Exit code (default: 1)
        """
        self.print_error(message)
        sys.exit(exit_code)
    
    # ==================== Utility Methods ====================
    
    def get_default_assignee(self) -> Optional[str]:
        """Get default assignee from context."""
        return self.context.get_default_assignee()
    
    def get_workspace_id(self) -> Optional[str]:
        """Get current workspace ID from context."""
        try:
            return self.context.resolve_id('workspace', 'current')
        except ValueError:
            return None
    
    def get_list_id(self) -> Optional[str]:
        """Get current list ID from context."""
        try:
            return self.context.resolve_id('list', 'current')
        except ValueError:
            return None
    
    def get_task_id(self) -> Optional[str]:
        """Get current task ID from context."""
        try:
            return self.context.resolve_id('task', 'current')
        except ValueError:
            return None

    # ==================== Issue Reporting Helpers ====================

    CLI_COMMANDS_LIST_ID = CLICKUP_FRAMEWORK_LIST_IDS["cli-commands"]
    CLI_COMMAND_TASK_IDS = CLI_COMMAND_TASK_IDS
    FRAMEWORK_REPORT_LISTS = {
        "development": {
            "id": CLICKUP_FRAMEWORK_LIST_IDS["development"],
            "label": "development",
            "aliases": ("development", "dev", "development-tasks"),
        },
        "feature-requests": {
            "id": CLICKUP_FRAMEWORK_LIST_IDS["feature-requests"],
            "label": "feature-requests",
            "aliases": ("feature-requests", "features", "feature", "enhancements"),
        },
        "bug-fixes": {
            "id": CLICKUP_FRAMEWORK_LIST_IDS["bug-fixes"],
            "label": "bug-fixes",
            "aliases": ("bug-fixes", "bugfixes", "bugs", "bug", "fixes"),
        },
        "documentation": {
            "id": CLICKUP_FRAMEWORK_LIST_IDS["documentation"],
            "label": "documentation",
            "aliases": ("documentation", "docs", "doc"),
        },
        "testing": {
            "id": CLICKUP_FRAMEWORK_LIST_IDS["testing"],
            "label": "testing",
            "aliases": ("testing", "tests", "test", "qa"),
        },
        "releases": {
            "id": CLICKUP_FRAMEWORK_LIST_IDS["releases"],
            "label": "releases",
            "aliases": ("releases", "release"),
        },
    }

    @staticmethod
    def _read_report_details(
        details: Optional[str] = None,
        details_file: Optional[str] = None,
    ) -> str:
        """Read issue report details from inline text or a UTF-8 file."""
        if details and details.strip():
            return details.strip()

        if not details_file:
            raise ValueError(
                "Provide --report-details or --report-details-file when using --report-issue."
            )

        path = Path(details_file)
        if not path.exists():
            raise ValueError(f"Report details file not found: {details_file}")
        if not path.is_file():
            raise ValueError(f"Report details path is not a file: {details_file}")

        try:
            content = path.read_text(encoding="utf-8").strip()
        except UnicodeDecodeError as exc:
            raise ValueError(
                f"Report details file is not valid UTF-8 text: {details_file}"
            ) from exc
        except OSError as exc:
            raise ValueError(
                f"Could not read report details file {details_file}: {exc}"
            ) from exc

        if not content:
            raise ValueError(f"Report details file is empty: {details_file}")

        return content

    @classmethod
    def framework_report_destinations(cls) -> str:
        """Return a compact list of supported framework report destinations."""
        return ", ".join(
            config["label"] for config in cls.FRAMEWORK_REPORT_LISTS.values()
        )

    @classmethod
    def resolve_framework_report_list(cls, report_list: Optional[str]) -> str:
        """Resolve a framework report destination alias to its internal list ID."""
        if not report_list or not report_list.strip():
            return cls.FRAMEWORK_REPORT_LISTS["bug-fixes"]["id"]

        candidate = report_list.strip()
        allowed_ids = {
            config["id"] for config in cls.FRAMEWORK_REPORT_LISTS.values()
        }
        if candidate in allowed_ids:
            return candidate

        normalized = candidate.lower()
        for config in cls.FRAMEWORK_REPORT_LISTS.values():
            if normalized in config["aliases"]:
                return config["id"]

        raise ValueError(
            "Report destination must be one of the ClickUp Framework lists: "
            f"{cls.framework_report_destinations()}."
        )

    @classmethod
    def get_catalog_task_name(cls, root_command: str) -> str:
        """Return the command-sync task name for a root CLI command."""
        from clickup_framework.commands.command_sync import (
            get_command_category,
            get_task_name,
        )

        category = get_command_category(root_command)
        return get_task_name(root_command, category)

    @classmethod
    def get_catalog_task_id(cls, root_command: str) -> Optional[str]:
        """Return the explicit CLI Commands task ID for a root command, if known."""
        return cls.CLI_COMMAND_TASK_IDS.get(root_command)

    @classmethod
    def find_catalog_task(
        cls,
        client: ClickUpClient,
        root_command: str,
        cli_commands_list_id: str = None,
    ) -> Optional[Dict[str, Any]]:
        """Find the related CLI Commands catalog task for a root command."""
        cli_commands_list_id = cli_commands_list_id or cls.CLI_COMMANDS_LIST_ID
        task_id = cls.get_catalog_task_id(root_command)
        if task_id:
            try:
                task = client.get_task(task_id)
                task_list_id = task.get("list", {}).get("id")
                if not task_list_id or task_list_id == cli_commands_list_id:
                    return task
            except Exception as exc:
                logging.debug("Direct catalog task lookup failed for %r, falling back to list scan: %s", root_command, exc)

        task_name = cls.get_catalog_task_name(root_command)
        fallback_suffix = f") CUM {root_command}"
        page = 0

        # The list tasks endpoint returns up to 100 items per page. Direct task ID
        # lookup handles known commands first, but we still page through the fallback
        # scan so new or unmapped CLI command tasks remain discoverable past page 1.
        while True:
            result = client.get_list_tasks(
                cli_commands_list_id,
                include_closed=True,
                page=page,
            )
            tasks = result.get("tasks", [])

            for task in tasks:
                if task.get("name") == task_name:
                    return task

            for task in tasks:
                task_name_value = task.get("name", "")
                if task_name_value.endswith(fallback_suffix):
                    return task

            if result.get("last_page", True) or not tasks:
                break
            page += 1

        return None

    @staticmethod
    def build_issue_report_description(
        details: str,
        root_command: str,
        command_path: Optional[str] = None,
        command_line: Optional[str] = None,
        cwd: Optional[str] = None,
    ) -> str:
        """Build a consistent markdown description for a command issue report."""
        timestamp = datetime.now().astimezone().isoformat(timespec="seconds")
        reported_path = command_path or root_command
        lines = [
            "# Command Issue Report",
            "",
            "## Command Context",
            f"- Root command: `{root_command}`",
            f"- Invoked command path: `{reported_path}`",
            f"- Reported at: `{timestamp}`",
        ]

        if command_line:
            lines.append(f"- Repro command: `{command_line}`")
        if cwd:
            lines.append(f"- Working directory: `{cwd}`")

        lines.extend(
            [
                "",
                "## Details",
                details.strip(),
                "",
                "## Evidence Checklist",
                "- Expected behaviour",
                "- Actual behaviour",
                "- Clear repro steps",
                "- Relevant IDs, filters, or input values",
                "- Logs, stack traces, screenshots, or failing output where available",
            ]
        )
        return "\n".join(lines)

    @classmethod
    def create_command_issue_report(
        cls,
        report_title: str,
        report_list_id: str,
        *,
        report_details: Optional[str] = None,
        report_details_file: Optional[str] = None,
        root_command: Optional[str] = None,
        command_path: Optional[str] = None,
        command_line: Optional[str] = None,
        cwd: Optional[str] = None,
        client: Optional[ClickUpClient] = None,
        context=None,
        cli_commands_list_id: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        Create a linked ClickUp issue report for a command.

        Returns:
            Dictionary containing the created task plus link status metadata.
        """
        if not report_title or not report_title.strip():
            raise ValueError("Issue title cannot be empty.")
        if not root_command:
            raise ValueError("Could not determine the command to link this report to.")

        context = context or get_context_manager()
        client = client or ClickUpClient()
        cli_commands_list_id = cli_commands_list_id or cls.CLI_COMMANDS_LIST_ID

        details = cls._read_report_details(report_details, report_details_file)
        framework_list_id = cls.resolve_framework_report_list(report_list_id)
        resolved_list_id = context.resolve_id("list", framework_list_id)

        # Validate the destination list early so the user gets a direct error.
        client.get_list(resolved_list_id)

        task_data = {
            "name": report_title.strip(),
            "markdown_description": cls.build_issue_report_description(
                details=details,
                root_command=root_command,
                command_path=command_path,
                command_line=command_line,
                cwd=cwd,
            ),
        }

        default_assignee = context.get_default_assignee()
        if default_assignee:
            task_data["assignees"] = [{"id": default_assignee}]

        created_task = client.create_task(resolved_list_id, **task_data)

        linked_command_task = cls.find_catalog_task(
            client,
            root_command=root_command,
            cli_commands_list_id=cli_commands_list_id,
        )

        link_created = False
        link_error = None
        if linked_command_task:
            try:
                client.add_task_link(created_task["id"], linked_command_task["id"])
                link_created = True
            except Exception as exc:
                link_error = str(exc)

        return {
            "task": created_task,
            "resolved_list_id": resolved_list_id,
            "linked_command_task": linked_command_task,
            "link_created": link_created,
            "link_error": link_error,
        }
    
    # ==================== Command Execution ====================
    
    def execute(self):
        """
        Execute the command.
        
        This method should be overridden by subclasses to implement
        the actual command logic.
        
        Raises:
            NotImplementedError: If not overridden by subclass
        """
        raise NotImplementedError(
            f"{self.__class__.__name__} must implement execute() method"
        )
    
    def run(self):
        """
        Run the command with error handling.
        
        This is the main entry point that should be called to execute
        the command. It wraps execute() with error handling.
        """
        try:
            return self.execute()
        except Exception as e:
            handle_cli_error(e, self.command_name)
            sys.exit(1)
    
    # ==================== Metadata Methods ====================
    
    def set_metadata(self, metadata: Dict[str, Any]):
        """Set command metadata."""
        self.command_metadata = metadata
    
    def get_metadata(self) -> Optional[Dict[str, Any]]:
        """Get command metadata."""
        return self.command_metadata
    
    # ==================== Image Export Methods ====================
    
    def export_output_to_jpg(
        self,
        output_path: str,
        output_text: Optional[str] = None,
        width: int = 1200,
        bg_color: str = "black",
        quality: int = 95
    ) -> bool:
        """
        Export command output to JPG image.
        
        Args:
            output_path: Path to output JPG file
            output_text: Text to export (if None, will capture from execute)
            width: Image width in pixels (default: 1200)
            bg_color: Background color - "black" or "white" (default: "black")
            quality: JPG quality 1-100 (default: 95)
        
        Returns:
            True if successful, False otherwise
        
        Example:
            >>> command.export_output_to_jpg("output.jpg", bg_color="black")
        """
        if output_text is None:
            # Capture output from execute method
            import io
            from contextlib import redirect_stdout
            
            f = io.StringIO()
            with redirect_stdout(f):
                try:
                    self.execute()
                except SystemExit:
                    pass
            
            output_text = f.getvalue()
        
        return console_to_jpg(output_text, output_path, width, bg_color, quality)

