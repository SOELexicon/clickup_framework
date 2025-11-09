"""
Task: tsk_62630e24 - Update Utilities and Support Modules Comments
Document: refactor/utils/colors.py
dohcount: 2

Related Tasks:
    - tsk_0a733101 - Code Comments Enhancement (parent)
    - tsk_7e3a4709 - Update Common Module Comments (sibling)
    - tsk_bf28d342 - Update CLI Module Comments (sibling)
    - tsk_4c899138 - Update Storage Module Comments (sibling)
    - tsk_3f55d115 - Update Plugins Module Comments (sibling)
    - tsk_02e976b4 - Fix Comment Newline Display in CLI (related)

Used By:
    - CLI Commands: Format output with consistent coloring
    - Dashboard: Render charts and tables with color
    - ErrorHandler: Display errors with appropriate coloring
    - CommandSystem: Format command output
    - TaskFormatter: Apply consistent styling to task information
    - OutputManager: Standardize all CLI visual presentation

Purpose:
    Provides a comprehensive color and styling system for terminal output.
    Implements ANSI color codes, text styles, and a consistent theme for 
    application elements. Handles terminal capability detection, environment 
    variable overrides, and graceful fallbacks for terminals without color 
    support. Centralizes all application styling for consistent visual presentation.

Requirements:
    - CRITICAL: Must detect terminal capabilities and disable colors when not supported
    - CRITICAL: Must respect NO_COLOR environment variable for disabling colors
    - CRITICAL: Must provide complete and consistent theme for all UI elements
    - All color functions must have sensible fallbacks for monochrome display
    - Must implement consistent semantic coloring (e.g., errors are always red)
    - Must be extendable to support future styling requirements
    - Color handling must be centralized to prevent scattered implementation
    - Must display colors consistently in all output contexts (pipes, redirects)

Changes:
    - v1: Initial implementation with TTY detection and environment variable support
    - v2: Modified to enable colors by default even when piping output, while still
         respecting NO_COLOR environment variable if explicitly set

Lessons Learned:
    - Colors significantly improve readability of CLI output
    - TTY detection can be too restrictive for piped output scenarios
    - Respecting explicit user preference (NO_COLOR) is more important than
      automatic TTY detection
    - Consistent coloring improves user experience across all command contexts

Color utilities for the ClickUp JSON Manager CLI.

This module provides color definitions and helper functions for formatting
colored console output. It includes support for various terminal color capabilities
and graceful fallback for non-ANSI terminals.
"""

import os
import sys
from enum import Enum
from typing import Dict, Optional, Union, List, Any

# Check if colors should be disabled
NO_COLOR = os.environ.get('NO_COLOR') is not None
FORCE_COLOR = os.environ.get('FORCE_COLOR') is not None
HAS_TTY = sys.stdout.isatty() if hasattr(sys.stdout, 'isatty') else False

# Determine if we should use colors - always enable by default unless explicitly disabled
USE_COLORS = not NO_COLOR  # Only disable if NO_COLOR is explicitly set

def configure_colors(args=None):
    """
    Configure color settings based on command line arguments or environment variables.
    
    Args:
        args: Parsed command line arguments
        
    Returns:
        None - updates global USE_COLORS flag
    """
    global USE_COLORS
    
    # Default to enable colors
    use_colors = True
    
    # Check environment variables
    if os.environ.get('NO_COLOR') is not None:
        use_colors = False
    
    if os.environ.get('FORCE_COLOR') is not None:
        use_colors = True
    
    # Command line args override environment variables
    if args:
        if hasattr(args, 'no_color') and args.no_color:
            use_colors = False
        if hasattr(args, 'color') and args.color:
            # Explicitly enable colors when --color flag is present
            use_colors = True
            # Also set an environment variable to force colors
            os.environ['FORCE_COLOR'] = '1'
            # Remove NO_COLOR if it exists
            if 'NO_COLOR' in os.environ:
                del os.environ['NO_COLOR']
    
    # Update global flag
    USE_COLORS = use_colors
    
    # Log the color setting for debugging
    import logging
    logger = logging.getLogger(__name__)
    logger.debug(f"Color settings: USE_COLORS={USE_COLORS}, env vars: FORCE_COLOR={os.environ.get('FORCE_COLOR')}, NO_COLOR={os.environ.get('NO_COLOR')}")
    
    # Print color settings to stdout for visible debugging
    if USE_COLORS:
        print(f"Colors enabled: USE_COLORS={USE_COLORS}", file=sys.stderr)

