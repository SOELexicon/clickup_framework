"""
Tasks API - Low-level API for ClickUp task endpoints.
"""

from typing import Dict, Any, Optional, List
from .base import BaseAPI


class TasksAPI(BaseAPI):
    """Low-level API for task operations."""

    def get_task(self, task_id: str, **params) -> Dict[str, Any]:
        """Get task by ID."""
        return self._request("GET", f"task/{task_id}", params=params)

    def get_list_tasks(self, list_id: str, **params) -> Dict[str, Any]:
        """Get all tasks in a list."""
        return self._request("GET", f"list/{list_id}/task", params=params)

    def get_team_tasks(self, team_id: str, **params) -> Dict[str, Any]:
        """Get all tasks in a team/workspace."""
        return self._request("GET", f"team/{team_id}/task", params=params)

    def create_task(self, list_id: str, **task_data) -> Dict[str, Any]:
        """Create a new task."""
        return self._request("POST", f"list/{list_id}/task", json=task_data)

    def update_task(self, task_id: str, **updates) -> Dict[str, Any]:
        """Update a task."""
        return self._request("PUT", f"task/{task_id}", json=updates)

    def delete_task(self, task_id: str) -> Dict[str, Any]:
        """Delete a task."""
        return self._request("DELETE", f"task/{task_id}")

    def merge_tasks(self, task_id: str, merge_task_id: str, **params) -> Dict[str, Any]:
        """Merge two tasks."""
        return self._request("POST", f"task/{task_id}/merge", json={"task_id": merge_task_id}, params=params)

    def get_task_time_in_status(self, task_id: str, **params) -> Dict[str, Any]:
        """Get task's time in status."""
        return self._request("GET", f"task/{task_id}/time_in_status", params=params)

    def get_bulk_tasks_time_in_status(self, task_ids: List[str], **params) -> Dict[str, Any]:
        """Get bulk tasks' time in status."""
        params["task_ids"] = task_ids
        return self._request("GET", "task/bulk_time_in_status/task_ids", params=params)

    def create_task_from_template(self, list_id: str, template_id: str, **task_data) -> Dict[str, Any]:
        """Create a task from a template."""
        return self._request("POST", f"list/{list_id}/taskTemplate/{template_id}", json=task_data)

    def add_task_dependency(
        self,
        task_id: str,
        depends_on: Optional[str] = None,
        dependency_of: Optional[str] = None,
        **params
    ) -> Dict[str, Any]:
        """
        Add a dependency relationship between tasks.

        Args:
            task_id: The task to add dependency to
            depends_on: Task ID that this task depends on (task_id waits for this)
            dependency_of: Task ID that depends on this task (this blocks dependency_of)
            **params: Additional query parameters (custom_task_ids, team_id)

        Returns:
            Empty dict on success

        Note:
            Only one of depends_on or dependency_of should be provided.
        """
        if not depends_on and not dependency_of:
            raise ValueError("Either depends_on or dependency_of must be provided")
        if depends_on and dependency_of:
            raise ValueError("Only one of depends_on or dependency_of can be provided")

        body = {}
        if depends_on:
            body["depends_on"] = depends_on
        if dependency_of:
            body["dependency_of"] = dependency_of

        return self._request("POST", f"task/{task_id}/dependency", json=body, params=params)

    def delete_task_dependency(
        self,
        task_id: str,
        depends_on: Optional[str] = None,
        dependency_of: Optional[str] = None,
        **params
    ) -> Dict[str, Any]:
        """
        Remove a dependency relationship between tasks.

        Args:
            task_id: The task to remove dependency from
            depends_on: Task ID to remove from "waiting on" list
            dependency_of: Task ID to remove from "blocking" list
            **params: Additional query parameters (custom_task_ids, team_id)

        Returns:
            Empty dict on success
        """
        if not depends_on and not dependency_of:
            raise ValueError("Either depends_on or dependency_of must be provided")

        query_params = params.copy()
        if depends_on:
            query_params["depends_on"] = depends_on
        if dependency_of:
            query_params["dependency_of"] = dependency_of

        return self._request("DELETE", f"task/{task_id}/dependency", params=query_params)

    def add_task_link(
        self,
        task_id: str,
        links_to: str,
        **params
    ) -> Dict[str, Any]:
        """
        Link two tasks together (simple relationship).

        Args:
            task_id: The task to link from
            links_to: The task to link to
            **params: Additional query parameters (custom_task_ids, team_id)

        Returns:
            Updated task object with linked_tasks field
        """
        return self._request("POST", f"task/{task_id}/link/{links_to}", params=params)

    def delete_task_link(
        self,
        task_id: str,
        links_to: str,
        **params
    ) -> Dict[str, Any]:
        """
        Remove a link between two tasks.

        Args:
            task_id: The task to unlink from
            links_to: The task to unlink
            **params: Additional query parameters (custom_task_ids, team_id)

        Returns:
            Updated task object with linked_tasks field
        """
        return self._request("DELETE", f"task/{task_id}/link/{links_to}", params=params)

