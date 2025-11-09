"""
Format Options Module

This module provides the FormatOptions dataclass for managing display settings.
"""

from dataclasses import dataclass, field
from typing import Dict, Any, Optional


@dataclass
class FormatOptions:
    """
    Dataclass to hold all formatting options.

    This makes it easier to pass options between functions and
    helps prevent issues with missing or renamed parameters.

    Attributes:
        colorize_output: Whether to use ANSI colors in output
        show_ids: Whether to show task IDs
        show_score: Whether to show task scores
        show_tags: Whether to show task tags
        tag_style: Style for tag display ('brackets', 'hash', 'colored')
        show_type_emoji: Whether to show task type emojis
        show_descriptions: Whether to show task descriptions
        show_dates: Whether to show task dates (created, updated, due)
        show_comments: Number of recent comments to show (0 to hide)
        show_relationships: Whether to show task relationships
        include_completed: Whether to include completed tasks
        hide_orphaned: Whether to hide orphaned tasks
        description_length: Maximum length for displayed descriptions
        show_container_diff: Whether to show container differences
        trace: Whether to show detailed debug traces
    """

    colorize_output: bool = True
    show_ids: bool = False
    show_score: bool = False
    show_tags: bool = True
    tag_style: str = "colored"
    show_type_emoji: bool = True
    show_descriptions: bool = False
    show_dates: bool = False
    show_comments: int = 0
    show_relationships: bool = False
    include_completed: bool = False
    hide_orphaned: bool = False
    description_length: int = 100
    show_container_diff: bool = True
    trace: bool = False

    @classmethod
    def from_dict(cls, options_dict: Dict[str, Any]) -> 'FormatOptions':
        """
        Create a FormatOptions instance from a dictionary of options.

        Args:
            options_dict: Dictionary with option names and values

        Returns:
            FormatOptions instance
        """
        return cls(**{k: v for k, v in options_dict.items() if k in cls.__dataclass_fields__})

    @classmethod
    def minimal(cls) -> 'FormatOptions':
        """
        Create minimal display options (ID and name only).

        Returns:
            FormatOptions configured for minimal display
        """
        return cls(
            colorize_output=False,
            show_ids=True,
            show_tags=False,
            show_type_emoji=False,
            show_descriptions=False
        )

    @classmethod
    def summary(cls) -> 'FormatOptions':
        """
        Create summary display options (status, assignees, dates).

        Returns:
            FormatOptions configured for summary display
        """
        return cls(
            colorize_output=True,
            show_ids=True,
            show_tags=True,
            show_type_emoji=True,
            show_dates=True
        )

    @classmethod
    def detailed(cls) -> 'FormatOptions':
        """
        Create detailed display options (priority, tags, custom fields).

        Returns:
            FormatOptions configured for detailed display
        """
        return cls(
            colorize_output=True,
            show_ids=True,
            show_tags=True,
            show_type_emoji=True,
            show_descriptions=True,
            show_dates=True,
            show_relationships=True
        )

    @classmethod
    def full(cls) -> 'FormatOptions':
        """
        Create full display options (everything including watchers, checklists).

        Returns:
            FormatOptions configured for full display
        """
        return cls(
            colorize_output=True,
            show_ids=True,
            show_score=True,
            show_tags=True,
            show_type_emoji=True,
            show_descriptions=True,
            show_dates=True,
            show_comments=3,
            show_relationships=True,
            include_completed=True
        )
