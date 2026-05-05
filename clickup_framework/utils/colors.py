"""
Color Utilities Module

Provides ANSI color codes and styling for terminal output.
"""

import os
import re
import sys
import platform
from enum import Enum
from typing import Optional, Dict, Any, List


# Check if colors should be disabled
NO_COLOR = os.environ.get("NO_COLOR") is not None
FORCE_COLOR = os.environ.get("FORCE_COLOR") is not None
HAS_TTY = sys.stdout.isatty() if hasattr(sys.stdout, "isatty") else False

# Enable VT100 mode for Windows (PowerShell/Windows Terminal)
def _enable_vt100_mode():
    """Enable VT100/VT220 terminal mode for Windows to support ANSI escape codes."""
    if platform.system() == 'Windows':
        try:
            import ctypes
            from ctypes import wintypes
            
            kernel32 = ctypes.windll.kernel32
            
            # Get console handles
            STD_OUTPUT_HANDLE = -11
            STD_ERROR_HANDLE = -12
            
            # Enable virtual terminal processing for stdout
            handle_out = kernel32.GetStdHandle(STD_OUTPUT_HANDLE)
            if handle_out and handle_out != -1:
                # Get current mode
                current_mode = wintypes.DWORD()
                if kernel32.GetConsoleMode(handle_out, ctypes.byref(current_mode)):
                    # Enable virtual terminal processing (0x0004)
                    # Also keep existing flags: ENABLE_PROCESSED_OUTPUT (0x0001) | ENABLE_WRAP_AT_EOL_OUTPUT (0x0002)
                    new_mode = current_mode.value | 0x0004
                    kernel32.SetConsoleMode(handle_out, new_mode)
            
            # Enable virtual terminal processing for stderr
            handle_err = kernel32.GetStdHandle(STD_ERROR_HANDLE)
            if handle_err and handle_err != -1:
                current_mode = wintypes.DWORD()
                if kernel32.GetConsoleMode(handle_err, ctypes.byref(current_mode)):
                    new_mode = current_mode.value | 0x0004
                    kernel32.SetConsoleMode(handle_err, new_mode)
        except Exception:
            pass  # If enabling fails, continue anyway

# Enable VT100 mode on import (for Windows)
_enable_vt100_mode()

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


# Task type emoji mapping - comprehensive mapping for all ClickUp task types
# Includes built-in types, custom workspace types, and common aliases
TASK_TYPE_EMOJI = {
    # Default/Built-in types
    "task": "📝",
    "milestone": "🏁",
    "form_response": "📝",
    "meeting_note": "📋",

    # Development & Code
    "feature": "🚀",
    "feat": "🚀",  # Alias
    "f": "🚀",  # Alias
    "features": "🚀",  # Plural
    "bug": "🐛",
    "b": "🐛",  # Alias
    "bugs": "🐛",  # Plural
    "refactor": "♻️",
    "enhancement": "✨",
    "chore": "🧹",

    # Documentation & Content
    "documentation": "📚",
    "docs": "📚",
    "doc": "📚",  # Alias
    "content": "📄",
    "c": "📄",  # Alias
    "user_story": "📖",
    "user story": "📖",
    "story": "📖",
    "us": "📖",  # Alias
    "lesson_learned": "📚",
    "lesson learned": "📚",
    "lesson": "📚",
    "ll": "📚",  # Alias

    # Project Management
    "project": "📂",
    "proj": "📂",
    "p": "📂",  # Alias
    "projects": "📂",  # Plural
    "project_file": "📁",
    "project file": "📁",
    "file": "📁",
    "pf": "📁",  # Alias
    "goal": "🎯",
    "g": "🎯",  # Alias
    "goals": "🎯",  # Plural
    "objective": "🏁",
    "obj": "🏁",
    "o": "🏁",  # Alias
    "objectives": "🏁",  # Plural

    # Testing & Quality
    "test_result": "🧪",
    "test result": "🧪",
    "test": "🧪",
    "testing": "🧪",
    "tr": "🧪",  # Alias
    "tests": "🧪",  # Plural
    "trest": "🏷️",  # Custom type (possibly typo)
    "warning": "⚠️",
    "warn": "⚠️",
    "w": "⚠️",  # Alias
    "warnings": "⚠️",  # Plural
    "error": "❌",
    "err": "❌",
    "e": "❌",  # Alias
    "errors": "❌",  # Plural

    # Git & Version Control
    "git": "🔀",
    "commit": "💾",
    "cmt": "💾",
    "commits": "💾",  # Plural
    "pull_request": "🔀",
    "pull request": "🔀",
    "pr": "🔀",
    "merge": "🔀",  # Alias
    "branch": "🌿",
    "br": "🌿",
    "branches": "🌿",  # Plural

    # CI/CD & Automation
    "actions_run": "⚙️",
    "actions run": "⚙️",
    "action": "⚙️",
    "ar": "⚙️",  # Alias
    "command": "⌨️",
    "cmd": "⌨️",
    "commands": "⌨️",  # Plural
    "process": "⚙️",
    "proc": "⚙️",
    "processes": "⚙️",  # Plural
    "utility": "🛠️",

    # ClickUp Entity Categories (for command documentation tasks)
    "clickup task": "✅",
    "clickup display": "📊",
    "clickup context": "🎯",
    "clickup custom field": "🏷️",
    "clickup checklist": "☑️",
    "clickup attachment": "📎",
    "clickup list": "📋",
    "clickup folder": "📁",
    "clickup space": "🌐",
    "clickup comment": "💬",
    "clickup doc": "📄",
    "clickup automation": "🤖",

    # Other Types
    "account": "👤",
    "acct": "👤",
    "a": "👤",  # Alias
    "accounts": "👤",  # Plural
    "request": "📨",
    "req": "📨",
    "requests": "📨",  # Plural
    "resource": "📦",
    "res": "📦",
    "resources": "📦",  # Plural
    "requirement": "🎨",
    "requirements": "🎨",  # Plural
    "idea": "💡",
    "i": "💡",  # Alias
    "ideas": "💡",  # Plural
    "category": "📑",
    "cat": "📑",
    "categories": "📑",  # Plural
    "item": "📦",
    "itm": "📦",
    "items": "📦",  # Plural
    "research": "🔬",
    "security": "🛡️",
}


