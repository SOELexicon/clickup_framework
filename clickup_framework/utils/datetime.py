"""
Date/Time Utilities

Helper functions for formatting ClickUp timestamps and dates.
"""

from datetime import datetime
from typing import Optional


def format_timestamp(timestamp: Optional[str], include_time: bool = False) -> str:
    """
    Format ClickUp timestamp (milliseconds) to human-readable date.

    Args:
        timestamp: Unix timestamp in milliseconds (as string or int)
        include_time: If True, include time in output

    Returns:
        Formatted date string (YYYY-MM-DD or YYYY-MM-DD HH:MM)

    Examples:
        >>> format_timestamp("1567780450202")
        '2019-09-06'
        >>> format_timestamp("1567780450202", include_time=True)
        '2019-09-06 14:20'
    """
    if not timestamp:
        return "No date"

    try:
        # Convert to integer if string
        ts = int(timestamp) if isinstance(timestamp, str) else timestamp

        # Convert milliseconds to seconds
        dt = datetime.fromtimestamp(ts / 1000)

        if include_time:
            return dt.strftime("%Y-%m-%d %H:%M")
        else:
            return dt.strftime("%Y-%m-%d")

    except (ValueError, OSError):
        return "Invalid date"


def format_duration(milliseconds: Optional[int]) -> str:
    """
    Format duration in milliseconds to human-readable format.

    Args:
        milliseconds: Duration in milliseconds

    Returns:
        Formatted duration (e.g., "2h 30m", "45m", "1d 3h")

    Examples:
        >>> format_duration(3600000)
        '1h'
        >>> format_duration(9000000)
        '2h 30m'
        >>> format_duration(90000000)
        '1d 1h'
    """
    if not milliseconds or milliseconds == 0:
        return "0m"

    seconds = milliseconds / 1000
    minutes = int(seconds / 60)
    hours = int(minutes / 60)
    days = int(hours / 24)

    if days > 0:
        remaining_hours = hours % 24
        if remaining_hours > 0:
            return f"{days}d {remaining_hours}h"
        return f"{days}d"
    elif hours > 0:
        remaining_minutes = minutes % 60
        if remaining_minutes > 0:
            return f"{hours}h {remaining_minutes}m"
        return f"{hours}h"
    else:
        return f"{minutes}m"


def format_relative_time(timestamp: Optional[str]) -> str:
    """
    Format timestamp as relative time (e.g., "2 days ago").

    Args:
        timestamp: Unix timestamp in milliseconds

    Returns:
        Relative time string

    Examples:
        >>> format_relative_time("1762368081507")  # Recent
        '2 hours ago'
    """
    if not timestamp:
        return "Unknown time"

    try:
        ts = int(timestamp) if isinstance(timestamp, str) else timestamp
        dt = datetime.fromtimestamp(ts / 1000)
        now = datetime.now()
        delta = now - dt

        seconds = delta.total_seconds()
        minutes = int(seconds / 60)
        hours = int(minutes / 60)
        days = int(hours / 24)

        if days > 365:
            years = int(days / 365)
            return f"{years} year{'s' if years > 1 else ''} ago"
        elif days > 30:
            months = int(days / 30)
            return f"{months} month{'s' if months > 1 else ''} ago"
        elif days > 0:
            return f"{days} day{'s' if days > 1 else ''} ago"
        elif hours > 0:
            return f"{hours} hour{'s' if hours > 1 else ''} ago"
        elif minutes > 0:
            return f"{minutes} minute{'s' if minutes > 1 else ''} ago"
        else:
            return "just now"

    except (ValueError, OSError):
        return "Unknown time"


def parse_timestamp(timestamp: Optional[str]) -> Optional[datetime]:
    """
    Parse ClickUp timestamp to datetime object.

    Args:
        timestamp: Unix timestamp in milliseconds

    Returns:
        datetime object or None if invalid
    """
    if not timestamp:
        return None

    try:
        ts = int(timestamp) if isinstance(timestamp, str) else timestamp
        return datetime.fromtimestamp(ts / 1000)
    except (ValueError, OSError):
        return None
