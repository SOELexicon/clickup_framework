"""
TimeAPI - High-level API for ClickUp time tracking operations

Provides convenient methods for time tracking with automatic formatting support.
"""

from typing import Dict, Any, Optional
from ..formatters import format_time_entry, format_time_entry_list


class TimeAPI:
    """
    High-level API for ClickUp time tracking operations.

    Wraps ClickUpClient methods with automatic formatting and convenience features.

    Usage:
        from clickup_framework import ClickUpClient
        from clickup_framework.resources import TimeAPI

        client = ClickUpClient()
        time = TimeAPI(client)

        # Get time entries for a task
        entries = time.get_entries(
            team_id="90151898946",
            task_id="task_id",
            detail_level="summary"
        )

        # Create time entry
        entry = time.create_entry(
            team_id="90151898946",
            duration=3600000,  # 1 hour in milliseconds
            description="Worked on feature"
        )
    """

    def __init__(self, client):
        """
        Initialize TimeAPI.

        Args:
            client: ClickUpClient instance
        """
        self.client = client

    def get_entries(
        self,
        team_id: str,
        detail_level: Optional[str] = None,
        start_date: Optional[int] = None,
        end_date: Optional[int] = None,
        assignee: Optional[int] = None,
        task_id: Optional[str] = None,
        **params
    ) -> Any:
        """
        Get time entries.

        Args:
            team_id: Team/workspace ID
            detail_level: Format detail level (minimal|summary|detailed|full)
                         If None, returns raw JSON
            start_date: Filter by start date (Unix timestamp in milliseconds)
            end_date: Filter by end date (Unix timestamp in milliseconds)
            assignee: Filter by user ID
            task_id: Filter by task ID
            **params: Additional query parameters

        Returns:
            Formatted string if detail_level specified, otherwise raw dict
        """
        query_params = {**params}

        if start_date:
            query_params["start_date"] = start_date
        if end_date:
            query_params["end_date"] = end_date
        if assignee:
            query_params["assignee"] = assignee
        if task_id:
            query_params["task_id"] = task_id

        result = self.client.get_time_entries(team_id, **query_params)

        if detail_level and 'data' in result:
            return format_time_entry_list(result['data'], detail_level)
        return result

    def create_entry(
        self,
        team_id: str,
        duration: int,
        description: Optional[str] = None,
        start: Optional[int] = None,
        task_id: Optional[str] = None,
        assignee: Optional[int] = None,
        billable: bool = False,
        tags: Optional[list] = None,
        **entry_data
    ) -> Dict[str, Any]:
        """
        Create a time entry.

        Args:
            team_id: Team/workspace ID
            duration: Duration in milliseconds
            description: Entry description
            start: Start time (Unix timestamp in milliseconds)
            task_id: Associated task ID
            assignee: User ID (defaults to current user)
            billable: Whether entry is billable
            tags: List of tag names
            **entry_data: Additional entry fields

        Returns:
            Created time entry (raw dict)
        """
        data = {
            "duration": duration,
            "billable": billable,
            **entry_data
        }

        if description:
            data["description"] = description
        if start:
            data["start"] = start
        if task_id:
            data["tid"] = task_id
        if assignee:
            data["assignee"] = assignee
        if tags:
            data["tags"] = tags

        return self.client.create_time_entry(team_id, **data)

    def get_task_time(
        self,
        team_id: str,
        task_id: str,
        detail_level: Optional[str] = None,
        **params
    ) -> Any:
        """
        Get all time entries for a specific task (convenience method).

        Args:
            team_id: Team/workspace ID
            task_id: Task ID
            detail_level: Format detail level (minimal|summary|detailed|full)
            **params: Additional query parameters

        Returns:
            Formatted string if detail_level specified, otherwise raw dict
        """
        return self.get_entries(
            team_id=team_id,
            task_id=task_id,
            detail_level=detail_level,
            **params
        )

    def get_user_time(
        self,
        team_id: str,
        user_id: int,
        detail_level: Optional[str] = None,
        start_date: Optional[int] = None,
        end_date: Optional[int] = None,
        **params
    ) -> Any:
        """
        Get all time entries for a specific user (convenience method).

        Args:
            team_id: Team/workspace ID
            user_id: User ID
            detail_level: Format detail level (minimal|summary|detailed|full)
            start_date: Filter by start date (Unix timestamp in milliseconds)
            end_date: Filter by end date (Unix timestamp in milliseconds)
            **params: Additional query parameters

        Returns:
            Formatted string if detail_level specified, otherwise raw dict
        """
        return self.get_entries(
            team_id=team_id,
            assignee=user_id,
            detail_level=detail_level,
            start_date=start_date,
            end_date=end_date,
            **params
        )
