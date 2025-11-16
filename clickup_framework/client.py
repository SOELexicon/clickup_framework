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
from .apis import (
    TasksAPI,
    ListsAPI,
    FoldersAPI,
    SpacesAPI,
    WorkspacesAPI,
    GoalsAPI,
    GuestsAPI,
    TagsAPI,
    TimeTrackingAPI,
    TimeTrackingLegacyAPI,
    MembersAPI,
    RolesAPI,
    TemplatesAPI,
    ChecklistsAPI,
    CommentsAPI,
    CustomFieldsAPI,
    ViewsAPI,
    WebhooksAPI,
    DocsAPI,
    AttachmentsAPI,
    AuthAPI,
    UsersAPI,
    GroupsAPI,
    SearchAPI,
)


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

        # Initialize API classes
        self.tasks = TasksAPI(self)
        self.lists = ListsAPI(self)
        self.folders = FoldersAPI(self)
        self.spaces = SpacesAPI(self)
        self.workspaces = WorkspacesAPI(self)
        self.goals = GoalsAPI(self)
        self.guests = GuestsAPI(self)
        self.tags = TagsAPI(self)
        self.time_tracking = TimeTrackingAPI(self)
        self.time_tracking_legacy = TimeTrackingLegacyAPI(self)
        self.members = MembersAPI(self)
        self.roles = RolesAPI(self)
        self.templates = TemplatesAPI(self)
        self.checklists = ChecklistsAPI(self)
        self.comments = CommentsAPI(self)
        self.custom_fields = CustomFieldsAPI(self)
        self.views = ViewsAPI(self)
        self.webhooks = WebhooksAPI(self)
        self.docs = DocsAPI(self)
        self.attachments = AttachmentsAPI(self)
        self.auth = AuthAPI(self)
        self.users = UsersAPI(self)
        self.groups = GroupsAPI(self)
        self.search_api = SearchAPI(self)

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
                    # Handle cases where API returns empty body with 200 (some PUT operations)
                    try:
                        return response.json()
                    except (ValueError, requests.exceptions.JSONDecodeError):
                        # Empty or malformed response body - return empty dict
                        return {}

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

    # Task endpoints - Delegated to TasksAPI
    def get_task(self, task_id: str, **params) -> Dict[str, Any]:
        """Get task by ID."""
        return self.tasks.get_task(task_id, **params)

    def get_list_tasks(self, list_id: str, **params) -> Dict[str, Any]:
        """Get all tasks in a list."""
        return self.tasks.get_list_tasks(list_id, **params)

    def get_team_tasks(self, team_id: str, **params) -> Dict[str, Any]:
        """Get all tasks in a team/workspace."""
        return self.tasks.get_team_tasks(team_id, **params)

    def create_task(self, list_id: str, **task_data) -> Dict[str, Any]:
        """Create a new task."""
        return self.tasks.create_task(list_id, **task_data)

    def update_task(self, task_id: str, **updates) -> Dict[str, Any]:
        """Update a task."""
        return self.tasks.update_task(task_id, **updates)

    def delete_task(self, task_id: str) -> Dict[str, Any]:
        """Delete a task."""
        return self.tasks.delete_task(task_id)

    def merge_tasks(self, task_id: str, merge_task_id: str, **params) -> Dict[str, Any]:
        """Merge two tasks."""
        return self.tasks.merge_tasks(task_id, merge_task_id, **params)

    def get_task_time_in_status(self, task_id: str, **params) -> Dict[str, Any]:
        """Get task's time in status."""
        return self.tasks.get_task_time_in_status(task_id, **params)

    def get_bulk_tasks_time_in_status(self, task_ids: List[str], **params) -> Dict[str, Any]:
        """Get bulk tasks' time in status."""
        return self.tasks.get_bulk_tasks_time_in_status(task_ids, **params)

    def create_task_from_template(self, list_id: str, template_id: str, **task_data) -> Dict[str, Any]:
        """Create a task from a template."""
        return self.tasks.create_task_from_template(list_id, template_id, **task_data)

    def add_task_tag(self, task_id: str, tag_name: str, **params) -> Dict[str, Any]:
        """Add a tag to a task."""
        return self.tags.add_task_tag(task_id, tag_name, **params)

    def remove_task_tag(self, task_id: str, tag_name: str, **params) -> Dict[str, Any]:
        """Remove a tag from a task."""
        return self.tags.remove_task_tag(task_id, tag_name, **params)

    def add_task_dependency(
        self,
        task_id: str,
        depends_on: Optional[str] = None,
        dependency_of: Optional[str] = None,
        **params
    ) -> Dict[str, Any]:
        """Add a dependency relationship between tasks."""
        return self.tasks.add_task_dependency(task_id, depends_on, dependency_of, **params)

    def delete_task_dependency(
        self,
        task_id: str,
        depends_on: Optional[str] = None,
        dependency_of: Optional[str] = None,
        **params
    ) -> Dict[str, Any]:
        """Remove a dependency relationship between tasks."""
        return self.tasks.delete_task_dependency(task_id, depends_on, dependency_of, **params)

    def add_task_link(
        self,
        task_id: str,
        links_to: str,
        **params
    ) -> Dict[str, Any]:
        """Link two tasks together (simple relationship)."""
        return self.tasks.add_task_link(task_id, links_to, **params)

    def delete_task_link(
        self,
        task_id: str,
        links_to: str,
        **params
    ) -> Dict[str, Any]:
        """Remove a link between two tasks."""
        return self.tasks.delete_task_link(task_id, links_to, **params)

    # List endpoints - Delegated to ListsAPI
    def get_list(self, list_id: str) -> Dict[str, Any]:
        """Get list by ID."""
        return self.lists.get_list(list_id)

    def create_list(self, folder_id: str, name: str, **list_data) -> Dict[str, Any]:
        """Create a new list."""
        return self.lists.create_list(folder_id, name, **list_data)

    def get_folder_lists(self, folder_id: str, archived: bool = False) -> Dict[str, Any]:
        """Get all lists in a folder."""
        return self.lists.get_folder_lists(folder_id, archived)

    def get_space_lists(self, space_id: str, archived: bool = False) -> Dict[str, Any]:
        """Get folderless lists in a space."""
        return self.lists.get_space_lists(space_id, archived)

    def create_space_list(self, space_id: str, name: str, **list_data) -> Dict[str, Any]:
        """Create a folderless list in a space."""
        return self.lists.create_space_list(space_id, name, **list_data)

    def delete_list(self, list_id: str) -> Dict[str, Any]:
        """Delete a list."""
        return self.lists.delete_list(list_id)

    def add_task_to_list(self, list_id: str, task_id: str) -> Dict[str, Any]:
        """Add a task to a list."""
        return self.lists.add_task_to_list(list_id, task_id)

    def remove_task_from_list(self, list_id: str, task_id: str) -> Dict[str, Any]:
        """Remove a task from a list."""
        return self.lists.remove_task_from_list(list_id, task_id)

    def create_list_from_template_in_folder(self, folder_id: str, template_id: str, **list_data) -> Dict[str, Any]:
        """Create a list from a template in a folder."""
        return self.lists.create_list_from_template_in_folder(folder_id, template_id, **list_data)

    def create_list_from_template_in_space(self, space_id: str, template_id: str, **list_data) -> Dict[str, Any]:
        """Create a list from a template in a space."""
        return self.lists.create_list_from_template_in_space(space_id, template_id, **list_data)

    def update_list(self, list_id: str, **updates) -> Dict[str, Any]:
        """Update a list."""
        return self.lists.update_list(list_id, **updates)

    # Folder endpoints - Delegated to FoldersAPI
    def get_folder(self, folder_id: str) -> Dict[str, Any]:
        """Get folder by ID."""
        return self.folders.get_folder(folder_id)

    def create_folder(self, space_id: str, name: str) -> Dict[str, Any]:
        """Create a new folder."""
        return self.folders.create_folder(space_id, name)

    def update_folder(self, folder_id: str, **updates) -> Dict[str, Any]:
        """Update a folder."""
        return self.folders.update_folder(folder_id, **updates)

    def get_space_folders(self, space_id: str, archived: bool = False) -> Dict[str, Any]:
        """Get all folders in a space."""
        return self.folders.get_space_folders(space_id, archived)

    def delete_folder(self, folder_id: str) -> Dict[str, Any]:
        """Delete a folder."""
        return self.folders.delete_folder(folder_id)

    def create_folder_from_template(self, space_id: str, template_id: str, **folder_data) -> Dict[str, Any]:
        """Create a folder from a template."""
        return self.folders.create_folder_from_template(space_id, template_id, **folder_data)

    # Space endpoints - Delegated to SpacesAPI
    def get_space(self, space_id: str) -> Dict[str, Any]:
        """Get space by ID."""
        return self.spaces.get_space(space_id)

    def get_team_spaces(self, team_id: str, archived: bool = False) -> Dict[str, Any]:
        """Get all spaces in a team."""
        return self.spaces.get_team_spaces(team_id, archived)

    def create_space(self, team_id: str, name: str, **space_data) -> Dict[str, Any]:
        """Create a new space."""
        return self.spaces.create_space(team_id, name, **space_data)

    def update_space(self, space_id: str, **updates) -> Dict[str, Any]:
        """Update a space."""
        return self.spaces.update_space(space_id, **updates)

    def delete_space(self, space_id: str) -> Dict[str, Any]:
        """Delete a space."""
        return self.spaces.delete_space(space_id)

    # Tags - Delegated to TagsAPI
    def get_space_tags(self, space_id: str) -> Dict[str, Any]:
        """Get all tags in a space."""
        return self.tags.get_space_tags(space_id)

    def create_space_tag(self, space_id: str, tag_name: str, tag_fg: str = "#000000", tag_bg: str = "#FFFFFF") -> Dict[str, Any]:
        """Create a tag in a space."""
        return self.tags.create_space_tag(space_id, tag_name, tag_fg, tag_bg)

    def update_space_tag(self, space_id: str, tag_name: str, **tag_updates) -> Dict[str, Any]:
        """Update a tag in a space."""
        return self.tags.update_space_tag(space_id, tag_name, **tag_updates)

    def delete_space_tag(self, space_id: str, tag_name: str) -> Dict[str, Any]:
        """Delete a tag from a space."""
        return self.tags.delete_space_tag(space_id, tag_name)

    # Workspace hierarchy - Delegated to WorkspacesAPI
    def get_workspace_hierarchy(self, team_id: str) -> Dict[str, Any]:
        """Get complete workspace hierarchy."""
        return self.workspaces.get_workspace_hierarchy(team_id)

    # Custom Fields endpoints - Delegated to CustomFieldsAPI
    def get_accessible_custom_fields(self, list_id: str) -> Dict[str, Any]:
        """Get custom fields accessible from a list."""
        return self.custom_fields.get_accessible_custom_fields(list_id)

    def set_custom_field_value(self, task_id: str, field_id: str, value: Any) -> Dict[str, Any]:
        """Set custom field value on a task."""
        return self.custom_fields.set_custom_field_value(task_id, field_id, value)

    def set_custom_field(self, task_id: str, field_id: str, value: Any) -> Dict[str, Any]:
        """Set custom field value on a task (alias for set_custom_field_value)."""
        return self.set_custom_field_value(task_id, field_id, value)

    def remove_custom_field_value(self, task_id: str, field_id: str) -> Dict[str, Any]:
        """Remove custom field value from a task."""
        return self.custom_fields.remove_custom_field_value(task_id, field_id)

    # Checklist endpoints - Delegated to ChecklistsAPI
    def create_checklist(self, task_id: str, name: str) -> Dict[str, Any]:
        """Create a checklist on a task."""
        return self.checklists.create_checklist(task_id, name)

    def update_checklist(self, checklist_id: str, **updates) -> Dict[str, Any]:
        """Update a checklist."""
        return self.checklists.update_checklist(checklist_id, **updates)

    def delete_checklist(self, checklist_id: str) -> Dict[str, Any]:
        """Delete a checklist."""
        return self.checklists.delete_checklist(checklist_id)

    def create_checklist_item(self, checklist_id: str, name: str, **item_data) -> Dict[str, Any]:
        """Create a checklist item."""
        return self.checklists.create_checklist_item(checklist_id, name, **item_data)

    def update_checklist_item(self, checklist_id: str, checklist_item_id: str, **updates) -> Dict[str, Any]:
        """Update a checklist item."""
        return self.checklists.update_checklist_item(checklist_id, checklist_item_id, **updates)

    def delete_checklist_item(self, checklist_id: str, checklist_item_id: str) -> Dict[str, Any]:
        """Delete a checklist item."""
        return self.checklists.delete_checklist_item(checklist_id, checklist_item_id)

    # Comments - Delegated to CommentsAPI
    def create_task_comment(self, task_id: str, comment_text: str) -> Dict[str, Any]:
        """Add comment to a task."""
        return self.comments.create_task_comment(task_id, comment_text)

    def get_task_comments(self, task_id: str) -> Dict[str, Any]:
        """Get all comments on a task."""
        return self.comments.get_task_comments(task_id)

    # Members - Delegated to MembersAPI
    def get_task_members(self, task_id: str) -> Dict[str, Any]:
        """Get task members."""
        return self.members.get_task_members(task_id)

    def get_list_members(self, list_id: str) -> Dict[str, Any]:
        """Get list members."""
        return self.members.get_list_members(list_id)

    # Search - Delegated to SearchAPI
    def search(self, team_id: str, query: str, **filters) -> Dict[str, Any]:
        """Search workspace."""
        return self.search_api.search(team_id, query, **filters)

    # Time tracking - Delegated to TimeTrackingAPI
    def get_time_entries(self, team_id: str, **params) -> Dict[str, Any]:
        """Get time entries."""
        return self.time_tracking.get_time_entries(team_id, **params)

    def create_time_entry(self, team_id: str, **entry_data) -> Dict[str, Any]:
        """Create a time entry."""
        return self.time_tracking.create_time_entry(team_id, **entry_data)

    def get_time_entry(self, team_id: str, timer_id: str) -> Dict[str, Any]:
        """Get a singular time entry."""
        return self.time_tracking.get_time_entry(team_id, timer_id)

    def update_time_entry(self, team_id: str, timer_id: str, **updates) -> Dict[str, Any]:
        """Update a time entry."""
        return self.time_tracking.update_time_entry(team_id, timer_id, **updates)

    def delete_time_entry(self, team_id: str, timer_id: str) -> Dict[str, Any]:
        """Delete a time entry."""
        return self.time_tracking.delete_time_entry(team_id, timer_id)

    def get_time_entry_history(self, team_id: str, timer_id: str) -> Dict[str, Any]:
        """Get time entry history."""
        return self.time_tracking.get_time_entry_history(team_id, timer_id)

    def get_current_time_entry(self, team_id: str) -> Dict[str, Any]:
        """Get running time entry."""
        return self.time_tracking.get_current_time_entry(team_id)

    def get_time_entry_tags(self, team_id: str) -> Dict[str, Any]:
        """Get all tags from time entries."""
        return self.time_tracking.get_time_entry_tags(team_id)

    def add_time_entry_tags(self, team_id: str, **tag_data) -> Dict[str, Any]:
        """Add tags from time entries."""
        return self.time_tracking.add_time_entry_tags(team_id, **tag_data)

    def update_time_entry_tags(self, team_id: str, **tag_data) -> Dict[str, Any]:
        """Change tag names from time entries."""
        return self.time_tracking.update_time_entry_tags(team_id, **tag_data)

    def delete_time_entry_tags(self, team_id: str, **params) -> Dict[str, Any]:
        """Remove tags from time entries."""
        return self.time_tracking.delete_time_entry_tags(team_id, **params)

    def start_time_entry(self, team_id: str, **entry_data) -> Dict[str, Any]:
        """Start a time entry."""
        return self.time_tracking.start_time_entry(team_id, **entry_data)

    def stop_time_entry(self, team_id: str, **params) -> Dict[str, Any]:
        """Stop a time entry."""
        return self.time_tracking.stop_time_entry(team_id, **params)

    # Docs API (v3 endpoints) - Delegated to DocsAPI
    def get_workspace_docs(self, workspace_id: str, **params) -> Dict[str, Any]:
        """Get all docs in a workspace."""
        return self.docs.get_workspace_docs(workspace_id, **params)

    def create_doc(self, workspace_id: str, name: str, **doc_data) -> Dict[str, Any]:
        """Create a new doc in workspace."""
        return self.docs.create_doc(workspace_id, name, **doc_data)

    def get_doc(self, workspace_id: str, doc_id: str) -> Dict[str, Any]:
        """Get doc by ID."""
        return self.docs.get_doc(workspace_id, doc_id)

    def get_doc_pages(self, workspace_id: str, doc_id: str, **params) -> Dict[str, Any]:
        """Get all pages belonging to a doc."""
        return self.docs.get_doc_pages(workspace_id, doc_id, **params)

    def create_page(self, workspace_id: str, doc_id: str, name: str, content: Optional[str] = None, **page_data) -> Dict[str, Any]:
        """Create a new page in a doc."""
        return self.docs.create_page(workspace_id, doc_id, name, content, **page_data)

    def get_page(self, workspace_id: str, doc_id: str, page_id: str) -> Dict[str, Any]:
        """Get page by ID."""
        return self.docs.get_page(workspace_id, doc_id, page_id)

    def update_page(self, workspace_id: str, doc_id: str, page_id: str, **updates) -> Dict[str, Any]:
        """Update a page."""
        return self.docs.update_page(workspace_id, doc_id, page_id, **updates)

    # Attachments - Delegated to AttachmentsAPI
    def create_task_attachment(self, task_id: str, file_path: str, **params) -> Dict[str, Any]:
        """Create task attachment by uploading a file."""
        return self.attachments.create_task_attachment(task_id, file_path, **params)

    # Authorization - Delegated to AuthAPI
    def get_access_token(self, client_id: str, client_secret: str, code: str) -> Dict[str, Any]:
        """Get OAuth access token."""
        return self.auth.get_access_token(client_id, client_secret, code)

    def get_authorized_user(self) -> Dict[str, Any]:
        """Get currently authenticated user info."""
        return self.auth.get_authorized_user()

    # Comments - Extended - Delegated to CommentsAPI
    def get_view_comments(self, view_id: str, **params) -> Dict[str, Any]:
        """Get chat comments for a view."""
        return self.comments.get_view_comments(view_id, **params)

    def create_view_comment(self, view_id: str, comment_text: str, notify_all: bool = False) -> Dict[str, Any]:
        """Create a chat comment on a view."""
        return self.comments.create_view_comment(view_id, comment_text, notify_all)

    def get_list_comments(self, list_id: str, **params) -> Dict[str, Any]:
        """Get comments for a list."""
        return self.comments.get_list_comments(list_id, **params)

    def create_list_comment(self, list_id: str, comment_text: str, notify_all: bool = False) -> Dict[str, Any]:
        """Create a comment on a list."""
        return self.comments.create_list_comment(list_id, comment_text, notify_all)

    def update_comment(self, comment_id: str, comment_text: str, **params) -> Dict[str, Any]:
        """Update a comment."""
        return self.comments.update_comment(comment_id, comment_text, **params)

    def delete_comment(self, comment_id: str) -> Dict[str, Any]:
        """Delete a comment."""
        return self.comments.delete_comment(comment_id)

    def get_threaded_comments(self, comment_id: str) -> Dict[str, Any]:
        """Get threaded/reply comments for a comment."""
        return self.comments.get_threaded_comments(comment_id)

    def create_threaded_comment(self, comment_id: str, comment_text: str, notify_all: bool = False) -> Dict[str, Any]:
        """Create a threaded reply to a comment."""
        return self.comments.create_threaded_comment(comment_id, comment_text, notify_all)

    # Custom Fields - Extended - Delegated to CustomFieldsAPI
    def get_folder_custom_fields(self, folder_id: str) -> Dict[str, Any]:
        """Get custom fields accessible from a folder."""
        return self.custom_fields.get_folder_custom_fields(folder_id)

    def get_space_custom_fields(self, space_id: str) -> Dict[str, Any]:
        """Get custom fields accessible from a space."""
        return self.custom_fields.get_space_custom_fields(space_id)

    def get_workspace_custom_fields(self, team_id: str) -> Dict[str, Any]:
        """Get all custom fields in a workspace."""
        return self.custom_fields.get_workspace_custom_fields(team_id)

    # Custom Task Types - Delegated to TemplatesAPI
    def get_custom_task_types(self, team_id: str) -> Dict[str, Any]:
        """Get custom task types for a workspace."""
        return self.templates.get_custom_task_types(team_id)

    # Time Tracking - Extended (Legacy) - Delegated to TimeTrackingLegacyAPI
    def get_task_time(self, task_id: str, **params) -> Dict[str, Any]:
        """Get tracked time for a task (legacy)."""
        return self.time_tracking_legacy.get_task_time(task_id, **params)

    def track_task_time(self, task_id: str, **time_data) -> Dict[str, Any]:
        """Track time on a task (legacy)."""
        return self.time_tracking_legacy.track_task_time(task_id, **time_data)

    def update_task_time_entry(self, task_id: str, interval_id: str, **updates) -> Dict[str, Any]:
        """Update a time entry (legacy)."""
        return self.time_tracking_legacy.update_task_time_entry(task_id, interval_id, **updates)

    def delete_task_time_entry(self, task_id: str, interval_id: str) -> Dict[str, Any]:
        """Delete a time entry (legacy)."""
        return self.time_tracking_legacy.delete_task_time_entry(task_id, interval_id)

    # User Groups - Delegated to GroupsAPI
    def create_user_group(self, team_id: str, name: str, member_ids: Optional[List[int]] = None) -> Dict[str, Any]:
        """Create a user group in a workspace."""
        return self.groups.create_user_group(team_id, name, member_ids)

    def update_user_group(self, group_id: str, **updates) -> Dict[str, Any]:
        """Update a user group."""
        return self.groups.update_user_group(group_id, **updates)

    def delete_user_group(self, group_id: str) -> Dict[str, Any]:
        """Delete a user group."""
        return self.groups.delete_user_group(group_id)

    def get_user_groups(self, **params) -> Dict[str, Any]:
        """Get user groups."""
        return self.groups.get_user_groups(**params)

    # Users - Delegated to UsersAPI
    def invite_user_to_workspace(self, team_id: str, email: str, **user_data) -> Dict[str, Any]:
        """Invite user to workspace."""
        return self.users.invite_user_to_workspace(team_id, email, **user_data)

    def get_user(self, team_id: str, user_id: str) -> Dict[str, Any]:
        """Get user information in a workspace."""
        return self.users.get_user(team_id, user_id)

    def edit_user_on_workspace(self, team_id: str, user_id: str, **updates) -> Dict[str, Any]:
        """Edit user on workspace."""
        return self.users.edit_user_on_workspace(team_id, user_id, **updates)

    def remove_user_from_workspace(self, team_id: str, user_id: str) -> Dict[str, Any]:
        """Remove user from workspace."""
        return self.users.remove_user_from_workspace(team_id, user_id)

    # Views - Delegated to ViewsAPI
    def get_workspace_views(self, team_id: str) -> Dict[str, Any]:
        """Get Everything level views for a workspace."""
        return self.views.get_workspace_views(team_id)

    def create_workspace_view(self, team_id: str, name: str, type: str, **view_data) -> Dict[str, Any]:
        """Create Everything level view for a workspace."""
        return self.views.create_workspace_view(team_id, name, type, **view_data)

    def get_space_views(self, space_id: str) -> Dict[str, Any]:
        """Get views for a space."""
        return self.views.get_space_views(space_id)

    def create_space_view(self, space_id: str, name: str, type: str, **view_data) -> Dict[str, Any]:
        """Create view for a space."""
        return self.views.create_space_view(space_id, name, type, **view_data)

    def get_folder_views(self, folder_id: str) -> Dict[str, Any]:
        """Get views for a folder."""
        return self.views.get_folder_views(folder_id)

    def create_folder_view(self, folder_id: str, name: str, type: str, **view_data) -> Dict[str, Any]:
        """Create view for a folder."""
        return self.views.create_folder_view(folder_id, name, type, **view_data)

    def get_list_views(self, list_id: str) -> Dict[str, Any]:
        """Get views for a list."""
        return self.views.get_list_views(list_id)

    def create_list_view(self, list_id: str, name: str, type: str, **view_data) -> Dict[str, Any]:
        """Create view for a list."""
        return self.views.create_list_view(list_id, name, type, **view_data)

    def get_view(self, view_id: str) -> Dict[str, Any]:
        """Get view by ID."""
        return self.views.get_view(view_id)

    def update_view(self, view_id: str, **updates) -> Dict[str, Any]:
        """Update a view."""
        return self.views.update_view(view_id, **updates)

    def delete_view(self, view_id: str) -> Dict[str, Any]:
        """Delete a view."""
        return self.views.delete_view(view_id)

    def get_view_tasks(self, view_id: str, **params) -> Dict[str, Any]:
        """Get tasks from a view."""
        return self.views.get_view_tasks(view_id, **params)

    # Webhooks - Delegated to WebhooksAPI
    def get_webhooks(self, team_id: str) -> Dict[str, Any]:
        """Get all webhooks for a workspace."""
        return self.webhooks.get_webhooks(team_id)

    def create_webhook(self, team_id: str, endpoint: str, events: List[str], **webhook_data) -> Dict[str, Any]:
        """Create a webhook."""
        return self.webhooks.create_webhook(team_id, endpoint, events, **webhook_data)

    def update_webhook(self, webhook_id: str, **updates) -> Dict[str, Any]:
        """Update a webhook."""
        return self.webhooks.update_webhook(webhook_id, **updates)

    def delete_webhook(self, webhook_id: str) -> Dict[str, Any]:
        """Delete a webhook."""
        return self.webhooks.delete_webhook(webhook_id)

    # Workspaces - Extended - Delegated to WorkspacesAPI
    def get_authorized_workspaces(self) -> Dict[str, Any]:
        """Get all authorized workspaces/teams for the current user."""
        return self.workspaces.get_authorized_workspaces()

    def get_workspace_seats(self, team_id: str) -> Dict[str, Any]:
        """Get workspace seat information."""
        return self.workspaces.get_workspace_seats(team_id)

    def get_workspace_plan(self, team_id: str) -> Dict[str, Any]:
        """Get workspace plan details."""
        return self.workspaces.get_workspace_plan(team_id)

    def get_shared_hierarchy(self, team_id: str) -> Dict[str, Any]:
        """Get shared hierarchy."""
        return self.workspaces.get_shared_hierarchy(team_id)

    # Roles - Delegated to RolesAPI
    def get_custom_roles(self, team_id: str) -> Dict[str, Any]:
        """Get custom roles for a workspace."""
        return self.roles.get_custom_roles(team_id)

    # Templates - Delegated to TemplatesAPI
    def get_task_templates(self, team_id: str) -> Dict[str, Any]:
        """Get task templates for a workspace."""
        return self.templates.get_task_templates(team_id)

    # Goals - Delegated to GoalsAPI
    def get_goals(self, team_id: str, **params) -> Dict[str, Any]:
        """Get goals for a workspace."""
        return self.goals.get_goals(team_id, **params)

    def create_goal(self, team_id: str, **goal_data) -> Dict[str, Any]:
        """Create a goal."""
        return self.goals.create_goal(team_id, **goal_data)

    def get_goal(self, goal_id: str) -> Dict[str, Any]:
        """Get a goal by ID."""
        return self.goals.get_goal(goal_id)

    def update_goal(self, goal_id: str, **updates) -> Dict[str, Any]:
        """Update a goal."""
        return self.goals.update_goal(goal_id, **updates)

    def delete_goal(self, goal_id: str) -> Dict[str, Any]:
        """Delete a goal."""
        return self.goals.delete_goal(goal_id)

    def create_key_result(self, goal_id: str, **key_result_data) -> Dict[str, Any]:
        """Create a key result for a goal."""
        return self.goals.create_key_result(goal_id, **key_result_data)

    def update_key_result(self, key_result_id: str, **updates) -> Dict[str, Any]:
        """Update a key result."""
        return self.goals.update_key_result(key_result_id, **updates)

    def delete_key_result(self, key_result_id: str) -> Dict[str, Any]:
        """Delete a key result."""
        return self.goals.delete_key_result(key_result_id)

    # Guests - Delegated to GuestsAPI
    def invite_guest_to_workspace(self, team_id: str, **guest_data) -> Dict[str, Any]:
        """Invite a guest to workspace."""
        return self.guests.invite_guest_to_workspace(team_id, **guest_data)

    def get_guest(self, team_id: str, guest_id: str) -> Dict[str, Any]:
        """Get a guest."""
        return self.guests.get_guest(team_id, guest_id)

    def update_guest(self, team_id: str, guest_id: str, **updates) -> Dict[str, Any]:
        """Edit a guest on workspace."""
        return self.guests.update_guest(team_id, guest_id, **updates)

    def remove_guest_from_workspace(self, team_id: str, guest_id: str) -> Dict[str, Any]:
        """Remove a guest from workspace."""
        return self.guests.remove_guest_from_workspace(team_id, guest_id)

    def add_guest_to_task(self, task_id: str, guest_id: str, **params) -> Dict[str, Any]:
        """Add a guest to a task."""
        return self.guests.add_guest_to_task(task_id, guest_id, **params)

    def remove_guest_from_task(self, task_id: str, guest_id: str, **params) -> Dict[str, Any]:
        """Remove a guest from a task."""
        return self.guests.remove_guest_from_task(task_id, guest_id, **params)

    def add_guest_to_list(self, list_id: str, guest_id: str) -> Dict[str, Any]:
        """Add a guest to a list."""
        return self.guests.add_guest_to_list(list_id, guest_id)

    def remove_guest_from_list(self, list_id: str, guest_id: str) -> Dict[str, Any]:
        """Remove a guest from a list."""
        return self.guests.remove_guest_from_list(list_id, guest_id)

    def add_guest_to_folder(self, folder_id: str, guest_id: str) -> Dict[str, Any]:
        """Add a guest to a folder."""
        return self.guests.add_guest_to_folder(folder_id, guest_id)

    def remove_guest_from_folder(self, folder_id: str, guest_id: str) -> Dict[str, Any]:
        """Remove a guest from a folder."""
        return self.guests.remove_guest_from_folder(folder_id, guest_id)

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
