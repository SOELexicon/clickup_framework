"""
Constants Module

This module centralizes all constants used throughout the application,
providing a single source of truth for values that may be referenced
in multiple places. This makes maintenance easier by ensuring that
changes only need to be made in one location.

Task: Centralize Application Constants
"""

from enum import Enum
from typing import Dict, List, Any, Optional, Union
from refactor.utils.colors import TextColor

#############################
# TASK TYPE CONSTANTS
#############################

TASK_TYPE_EMOJI_MAP = {
    "task": "📝",
    "bug": "🐛",
    "feature": "🚀",
    "refactor": "♻️",
    "documentation": "📚",
    "enhancement": "✨",
    "chore": "🧹",
    "research": "🔬",
    "testing": "🧪",
    "security": "🛡️",
    "project": "📂",
    "milestone": "🏁"
}

# Generic emoji constants
TAG_EMOJI = "🏷️"
COMMENT_EMOJI = "💬"
CHECKLIST_EMOJI = "📋"
SUBTASK_EMOJI = "📎"
WARNING_EMOJI = "⚠️"
SUCCESS_EMOJI = "✅"
ERROR_EMOJI = "❌"
INFO_EMOJI = "ℹ️"

#############################
# STATUS CONSTANTS
#############################

# Status display strings keyed by normalized value
STATUS_DISPLAY_MAP = {
    "todo": "To Do",
    "to do": "To Do", 
    "in progress": "In Progress",
    "inprogress": "In Progress",
    "in_progress": "In Progress",
    "complete": "Complete",
    "completed": "Complete",
    "done": "Complete",
    "blocked": "Blocked",
    "cancelled": "Cancelled"
}

# Status names to canonical values
STATUS_CANONICAL_MAP = {
    "todo": "to do",
    "to_do": "to do",
    "in_progress": "in progress",
    "inprogress": "in progress",
    "completed": "complete",
    "done": "complete"
}

#############################
# PRIORITY CONSTANTS
#############################

# Priority display strings
PRIORITY_DISPLAY_MAP = {
    1: "Urgent",
    2: "High",
    3: "Normal",
    4: "Low"
}

# Priority names to numerical values
PRIORITY_VALUE_MAP = {
    "urgent": 1,
    "critical": 1,
    "high": 2,
    "normal": 3,
    "medium": 3,
    "low": 4
}

#############################
# COLOR CONSTANTS
#############################

# Status color mapping
STATUS_COLOR_MAP = {
    "to do": TextColor.YELLOW,
    "in progress": TextColor.BRIGHT_BLUE,
    "complete": TextColor.BRIGHT_GREEN,
    "blocked": TextColor.BRIGHT_RED,
    "cancelled": TextColor.BRIGHT_BLACK
}

# Priority color mapping
PRIORITY_COLOR_MAP = {
    1: TextColor.BRIGHT_RED,     # Urgent
    2: TextColor.BRIGHT_YELLOW,  # High
    3: TextColor.BRIGHT_BLUE,    # Normal
    4: TextColor.BRIGHT_GREEN    # Low
}

# Task type color mapping
TASK_TYPE_COLOR_MAP = {
    "task": TextColor.CYAN,
    "bug": TextColor.BRIGHT_RED,
    "feature": TextColor.BRIGHT_GREEN,
    "refactor": TextColor.BLUE,
    "documentation": TextColor.BRIGHT_MAGENTA,
    "enhancement": TextColor.GREEN,
    "chore": TextColor.BRIGHT_BLACK,
    "research": TextColor.YELLOW,
    "testing": TextColor.BRIGHT_CYAN,
    "security": TextColor.RED,
    "project": TextColor.MAGENTA,
    "milestone": TextColor.BRIGHT_YELLOW
}

# Relationship color mapping
RELATIONSHIP_COLOR_MAP = {
    "depends_on": TextColor.BRIGHT_YELLOW,
    "blocks": TextColor.BRIGHT_RED,
    "related_to": TextColor.BRIGHT_BLUE,
    "documents": TextColor.BRIGHT_GREEN,
    "documented_by": TextColor.BRIGHT_CYAN
}

# Container color mapping
CONTAINER_COLOR_MAP = {
    "space": TextColor.BRIGHT_BLUE,
    "folder": TextColor.BRIGHT_CYAN,
    "list": TextColor.BRIGHT_MAGENTA
}

#############################
# RELATIONSHIP CONSTANTS
#############################

# Relationship type mapping to inverses
RELATIONSHIP_INVERSE_MAP = {
    "depends_on": "blocks",
    "blocks": "depends_on",
    "related_to": "related_to",
    "documents": "documented_by",
    "documented_by": "documents"
}

#############################
# VALIDATION CONSTANTS
#############################

# ID prefixes for different entity types
ID_PREFIX_MAP = {
    "task": "tsk_",
    "subtask": "stk_",
    "checklist": "chk_",
    "item": "itm_",
    "comment": "cmt_",
    "section": "sec_",
    "document": "doc_"
}

# Regex patterns for common validations
REGEX_PATTERNS = {
    "task_id": r"^(tsk|stk)_[a-f0-9]{8}$",
    "checklist_id": r"^chk_[a-f0-9]{8}$",
    "item_id": r"^itm_[a-f0-9]{8}$",
    "comment_id": r"^cmt_[a-f0-9]{8}$",
    "section_id": r"^sec_[a-f0-9]{8}$",
    "document_id": r"^doc_[a-f0-9]{8}$",
    "email": r"^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$"
}

#############################
# FORMATTING CONSTANTS
#############################

# Default date format strings
DATE_FORMAT_STANDARD = "%Y-%m-%d %H:%M:%S"
DATE_FORMAT_SHORT = "%Y-%m-%d"
DATE_FORMAT_ISO = "%Y-%m-%dT%H:%M:%S.%fZ"

# Maximum display lengths
MAX_DESCRIPTION_PREVIEW_LENGTH = 100
MAX_COMMENT_PREVIEW_LENGTH = 80
MAX_TASK_NAME_DISPLAY_LENGTH = 50
MAX_COMMENTS_TO_DISPLAY = 3

# Tag display styles
TAG_STYLE_OPTIONS = ["colored", "plain", "emoji", "brackets", "hash"]

#############################
# SYSTEM CONFIGURATION
#############################

# Default file paths
DEFAULT_JSON_DIR = "./json"
DEFAULT_CONFIG_FILE = "./.cujm_config"
DEFAULT_LOG_FILE = "./cujm.log"

# Environment variable names
ENV_CONFIG_PATH = "CUJM_CONFIG_PATH"
ENV_LOG_LEVEL = "CUJM_LOG_LEVEL"
ENV_COLOR_MODE = "CUJM_COLOR_MODE" 