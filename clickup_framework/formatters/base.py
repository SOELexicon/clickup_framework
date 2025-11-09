"""
Base Formatter

Abstract base class for all formatters.
"""

from abc import ABC, abstractmethod
from typing import Dict, Any, List, Literal

DetailLevel = Literal["minimal", "summary", "detailed", "full"]


class BaseFormatter(ABC):
    """
    Abstract base class for formatters.

    All formatters should inherit from this class and implement
    the format method for each detail level.
    """

    @abstractmethod
    def format(self, data: Dict[str, Any], detail_level: DetailLevel = "summary") -> str:
        """
        Format data based on detail level.

        Args:
            data: Raw API response data
            detail_level: One of "minimal", "summary", "detailed", "full"

        Returns:
            Formatted string
        """
        pass

    @classmethod
    def format_list(
        cls, items: List[Dict[str, Any]], detail_level: DetailLevel = "summary"
    ) -> str:
        """
        Format list of items.

        Args:
            items: List of raw API response items
            detail_level: Detail level for each item

        Returns:
            Formatted string with all items
        """
        if not items:
            return "No items found"

        formatter = cls()
        lines = []

        for i, item in enumerate(items, 1):
            formatted = formatter.format(item, detail_level)

            # Add item number prefix for lists
            if detail_level == "minimal":
                lines.append(f"{i}. {formatted}")
            else:
                lines.append(f"\n{i}. {formatted}")

        return "\n".join(lines)

    def _get_field(self, data: Dict, field: str, default: Any = None) -> Any:
        """
        Safely get field from data with default.

        Args:
            data: Dictionary to extract from
            field: Field name (supports dot notation)
            default: Default value if not found

        Returns:
            Field value or default
        """
        if not data:
            return default

        # Support dot notation (e.g., "status.status")
        if "." in field:
            parts = field.split(".")
            value = data
            for part in parts:
                if isinstance(value, dict):
                    value = value.get(part)
                else:
                    return default
            return value if value is not None else default

        return data.get(field, default)
