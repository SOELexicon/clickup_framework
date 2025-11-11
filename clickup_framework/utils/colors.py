"""
Color Utilities Module

Provides ANSI color codes and styling for terminal output.
"""

import os
import re
import sys
from enum import Enum
from typing import Optional


# Check if colors should be disabled
NO_COLOR = os.environ.get("NO_COLOR") is not None
FORCE_COLOR = os.environ.get("FORCE_COLOR") is not None
HAS_TTY = sys.stdout.isatty() if hasattr(sys.stdout, "isatty") else False

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
    force: bool = False,
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
    # Check HIDE_ANSI environment variable directly alongside NO_COLOR
    # This avoids circular dependency with ContextManager
    should_use_colors = USE_COLORS
    if not force:
        # If HIDE_ANSI is set to '1', disable colors (consistent with NO_COLOR behavior)
        hide_ansi = os.environ.get("HIDE_ANSI", "").strip()
        if hide_ansi == "1":
            should_use_colors = False

    if (not should_use_colors and not force) or (color is None and style is None):
        return text

    codes = []
    if color is not None:
        codes.append(color.value)
    if style is not None:
        codes.append(style.value)

    reset = TextColor.RESET.value
    return f"{''.join(codes)}{text}{reset}"


def strip_ansi(text: str) -> str:
    """
    Remove ANSI escape codes from text.

    Args:
        text: Text containing ANSI codes

    Returns:
        Text with ANSI codes removed
    """
    ansi_escape = re.compile(r"\x1B(?:[@-Z\\-_]|\[[0-?]*[ -/]*[@-~])")
    return ansi_escape.sub("", text)


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

    # Comprehensive status mappings for common ClickUp workflows
    status_map = {
        # Starting states
        "to do": "TDO",
        "todo": "TDO",
        "open": "OPN",
        "backlog": "BLG",
        "ready": "RDY",
        # Active work states
        "in progress": "PRG",
        "in development": "DEV",
        "in dev": "DEV",
        "wip": "WIP",
        "working": "WRK",
        # Testing states
        "testing": "TST",
        "test": "TST",
        "qa": "QA ",
        "validation": "VAL",
        "validating": "VAL",
        # Review states
        "in review": "REV",
        "review": "REV",
        "approval": "APR",
        "pending approval": "PND",
        "awaiting approval": "AWA",
        # Accepted states
        "accepted": "ACC",
        "approved": "APP",
        "ready to deploy": "RTD",
        # Committed states
        "committed": "CMT",
        "comitted": "CMT",  # Common typo
        "deploying": "DPL",
        "staging": "STG",
        # Complete states
        "complete": "CMP",
        "completed": "CMP",
        "done": "DON",
        "closed": "CLS",
        "resolved": "RES",
        "finished": "FIN",
        # Rejected states
        "rejected": "REJ",
        "declined": "DEC",
        "cancelled": "CAN",
        "canceled": "CAN",
        "abandoned": "ABD",
        # Blocked states
        "blocked": "BLK",
        "block": "BLK",
        "on hold": "HLD",
        "waiting": "WAI",
        "paused": "PAU",
    }

    # Check if we have a mapping
    if status_lower in status_map:
        return status_map[status_lower]

    # Otherwise, take first 3 letters and uppercase
    return status[:3].upper()


