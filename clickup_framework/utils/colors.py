"""
Color Utilities Module

Provides ANSI color codes and styling for terminal output.
"""

import os
import sys
from enum import Enum
from typing import Optional


# Check if colors should be disabled
NO_COLOR = os.environ.get('NO_COLOR') is not None
FORCE_COLOR = os.environ.get('FORCE_COLOR') is not None
HAS_TTY = sys.stdout.isatty() if hasattr(sys.stdout, 'isatty') else False

# Determine if we should use colors - enable by default unless explicitly disabled
USE_COLORS = not NO_COLOR


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


class TextStyle(Enum):
    """Text style ANSI codes."""
    BOLD = "\033[1m"
    DIM = "\033[2m"
    ITALIC = "\033[3m"
    UNDERLINE = "\033[4m"
    RESET = "\033[0m"


def colorize(
    text: str,
    color: Optional[TextColor] = None,
    style: Optional[TextStyle] = None,
    force: bool = False
) -> str:
    """
    Apply color and style to text for terminal output.

    Args:
        text: Text to colorize
        color: Text color to apply
        style: Text style to apply
        force: Whether to force color output regardless of global settings

    Returns:
        Colorized text string with ANSI codes (if colors are enabled)
    """
    if (not USE_COLORS and not force) or (color is None and style is None):
        return text

    codes = []
    if color is not None:
        codes.append(color.value)
    if style is not None:
        codes.append(style.value)

    reset = TextColor.RESET.value
    return f"{''.join(codes)}{text}{reset}"


def status_to_code(status: str) -> str:
    """
    Convert task status to a 3-letter code.

    Args:
        status: Task status string

    Returns:
        3-letter status code (uppercase)
    """
    if not status:
        return "UNK"

    status_lower = str(status).lower().strip()

    # Common status mappings
    status_map = {
        "to do": "TDO",
        "todo": "TDO",
        "open": "OPN",
        "in progress": "PRG",
        "in review": "REV",
        "complete": "CMP",
        "completed": "CMP",
        "done": "DON",
        "closed": "CLS",
        "blocked": "BLK",
        "block": "BLK",
        "testing": "TST",
        "backlog": "BLG",
        "ready": "RDY",
    }

    # Check if we have a mapping
    if status_lower in status_map:
        return status_map[status_lower]

    # Otherwise, take first 3 letters and uppercase
    return status[:3].upper()


def status_color(status: str) -> TextColor:
    """
    Get the appropriate color for a task status.

    Args:
        status: Task status string

    Returns:
        TextColor for the status
    """
    if not status:
        return TextColor.WHITE

    status_lower = str(status).lower().strip()

    if status_lower in ("to do", "todo", "open"):
        return TextColor.YELLOW
    elif status_lower in ("in progress", "in review"):
        return TextColor.BRIGHT_BLUE
    elif status_lower in ("complete", "completed", "done", "closed"):
        return TextColor.BRIGHT_GREEN
    elif status_lower in ("blocked", "block"):
        return TextColor.BRIGHT_RED
    else:
        return TextColor.WHITE


def priority_color(priority) -> TextColor:
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
        except (ValueError, TypeError):
            return TextColor.WHITE

    if priority == 1:
        return TextColor.BRIGHT_RED  # Urgent
    elif priority == 2:
        return TextColor.BRIGHT_YELLOW  # High
    elif priority == 3:
        return TextColor.BRIGHT_BLUE  # Normal
    elif priority == 4:
        return TextColor.BRIGHT_GREEN  # Low
    else:
        return TextColor.WHITE


def container_color(container_type: str) -> TextColor:
    """
    Get the appropriate color for a container based on its type.

    Args:
        container_type: The type of container (workspace, space, folder, list)

    Returns:
        TextColor enum value for the appropriate color
    """
    container_type = str(container_type).lower()

    if container_type == 'workspace':
        return TextColor.BRIGHT_MAGENTA
    elif container_type == 'space':
        return TextColor.BRIGHT_BLUE
    elif container_type == 'folder':
        return TextColor.BRIGHT_CYAN
    elif container_type == 'list':
        return TextColor.BRIGHT_YELLOW
    else:
        return TextColor.WHITE


def completion_color(completed: int, total: int) -> TextColor:
    """
    Get the appropriate color for completion statistics.

    Args:
        completed: Number of completed items
        total: Total number of items

    Returns:
        TextColor enum value for the appropriate color
    """
    if total == 0:
        return TextColor.BRIGHT_BLACK  # Gray for no items

    ratio = completed / total

    if ratio == 1.0:
        return TextColor.BRIGHT_GREEN  # Green for fully complete
    elif ratio >= 0.75:
        return TextColor.GREEN  # Green for mostly complete
    elif ratio >= 0.5:
        return TextColor.BRIGHT_YELLOW  # Yellow for half complete
    elif ratio >= 0.25:
        return TextColor.YELLOW  # Yellow for partially complete
    else:
        return TextColor.BRIGHT_RED  # Red for barely started


# Task type emoji mapping
TASK_TYPE_EMOJI = {
    "task": "📝",
    "bug": "🐛",
    "feature": "🚀",
    "refactor": "♻️",
    "documentation": "📚",
    "docs": "📚",
    "enhancement": "✨",
    "chore": "🧹",
    "research": "🔬",
    "testing": "🧪",
    "test": "🧪",
    "security": "🛡️",
    "project": "📂",
    "milestone": "🏁"
}


def get_task_emoji(task_type: str) -> str:
    """
    Get the emoji for a task type.

    Args:
        task_type: The task type

    Returns:
        The emoji for the task type
    """
    if not task_type:
        return TASK_TYPE_EMOJI["task"]  # Default to task emoji

    # Normalize task type
    normalized_type = str(task_type).lower().strip()

    # Return the corresponding emoji or default to task emoji
    return TASK_TYPE_EMOJI.get(normalized_type, TASK_TYPE_EMOJI["task"])