# Task type color mapping
TASK_TYPE_COLOR = {
    # Default/Built-in types
    "task": TextColor.BRIGHT_BLACK,
    "milestone": TextColor.BRIGHT_MAGENTA,
    "form_response": TextColor.BRIGHT_WHITE,
    "meeting_note": TextColor.BRIGHT_WHITE,

    # Development & Code
    "feature": TextColor.BRIGHT_BLUE,
    "feat": TextColor.BRIGHT_BLUE,
    "bug": TextColor.BRIGHT_RED,
    "refactor": TextColor.BRIGHT_GREEN,
    "enhancement": TextColor.BRIGHT_CYAN,
    "chore": TextColor.BRIGHT_BLACK,

    # Documentation & Content
    "documentation": TextColor.BRIGHT_YELLOW,
    "docs": TextColor.BRIGHT_YELLOW,
    "content": TextColor.WHITE,
    "user_story": TextColor.BRIGHT_BLUE,
    "user story": TextColor.BRIGHT_BLUE,

    # Project Management
    "project": TextColor.BRIGHT_MAGENTA,
    "goal": TextColor.BRIGHT_YELLOW,
    "objective": TextColor.BRIGHT_RED,

    # Testing & Quality
    "test_result": TextColor.BRIGHT_GREEN,
    "warning": TextColor.BRIGHT_YELLOW,
    "error": TextColor.BRIGHT_RED,

    # Git & Version Control
    "git": TextColor.BRIGHT_BLUE,
    "commit": TextColor.BRIGHT_GREEN,
    "pull_request": TextColor.BRIGHT_MAGENTA,
    "branch": TextColor.BRIGHT_CYAN,

    # ClickUp Entity Categories
    "clickup task": TextColor.BRIGHT_GREEN,
    "clickup space": TextColor.BRIGHT_BLUE,
    "clickup context": TextColor.BRIGHT_YELLOW,
    
    # Custom Types from discovery
    "plugin": TextColor.BRIGHT_CYAN,
}


def get_task_type_color(task_type: str) -> TextColor:
    """Get the color for a task type."""
    if not task_type:
        return TextColor.BRIGHT_BLACK
    
    normalized_type = str(task_type).lower().strip()
    return TASK_TYPE_COLOR.get(normalized_type, TextColor.WHITE)


def get_task_type_info(task: Dict[str, Any]) -> Dict[str, Any]:
    """
    Extract task type information (id, name, emoji, color) from a task object.
    
    Args:
        task: Task dictionary from API
        
    Returns:
        Dict with 'id', 'name', 'emoji', 'color'
    """
    # custom_item_id is the numeric ID
    type_id = task.get('custom_item_id')
    
    # Try to find a name. Sometimes ClickUp tasks have a 'custom_type' field if enriched,
    # otherwise we might have to rely on our own mapping or the task name prefix.
    type_name = task.get('custom_type')
    
    # Common ID to Name mapping
    id_to_name = {
        1: "Milestone",
        3: "Form",
        4: "Meeting",
    }
    
    if not type_name and type_id in id_to_name:
        type_name = id_to_name[type_id]
        
    if not type_name:
        # Check task name for (Category) pattern
        category = extract_category_from_name(task.get('name', ''))
        if category:
            type_name = category
            
    if not type_name:
        if type_id is None or type_id == 1:
             type_name = "Task"
        else:
             type_name = f"Type {type_id}"
             
    # Normalize for lookup
    norm_name = type_name.lower().strip()
    
    # Fix for Plugin type if ID is 1030 (based on previous discovery)
    if type_id == 1030:
        type_name = "Plugin"
        norm_name = "plugin"
    elif type_id == 1001:
        type_name = "Feature"
        norm_name = "feature"
    elif type_id == 1002:
        type_name = "Bug"
        norm_name = "bug"

    emoji = get_task_emoji(norm_name)
    color = get_task_type_color(norm_name)
    
    return {
        'id': type_id,
        'name': type_name,
        'emoji': emoji,
        'color': color
    }


