"""
Formatters Module

Transform verbose ClickUp JSON responses into concise, human-readable text.
Achieves 90-95% token reduction through intelligent formatting.
"""

from .task import TaskFormatter, format_task, format_task_list
from .comment import CommentFormatter, format_comment, format_comment_list
from .time_entry import TimeEntryFormatter, format_time_entry, format_time_entry_list

__all__ = [
    # Task formatters
    "TaskFormatter",
    "format_task",
    "format_task_list",
    # Comment formatters
    "CommentFormatter",
    "format_comment",
    "format_comment_list",
    # Time entry formatters
    "TimeEntryFormatter",
    "format_time_entry",
    "format_time_entry_list",
]