def status_color(status: str) -> TextColor:
    """
    Get the appropriate color for a task status.

    Provides comprehensive color mapping for common ClickUp statuses:
    - Open/To Do: Yellow (starting state)
    - In Progress/Development: Bright Blue (active work)
    - Testing/QA: Cyan (quality assurance)
    - Review/Approval: Magenta (awaiting decision)
    - Accepted: Bright Cyan (approved)
    - Committed: Blue (committed to deployment)
    - Complete/Closed: Bright Green (finished)
    - Rejected: Red (declined)
    - Blocked: Bright Red (blocked)

    Args:
        status: Task status string

    Returns:
        TextColor for the status
    """
    if not status:
        return TextColor.WHITE

    status_lower = str(status).lower().strip()

    # Starting/Queued states
    if status_lower in ("to do", "todo", "open", "backlog", "ready"):
        return TextColor.YELLOW
    # Active work states
    elif status_lower in ("in progress", "in development", "in dev", "wip", "working"):
        return TextColor.BRIGHT_BLUE
    # Testing/QA states
    elif status_lower in ("testing", "test", "qa", "validation", "validating"):
        return TextColor.CYAN
    # Review/Approval states
    elif status_lower in ("in review", "review", "approval", "pending approval", "awaiting approval"):
        return TextColor.MAGENTA
    # Accepted/Approved states
    elif status_lower in ("accepted", "approved", "ready to deploy"):
        return TextColor.BRIGHT_CYAN
    # Committed/Deployment states
    elif status_lower in ("committed", "comitted", "deploying", "staging"):
        return TextColor.BLUE
    # Complete states
    elif status_lower in ("complete", "completed", "done", "closed", "resolved", "finished"):
        return TextColor.BRIGHT_GREEN
    # Rejected/Cancelled states
    elif status_lower in ("rejected", "declined", "cancelled", "canceled", "abandoned"):
        return TextColor.RED
    # Blocked states
    elif status_lower in ("blocked", "block", "on hold", "waiting", "paused"):
        return TextColor.BRIGHT_RED
    # Default fallback
    else:
        return TextColor.WHITE


def priority_color(priority) -> TextColor:
    """
    Get the appropriate color for a task priority.

    Args:
        priority: Task priority (1-4, with 1 being highest)

    Returns:
        TextColor for the priority according to requirements:
        - P1 (Urgent): Bright Red
        - P2 (High): Yellow
        - P3 (Normal): White
        - P4 (Low): Gray
    """
    if isinstance(priority, str):
        try:
            priority = int(priority)
        except (ValueError, TypeError):
            return TextColor.WHITE

    if priority == 1:
        return TextColor.BRIGHT_RED  # P1 - Urgent
    elif priority == 2:
        return TextColor.YELLOW  # P2 - High
    elif priority == 3:
        return TextColor.WHITE  # P3 - Normal
    elif priority == 4:
        return TextColor.BRIGHT_BLACK  # P4 - Low (gray)
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

    if container_type == "workspace":
        return TextColor.BRIGHT_MAGENTA
    elif container_type == "space":
        return TextColor.BRIGHT_BLUE
    elif container_type == "folder":
        return TextColor.BRIGHT_CYAN
    elif container_type == "list":
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


# Task status icon mapping
STATUS_ICON_MAP = {
    # Todo/Open states
    "to do": "⬜",
    "todo": "⬜",
    "open": "⬜",
    "backlog": "📋",
    "ready": "🔵",

    # In progress states
    "in progress": "🔄",
    "in development": "⚙️",
    "in dev": "⚙️",
    "in review": "👀",
    "active": "▶️",
    "working": "💼",
    "started": "🟡",

    # Complete states
    "complete": "✅",
    "completed": "✅",
    "done": "✅",
    "closed": "✅",

    # Blocked states
    "blocked": "🚫",
    "block": "🚫",

    # Testing states
    "testing": "🧪",
    "qa": "🔍",

    # Other states
    "on hold": "⏸️",
    "paused": "⏸️",
    "cancelled": "❌",
    "canceled": "❌",
}


def get_status_icon(status: str, fallback_to_code: bool = True) -> str:
    """
    Get the icon/emoji for a task status.

    Args:
        status: The task status string
        fallback_to_code: If True, falls back to 3-letter code when no icon is found

    Returns:
        Icon/emoji for the status, or 3-letter code if fallback is enabled

    Examples:
        >>> get_status_icon("in progress")
        '🔄'
        >>> get_status_icon("to do")
        '⬜'
        >>> get_status_icon("custom status", fallback_to_code=True)
        'CUS'
    """
    if not status:
        return "❓" if not fallback_to_code else "UNK"

    # Normalize status
    status_lower = str(status).lower().strip()

    # Check if we have a direct mapping
    if status_lower in STATUS_ICON_MAP:
        return STATUS_ICON_MAP[status_lower]

    # Fallback to code if requested
    if fallback_to_code:
        return status_to_code(status)

    # Otherwise return a generic marker
    return "◻️"


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
    "milestone": "🏁",
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
