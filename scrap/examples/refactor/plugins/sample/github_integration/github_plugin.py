"""
GitHub Integration Plugin

This plugin integrates the ClickUp JSON Manager with GitHub repositories
for issue tracking and synchronization.
"""

from typing import Any, Dict, List, Optional, Tuple

from ....common.exceptions import PluginError
from ...hooks.task_hooks import TaskHooks
from ...plugin_interface import IntegrationPlugin
from ...plugin_manager import Plugin


class GitHubIntegrationPlugin(IntegrationPlugin):
    """
    GitHub integration plugin for ClickUp JSON Manager.
    
    This plugin allows:
    - Synchronizing tasks with GitHub issues
    - Creating GitHub issues from tasks
    - Updating tasks from GitHub webhooks
    - Linking commits to tasks
    """
    
    def __init__(self, plugin_id: str, manager: 'PluginManager'):
        """Initialize the GitHub integration plugin."""
        super().__init__(plugin_id, manager)
        self.gh_client = None
    
    def initialize(self) -> bool:
        """
        Initialize the plugin.
        
        This registers hooks for task operations to sync with GitHub.
        
        Returns:
            bool: True if initialization was successful, False otherwise.
        """
        try:
            # Ensure we have the required configuration
            if not self._validate_required_config():
                logger.error("GitHub plugin initialization failed: missing required configuration")
                return False
            
            # Register hooks for task operations
            hook_registry = self.manager.get_service("hook_registry")
            if hook_registry:
                # Register for task status changes
                hook_registry.get_hook(TaskHooks.POST_STATUS_CHANGE).register(
                    self.plugin_id, 
                    self._on_task_status_change, 
                    plugin_id=self.plugin_id
                )
                
                # Register for task updates
                hook_registry.get_hook(TaskHooks.TASK_UPDATED).register(
                    self.plugin_id, 
                    self._on_task_updated,
                    plugin_id=self.plugin_id
                )
                
                # Register for task creation
                hook_registry.get_hook(TaskHooks.TASK_CREATED).register(
                    self.plugin_id, 
                    self._on_task_created,
                    plugin_id=self.plugin_id
                )
            
            # Initialize GitHub client (would use a real GitHub API library in production)
            self._init_github_client()
            
            return super().initialize()
        except Exception as e:
            logger.error(f"Error initializing GitHub plugin: {str(e)}")
            return False
    
    def cleanup(self) -> bool:
        """
        Clean up resources used by the plugin.
        
        Returns:
            bool: True if cleanup was successful, False otherwise.
        """
        try:
            # Unregister hooks
            hook_registry = self.manager.get_service("hook_registry")
            if hook_registry:
                hook_registry.unregister_hooks(self.plugin_id)
            
            # Clean up GitHub client
            self.gh_client = None
            
            return super().cleanup()
        except Exception as e:
            logger.error(f"Error cleaning up GitHub plugin: {str(e)}")
            return False
    
    def get_integration_name(self) -> str:
        """
        Get the name of the integration.
        
        Returns:
            str: Name of the integration
        """
        return "GitHub"
    
    def get_config_schema(self) -> Dict[str, Dict[str, Any]]:
        """
        Get the configuration schema for this plugin.
        
        Returns:
            Dict[str, Dict[str, Any]]: Configuration schema
        """
        return {
            "github_token": {
                "type": "string",
                "description": "GitHub API token with repo scope",
                "required": True
            },
            "repository": {
                "type": "string",
                "description": "GitHub repository in format owner/repo",
                "required": True
            },
            "sync_statuses": {
                "type": "boolean",
                "description": "Sync task statuses with GitHub issue state",
                "default": True
            },
            "sync_comments": {
                "type": "boolean",
                "description": "Sync task comments with GitHub issue comments",
                "default": True
            },
            "auto_create_issues": {
                "type": "boolean",
                "description": "Automatically create GitHub issues for new tasks",
                "default": False
            },
            "status_mapping": {
                "type": "object",
                "description": "Mapping of task statuses to GitHub issue states",
                "default": {
                    "to do": "open",
                    "in progress": "open",
                    "review": "open",
                    "complete": "closed"
                }
            }
        }
    
    def get_required_config(self) -> Dict[str, Dict[str, Any]]:
        """
        Get the configuration required for this integration.
        
        Returns:
            Dict[str, Dict[str, Any]]: Configuration schema
        """
        return self.get_config_schema()
    
    def validate_config(self, config: Dict[str, Any]) -> Tuple[bool, Optional[str]]:
        """
        Validate the configuration for this integration.
        
        Args:
            config: Configuration to validate
            
        Returns:
            Tuple[bool, Optional[str]]: (is_valid, error_message)
        """
        # Check required fields
        if "github_token" not in config:
            return False, "GitHub token is required"
        
        if "repository" not in config:
            return False, "GitHub repository is required"
        
        # Validate repository format
        repo = config.get("repository", "")
        if "/" not in repo or len(repo.split("/")) != 2:
            return False, "Repository must be in format owner/repo"
        
        # Validate status mapping if provided
        status_mapping = config.get("status_mapping", {})
        if status_mapping:
            if not isinstance(status_mapping, dict):
                return False, "Status mapping must be a dictionary"
            
            for status, gh_state in status_mapping.items():
                if gh_state not in ["open", "closed"]:
                    return False, f"Invalid GitHub state '{gh_state}' for status '{status}'"
        
        return True, None
    
    def _validate_required_config(self) -> bool:
        """
        Check if all required configuration is present.
        
        Returns:
            bool: True if all required configuration is present, False otherwise
        """
        config = self.get_config()
        
        # Check for required fields
        if not config.get("github_token"):
            logger.error("GitHub token is required in the configuration")
            return False
        
        if not config.get("repository"):
            logger.error("GitHub repository is required in the configuration")
            return False
        
        return True
    
    def _init_github_client(self):
        """Initialize the GitHub client with the plugin configuration."""
        # In a real implementation, this would initialize a GitHub API client
        # using a library like PyGithub
        config = self.get_config()
        
        self.gh_client = {
            "initialized": True,
            "token": config.get("github_token"),
            "repository": config.get("repository"),
            "sync_statuses": config.get("sync_statuses", True),
            "sync_comments": config.get("sync_comments", True),
            "auto_create_issues": config.get("auto_create_issues", False),
            "status_mapping": config.get("status_mapping", {})
        }
        
        logger.debug(f"Initialized GitHub client for repository: {config.get('repository')}")
    
    def _on_task_status_change(self, task: Dict[str, Any], old_status: str, new_status: str) -> None:
        """
        Handle task status changes to sync with GitHub issues.
        
        Args:
            task: The task that was updated
            old_status: The previous status
            new_status: The new status
        """
        logger.debug(f"GitHub: Task {task['id']} status changed from {old_status} to {new_status}")
        
        # Skip if status sync is disabled
        if not self.gh_client.get("sync_statuses", True):
            return
        
        # In a real implementation, this would update the GitHub issue state
        # based on the status mapping
        issue_url = task.get("metadata", {}).get("github_issue_url")
        if issue_url:
            status_mapping = self.gh_client.get("status_mapping", {})
            gh_state = status_mapping.get(new_status.lower(), "open")
            logger.info(f"GitHub: Would update issue {issue_url} to state {gh_state}")
    
    def _on_task_updated(self, task: Dict[str, Any], changed_fields: List[str]) -> None:
        """
        Handle task updates to sync with GitHub issues.
        
        Args:
            task: The task that was updated
            changed_fields: List of fields that were changed
        """
        logger.debug(f"GitHub: Task {task['id']} updated, fields: {changed_fields}")
        
        # In a real implementation, this would update the GitHub issue with the
        # changed fields (title, description, etc.)
        issue_url = task.get("metadata", {}).get("github_issue_url")
        if issue_url:
            logger.info(f"GitHub: Would update issue {issue_url} with changed fields")
    
    def _on_task_created(self, task: Dict[str, Any]) -> None:
        """
        Handle task creation to sync with GitHub issues.
        
        Args:
            task: The task that was created
        """
        logger.debug(f"GitHub: Task {task['id']} created")
        
        # Skip if auto-create is disabled
        if not self.gh_client.get("auto_create_issues", False):
            return
            
        # In a real implementation, this would create a GitHub issue for the task
        logger.info(f"GitHub: Would create issue for task {task['id']}")
        
        # Simulate creating an issue and storing the URL in task metadata
        issue_number = 123  # This would be the actual issue number from GitHub
        repo = self.gh_client.get("repository", "owner/repo")
        issue_url = f"https://github.com/{repo}/issues/{issue_number}"
        
        # In a real implementation, this would update the task's metadata
        logger.info(f"GitHub: Created issue {issue_url} for task {task['id']}")


# Import logger outside of class to avoid circular imports
import logging
logger = logging.getLogger(__name__) 