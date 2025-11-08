"""
ClickUp API Client

Core client for ClickUp API with authentication, rate limiting, and error handling.
"""

import os
import time
import logging
from typing import Dict, Any, Optional
import requests

from .exceptions import (
    ClickUpAPIError,
    ClickUpAuthError,
    ClickUpRateLimitError,
    ClickUpNotFoundError,
    ClickUpTimeoutError,
)
from .rate_limiter import RateLimiter


logger = logging.getLogger(__name__)


class ClickUpClient:
    """
    Core ClickUp API client.

    Handles authentication, rate limiting, retries, and error handling.

    Usage:
        client = ClickUpClient(api_token="your_token")
        task = client.get_task("task_id")
    """

    BASE_URL = "https://api.clickup.com/api/v2"
    DEFAULT_TIMEOUT = 30  # seconds
    MAX_RETRIES = 3

    def __init__(
        self,
        api_token: Optional[str] = None,
        rate_limit: int = 100,
        timeout: int = DEFAULT_TIMEOUT,
        max_retries: int = MAX_RETRIES,
    ):
        """
        Initialize ClickUp client.

        Args:
            api_token: ClickUp API token (defaults to CLICKUP_API_TOKEN env var)
            rate_limit: Requests per minute (default: 100)
            timeout: Request timeout in seconds (default: 30)
            max_retries: Maximum retry attempts (default: 3)
        """
        self.api_token = api_token or os.environ.get("CLICKUP_API_TOKEN")
        if not self.api_token:
            raise ClickUpAuthError("API token not provided")

        self.rate_limiter = RateLimiter(requests_per_minute=rate_limit)
        self.timeout = timeout
        self.max_retries = max_retries

        # Create session for connection pooling
        self.session = requests.Session()
        self.session.headers.update(
            {
                "Authorization": self.api_token,
                "Content-Type": "application/json",
            }
        )

    def _request(
        self,
        method: str,
        endpoint: str,
        params: Optional[Dict] = None,
        json: Optional[Dict] = None,
        **kwargs,
    ) -> Dict[str, Any]:
        """
        Make authenticated API request with rate limiting and retries.

        Args:
            method: HTTP method (GET, POST, PUT, DELETE)
            endpoint: API endpoint (without base URL)
            params: Query parameters
            json: JSON body
            **kwargs: Additional arguments for requests

        Returns:
            API response as dictionary

        Raises:
            ClickUpAuthError: Authentication failed
            ClickUpRateLimitError: Rate limit exceeded
            ClickUpNotFoundError: Resource not found
            ClickUpAPIError: Other API errors
            ClickUpTimeoutError: Request timeout
        """
        url = f"{self.BASE_URL}/{endpoint.lstrip('/')}"

        # Acquire rate limit token
        self.rate_limiter.acquire()

        # Retry loop with exponential backoff
        for attempt in range(self.max_retries):
            try:
                logger.debug(f"{method} {url} (attempt {attempt + 1}/{self.max_retries})")

                response = self.session.request(
                    method=method,
                    url=url,
                    params=params,
                    json=json,
                    timeout=self.timeout,
                    **kwargs,
                )

                # Handle different status codes
                # Success codes: 200 OK, 201 Created, 204 No Content
                if response.status_code in [200, 201, 204]:
                    # 204 No Content - successful but no response body (DELETE operations)
                    if response.status_code == 204:
                        return {}
                    # 200 OK and 201 Created - return response body
                    return response.json()

                elif response.status_code == 401:
                    raise ClickUpAuthError("Invalid or expired API token")

                elif response.status_code == 404:
                    # Try to extract resource info from endpoint
                    parts = endpoint.split("/")
                    resource = parts[0] if parts else "Resource"
                    resource_id = parts[1] if len(parts) > 1 else None
                    raise ClickUpNotFoundError(resource, resource_id)

                elif response.status_code == 429:
                    retry_after = int(response.headers.get("Retry-After", 60))
                    raise ClickUpRateLimitError(retry_after)

                else:
                    # Generic API error
                    try:
                        error_data = response.json()
                        message = error_data.get("err", error_data.get("error", "Unknown error"))
                    except:
                        message = response.text or "Unknown error"

                    raise ClickUpAPIError(response.status_code, message, error_data if 'error_data' in locals() else None)

            except requests.exceptions.Timeout:
                if attempt == self.max_retries - 1:
                    raise ClickUpTimeoutError(f"Request timed out after {self.timeout}s")
                logger.warning(f"Request timeout, retrying... ({attempt + 1}/{self.max_retries})")

            except requests.exceptions.ConnectionError as e:
                if attempt == self.max_retries - 1:
                    raise ClickUpAPIError(0, f"Connection error: {str(e)}")
                logger.warning(f"Connection error, retrying... ({attempt + 1}/{self.max_retries})")

            except ClickUpRateLimitError as e:
                if attempt == self.max_retries - 1:
                    raise
                # Wait for rate limit reset
                wait_time = e.retry_after if e.retry_after else 60
                logger.warning(f"Rate limit hit, waiting {wait_time}s...")
                time.sleep(wait_time)
                continue

            except (ClickUpAuthError, ClickUpNotFoundError):
                # Don't retry auth or not found errors
                raise

            # Exponential backoff for retries
            if attempt < self.max_retries - 1:
                backoff = 2 ** attempt
                logger.debug(f"Backing off for {backoff}s...")
                time.sleep(backoff)

        raise ClickUpAPIError(0, "Max retries exceeded")

    # Task endpoints
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

    # List endpoints
    def get_list(self, list_id: str) -> Dict[str, Any]:
        """Get list by ID."""
        return self._request("GET", f"list/{list_id}")

    def create_list(self, folder_id: str, name: str, **list_data) -> Dict[str, Any]:
        """Create a new list."""
        data = {"name": name, **list_data}
        return self._request("POST", f"folder/{folder_id}/list", json=data)

    def update_list(self, list_id: str, **updates) -> Dict[str, Any]:
        """Update a list."""
        return self._request("PUT", f"list/{list_id}", json=updates)

    # Folder endpoints
    def get_folder(self, folder_id: str) -> Dict[str, Any]:
        """Get folder by ID."""
        return self._request("GET", f"folder/{folder_id}")

    def create_folder(self, space_id: str, name: str) -> Dict[str, Any]:
        """Create a new folder."""
        return self._request("POST", f"space/{space_id}/folder", json={"name": name})

    def update_folder(self, folder_id: str, **updates) -> Dict[str, Any]:
        """Update a folder."""
        return self._request("PUT", f"folder/{folder_id}", json=updates)

    # Space endpoints
    def get_space(self, space_id: str) -> Dict[str, Any]:
        """Get space by ID."""
        return self._request("GET", f"space/{space_id}")

    def get_team_spaces(self, team_id: str, archived: bool = False) -> Dict[str, Any]:
        """Get all spaces in a team."""
        params = {"archived": str(archived).lower()}
        return self._request("GET", f"team/{team_id}/space", params=params)

    def create_space(self, team_id: str, name: str, **space_data) -> Dict[str, Any]:
        """Create a new space."""
        data = {"name": name, **space_data}
        return self._request("POST", f"team/{team_id}/space", json=data)

    def update_space(self, space_id: str, **updates) -> Dict[str, Any]:
        """Update a space."""
        return self._request("PUT", f"space/{space_id}", json=updates)

    def delete_space(self, space_id: str) -> Dict[str, Any]:
        """Delete a space."""
        return self._request("DELETE", f"space/{space_id}")

    def get_space_tags(self, space_id: str) -> Dict[str, Any]:
        """Get all tags in a space."""
        return self._request("GET", f"space/{space_id}/tag")

    def create_space_tag(self, space_id: str, tag_name: str, tag_fg: str = "#000000", tag_bg: str = "#FFFFFF") -> Dict[str, Any]:
        """Create a tag in a space."""
        data = {"tag": {"name": tag_name, "tag_fg": tag_fg, "tag_bg": tag_bg}}
        return self._request("POST", f"space/{space_id}/tag", json=data)

    # Workspace hierarchy
    def get_workspace_hierarchy(self, team_id: str) -> Dict[str, Any]:
        """Get complete workspace hierarchy."""
        return self._request("GET", f"team/{team_id}")

    # Custom Fields endpoints
    def get_accessible_custom_fields(self, list_id: str) -> Dict[str, Any]:
        """Get custom fields accessible from a list."""
        return self._request("GET", f"list/{list_id}/field")

    def set_custom_field_value(self, task_id: str, field_id: str, value: Any) -> Dict[str, Any]:
        """Set custom field value on a task."""
        return self._request("POST", f"task/{task_id}/field/{field_id}", json={"value": value})

    def remove_custom_field_value(self, task_id: str, field_id: str) -> Dict[str, Any]:
        """Remove custom field value from a task."""
        return self._request("DELETE", f"task/{task_id}/field/{field_id}")

    # Checklist endpoints
    def create_checklist(self, task_id: str, name: str) -> Dict[str, Any]:
        """Create a checklist on a task."""
        return self._request("POST", f"task/{task_id}/checklist", json={"name": name})

    def update_checklist(self, checklist_id: str, **updates) -> Dict[str, Any]:
        """Update a checklist."""
        return self._request("PUT", f"checklist/{checklist_id}", json=updates)

    def delete_checklist(self, checklist_id: str) -> Dict[str, Any]:
        """Delete a checklist."""
        return self._request("DELETE", f"checklist/{checklist_id}")

    def create_checklist_item(self, checklist_id: str, name: str, **item_data) -> Dict[str, Any]:
        """Create a checklist item."""
        data = {"name": name, **item_data}
        return self._request("POST", f"checklist/{checklist_id}/checklist_item", json=data)

    def update_checklist_item(self, checklist_id: str, checklist_item_id: str, **updates) -> Dict[str, Any]:
        """Update a checklist item."""
        return self._request("PUT", f"checklist/{checklist_id}/checklist_item/{checklist_item_id}", json=updates)

    def delete_checklist_item(self, checklist_id: str, checklist_item_id: str) -> Dict[str, Any]:
        """Delete a checklist item."""
        return self._request("DELETE", f"checklist/{checklist_id}/checklist_item/{checklist_item_id}")

    # Comments
    def create_task_comment(self, task_id: str, comment_text: str) -> Dict[str, Any]:
        """Add comment to a task."""
        return self._request(
            "POST", f"task/{task_id}/comment", json={"comment_text": comment_text}
        )

    def get_task_comments(self, task_id: str) -> Dict[str, Any]:
        """Get all comments on a task."""
        return self._request("GET", f"task/{task_id}/comment")

    # Search
    def search(self, team_id: str, query: str, **filters) -> Dict[str, Any]:
        """Search workspace."""
        params = {"query": query, **filters}
        return self._request("GET", f"team/{team_id}/search", params=params)

    # Time tracking
    def get_time_entries(self, team_id: str, **params) -> Dict[str, Any]:
        """Get time entries."""
        return self._request("GET", f"team/{team_id}/time_entries", params=params)

    def create_time_entry(self, team_id: str, **entry_data) -> Dict[str, Any]:
        """Create a time entry."""
        return self._request("POST", f"team/{team_id}/time_entries", json=entry_data)

    def __repr__(self) -> str:
        token_preview = self.api_token[:20] if self.api_token else "None"
        return f"ClickUpClient(token={token_preview}...)"

    def __enter__(self):
        """Context manager support."""
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """Clean up session on exit."""
        self.session.close()
