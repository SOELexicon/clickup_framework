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

import sys
from typing import Optional, Dict, Any
from clickup_framework import ClickUpClient, get_context_manager
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
        self.context = get_context_manager()
        self.client = ClickUpClient()
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
                   style: TextStyle = TextStyle.NORMAL):
        """Print colorized text."""
        if self.use_color:
            print(colorize(text, color, style))
        else:
            print(text)
    
    def print_error(self, message: str):
        """Print error message."""
        if self.use_color:
            print(ANSIAnimations.error_message(message), file=sys.stderr)
        else:
            print(f"Error: {message}", file=sys.stderr)
    
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