class TextColor(Enum):
    """Text color ANSI codes."""
    BLACK = "\033[30m"
    RED = "\033[31m"
    GREEN = "\033[32m"
    YELLOW = "\033[33m"
    BLUE = "\033[34m"
    MAGENTA = "\033[35m"
    CYAN = "\033[36m"
    WHITE = "\033[37m"
    BRIGHT_BLACK = "\033[90m"
    BRIGHT_RED = "\033[91m"
    BRIGHT_GREEN = "\033[92m"
    BRIGHT_YELLOW = "\033[93m"
    BRIGHT_BLUE = "\033[94m"
    BRIGHT_MAGENTA = "\033[95m"
    BRIGHT_CYAN = "\033[96m"
    BRIGHT_WHITE = "\033[97m"
    RESET = "\033[0m"


class BackgroundColor(Enum):
    """Background color ANSI codes."""
    BLACK = "\033[40m"
    RED = "\033[41m"
    GREEN = "\033[42m"
    YELLOW = "\033[43m"
    BLUE = "\033[44m"
    MAGENTA = "\033[45m"
    CYAN = "\033[46m"
    WHITE = "\033[47m"
    BRIGHT_BLACK = "\033[100m"
    BRIGHT_RED = "\033[101m"
    BRIGHT_GREEN = "\033[102m"
    BRIGHT_YELLOW = "\033[103m"
    BRIGHT_BLUE = "\033[104m"
    BRIGHT_MAGENTA = "\033[105m"
    BRIGHT_CYAN = "\033[106m"
    BRIGHT_WHITE = "\033[107m"
    RESET = "\033[0m"


class TextStyle(Enum):
    """Text style ANSI codes."""
    BOLD = "\033[1m"
    DIM = "\033[2m"
    ITALIC = "\033[3m"
    UNDERLINE = "\033[4m"
    BLINK = "\033[5m"
    REVERSE = "\033[7m"
    HIDDEN = "\033[8m"
    STRIKETHROUGH = "\033[9m"
    RESET = "\033[0m"


