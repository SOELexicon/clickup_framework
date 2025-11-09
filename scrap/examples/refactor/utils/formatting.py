"""
Task: tsk_62630e24 - Update Utilities and Support Modules Comments
Document: refactor/utils/formatting.py
dohcount: 1

Related Tasks:
    - tsk_0a733101 - Code Comments Enhancement (parent)
    - tsk_7e3a4709 - Update Common Module Comments (sibling)
    - tsk_bf28d342 - Update CLI Module Comments (sibling)
    - tsk_4c899138 - Update Storage Module Comments (sibling)
    - tsk_3f55d115 - Update Plugins Module Comments (sibling)

Used By:
    - CLI Commands: Create formatted text output for terminal display
    - TaskFormatter: Format task details in consistent layouts
    - Dashboard: Create tables and charts for data visualization
    - OutputManager: Apply consistent styling to program output
    - SearchResults: Display search results in formatted tables
    - ChecklistDisplay: Format checklist items with proper indentation

Purpose:
    Provides text formatting utilities for creating consistent, readable 
    terminal output throughout the application. Implements functions for
    color formatting, table generation, text alignment, indentation, and 
    truncation. These utilities ensure a uniform presentation style
    that enhances readability while supporting terminals with different
    capabilities.

Requirements:
    - CRITICAL: Must handle terminals with different color capabilities
    - CRITICAL: Must respect NO_COLOR environment variable
    - CRITICAL: Table formatting must gracefully handle various data types
    - Text truncation must preserve meaning when possible
    - Indentation must be consistent across the application
    - Table formatting must support alignment and width constraints
    - All formatting must degrade gracefully in non-ANSI terminals

Text formatting utilities for the ClickUp JSON Manager.

This module provides utilities for formatting text output, including:
- Colored output for terminal display
- Table formatting
- Indentation and alignment
"""

from enum import Enum
from typing import List, Dict, Any, Optional, Union, Tuple
import os
import sys


class Color(Enum):
    """ANSI color codes for terminal output."""
    
    # Text colors
    BLACK = "\033[30m"
    RED = "\033[31m"
    GREEN = "\033[32m"
    YELLOW = "\033[33m"
    BLUE = "\033[34m"
    MAGENTA = "\033[35m"
    CYAN = "\033[36m"
    WHITE = "\033[37m"
    
    # Background colors
    BG_BLACK = "\033[40m"
    BG_RED = "\033[41m"
    BG_GREEN = "\033[42m"
    BG_YELLOW = "\033[43m"
    BG_BLUE = "\033[44m"
    BG_MAGENTA = "\033[45m"
    BG_CYAN = "\033[46m"
    BG_WHITE = "\033[47m"
    
    # Styles
    BOLD = "\033[1m"
    ITALIC = "\033[3m"
    UNDERLINE = "\033[4m"
    
    # Reset
    RESET = "\033[0m"


def colorize(text: str, color: Color) -> str:
    """
    Add ANSI color codes to text for terminal display.
    
    Args:
        text: The text to colorize
        color: The color to apply
        
    Returns:
        Colorized text string
    """
    # Disable colors if not in a terminal or if explicitly requested
    if os.environ.get("NO_COLOR") or not sys.stdout.isatty():
        return text
        
    return f"{color.value}{text}{Color.RESET.value}"


def format_table(headers: List[str], rows: List[List[Any]], 
                align: Optional[List[str]] = None,
                min_width: Optional[List[int]] = None,
                max_width: Optional[List[int]] = None,
                colors: Optional[Dict[str, Color]] = None) -> str:
    """
    Format data as a text-based table.
    
    Args:
        headers: Column headers
        rows: Row data (list of lists)
        align: Alignment for each column ('left', 'center', 'right')
        min_width: Minimum width for each column
        max_width: Maximum width for each column
        colors: Optional color settings for headers and data
        
    Returns:
        Formatted table string
    """
    if not rows:
        return "[No data]"
        
    # Set default alignment
    if not align:
        align = ["left"] * len(headers)
    
    # Ensure all alignments are valid
    for i, a in enumerate(align):
        if a not in ("left", "center", "right"):
            align[i] = "left"
    
    # Set default min/max widths
    if not min_width:
        min_width = [0] * len(headers)
    if not max_width:
        max_width = [100] * len(headers)
    
    # Set defaults for colors
    if not colors:
        colors = {}
    
    # Get the maximum width needed for each column
    widths = []
    for i in range(len(headers)):
        col_width = len(headers[i])
        for row in rows:
            if i < len(row):
                col_width = max(col_width, len(str(row[i])))
        
        # Apply min/max constraints
        col_width = max(col_width, min_width[i])
        col_width = min(col_width, max_width[i])
        widths.append(col_width)
    
    # Create the table
    result = []
    
    # Add header
    header_row = "| "
    for i, header in enumerate(headers):
        header_text = str(header)
        if len(header_text) > widths[i]:
            header_text = header_text[:widths[i]-3] + "..."
        
        if align[i] == "center":
            header_text = header_text.center(widths[i])
        elif align[i] == "right":
            header_text = header_text.rjust(widths[i])
        else:
            header_text = header_text.ljust(widths[i])
        
        if "header" in colors:
            header_text = colorize(header_text, colors["header"])
        
        header_row += header_text + " | "
    
    result.append(header_row)
    
    # Add separator
    separator = "|-" + "-|-".join("-" * width for width in widths) + "-|"
    result.append(separator)
    
    # Add rows
    for row in rows:
        row_text = "| "
        for i in range(len(headers)):
            if i < len(row):
                cell = str(row[i]) if row[i] is not None else ""
                if len(cell) > widths[i]:
                    cell = cell[:widths[i]-3] + "..."
                
                if align[i] == "center":
                    cell = cell.center(widths[i])
                elif align[i] == "right":
                    cell = cell.rjust(widths[i])
                else:
                    cell = cell.ljust(widths[i])
                
                if i < len(row) and row[i] is not None and str(i) in colors:
                    cell = colorize(cell, colors[str(i)])
            else:
                cell = " " * widths[i]
            
            row_text += cell + " | "
        
        result.append(row_text)
    
    return "\n".join(result)


def indent_text(text: str, indent: int = 2, prefix: str = "") -> str:
    """
    Indent each line of a text block.
    
    Args:
        text: Text to indent
        indent: Number of spaces to indent
        prefix: Optional prefix for each line
        
    Returns:
        Indented text
    """
    spacer = " " * indent
    return "\n".join(f"{prefix}{spacer}{line}" for line in text.split("\n"))


def truncate(text: str, max_length: int = 80, suffix: str = "...") -> str:
    """
    Truncate text to a maximum length.
    
    Args:
        text: Text to truncate
        max_length: Maximum length
        suffix: String to append when truncated
        
    Returns:
        Truncated text
    """
    if len(text) <= max_length:
        return text
    return text[:max_length - len(suffix)] + suffix 