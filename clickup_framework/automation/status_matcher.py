"""
Status matching logic for parent task automation.

Handles flexible status name matching with fuzzy logic and aliases.
"""

import re
from difflib import SequenceMatcher
from typing import Dict, List
from clickup_framework.automation.config import AutomationConfig


class StatusMatcher:
    """
    Intelligent status name matching with fuzzy logic and aliases.

    Handles variations in status naming across ClickUp workspaces.
    Uses string similarity and predefined aliases for matching.

    Attributes:
        config (AutomationConfig): Automation configuration object.
        _alias_map (Dict[str, List[str]]): Map of canonical statuses to common aliases.
        _similarity_threshold (float): Minimum similarity score for fuzzy match.

    Examples:
        >>> matcher = StatusMatcher(config)
        >>> matcher.is_development_status("in dev")
        True

    Notes:
        - Designed for flexible status matching in automation workflows.
    """

    def __init__(self, config: AutomationConfig):
        """
        Initialize status matcher.

        Args:
            config: Automation configuration
        """
        self.config = config
        self._alias_map = self._build_alias_map()
        self._similarity_threshold = 0.85

    def _build_alias_map(self) -> Dict[str, List[str]]:
        """
        Build map of canonical statuses to common aliases.

        Returns:
            Dict mapping canonical status to list of aliases
        """
        return {
            "in progress": [
                "in progress", "in-progress", "in_progress",
                "in development", "in dev", "in-dev",
                "active", "working", "started", "wip",
                "doing", "current", "ongoing"
            ],
            "to do": [
                "to do", "todo", "to-do", "to_do",
                "backlog", "not started", "open",
                "ready", "planned", "queued",
                "pending", "new"
            ]
        }

    def is_development_status(self, status: str) -> bool:
        """
        Check if status indicates active development.

        Uses configured trigger statuses plus fuzzy matching.

        Args:
            status: Status string to check

        Returns:
            bool: True if status matches development state
        """
        normalized = self.normalize_status(status)

        # Check exact matches in config
        for trigger in self.config.trigger_statuses:
            if normalized == self.normalize_status(trigger):
                return True

        # Check fuzzy matches against aliases
        for alias in self._alias_map.get("in progress", []):
            if self.fuzzy_match(normalized, alias):
                return True

        return False

    def is_inactive_status(self, status: str) -> bool:
        """
        Check if status indicates inactive/not-started state.

        Args:
            status: Status string to check

        Returns:
            bool: True if status matches inactive state
        """
        normalized = self.normalize_status(status)

        # Check exact matches in config
        for inactive in self.config.parent_inactive_statuses:
            if normalized == self.normalize_status(inactive):
                return True

        # Check fuzzy matches against aliases
        for alias in self._alias_map.get("to do", []):
            if self.fuzzy_match(normalized, alias):
                return True

        return False

    @staticmethod
    def normalize_status(status: str) -> str:
        """
        Normalize status string for comparison.

        Removes special characters, emoji, and normalizes whitespace.

        Args:
            status: Raw status string

        Returns:
            Normalized string (lowercase, trimmed, no special chars)
        """
        # Remove emoji (Unicode range)
        no_emoji = re.sub(
            r'[\U0001F600-\U0001F64F\U0001F300-\U0001F5FF\U0001F680-\U0001F6FF\U0001F1E0-\U0001F1FF]',
            '',
            status
        )

        # Remove special characters except spaces
        no_special = re.sub(r'[^a-zA-Z0-9\s]', '', no_emoji)

        # Normalize whitespace and convert to lowercase
        normalized = re.sub(r'\s+', ' ', no_special.strip().lower())

        return normalized

    def fuzzy_match(self, status1: str, status2: str) -> bool:
        """
        Check if two statuses are similar enough to match.

        Uses Levenshtein distance for fuzzy matching.

        Args:
            status1: First status string (normalized)
            status2: Second status string (normalized)

        Returns:
            bool: True if similarity >= threshold
        """
        similarity = SequenceMatcher(None, status1, status2).ratio()
        return similarity >= self._similarity_threshold