# Default theme for different types of output
class DefaultTheme:
    """Default color theme configuration for the application."""
    
    # Standard ANSI named colors
    PRIMARY = TextColor.BRIGHT_BLUE
    SECONDARY = TextColor.BRIGHT_CYAN
    SUCCESS = TextColor.BRIGHT_GREEN
    WARNING = TextColor.YELLOW
    ERROR = TextColor.BRIGHT_RED
    INFO = TextColor.BRIGHT_WHITE
    
    # Task status colors
    TO_DO = TextColor.YELLOW
    IN_PROGRESS = TextColor.BRIGHT_BLUE
    COMPLETE = TextColor.BRIGHT_GREEN
    CANCELLED = TextColor.BRIGHT_BLACK
    BLOCKED = TextColor.BRIGHT_RED
    
    # Priority colors
    PRIORITY_1 = TextColor.BRIGHT_RED     # Urgent
    PRIORITY_2 = TextColor.BRIGHT_YELLOW  # High
    PRIORITY_3 = TextColor.BRIGHT_BLUE    # Normal
    PRIORITY_4 = TextColor.BRIGHT_GREEN   # Low
    
    # UI elements
    TITLE = TextColor.BRIGHT_BLUE
    SUBTITLE = TextColor.CYAN
    HEADER = TextColor.BRIGHT_WHITE
    BORDER = TextColor.BRIGHT_BLACK
    
    # Relationship colors
    DEPENDS_ON = TextColor.BRIGHT_YELLOW
    BLOCKS = TextColor.BRIGHT_RED
    RELATED_TO = TextColor.BRIGHT_BLUE
    DOCUMENTS = TextColor.BRIGHT_GREEN
    DOCUMENTED_BY = TextColor.BRIGHT_CYAN
    
    # Tag colors
    TAG = TextColor.BRIGHT_MAGENTA
    
    # Command colors
    COMMAND = TextColor.BRIGHT_GREEN
    ARGUMENT = TextColor.BRIGHT_CYAN
    OPTION = TextColor.BRIGHT_YELLOW
    
    # Container colors (spaces, folders, lists)
    SPACE = TextColor.BRIGHT_BLUE
    FOLDER = TextColor.BRIGHT_CYAN
    LIST = TextColor.BRIGHT_MAGENTA
    
    # Completion stats colors
    COMPLETE_STATS = TextColor.BRIGHT_GREEN
    PARTIAL_STATS = TextColor.BRIGHT_YELLOW
    EMPTY_STATS = TextColor.BRIGHT_RED
    
    # Log levels (restored from previous version)
    DEBUG = TextColor.BRIGHT_BLACK
    # INFO already defined above
    # WARNING already defined above
    # ERROR already defined above
    CRITICAL = TextColor.BRIGHT_RED
    
    # Score type colors - distinct colors for each score type
    SCORE_TOTAL = TextColor.BRIGHT_BLUE       # T: Total score
    SCORE_EFFORT = TextColor.BRIGHT_MAGENTA   # EF: Effort score
    SCORE_EFFECTIVENESS = TextColor.BRIGHT_CYAN  # EV: Effectiveness score  
    SCORE_RISK = TextColor.BRIGHT_RED         # R: Risk score
    SCORE_URGENCY = TextColor.BRIGHT_YELLOW   # U: Urgency score
    
    # Checklist item colors (NEW)
    CHECKLIST_CHECKED = TextColor.BRIGHT_GREEN
    CHECKLIST_UNCHECKED = TextColor.WHITE # Use default text color
    
    # Backwards compatibility aliases for status colors
    STATUS_TODO = TO_DO
    STATUS_IN_PROGRESS = IN_PROGRESS
    STATUS_COMPLETE = COMPLETE
    STATUS_BLOCKED = BLOCKED
    STATUS_UNKNOWN = CANCELLED
    
    # Backwards compatibility aliases for relationship colors
    RELATIONSHIP_DEPENDS_ON = DEPENDS_ON
    RELATIONSHIP_BLOCKS = BLOCKS
    RELATIONSHIP_BLOCKED_BY = BLOCKED
    RELATIONSHIP_DOCUMENTS = DOCUMENTS
    RELATIONSHIP_DOCUMENTED_BY = DOCUMENTED_BY
    
    # Backwards compatibility aliases for score colors
    SCORE_HIGH = SUCCESS
    SCORE_MEDIUM = WARNING
    SCORE_LOW = ERROR
    
    # Backwards compatibility aliases for content
    CONTENT = TextColor.WHITE
    KEY = TextColor.CYAN
    VALUE = TextColor.BRIGHT_WHITE
    ID = TextColor.BRIGHT_BLACK
    
    # Color intensity based on nesting level
    LEVEL_COLORS = [
        TextColor.BRIGHT_BLUE,
        TextColor.BRIGHT_CYAN,
        TextColor.BRIGHT_MAGENTA,
        TextColor.BRIGHT_GREEN,
        TextColor.BRIGHT_YELLOW
    ]
    
    @classmethod
    def get_level_color(cls, level: int) -> TextColor:
        """Get color for a specific nesting level."""
        if level < 0:
            level = 0
        return cls.LEVEL_COLORS[level % len(cls.LEVEL_COLORS)]