def extract_category_from_name(task_name: str) -> Optional[str]:
    """
    Extract category from task name if it follows the pattern "(Category) Task Name".

    Args:
        task_name: The task name string

    Returns:
        The extracted category string, or None if no category found

    Examples:
        >>> extract_category_from_name("(GIT) CUM pull")
        'GIT'
        >>> extract_category_from_name("(ClickUp Task) CUM task_create")
        'ClickUp Task'
        >>> extract_category_from_name("Regular Task Name")
        None
    """
    if not task_name:
        return None

    # Check if task name starts with (Category) pattern
    import re
    match = re.match(r'^\(([^)]+)\)', task_name.strip())
    if match:
        return match.group(1)

    return None


def get_task_emoji(task_type: str, task_name: Optional[str] = None) -> str:
    """
    Get the emoji for a task type.

    Supports all custom ClickUp task types and common aliases:
    - Case-insensitive matching (Feature, feature, FEATURE)
    - Underscore/space variations (user_story, user story)
    - Common abbreviations (feat, f, pr, etc.)
    - Plural forms (features, bugs, etc.)
    - Category extraction from task names with "(Category) Name" format

    Args:
        task_type: The task type string or ID
        task_name: Optional task name to extract category from if task_type is generic

    Returns:
        The emoji for the task type, or 📝 (task emoji) if not found

    Examples:
        >>> get_task_emoji("Feature")
        '🚀'
        >>> get_task_emoji("user_story")
        '📖'
        >>> get_task_emoji("pr")
        '🔀'
        >>> get_task_emoji("task", "(GIT) CUM pull")
        '🔀'
        >>> get_task_emoji("unknown")
        '📝'
    """
    if not task_type:
        return TASK_TYPE_EMOJI["task"]  # Default to task emoji

    # Normalize task type (lowercase, strip whitespace)
    normalized_type = str(task_type).lower().strip()

    # If task_type is generic (like "task") and we have a task_name,
    # try to extract category from the task name
    if normalized_type == "task" and task_name:
        category = extract_category_from_name(task_name)
        if category:
            normalized_category = category.lower().strip()
            if normalized_category in TASK_TYPE_EMOJI:
                return TASK_TYPE_EMOJI[normalized_category]

    # Return the corresponding emoji or default to task emoji
    return TASK_TYPE_EMOJI.get(normalized_type, TASK_TYPE_EMOJI["task"])


def get_progress_state(status: str, use_color: bool = True) -> str:
    """
    Get formatted progress state indicator for a task status.

    Returns a colored progress label based on the task status:
    - [to do] - Gray - For Open, To Do, Backlog
    - [in progress] - Blue - For In Progress, In Development, Working
    - [complete] - Green - For Complete, Done, Closed
    - [blocked] - Red - For Blocked, On Hold, Paused

    Args:
        status: Task status string
        use_color: Whether to apply color coding (default: True)

    Returns:
        Formatted progress state indicator string

    Examples:
        >>> get_progress_state("open")
        '\033[90m[to do]\033[0m'
        >>> get_progress_state("in progress")
        '\033[94m[in progress]\033[0m'
        >>> get_progress_state("complete")
        '\033[92m[complete]\033[0m'
    """
    if not status:
        return colorize("[unknown]", TextColor.BRIGHT_BLACK) if use_color else "[unknown]"

    status_lower = str(status).lower().strip()

    # Map statuses to progress states
    if status_lower in ("to do", "todo", "open", "backlog", "ready"):
        label = "[to do]"
        color = TextColor.BRIGHT_BLACK  # Gray
    elif status_lower in ("in progress", "in development", "in dev", "wip", "working", "started"):
        label = "[in progress]"
        color = TextColor.BRIGHT_BLUE  # Blue
    elif status_lower in ("complete", "completed", "done", "closed", "resolved", "finished"):
        label = "[complete]"
        color = TextColor.BRIGHT_GREEN  # Green
    elif status_lower in ("blocked", "block", "on hold", "waiting", "paused"):
        label = "[blocked]"
        color = TextColor.BRIGHT_RED  # Red
    elif status_lower in ("testing", "test", "qa", "validation", "validating"):
        label = "[testing]"
        color = TextColor.CYAN  # Cyan
    elif status_lower in ("in review", "review", "approval", "pending approval", "awaiting approval"):
        label = "[in review]"
        color = TextColor.MAGENTA  # Magenta
    else:
        # For unknown statuses, show the status code
        label = f"[{status_to_code(status).lower()}]"
        color = TextColor.WHITE

    return colorize(label, color) if use_color else label
