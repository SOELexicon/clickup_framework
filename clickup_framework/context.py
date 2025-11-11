"""
Context Management for ClickUp Framework

Provides persistent context storage for remembering current task, list, space, etc.
This allows users to work with "current" items without repeatedly specifying IDs.

Example:
    # Set current task
    context = ContextManager()
    context.set_current_task("task_123")

    # Get current task
    task_id = context.get_current_task()

    # Use via CLI
    ./clickup set_current task task_123
    ./clickup detail current
"""

import json
import os
from typing import Dict, Any, Optional
from pathlib import Path
from datetime import datetime, timedelta


class ContextManager:
    """
    Manages persistent context for ClickUp operations.

    Stores current task, list, space, folder, and workspace IDs in a JSON file
    at ~/.clickup_context.json for easy access across CLI commands.

    Security:
    - Can optionally store API token for convenience
    - Stores resource IDs for convenience
    - File permissions are set to user-only (0600)
    """

    DEFAULT_CONTEXT_PATH = os.path.expanduser("~/.clickup_context.json")
    DEFAULT_CACHE_TTL = 3600  # 1 hour in seconds

    def __init__(self, context_path: Optional[str] = None, cache_ttl: int = DEFAULT_CACHE_TTL):
        """
        Initialize ContextManager.

        Args:
            context_path: Path to context file (defaults to ~/.clickup_context.json)
            cache_ttl: Cache time-to-live in seconds (default: 3600 = 1 hour)
        """
        self.context_path = context_path or self.DEFAULT_CONTEXT_PATH
        self.cache_ttl = cache_ttl
        self._context: Dict[str, Any] = {}
        self._load()

    def _load(self) -> None:
        """Load context from JSON file."""
        if os.path.exists(self.context_path):
            try:
                with open(self.context_path, 'r') as f:
                    self._context = json.load(f)
            except (json.JSONDecodeError, IOError) as e:
                # If file is corrupted, start fresh
                self._context = {}
                print(f"Warning: Could not load context file: {e}")
        else:
            self._context = {}

    def _save(self) -> None:
        """Save context to JSON file with secure permissions."""
        # Ensure parent directory exists
        parent_dir = Path(self.context_path).parent
        try:
            parent_dir.mkdir(parents=True, exist_ok=True)
        except FileExistsError:
            # Parent path exists but is a file, not a directory
            # This can happen if ~/.cum is a file instead of a directory
            raise RuntimeError(
                f"Cannot create config directory: {parent_dir} exists but is not a directory. "
                f"Please remove the file or choose a different config location."
            )
        except OSError as e:
            # Permission denied or other OS error
            raise RuntimeError(
                f"Cannot create config directory {parent_dir}: {e}"
            )

        # Write context file
        with open(self.context_path, 'w') as f:
            json.dump(self._context, f, indent=2)

        # Set file permissions to user-only (0600)
        try:
            os.chmod(self.context_path, 0o600)
        except OSError:
            # On Windows, chmod may not work as expected
            pass

    def set_current_task(self, task_id: str) -> None:
        """
        Set the current task ID.

        Args:
            task_id: Task ID to set as current
        """
        self._context['current_task'] = task_id
        self._context['last_updated'] = datetime.now().isoformat()
        self._save()

    def get_current_task(self) -> Optional[str]:
        """
        Get the current task ID.

        Returns:
            Current task ID or None if not set
        """
        return self._context.get('current_task')

    def set_current_list(self, list_id: str) -> None:
        """
        Set the current list ID.

        Args:
            list_id: List ID to set as current
        """
        self._context['current_list'] = list_id
        self._context['last_updated'] = datetime.now().isoformat()
        self._save()

    def get_current_list(self) -> Optional[str]:
        """
        Get the current list ID.

        Returns:
            Current list ID from context, or from CLICKUP_DEFAULT_LIST env var, or None if neither is set
        """
        # First try context, then environment variable
        list_id = self._context.get('current_list')
        if not list_id:
            list_id = os.environ.get('CLICKUP_DEFAULT_LIST')
        return list_id

    def set_current_space(self, space_id: str) -> None:
        """
        Set the current space ID.

        Args:
            space_id: Space ID to set as current
        """
        self._context['current_space'] = space_id
        self._context['last_updated'] = datetime.now().isoformat()
        self._save()

    def get_current_space(self) -> Optional[str]:
        """
        Get the current space ID.

        Returns:
            Current space ID or None if not set
        """
        return self._context.get('current_space')

    def set_current_folder(self, folder_id: str) -> None:
        """
        Set the current folder ID.

        Args:
            folder_id: Folder ID to set as current
        """
        self._context['current_folder'] = folder_id
        self._context['last_updated'] = datetime.now().isoformat()
        self._save()

    def get_current_folder(self) -> Optional[str]:
        """
        Get the current folder ID.

        Returns:
            Current folder ID or None if not set
        """
        return self._context.get('current_folder')

    def set_current_workspace(self, workspace_id: str) -> None:
        """
        Set the current workspace/team ID.

        Args:
            workspace_id: Workspace/team ID to set as current
        """
        self._context['current_workspace'] = workspace_id
        self._context['last_updated'] = datetime.now().isoformat()
        self._save()

    def get_current_workspace(self) -> Optional[str]:
        """
        Get the current workspace/team ID.

        Returns:
            Current workspace/team ID from context, or from CLICKUP_DEFAULT_WORKSPACE env var, or None if neither is set
        """
        # First try context, then environment variable
        workspace_id = self._context.get('current_workspace')
        if not workspace_id:
            workspace_id = os.environ.get('CLICKUP_DEFAULT_WORKSPACE')
        return workspace_id

    def clear_current_task(self) -> None:
        """Clear the current task ID."""
        if 'current_task' in self._context:
            del self._context['current_task']
            self._context['last_updated'] = datetime.now().isoformat()
            self._save()

    def clear_current_list(self) -> None:
        """Clear the current list ID."""
        if 'current_list' in self._context:
            del self._context['current_list']
            self._context['last_updated'] = datetime.now().isoformat()
            self._save()

    def clear_current_space(self) -> None:
        """Clear the current space ID."""
        if 'current_space' in self._context:
            del self._context['current_space']
            self._context['last_updated'] = datetime.now().isoformat()
            self._save()

    def clear_current_folder(self) -> None:
        """Clear the current folder ID."""
        if 'current_folder' in self._context:
            del self._context['current_folder']
            self._context['last_updated'] = datetime.now().isoformat()
            self._save()

    def clear_current_workspace(self) -> None:
        """Clear the current workspace ID."""
        if 'current_workspace' in self._context:
            del self._context['current_workspace']
            self._context['last_updated'] = datetime.now().isoformat()
            self._save()

    def set_api_token(self, token: str, validate: bool = True) -> None:
        """
        Set the ClickUp API token.

        Args:
            token: ClickUp API token to store
            validate: Whether to validate the token by making a test API call (default: True)

        Raises:
            ValueError: If validation is enabled and the token is invalid
        """
        # Validate token format
        if not token or not isinstance(token, str):
            raise ValueError("API token must be a non-empty string")

        # Strip any whitespace
        token = token.strip()

        # Validate token by making a test API call if requested
        if validate:
            import requests
            try:
                response = requests.get(
                    "https://api.clickup.com/api/v2/user",
                    headers={"Authorization": token},
                    timeout=10
                )
                if response.status_code == 401:
                    raise ValueError(
                        "Invalid or expired API token. Please check your token and try again.\n"
                        "You can generate a new token at: https://app.clickup.com/settings/apps"
                    )
                elif response.status_code != 200:
                    raise ValueError(
                        f"Token validation failed with status {response.status_code}. "
                        "Please check your token and try again."
                    )
                # Token is valid, continue
            except requests.exceptions.RequestException as e:
                raise ValueError(f"Failed to validate token: {str(e)}")

        self._context['api_token'] = token
        self._context['last_updated'] = datetime.now().isoformat()
        self._save()

    def get_api_token(self) -> Optional[str]:
        """
        Get the stored ClickUp API token.

        Returns:
            Stored API token or None if not set
        """
        return self._context.get('api_token')

    def clear_api_token(self) -> None:
        """Clear the stored API token."""
        if 'api_token' in self._context:
            del self._context['api_token']
            self._context['last_updated'] = datetime.now().isoformat()
            self._save()

    def set_default_assignee(self, user_id: int) -> None:
        """
        Set the default assignee user ID for task creation.

        Args:
            user_id: User ID to set as default assignee
        """
        self._context['default_assignee'] = user_id
        self._context['last_updated'] = datetime.now().isoformat()
        self._save()

    def get_default_assignee(self) -> Optional[int]:
        """
        Get the default assignee user ID.

        Returns:
            Default assignee user ID from context, or from CLICKUP_DEFAULT_ASSIGNEE env var, or None if neither is set
        """
        # First try context, then environment variable
        assignee_id = self._context.get('default_assignee')
        if not assignee_id:
            env_assignee = os.environ.get('CLICKUP_DEFAULT_ASSIGNEE')
            if env_assignee:
                try:
                    assignee_id = int(env_assignee)
                except ValueError:
                    # If env var is not a valid integer, ignore it
                    pass
        return assignee_id

    def clear_default_assignee(self) -> None:
        """Clear the default assignee."""
        if 'default_assignee' in self._context:
            del self._context['default_assignee']
            self._context['last_updated'] = datetime.now().isoformat()
            self._save()

    def set_ansi_output(self, enabled: bool) -> None:
        """
        Set whether ANSI color output is enabled.

        Args:
            enabled: True to enable ANSI colors, False to disable
        """
        self._context['ansi_output'] = enabled
        self._context['last_updated'] = datetime.now().isoformat()
        self._save()

    def get_ansi_output(self) -> bool:
        """
        Get whether ANSI color output is enabled.

        Checks in order:
        1. Environment variable HIDE_ANSI (if set to '1', disables ANSI)
        2. Context setting 'ansi_output'
        3. Default: False

        Returns:
            True if ANSI output is enabled, False otherwise (default: False)
        """
        # Check environment variable first - if HIDE_ANSI=1, disable ANSI
        hide_ansi = os.environ.get('HIDE_ANSI', '').strip()
        if hide_ansi == '1':
            return False

        # Otherwise use context setting
        return self._context.get('ansi_output', False)

    def clear_all(self) -> None:
        """Clear all context."""
        self._context = {}
        self._save()

    def get_all(self) -> Dict[str, Any]:
        """
        Get all context data.

        Returns:
            Dictionary of all context data
        """
        return self._context.copy()

    def resolve_id(self, resource_type: str, id_or_current: str) -> str:
        """
        Resolve an ID or "current" keyword to an actual ID.

        Args:
            resource_type: Type of resource (task, list, space, folder, workspace)
            id_or_current: Either an ID or the keyword "current"

        Returns:
            Resolved ID

        Raises:
            ValueError: If "current" is used but no current ID is set
        """
        if id_or_current.lower() != "current":
            return id_or_current

        # Map resource types to getter methods
        getters = {
            'task': self.get_current_task,
            'list': self.get_current_list,
            'space': self.get_current_space,
            'folder': self.get_current_folder,
            'workspace': self.get_current_workspace,
            'team': self.get_current_workspace,  # Alias for workspace
        }

        getter = getters.get(resource_type.lower())
        if not getter:
            raise ValueError(f"Unknown resource type: {resource_type}")

        current_id = getter()
        if not current_id:
            raise ValueError(
                f"No current {resource_type} set. "
                f"Use 'set_current {resource_type} <id>' first."
            )

        return current_id

    def cache_list_metadata(self, list_id: str, metadata: Dict[str, Any]) -> None:
        """
        Cache list metadata including statuses.

        Args:
            list_id: List ID
            metadata: List metadata from API (should include 'statuses' field)
        """
        if 'list_cache' not in self._context:
            self._context['list_cache'] = {}

        self._context['list_cache'][list_id] = {
            'metadata': metadata,
            'cached_at': datetime.now().isoformat()
        }
        self._save()

    def get_cached_list_metadata(self, list_id: str) -> Optional[Dict[str, Any]]:
        """
        Get cached list metadata if still valid.

        Args:
            list_id: List ID

        Returns:
            Cached metadata dict or None if not cached or expired
        """
        if 'list_cache' not in self._context:
            return None

        cached_data = self._context['list_cache'].get(list_id)
        if not cached_data:
            return None

        # Check if cache is still valid
        cached_at = datetime.fromisoformat(cached_data['cached_at'])
        age = datetime.now() - cached_at

        if age.total_seconds() > self.cache_ttl:
            # Cache expired, remove it
            del self._context['list_cache'][list_id]
            self._save()
            return None

        return cached_data['metadata']

    def clear_list_cache(self, list_id: Optional[str] = None) -> None:
        """
        Clear cached list metadata.

        Args:
            list_id: Specific list ID to clear, or None to clear all
        """
        if 'list_cache' not in self._context:
            return

        if list_id:
            if list_id in self._context['list_cache']:
                del self._context['list_cache'][list_id]
        else:
            self._context['list_cache'] = {}

        self._save()


def get_context_manager() -> ContextManager:
    """
    Get a ContextManager instance (singleton pattern).

    Returns:
        ContextManager instance
    """
    if not hasattr(get_context_manager, '_instance'):
        get_context_manager._instance = ContextManager()
    return get_context_manager._instance