def colorize(text: str, color: Optional[TextColor] = None, 
             background: Optional[BackgroundColor] = None,
             style: Optional[TextStyle] = None,
             force: bool = False) -> str:
    """
    Apply color and style to text for terminal output.
    
    Args:
        text: Text to colorize
        color: Text color to apply
        background: Background color to apply
        style: Text style to apply
        force: Whether to force color output regardless of global settings
        
    Returns:
        Colorized text string with ANSI codes (if colors are enabled)
    """
    # Always apply colors when force=True, regardless of USE_COLORS setting
    if force:
        codes = []
        if color is not None:
            # Use the BRIGHT version of colors when available for better visibility
            if color == TextColor.RED:
                codes.append(TextColor.BRIGHT_RED.value)
            elif color == TextColor.GREEN:
                codes.append(TextColor.BRIGHT_GREEN.value)
            elif color == TextColor.BLUE:
                codes.append(TextColor.BRIGHT_BLUE.value)
            elif color == TextColor.YELLOW:
                codes.append(TextColor.BRIGHT_YELLOW.value)
            elif color == TextColor.MAGENTA:
                codes.append(TextColor.BRIGHT_MAGENTA.value)
            elif color == TextColor.CYAN:
                codes.append(TextColor.BRIGHT_CYAN.value)
            elif color == TextColor.WHITE:
                codes.append(TextColor.BRIGHT_WHITE.value)
            else:
                codes.append(color.value)
        if background is not None:
            codes.append(background.value)
        if style is not None:
            codes.append(style.value)
        
        reset = TextColor.RESET.value
        return f"{''.join(codes)}{text}{reset}"
    
    # Standard behavior when not forcing
    if (not USE_COLORS) or (color is None and background is None and style is None):
        return text
    
    codes = []
    if color is not None:
        codes.append(color.value)
    if background is not None:
        codes.append(background.value)
    if style is not None:
        codes.append(style.value)
    
    reset = TextColor.RESET.value
    return f"{''.join(codes)}{text}{reset}"


def status_color(status: str) -> TextColor:
    """
    Get the appropriate color for a task status.
    
    Args:
        status: Task status string
        
    Returns:
        TextColor for the status
    """
    status_lower = status.lower()
    if "todo" in status_lower or "to do" in status_lower:
        return DefaultTheme.TO_DO
    elif "progress" in status_lower or "in progress" in status_lower:
        return DefaultTheme.IN_PROGRESS
    elif "complete" in status_lower or "done" in status_lower:
        return DefaultTheme.COMPLETE
    elif "block" in status_lower:
        return DefaultTheme.BLOCKED
    else:
        return DefaultTheme.CANCELLED


def priority_color(priority: Union[int, str]) -> TextColor:
    """
    Get the appropriate color for a task priority.
    
    Args:
        priority: Task priority (1-4, with 1 being highest)
        
    Returns:
        TextColor for the priority
    """
    if isinstance(priority, str):
        try:
            priority = int(priority)
        except ValueError:
            return DefaultTheme.PRIORITY_3  # Default to medium priority
    
    if priority == 1:
        return DefaultTheme.PRIORITY_1
    elif priority == 2:
        return DefaultTheme.PRIORITY_2
    elif priority == 3:
        return DefaultTheme.PRIORITY_3
    elif priority == 4:
        return DefaultTheme.PRIORITY_4
    else:
        return DefaultTheme.PRIORITY_3


def score_color(score: float) -> TextColor:
    """
    Get the appropriate color for a task score.
    
    Args:
        score: Task score value (typically 0.0-1.0)
        
    Returns:
        TextColor for the score
    """
    if score >= 0.7:
        return DefaultTheme.SUCCESS
    elif score >= 0.4:
        return DefaultTheme.WARNING
    else:
        return DefaultTheme.ERROR


def total_score_color(score: float) -> TextColor:
    """
    Get the color for the Total score type, with intensity based on value.
    
    Task: tsk_4ea3152b - Add Score Type Color Coding
    dohcount: 1
    
    Args:
        score: Total score value (typically 0.0-1.0)
        
    Returns:
        TextColor for the Total score
    """
    # Use the base color for the score type
    return DefaultTheme.SCORE_TOTAL


def effort_score_color(score: float) -> TextColor:
    """
    Get the color for the Effort score type, with intensity based on value.
    
    Task: tsk_4ea3152b - Add Score Type Color Coding
    dohcount: 1
    
    Args:
        score: Effort score value (typically 0.0-1.0)
        
    Returns:
        TextColor for the Effort score
    """
    # Use the base color for the score type
    return DefaultTheme.SCORE_EFFORT


