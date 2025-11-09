"""
Task: tsk_02e976b4 - Fix Comment Newline Display in CLI
Document: refactor/utils/log_formatter.py
dohcount: 1

Related Tasks:
    - tsk_40d54e79 - Fix Unit Test Failures (parent)
    - tsk_7c3b4a40 - Improve Console Output Formatting (related)

Used By:
    - main.py: Sets up logging with improved formatting
    - All modules: Displays formatted log messages

Purpose:
    Provides a custom log formatter that enhances log readability with:
    - Color-coded log levels
    - Structured format with headers and indented content
    - Consistent styling for all log messages

Requirements:
    - Must format logs with a header line and indented content
    - Must color-code different log levels for better readability
    - Must preserve all log information (level, name, message)
    - CRITICAL: Must be compatible with existing logging usage
    - CRITICAL: Must maintain compatibility with redirected output
    - Must work consistently in all environments

Parameters:
    N/A - This is a module file

Returns:
    N/A - This is a module file

Changes:
    - v1: Initial implementation with color support and structured formatting
"""

import logging
import os
from refactor.utils.colors import TextColor, colorize, DefaultTheme, USE_COLORS

# Global variables for log formatter configuration
LOG_SEPARATOR_ENABLED = False

def toggle_log_separator(enabled=True):
    """
    Toggle whether to show a separator between log output and command output.
    
    Args:
        enabled: Whether to enable the separator
    """
    global LOG_SEPARATOR_ENABLED
    LOG_SEPARATOR_ENABLED = enabled
    
    # Set environment variable for main.py to check
    if enabled:
        os.environ['LOG_SEPARATOR'] = '1'
    elif 'LOG_SEPARATOR' in os.environ:
        del os.environ['LOG_SEPARATOR']

class ColoredFormatter(logging.Formatter):
    """
    Custom log formatter that provides color-coded, structured log messages.
    
    Features:
    - Color-coded log levels for easy identification
    - Header line with log level and logger name
    - Indented message content for readability
    """
    
    # Define colors for different log levels
    LEVEL_COLORS = {
        'DEBUG': DefaultTheme.DEBUG,
        'INFO': DefaultTheme.INFO,
        'WARNING': DefaultTheme.WARNING,
        'ERROR': DefaultTheme.ERROR,
        'CRITICAL': DefaultTheme.ERROR
    }
    
    def __init__(self, fmt=None, datefmt=None, style='%', indent_width=6):
        """
        Initialize the formatter with custom format and styling.
        
        Args:
            fmt: Log format string
            datefmt: Date format string
            style: Format style (%, { or $)
            indent_width: Width of indentation for message content
        """
        super().__init__(fmt, datefmt, style)
        self.indent_width = indent_width
    
    def format(self, record):
        """
        Format the log record with color and structure.
        
        Args:
            record: The log record to format
            
        Returns:
            Formatted log string with color coding and structure
        """
        # Get the level color
        level_color = self.LEVEL_COLORS.get(record.levelname, TextColor.WHITE)
        
        # Format the header with color
        header = f"{colorize(record.levelname, level_color)}:{colorize(record.name, DefaultTheme.ID)}"
        
        # Format the message content with indentation
        indent = " " * self.indent_width
        message_parts = record.getMessage().split('\n')
        if len(message_parts) == 1:
            # Single-line message
            message_formatted = f"{indent}{message_parts[0]}"
        else:
            # Multi-line message
            message_formatted = "\n" + "\n".join(f"{indent}{line}" for line in message_parts)
        
        # Combine header and content
        return f"{header}:\n{message_formatted}"


class PlainFormatter(logging.Formatter):
    """
    Plain text formatter for when colors are disabled or for file output.
    Maintains the structured format without color codes.
    """
    
    def __init__(self, fmt=None, datefmt=None, style='%', indent_width=6):
        """Initialize the formatter with custom format and styling."""
        super().__init__(fmt, datefmt, style)
        self.indent_width = indent_width
    
    def format(self, record):
        """Format the log record with structure but no color."""
        # Format the header
        header = f"{record.levelname}:{record.name}"
        
        # Format the message content with indentation
        indent = " " * self.indent_width
        message_parts = record.getMessage().split('\n')
        if len(message_parts) == 1:
            # Single-line message
            message_formatted = f"{indent}{message_parts[0]}"
        else:
            # Multi-line message
            message_formatted = "\n" + "\n".join(f"{indent}{line}" for line in message_parts)
        
        # Combine header and content
        return f"{header}:\n{message_formatted}"


def get_formatter(use_colors=True):
    """
    Get the appropriate formatter based on color settings.
    
    Args:
        use_colors: Whether to use colors in formatting
        
    Returns:
        Appropriate formatter instance
    """
    if use_colors and USE_COLORS:
        return ColoredFormatter()
    else:
        return PlainFormatter() 