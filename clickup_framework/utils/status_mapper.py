"""
Status Mapper Utility

Maps common status names to actual ClickUp list statuses.
Provides fuzzy matching and suggestions when status is not found.
"""

from typing import Optional, List, Dict, Tuple
from difflib import get_close_matches


class StatusMapper:
    """Maps user-provided status names to actual list statuses."""

    # Common status name mappings
    COMMON_MAPPINGS = {
        # Completed/Done variants
        'complete': ['complete', 'completed', 'done', 'closed', 'finished'],
        'completed': ['complete', 'completed', 'done', 'closed', 'finished'],
        'done': ['complete', 'completed', 'done', 'closed', 'finished'],
        'closed': ['complete', 'completed', 'done', 'closed', 'finished'],
        'finished': ['complete', 'completed', 'done', 'closed', 'finished'],

        # In Progress variants
        'in progress': ['in progress', 'in development', 'in dev', 'working', 'active', 'wip', 'doing'],
        'in development': ['in progress', 'in development', 'in dev', 'working', 'active', 'wip'],
        'in dev': ['in progress', 'in development', 'in dev', 'working', 'active'],
        'working': ['in progress', 'in development', 'working', 'active', 'wip'],
        'active': ['in progress', 'in development', 'active', 'working'],
        'wip': ['in progress', 'in development', 'wip', 'working'],
        'doing': ['in progress', 'in development', 'doing', 'working'],

        # To Do variants
        'to do': ['to do', 'todo', 'open', 'pending', 'backlog'],
        'todo': ['to do', 'todo', 'open', 'pending', 'backlog'],
        'open': ['to do', 'todo', 'open', 'pending', 'backlog'],
        'pending': ['to do', 'todo', 'pending', 'open', 'backlog'],
        'backlog': ['to do', 'backlog', 'pending'],

        # Review variants
        'review': ['review', 'in review', 'reviewing', 'needs review'],
        'in review': ['review', 'in review', 'reviewing', 'needs review'],
        'reviewing': ['review', 'in review', 'reviewing'],
        'needs review': ['review', 'needs review', 'in review'],

        # Blocked variants
        'blocked': ['blocked', 'on hold', 'waiting', 'paused'],
        'on hold': ['blocked', 'on hold', 'waiting', 'paused'],
        'waiting': ['blocked', 'waiting', 'on hold'],
        'paused': ['blocked', 'paused', 'on hold'],

        # Testing variants
        'testing': ['testing', 'qa', 'quality assurance', 'test'],
        'qa': ['testing', 'qa', 'quality assurance'],
        'test': ['testing', 'test', 'qa'],
    }

    @classmethod
    def get_available_statuses(cls, list_data: Dict) -> List[Dict[str, str]]:
        """
        Extract available statuses from list data.

        Args:
            list_data: List data from ClickUp API

        Returns:
            List of status dicts with 'status' and 'type' fields
        """
        statuses = []

        # ClickUp lists have a 'statuses' field
        if 'statuses' in list_data:
            for status in list_data['statuses']:
                statuses.append({
                    'status': status.get('status', ''),
                    'type': status.get('type', ''),
                    'color': status.get('color', ''),
                    'orderindex': status.get('orderindex', 0),
                })

        return statuses

    @classmethod
    def map_status(cls, user_status: str, available_statuses: List[Dict[str, str]]) -> Optional[str]:
        """
        Map user-provided status to an actual list status.

        Args:
            user_status: Status name provided by user
            available_statuses: List of available statuses from the list

        Returns:
            Mapped status name if found, None otherwise
        """
        if not user_status:
            return None

        user_status_lower = user_status.lower().strip()
        available_status_names = [s['status'] for s in available_statuses]
        available_status_names_lower = [s.lower() for s in available_status_names]

        # 1. Exact match (case-insensitive)
        if user_status_lower in available_status_names_lower:
            idx = available_status_names_lower.index(user_status_lower)
            return available_status_names[idx]

        # 2. Check common mappings
        if user_status_lower in cls.COMMON_MAPPINGS:
            candidates = cls.COMMON_MAPPINGS[user_status_lower]
            for candidate in candidates:
                if candidate in available_status_names_lower:
                    idx = available_status_names_lower.index(candidate)
                    return available_status_names[idx]

        # 3. Fuzzy matching (≥80% similarity)
        close_matches = get_close_matches(
            user_status_lower,
            available_status_names_lower,
            n=1,
            cutoff=0.8
        )
        if close_matches:
            idx = available_status_names_lower.index(close_matches[0])
            return available_status_names[idx]

        # 4. Partial match (check if user_status is contained in any available status)
        for i, status_lower in enumerate(available_status_names_lower):
            if user_status_lower in status_lower or status_lower in user_status_lower:
                return available_status_names[i]

        return None

    @classmethod
    def format_available_statuses(cls, available_statuses: List[Dict[str, str]], highlight_type: Optional[str] = None) -> str:
        """
        Format available statuses for display.

        Args:
            available_statuses: List of available statuses
            highlight_type: Optional status type to highlight (e.g., 'closed', 'open')

        Returns:
            Formatted string of available statuses
        """
        if not available_statuses:
            return "No statuses available"

        # Group by type
        grouped = {}
        for status in available_statuses:
            status_type = status.get('type', 'custom')
            if status_type not in grouped:
                grouped[status_type] = []
            grouped[status_type].append(status)

        lines = []

        # Show statuses grouped by type
        for status_type in ['open', 'custom', 'closed']:
            if status_type not in grouped:
                continue

            # Type header
            type_label = {
                'open': '📝 Open Statuses',
                'custom': '🔄 In Progress Statuses',
                'closed': '✅ Closed Statuses',
            }.get(status_type, f'Status Type: {status_type}')

            lines.append(type_label)

            # Status names
            for status in grouped[status_type]:
                status_name = status['status']
                lines.append(f"   - {status_name}")

        return '\n'.join(lines)

    @classmethod
    def suggest_status(cls, user_status: str, available_statuses: List[Dict[str, str]], max_suggestions: int = 3) -> List[str]:
        """
        Suggest similar status names.

        Args:
            user_status: Status name provided by user
            available_statuses: List of available statuses
            max_suggestions: Maximum number of suggestions

        Returns:
            List of suggested status names
        """
        if not user_status or not available_statuses:
            return []

        user_status_lower = user_status.lower().strip()
        available_status_names = [s['status'] for s in available_statuses]
        available_status_names_lower = [s.lower() for s in available_status_names]

        # Get close matches with lower cutoff for suggestions
        close_matches = get_close_matches(
            user_status_lower,
            available_status_names_lower,
            n=max_suggestions,
            cutoff=0.6
        )

        # Convert back to original case
        suggestions = []
        for match in close_matches:
            idx = available_status_names_lower.index(match)
            suggestions.append(available_status_names[idx])

        return suggestions


def map_status(user_status: str, available_statuses: List[Dict[str, str]]) -> Optional[str]:
    """Convenience function for StatusMapper.map_status()."""
    return StatusMapper.map_status(user_status, available_statuses)


def get_available_statuses(list_data: Dict) -> List[Dict[str, str]]:
    """Convenience function for StatusMapper.get_available_statuses()."""
    return StatusMapper.get_available_statuses(list_data)


def format_available_statuses(available_statuses: List[Dict[str, str]], highlight_type: Optional[str] = None) -> str:
    """Convenience function for StatusMapper.format_available_statuses()."""
    return StatusMapper.format_available_statuses(available_statuses, highlight_type)


def suggest_status(user_status: str, available_statuses: List[Dict[str, str]], max_suggestions: int = 3) -> List[str]:
    """Convenience function for StatusMapper.suggest_status()."""
    return StatusMapper.suggest_status(user_status, available_statuses, max_suggestions)