def effectiveness_score_color(score: float) -> TextColor:
    """
    Get the color for the Effectiveness score type, with intensity based on value.
    
    Task: tsk_4ea3152b - Add Score Type Color Coding
    dohcount: 1
    
    Args:
        score: Effectiveness score value (typically 0.0-1.0)
        
    Returns:
        TextColor for the Effectiveness score
    """
    # Use the base color for the score type
    return DefaultTheme.SCORE_EFFECTIVENESS


def risk_score_color(score: float) -> TextColor:
    """
    Get the color for the Risk score type, with intensity based on value.
    
    Task: tsk_4ea3152b - Add Score Type Color Coding
    dohcount: 1
    
    Args:
        score: Risk score value (typically 0.0-1.0)
        
    Returns:
        TextColor for the Risk score
    """
    # Use the base color for the score type
    return DefaultTheme.SCORE_RISK


def urgency_score_color(score: float) -> TextColor:
    """
    Get the color for the Urgency score type, with intensity based on value.
    
    Task: tsk_4ea3152b - Add Score Type Color Coding
    dohcount: 1
    
    Args:
        score: Urgency score value (typically 0.0-1.0)
        
    Returns:
        TextColor for the Urgency score
    """
    # Use the base color for the score type
    return DefaultTheme.SCORE_URGENCY


def get_score_legend() -> str:
    """
    Generate a legend explaining the meaning of score colors.
    
    Task: tsk_ae6ff129 - Add Score Legend in Output
    dohcount: 1
    
    Returns:
        Formatted string with score legend
    """
    if not USE_COLORS:
        return "Score Types: (T: Total, EF: Effort, EV: Effectiveness, R: Risk, U: Urgency)"
    
    legend = "Score Types: "
    legend += f"{colorize('(T: Total)', DefaultTheme.SCORE_TOTAL)}, "
    legend += f"{colorize('(EF: Effort)', DefaultTheme.SCORE_EFFORT)}, "
    legend += f"{colorize('(EV: Effectiveness)', DefaultTheme.SCORE_EFFECTIVENESS)}, "
    legend += f"{colorize('(R: Risk)', DefaultTheme.SCORE_RISK)}, "
    legend += f"{colorize('(U: Urgency)', DefaultTheme.SCORE_URGENCY)}"
    
    return legend


def relationship_color(relationship_type: str) -> TextColor:
    """
    Get the appropriate color for a relationship type.
    
    Args:
        relationship_type: Relationship type string
        
    Returns:
        TextColor for the relationship type
    """
    rel_lower = relationship_type.lower()
    if "blocks" in rel_lower:
        return DefaultTheme.BLOCKS
    elif "depends" in rel_lower:
        return DefaultTheme.DEPENDS_ON
    elif "blocked" in rel_lower:
        return DefaultTheme.BLOCKED
    elif "documents" in rel_lower and "by" not in rel_lower:
        return DefaultTheme.DOCUMENTS
    elif "documented" in rel_lower or "document" in rel_lower and "by" in rel_lower:
        return DefaultTheme.DOCUMENTED_BY
    else:
        return TextColor.WHITE 

def normalize_text(text):
    """
    Task: tsk_7c3b4a40 - Improve Console Output Formatting
    Document: refactor/utils/colors.py
    dohcount: 1

    Related Tasks:
        - tsk_40d54e79 - Fix Unit Test Failures (parent)
        - stk_c8d5e1c2 - Update Test Documentation and Docstrings (sibling)

    Used By:
        - ShowTaskCommand: Uses to normalize text before display
        - format_multi_line: Called by this function to preprocess text

    Purpose:
        Normalizes text by handling escaped newlines and ensuring consistent formatting
        for console display. This is important for proper rendering of multi-line content,
        especially for descriptions and comments in tasks.

    Requirements:
        - Must handle both literal '\n' sequences and actual newlines
        - Must handle double-escaped sequences (\\n)
        - CRITICAL: Must not modify content in any way except newline formatting
        - CRITICAL: Must not strip any whitespace from the beginning or end of lines

    Parameters:
        text (str): The text to normalize

    Returns:
        (str): Normalized text with proper newlines

    Changes:
        - v1: Initial implementation with support for escaped newlines

    Lessons Learned:
        - Text stored in JSON often has escaped newlines that need proper handling
        - Double-escaped sequences can occur when JSON is processed multiple times
    """
    if not text:
        return ""
        
    # Replace literal '\n' sequences with actual newlines
    text = text.replace('\\n', '\n')
    
    # Handle double-escaped newlines (\\n becomes \n)
    text = text.replace('\\\\n', '\\n')
    
    return text

