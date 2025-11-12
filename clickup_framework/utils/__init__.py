"""
Utilities Module

Helper functions for date/time formatting, text manipulation, error formatting, etc.
"""

from .datetime import (
    format_timestamp,
    format_duration,
    format_relative_time,
    parse_timestamp,
)
from .text import (
    truncate,
    format_list,
    pluralize,
    clean_html,
    indent,
    format_user_list,
    unescape_content,
)
from .error_formatter import (
    ErrorFormatter,
    format_error,
    format_api_error,
    format_missing_context_error,
    format_known_limitation,
)

__all__ = [
    # datetime
    "format_timestamp",
    "format_duration",
    "format_relative_time",
    "parse_timestamp",
    # text
    "truncate",
    "format_list",
    "pluralize",
    "clean_html",
    "indent",
    "format_user_list",
    "unescape_content",
    # error formatting
    "ErrorFormatter",
    "format_error",
    "format_api_error",
    "format_missing_context_error",
    "format_known_limitation",
]
