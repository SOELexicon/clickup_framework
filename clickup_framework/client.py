"""
ClickUp API Client

Core client for ClickUp API with authentication, rate limiting, and error handling.
"""

import os
import time
import logging
from typing import Dict, Any, Optional, List
import requests

from .exceptions import (
    ClickUpAPIError,
    ClickUpAuthError,
    ClickUpRateLimitError,
    ClickUpNotFoundError,
    ClickUpTimeoutError,
)
from .rate_limiter import RateLimiter
from .context import get_context_manager


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
            api_token: ClickUp API token (defaults to CLICKUP_API_TOKEN env var or stored context)
            rate_limit: Requests per minute (default: 100)
            timeout: Request timeout in seconds (default: 30)
            max_retries: Maximum retry attempts (default: 3)
        """
        # Store token sources for fallback functionality
        self.param_token = api_token
        self.env_token = os.environ.get("CLICKUP_API_TOKEN")
        context = get_context_manager()
        self.context_token = context.get_api_token()

        # Check for token in priority order: 1) parameter, 2) environment variable, 3) stored context
        self.api_token = self.param_token or self.env_token
        if not self.api_token:
            self.api_token = self.context_token
        if not self.api_token:
            raise ClickUpAuthError("API token not provided. Set via parameter, CLICKUP_API_TOKEN env var, or use 'set_current token <token>'")

        # Track which token source is currently active
        if self.param_token:
            self.token_source = "parameter"
        elif self.env_token and self.api_token == self.env_token:
            self.token_source = "environment"
        else:
            self.token_source = "context"

        # Track which token sources have been tried (for preventing infinite fallback loops)
        self._tried_sources = {self.token_source}

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

    def _switch_to_fallback_token(self) -> bool:
        """
        Attempt to switch to a fallback token source on authentication failure.

        Returns:
            True if a fallback token was found and switched to, False otherwise
        """
        fallback_token = None
        fallback_source = None

        # Determine fallback based on current source, skipping already-tried sources
        if self.token_source == "environment" and "context" not in self._tried_sources:
            if self.context_token and self.context_token != self.env_token:
                fallback_token = self.context_token
                fallback_source = "context"
        elif self.token_source == "context" and "environment" not in self._tried_sources:
            if self.env_token and self.env_token != self.context_token:
                fallback_token = self.env_token
                fallback_source = "environment"
        elif self.token_source == "parameter":
            # Try environment first, then context (skip already-tried sources)
            if "environment" not in self._tried_sources and self.env_token and self.env_token != self.param_token:
                fallback_token = self.env_token
                fallback_source = "environment"
            elif "context" not in self._tried_sources and self.context_token and self.context_token != self.param_token:
                fallback_token = self.context_token
                fallback_source = "context"

        if fallback_token:
            logger.info(f"Switching from {self.token_source} token to {fallback_source} token due to 401 error")
            self.api_token = fallback_token
            self.token_source = fallback_source
            self._tried_sources.add(fallback_source)
            # Update session headers with new token
            self.session.headers.update({"Authorization": self.api_token})
            return True

        return False

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
        # Handle v3 endpoints (Docs API) - they use a different base path
        endpoint_stripped = endpoint.lstrip('/')
        if endpoint_stripped.startswith('v3/'):
            url = f"https://api.clickup.com/api/{endpoint_stripped}"
        else:
            url = f"{self.BASE_URL}/{endpoint_stripped}"

        # Convert list parameters to bracket notation for ClickUp API
        # e.g., assignees=[1, 2] becomes assignees[]=[1, 2] for proper array handling
        if params:
            normalized_params = {}
            for key, value in params.items():
                if isinstance(value, list):
                    # Use bracket notation for array parameters
                    normalized_params[f"{key}[]"] = value
                else:
                    normalized_params[key] = value
            params = normalized_params

        # Acquire rate limit token
        self.rate_limiter.acquire()

        # Track if we've already tried fallback to prevent infinite loop
        fallback_attempted = False

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
                    # Try fallback token if available and not already attempted
                    if not fallback_attempted and self._switch_to_fallback_token():
                        fallback_attempted = True
                        logger.info("Retrying request with fallback token...")
                        # Retry immediately with new token (don't count as an attempt)
                        continue
                    # Extract actual error message from API response
                    try:
                        error_data = response.json()
                        message = error_data.get("err", error_data.get("error", "Invalid or expired API token"))
                    except:
                        message = response.text or "Invalid or expired API token"
                    raise ClickUpAuthError(message)

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

    # Task Relationships - Dependencies
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
            - depends_on: Creates "waiting on" relationship (task_id waits for depends_on)
            - dependency_of: Creates "blocking" relationship (task_id blocks dependency_of)
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

        Note:
            Only one of depends_on or dependency_of should be provided.
        """
        if not depends_on and not dependency_of:
            raise ValueError("Either depends_on or dependency_of must be provided")

        query_params = params.copy()
        if depends_on:
            query_params["depends_on"] = depends_on
        if dependency_of:
            query_params["dependency_of"] = dependency_of

        return self._request("DELETE", f"task/{task_id}/dependency", params=query_params)

    # Task Relationships - Links
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

    # Docs API (v3 endpoints)
    def get_workspace_docs(self, workspace_id: str, **params) -> Dict[str, Any]:
        """Get all docs in a workspace."""
        return self._request("GET", f"/v3/workspaces/{workspace_id}/docs", params=params)

    def create_doc(self, workspace_id: str, name: str, **doc_data) -> Dict[str, Any]:
        """Create a new doc in workspace."""
        data = {"name": name, **doc_data}
        return self._request("POST", f"/v3/workspaces/{workspace_id}/docs", json=data)

    def get_doc(self, workspace_id: str, doc_id: str) -> Dict[str, Any]:
        """Get doc by ID."""
        return self._request("GET", f"/v3/workspaces/{workspace_id}/docs/{doc_id}")

    def get_doc_pages(self, workspace_id: str, doc_id: str, **params) -> Dict[str, Any]:
        """Get all pages belonging to a doc."""
        return self._request("GET", f"/v3/workspaces/{workspace_id}/docs/{doc_id}/pages", params=params)

    def create_page(self, workspace_id: str, doc_id: str, name: str, content: Optional[str] = None, **page_data) -> Dict[str, Any]:
        """Create a new page in a doc."""
        data = {"name": name}
        if content:
            data["content"] = content
        data.update(page_data)
        return self._request("POST", f"/v3/workspaces/{workspace_id}/docs/{doc_id}/pages", json=data)

    def get_page(self, workspace_id: str, doc_id: str, page_id: str) -> Dict[str, Any]:
        """Get page by ID."""
        return self._request("GET", f"/v3/workspaces/{workspace_id}/docs/{doc_id}/pages/{page_id}")

    def update_page(self, workspace_id: str, doc_id: str, page_id: str, **updates) -> Dict[str, Any]:
        """Update a page."""
        return self._request("PUT", f"/v3/workspaces/{workspace_id}/docs/{doc_id}/pages/{page_id}", json=updates)

    # Attachments
    def create_task_attachment(self, task_id: str, file_path: str, **params) -> Dict[str, Any]:
        """
        Create task attachment by uploading a file.

        Args:
            task_id: Task ID
            file_path: Path to file to upload
            **params: Additional query parameters (custom_task_ids, team_id)

        Returns:
            Attachment info

        Note:
            This method requires the file to be accessible on the local filesystem.
        """
        import os
        from pathlib import Path

        if not os.path.exists(file_path):
            raise FileNotFoundError(f"File not found: {file_path}")

        file_name = Path(file_path).name

        # Temporarily remove Content-Type header for multipart/form-data
        original_headers = self.session.headers.copy()
        self.session.headers.pop('Content-Type', None)

        try:
            url = f"{self.BASE_URL}/task/{task_id}/attachment"
            self.rate_limiter.acquire()

            with open(file_path, 'rb') as f:
                files = {'attachment': (file_name, f)}
                response = self.session.post(
                    url,
                    files=files,
                    params=params,
                    timeout=self.timeout
                )

            if response.status_code in [200, 201]:
                return response.json()
            elif response.status_code == 401:
                # Extract actual error message from API response
                try:
                    error_data = response.json()
                    message = error_data.get("err", error_data.get("error", "Invalid or expired API token"))
                except:
                    message = response.text or "Invalid or expired API token"
                raise ClickUpAuthError(message)
            elif response.status_code == 404:
                raise ClickUpNotFoundError("task", task_id)
            else:
                try:
                    error_data = response.json()
                    message = error_data.get("err", error_data.get("error", "Unknown error"))
                except:
                    message = response.text or "Unknown error"
                raise ClickUpAPIError(response.status_code, message)
        finally:
            # Restore Content-Type header
            self.session.headers.update(original_headers)

    # Authorization
    def get_access_token(self, client_id: str, client_secret: str, code: str) -> Dict[str, Any]:
        """
        Get OAuth access token.

        Args:
            client_id: OAuth app client ID
            client_secret: OAuth app client secret
            code: Authorization code from OAuth flow

        Returns:
            Access token response with access_token field
        """
        return self._request("POST", "oauth/token", json={
            "client_id": client_id,
            "client_secret": client_secret,
            "code": code
        })

    def get_authorized_user(self) -> Dict[str, Any]:
        """
        Get currently authenticated user info.

        Returns:
            User object with id, username, email, etc.
        """
        return self._request("GET", "user")

    # Comments - Extended
    def get_view_comments(self, view_id: str, **params) -> Dict[str, Any]:
        """Get chat comments for a view."""
        return self._request("GET", f"view/{view_id}/comment", params=params)

    def create_view_comment(self, view_id: str, comment_text: str, notify_all: bool = False) -> Dict[str, Any]:
        """Create a chat comment on a view."""
        return self._request("POST", f"view/{view_id}/comment", json={
            "comment_text": comment_text,
            "notify_all": notify_all
        })

    def get_list_comments(self, list_id: str, **params) -> Dict[str, Any]:
        """Get comments for a list."""
        return self._request("GET", f"list/{list_id}/comment", params=params)

    def create_list_comment(self, list_id: str, comment_text: str, notify_all: bool = False) -> Dict[str, Any]:
        """Create a comment on a list."""
        return self._request("POST", f"list/{list_id}/comment", json={
            "comment_text": comment_text,
            "notify_all": notify_all
        })

    def update_comment(self, comment_id: str, comment_text: str, **params) -> Dict[str, Any]:
        """Update a comment."""
        return self._request("PUT", f"comment/{comment_id}", json={"comment_text": comment_text}, params=params)

    def delete_comment(self, comment_id: str) -> Dict[str, Any]:
        """Delete a comment."""
        return self._request("DELETE", f"comment/{comment_id}")

    def get_threaded_comments(self, comment_id: str) -> Dict[str, Any]:
        """Get threaded/reply comments for a comment."""
        return self._request("GET", f"comment/{comment_id}/reply")

    def create_threaded_comment(self, comment_id: str, comment_text: str, notify_all: bool = False) -> Dict[str, Any]:
        """Create a threaded reply to a comment."""
        return self._request("POST", f"comment/{comment_id}/reply", json={
            "comment_text": comment_text,
            "notify_all": notify_all
        })

    # Custom Fields - Extended
    def get_folder_custom_fields(self, folder_id: str) -> Dict[str, Any]:
        """Get custom fields accessible from a folder."""
        return self._request("GET", f"folder/{folder_id}/field")

    def get_space_custom_fields(self, space_id: str) -> Dict[str, Any]:
        """Get custom fields accessible from a space."""
        return self._request("GET", f"space/{space_id}/field")

    def get_workspace_custom_fields(self, team_id: str) -> Dict[str, Any]:
        """Get all custom fields in a workspace."""
        return self._request("GET", f"team/{team_id}/field")

    # Custom Task Types
    def get_custom_task_types(self, team_id: str) -> Dict[str, Any]:
        """Get custom task types for a workspace."""
        return self._request("GET", f"team/{team_id}/custom_item")

    # Time Tracking - Extended
    def update_time_entry(self, task_id: str, interval_id: str, **updates) -> Dict[str, Any]:
        """
        Update a time entry.

        Args:
            task_id: Task ID
            interval_id: Time entry interval ID
            **updates: Fields to update (start, end, duration, description, etc.)

        Returns:
            Updated time entry
        """
        return self._request("PUT", f"task/{task_id}/time/{interval_id}", json=updates)

    def delete_time_entry(self, task_id: str, interval_id: str) -> Dict[str, Any]:
        """Delete a time entry."""
        return self._request("DELETE", f"task/{task_id}/time/{interval_id}")

    # User Groups
    def create_user_group(self, team_id: str, name: str, member_ids: Optional[List[int]] = None) -> Dict[str, Any]:
        """
        Create a user group in a workspace.

        Args:
            team_id: Workspace/team ID
            name: Group name
            member_ids: List of user IDs to add to the group

        Returns:
            Created group object
        """
        data = {"name": name}
        if member_ids:
            data["members"] = member_ids
        return self._request("POST", f"team/{team_id}/group", json=data)

    def update_user_group(self, group_id: str, **updates) -> Dict[str, Any]:
        """
        Update a user group.

        Args:
            group_id: Group ID
            **updates: Fields to update (name, members, etc.)

        Returns:
            Updated group object
        """
        return self._request("PUT", f"group/{group_id}", json=updates)

    def delete_user_group(self, group_id: str) -> Dict[str, Any]:
        """Delete a user group."""
        return self._request("DELETE", f"group/{group_id}")

    def get_user_groups(self, **params) -> Dict[str, Any]:
        """
        Get user groups.

        Args:
            **params: Query parameters (team_id, group_ids)

        Returns:
            Groups list
        """
        return self._request("GET", "group", params=params)

    # Users
    def invite_user_to_workspace(self, team_id: str, email: str, **user_data) -> Dict[str, Any]:
        """
        Invite user to workspace.

        Args:
            team_id: Workspace/team ID
            email: User email to invite
            **user_data: Additional user data (admin, custom_role_id)

        Returns:
            Invited user object
        """
        data = {"email": email, **user_data}
        return self._request("POST", f"team/{team_id}/user", json=data)

    def get_user(self, team_id: str, user_id: str) -> Dict[str, Any]:
        """Get user information in a workspace."""
        return self._request("GET", f"team/{team_id}/user/{user_id}")

    def edit_user_on_workspace(self, team_id: str, user_id: str, **updates) -> Dict[str, Any]:
        """
        Edit user on workspace.

        Args:
            team_id: Workspace/team ID
            user_id: User ID
            **updates: Fields to update (username, admin, custom_role_id)

        Returns:
            Updated user object
        """
        return self._request("PUT", f"team/{team_id}/user/{user_id}", json=updates)

    def remove_user_from_workspace(self, team_id: str, user_id: str) -> Dict[str, Any]:
        """Remove user from workspace."""
        return self._request("DELETE", f"team/{team_id}/user/{user_id}")

    # Views
    def get_workspace_views(self, team_id: str) -> Dict[str, Any]:
        """Get Everything level views for a workspace."""
        return self._request("GET", f"team/{team_id}/view")

    def create_workspace_view(self, team_id: str, name: str, type: str, **view_data) -> Dict[str, Any]:
        """
        Create Everything level view for a workspace.

        Args:
            team_id: Workspace/team ID
            name: View name
            type: View type (list, board, calendar, etc.)
            **view_data: Additional view configuration

        Returns:
            Created view object
        """
        data = {"name": name, "type": type, **view_data}
        return self._request("POST", f"team/{team_id}/view", json=data)

    def get_space_views(self, space_id: str) -> Dict[str, Any]:
        """Get views for a space."""
        return self._request("GET", f"space/{space_id}/view")

    def create_space_view(self, space_id: str, name: str, type: str, **view_data) -> Dict[str, Any]:
        """
        Create view for a space.

        Args:
            space_id: Space ID
            name: View name
            type: View type (list, board, calendar, etc.)
            **view_data: Additional view configuration

        Returns:
            Created view object
        """
        data = {"name": name, "type": type, **view_data}
        return self._request("POST", f"space/{space_id}/view", json=data)

    def get_folder_views(self, folder_id: str) -> Dict[str, Any]:
        """Get views for a folder."""
        return self._request("GET", f"folder/{folder_id}/view")

    def create_folder_view(self, folder_id: str, name: str, type: str, **view_data) -> Dict[str, Any]:
        """
        Create view for a folder.

        Args:
            folder_id: Folder ID
            name: View name
            type: View type (list, board, calendar, etc.)
            **view_data: Additional view configuration

        Returns:
            Created view object
        """
        data = {"name": name, "type": type, **view_data}
        return self._request("POST", f"folder/{folder_id}/view", json=data)

    def get_list_views(self, list_id: str) -> Dict[str, Any]:
        """Get views for a list."""
        return self._request("GET", f"list/{list_id}/view")

    def create_list_view(self, list_id: str, name: str, type: str, **view_data) -> Dict[str, Any]:
        """
        Create view for a list.

        Args:
            list_id: List ID
            name: View name
            type: View type (list, board, calendar, etc.)
            **view_data: Additional view configuration

        Returns:
            Created view object
        """
        data = {"name": name, "type": type, **view_data}
        return self._request("POST", f"list/{list_id}/view", json=data)

    def get_view(self, view_id: str) -> Dict[str, Any]:
        """Get view by ID."""
        return self._request("GET", f"view/{view_id}")

    def update_view(self, view_id: str, **updates) -> Dict[str, Any]:
        """Update a view."""
        return self._request("PUT", f"view/{view_id}", json=updates)

    def delete_view(self, view_id: str) -> Dict[str, Any]:
        """Delete a view."""
        return self._request("DELETE", f"view/{view_id}")

    def get_view_tasks(self, view_id: str, **params) -> Dict[str, Any]:
        """
        Get tasks from a view.

        Args:
            view_id: View ID
            **params: Query parameters (page, order_by, etc.)

        Returns:
            Tasks from the view
        """
        return self._request("GET", f"view/{view_id}/task", params=params)

    # Webhooks
    def get_webhooks(self, team_id: str) -> Dict[str, Any]:
        """Get all webhooks for a workspace."""
        return self._request("GET", f"team/{team_id}/webhook")

    def create_webhook(self, team_id: str, endpoint: str, events: List[str], **webhook_data) -> Dict[str, Any]:
        """
        Create a webhook.

        Args:
            team_id: Workspace/team ID
            endpoint: Webhook URL endpoint
            events: List of event types to subscribe to
            **webhook_data: Additional webhook configuration (space_id, folder_id, list_id, task_id)

        Returns:
            Created webhook object
        """
        data = {"endpoint": endpoint, "events": events, **webhook_data}
        return self._request("POST", f"team/{team_id}/webhook", json=data)

    def update_webhook(self, webhook_id: str, **updates) -> Dict[str, Any]:
        """
        Update a webhook.

        Args:
            webhook_id: Webhook ID
            **updates: Fields to update (endpoint, events, status)

        Returns:
            Updated webhook object
        """
        return self._request("PUT", f"webhook/{webhook_id}", json=updates)

    def delete_webhook(self, webhook_id: str) -> Dict[str, Any]:
        """Delete a webhook."""
        return self._request("DELETE", f"webhook/{webhook_id}")

    # Workspaces - Extended
    def get_authorized_workspaces(self) -> Dict[str, Any]:
        """Get all authorized workspaces/teams for the current user."""
        return self._request("GET", "team")

    def get_workspace_seats(self, team_id: str) -> Dict[str, Any]:
        """Get workspace seat information."""
        return self._request("GET", f"team/{team_id}/seats")

    def get_workspace_plan(self, team_id: str) -> Dict[str, Any]:
        """Get workspace plan details."""
        return self._request("GET", f"team/{team_id}/plan")

    def get_token_source(self) -> str:
        """
        Get the currently active token source.

        Returns:
            String indicating the token source: "parameter", "environment", or "context"
        """
        return self.token_source

    def __repr__(self) -> str:
        token_preview = self.api_token[:20] if self.api_token else "None"
        return f"ClickUpClient(token={token_preview}..., source={self.token_source})"

    def __enter__(self):
        """Context manager support."""
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """Clean up session on exit."""
        self.session.close()