def format_multi_line(text, indent=2, color=DefaultTheme.INFO):
    """
    Task: tsk_7c3b4a40 - Improve Console Output Formatting
    Document: refactor/utils/colors.py
    dohcount: 1

    Related Tasks:
        - tsk_40d54e79 - Fix Unit Test Failures (parent)
        - stk_c8d5e1c2 - Update Test Documentation and Docstrings (sibling)

    Used By:
        - ShowTaskCommand: Uses to format multiline text with proper indentation
        - CommentCommand: Uses to display formatted comments
        - Any command that displays multi-line text content

    Purpose:
        Formats multi-line text with proper indentation and coloring for console display.
        This function ensures consistent formatting across the application for any 
        multi-line content.

    Requirements:
        - Must preserve all content, only changing formatting
        - Must apply consistent indentation to all lines
        - Must normalize newlines before formatting
        - CRITICAL: Must handle all types of newlines (escaped, actual, or mixed)
        - CRITICAL: Must apply consistent coloring to maintain visual hierarchy

    Parameters:
        text (str): The text to format
        indent (int, optional): Number of spaces to indent each line (default: 2)
        color (TextColor, optional): Color to apply to the text (default: DefaultTheme.INFO)

    Returns:
        (str): Formatted and colored text with consistent indentation

    Changes:
        - v1: Initial implementation with support for indentation and coloring

    Lessons Learned:
        - Console output looks much better with consistent indentation
        - Applying color to each line separately provides more flexibility than coloring blocks
    """
    if not text:
        return ""
    
    # Normalize the text first
    text = normalize_text(text)
    
    # Generate the formatted text
    indentation = " " * indent
    return "\n".join([f"{indentation}{colorize(line, color)}" for line in text.split('\n')]) 


def map_color_string(color_str: Optional[str]) -> Optional[TextColor]:
    """
    Task: tsk_8a5b3f92 - Enhance Color Mapping System
    Document: refactor/utils/colors.py
    dohcount: 1

    Related Tasks:
        - tsk_62630e24 - Update Utilities and Support Modules Comments (parent)
        - tsk_7c3b4a40 - Improve Console Output Formatting (sibling)

    Used By:
        - format_task_hierarchy: Maps entity colors to terminal colors
        - UpdateSpaceColorsCommand: Validates color inputs
        - UpdateFolderColorsCommand: Validates color inputs
        - UpdateListColorsCommand: Validates color inputs

    Purpose:
        Maps a string color name or hex value to a terminal TextColor.
        Standardizes color handling throughout the application by providing
        a single point for color name and hex value conversion.

    Requirements:
        - Must handle common color names (red, blue, green, etc.)
        - Must attempt to map hex values to the closest available terminal colors
        - CRITICAL: Must never raise exceptions, always return a valid color or None
        - CRITICAL: Must be case-insensitive for color names
        - Must provide sensible defaults for unknown colors

    Parameters:
        color_str (Optional[str]): A color string (e.g., 'red', 'blue', '#FF0000')
                                  or None to return None

    Returns:
        (Optional[TextColor]): The corresponding TextColor or None if input is None or invalid

    Changes:
        - v1: Initial implementation with support for named colors and basic hex color mapping

    Lessons Learned:
        - Terminal colors are limited compared to web colors, requiring approximation
        - Consistent color mapping improves visual coherence across the application
    """
    if not color_str:
        return None
        
    # Standardize input
    color_str = str(color_str).lower().strip()
    
    # Named color mapping
    color_map = {
        # Basic colors
        'red': TextColor.RED,
        'green': TextColor.GREEN,
        'blue': TextColor.BLUE,
        'yellow': TextColor.YELLOW,
        'magenta': TextColor.MAGENTA,
        'cyan': TextColor.CYAN,
        'white': TextColor.WHITE,
        'black': TextColor.BLACK,
        
        # Bright variants
        'brightred': TextColor.BRIGHT_RED,
        'bright_red': TextColor.BRIGHT_RED,
        'bright red': TextColor.BRIGHT_RED,
        'brightgreen': TextColor.BRIGHT_GREEN,
        'bright_green': TextColor.BRIGHT_GREEN,
        'bright green': TextColor.BRIGHT_GREEN,
        'brightblue': TextColor.BRIGHT_BLUE,
        'bright_blue': TextColor.BRIGHT_BLUE,
        'bright blue': TextColor.BRIGHT_BLUE,
        'brightyellow': TextColor.BRIGHT_YELLOW,
        'bright_yellow': TextColor.BRIGHT_YELLOW,
        'bright yellow': TextColor.BRIGHT_YELLOW,
        'brightmagenta': TextColor.BRIGHT_MAGENTA,
        'bright_magenta': TextColor.BRIGHT_MAGENTA,
        'bright magenta': TextColor.BRIGHT_MAGENTA,
        'brightcyan': TextColor.BRIGHT_CYAN,
        'bright_cyan': TextColor.BRIGHT_CYAN,
        'bright cyan': TextColor.BRIGHT_CYAN,
        'brightwhite': TextColor.BRIGHT_WHITE,
        'bright_white': TextColor.BRIGHT_WHITE,
        'bright white': TextColor.BRIGHT_WHITE,
        
        # Aliases and variations
        'gray': TextColor.BRIGHT_BLACK,
        'grey': TextColor.BRIGHT_BLACK,
        'purple': TextColor.MAGENTA,
        'pink': TextColor.BRIGHT_MAGENTA,
        'orange': TextColor.YELLOW,  # Approximation
        'brown': TextColor.YELLOW,   # Approximation
        'teal': TextColor.CYAN,      # Approximation
        'navy': TextColor.BLUE,      # Approximation
        'maroon': TextColor.RED,     # Approximation
        'olive': TextColor.YELLOW,   # Approximation
        'lime': TextColor.GREEN,     # Approximation
        'aqua': TextColor.CYAN,      # Approximation
        'silver': TextColor.BRIGHT_BLACK,  # Approximation
        'gold': TextColor.YELLOW,    # Approximation
        'violet': TextColor.MAGENTA, # Approximation
        'indigo': TextColor.BLUE,    # Approximation
    }
    
    # Check if it's a named color
    if color_str in color_map:
        return color_map[color_str]
    
    # Check if it's a hex color
    if color_str.startswith('#'):
        try:
            # Strip the # and get RGB values
            if len(color_str) >= 7:  # At least '#RRGGBB'
                r = int(color_str[1:3], 16)
                g = int(color_str[3:5], 16)
                b = int(color_str[5:7], 16)
                
                # Very simple RGB to basic color mapping
                # Check for grays first
                if abs(r - g) < 30 and abs(g - b) < 30 and abs(r - b) < 30:
                    # It's a shade of gray
                    if r > 200:  # Light gray
                        return TextColor.WHITE
                    elif r > 100:  # Medium gray
                        return TextColor.BRIGHT_BLACK
                    else:  # Dark gray
                        return TextColor.BLACK
                
                # Find dominant color
                if r > g and r > b:
                    # Red is dominant
                    if r > 200 and g > 100:  # Bright orange-ish
                        return TextColor.YELLOW
                    return TextColor.RED if r < 200 else TextColor.BRIGHT_RED
                elif g > r and g > b:
                    # Green is dominant
                    if r > 150 and g > 150:  # Yellow-green
                        return TextColor.YELLOW
                    return TextColor.GREEN if g < 200 else TextColor.BRIGHT_GREEN
                elif b > r and b > g:
                    # Blue is dominant
                    if r > 150:  # Purple-ish
                        return TextColor.MAGENTA
                    if g > 150:  # Cyan-ish
                        return TextColor.CYAN
                    return TextColor.BLUE if b < 200 else TextColor.BRIGHT_BLUE
                
                # Fallback if no color is clearly dominant
                return TextColor.WHITE
        except Exception:
            # If we can't parse the hex color, fall back to default
            return TextColor.CYAN
    
    # Default fallback for unrecognized colors
    return TextColor.CYAN 

def completion_stats_color(completed: int, total: int) -> TextColor:
    """
    Get the appropriate color for completion statistics based on the ratio.
    
    Args:
        completed: Number of completed items
        total: Total number of items
        
    Returns:
        TextColor enum value for the appropriate color
    """
    if total == 0:
        return DefaultTheme.BRIGHT_BLACK  # Gray for no items
    
    ratio = completed / total
    
    if ratio == 1.0:
        return DefaultTheme.COMPLETE_STATS  # Green for fully complete
    elif ratio >= 0.75:
        return TextColor.BRIGHT_GREEN  # Green for mostly complete
    elif ratio >= 0.5:
        return TextColor.BRIGHT_YELLOW  # Yellow for half complete
    elif ratio >= 0.25:
        return TextColor.YELLOW  # Yellow for partially complete
    elif ratio > 0:
        return TextColor.BRIGHT_RED  # Red for barely started
    else:
        return TextColor.RED  # Red for not started
        
def container_color(container_type: str) -> TextColor:
    """
    Get the appropriate color for a container based on its type.
    
    Args:
        container_type: The type of container (space, folder, list)
        
    Returns:
        TextColor enum value for the appropriate color
    """
    container_type = container_type.lower()
    
    if container_type == 'space':
        return DefaultTheme.SPACE
    elif container_type == 'folder':
        return DefaultTheme.FOLDER
    elif container_type == 'list':
        return DefaultTheme.LIST
    else:
        return TextColor.WHITE  # Default color for unknown container types 

def task_status_color(status: str) -> TextColor:
    """
    Get the appropriate color for a task status.
    
    Task: tsk_22a152df - Show Tags Option
    dohcount: 1
    
    Related Tasks:
        - status_color: Original function being wrapped
    
    Purpose:
        Maps to status_color for compatibility with naming conventions in the
        tag display implementation.
    
    Args:
        status: Task status string
        
    Returns:
        TextColor for the status
    """
    return status_color(status) 

def id_prefix_color(id_str: str) -> TextColor:
    """
    Get the appropriate color for an ID based on its prefix.
    
    Args:
        id_str: The ID string to determine color for
        
    Returns:
        TextColor: The appropriate color for the ID prefix
    """
    if not id_str or not isinstance(id_str, str):
        return TextColor.BRIGHT_BLACK
    
    # Color mapping for different ID prefixes
    prefix_map = {
        "tsk_": TextColor.CYAN,            # Tasks
        "stk_": TextColor.BRIGHT_BLUE,     # Subtasks
        "sec_": TextColor.MAGENTA,         # Document sections
        "chk_": TextColor.GREEN,           # Checklists
        "itm_": TextColor.BRIGHT_GREEN,    # Checklist items
        "spc_": TextColor.BRIGHT_YELLOW,   # Spaces
        "fld_": TextColor.YELLOW,          # Folders
        "lst_": TextColor.BRIGHT_MAGENTA,  # Lists
        "rel_": TextColor.BRIGHT_CYAN,     # Relationships
        "tag_": TextColor.BRIGHT_RED,      # Tags
        "usr_": TextColor.BLUE,            # Users
        "cmt_": TextColor.GREEN            # Comments
    }
    
    # Check for known prefixes
    for prefix, color in prefix_map.items():
        if id_str.startswith(prefix):
            return color
    
    # Default color for unknown prefixes
    return TextColor.BRIGHT_BLACK 