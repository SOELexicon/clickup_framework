"""
Centralized CLI Error Handler

Provides user-friendly error handling for the ClickUp Framework CLI.
Converts ClickUp exceptions into beautiful, actionable error messages.
"""

import sys
import re
from typing import Optional, Dict, Any
from clickup_framework.exceptions import (
    ClickUpAPIError,
    ClickUpAuthError,
    ClickUpRateLimitError,
    ClickUpNotFoundError,
    ClickUpValidationError,
    ClickUpTimeoutError,
)
from clickup_framework.utils.error_formatter import ErrorFormatter
from clickup_framework.context import get_context_manager


def handle_cli_error(error: Exception, context_info: Optional[Dict[str, Any]] = None) -> None:
    """
    Handle CLI errors with beautiful formatting and helpful suggestions.

    Args:
        error: The exception that was raised
        context_info: Optional additional context information

    This function formats the error and exits with status code 1.
    """
    # Get context manager for ANSI color settings
    context = get_context_manager()
    use_color = context.get_ansi_output()

    # Build context information
    error_context = {}
    if context_info:
        error_context.update(context_info)

    # Add current context if it's a context-related error
    try:
        current_workspace = context.get_current_workspace()
        current_list = context.get_current_list()
        if current_workspace or current_list:
            error_context.update({
                'current_workspace': current_workspace or 'Not set',
                'current_list': current_list or 'Not set',
            })
    except:
        pass  # Don't fail error handling due to context issues

    # Format the error based on type
    formatted_error = None

    if isinstance(error, ClickUpAuthError):
        formatted_error = _format_auth_error(error, error_context, use_color)
    elif isinstance(error, ClickUpNotFoundError):
        formatted_error = _format_not_found_error(error, error_context, use_color)
    elif isinstance(error, ClickUpRateLimitError):
        formatted_error = _format_rate_limit_error(error, error_context, use_color)
    elif isinstance(error, ClickUpValidationError):
        formatted_error = _format_validation_error(error, error_context, use_color)
    elif isinstance(error, ClickUpTimeoutError):
        formatted_error = _format_timeout_error(error, error_context, use_color)
    elif isinstance(error, ClickUpAPIError):
        formatted_error = _format_api_error(error, error_context, use_color)
    elif isinstance(error, ValueError):
        formatted_error = _format_value_error(error, error_context, use_color)
    else:
        # Generic error formatting
        formatted_error = ErrorFormatter.format_error(
            error_type="Error",
            message=str(error),
            context=error_context,
            suggestions=["Check your input and try again", "Use --help to see command usage"],
            no_color=not use_color,
        )

    # Print the formatted error to stderr
    print(formatted_error, file=sys.stderr)
    sys.exit(1)


def _format_auth_error(error: ClickUpAuthError, context: Dict, use_color: bool) -> str:
    """Format authentication errors."""
    error_msg = str(error)

    # Detect specific auth error types
    suggestions = []
    docs_link = "https://docs.clickup.com/en/articles/1367130-getting-started-with-the-clickup-api"

    if "not provided" in error_msg.lower():
        suggestions = [
            "Set your API token: export CLICKUP_API_TOKEN='your_token_here'",
            "Or store it in context: cum set token <your_token>",
            "Get your token from: https://app.clickup.com/settings/apps",
        ]
    elif "team not authorized" in error_msg.lower():
        suggestions = [
            "Verify the workspace/team ID is correct",
            "Check that your API token has access to this workspace",
            "Ensure you're using the correct workspace: cum set workspace <workspace_id>",
            "List available workspaces: cum hierarchy --all",
        ]
    elif "invalid" in error_msg.lower() or "expired" in error_msg.lower():
        suggestions = [
            "Check that your API token is correct and not expired",
            "Generate a new token at: https://app.clickup.com/settings/apps",
            "Update your token: export CLICKUP_API_TOKEN='new_token'",
        ]
    else:
        suggestions = [
            "Verify your CLICKUP_API_TOKEN environment variable is set correctly",
            "Check that your API token is valid and not expired",
            "Ensure your token has permissions for this workspace",
        ]

    return ErrorFormatter.format_error(
        error_type="Authentication Failed",
        message=error.message if hasattr(error, 'message') else str(error),
        context=context,
        suggestions=suggestions,
        docs_link=docs_link,
        no_color=not use_color,
    )


def _format_not_found_error(error: ClickUpNotFoundError, context: Dict, use_color: bool) -> str:
    """Format resource not found errors."""
    error_msg = str(error)

    # Extract resource type and ID if available
    resource_type = getattr(error, 'resource', 'Resource')
    resource_id = getattr(error, 'resource_id', None)

    suggestions = []

    if 'task' in resource_type.lower():
        suggestions = [
            "Verify the task ID is correct",
            "Check if the task was deleted or moved",
            "Search for the task: cum hierarchy <list_id>",
            "Use task URL to get ID: https://app.clickup.com/t/<task_id>",
        ]
    elif 'list' in resource_type.lower():
        suggestions = [
            "Verify the list ID is correct",
            "Check if the list was deleted or archived",
            "View all lists: cum hierarchy --all",
            "Set a valid list: cum set list <list_id>",
        ]
    elif 'workspace' in resource_type.lower() or 'team' in resource_type.lower():
        suggestions = [
            "Verify the workspace ID is correct",
            "List available workspaces: cum hierarchy --all",
            "Set correct workspace: cum set workspace <workspace_id>",
        ]
    else:
        suggestions = [
            f"Verify the {resource_type} ID is correct",
            "Check that the resource exists and you have access to it",
            "Ensure you're working in the correct workspace",
        ]

    context_with_id = context.copy()
    if resource_id:
        context_with_id['resource_id'] = resource_id
        context_with_id['resource_type'] = resource_type

    return ErrorFormatter.format_error(
        error_type=f"{resource_type} Not Found",
        message=error.message if hasattr(error, 'message') else str(error),
        context=context_with_id,
        suggestions=suggestions,
        no_color=not use_color,
    )


def _format_rate_limit_error(error: ClickUpRateLimitError, context: Dict, use_color: bool) -> str:
    """Format rate limit errors."""
    retry_after = getattr(error, 'retry_after', 60)

    suggestions = [
        f"Wait {retry_after} seconds before retrying",
        "Consider caching results to reduce API calls",
        "Implement exponential backoff in scripts",
        "Reduce the frequency of API requests",
    ]

    context_with_retry = context.copy()
    context_with_retry['retry_after'] = f"{retry_after}s"

    return ErrorFormatter.format_error(
        error_type="Rate Limit Exceeded",
        message="You've made too many API requests. Please wait before trying again.",
        context=context_with_retry,
        suggestions=suggestions,
        docs_link="https://docs.clickup.com/en/articles/rate-limiting",
        no_color=not use_color,
    )


def _format_validation_error(error: ClickUpValidationError, context: Dict, use_color: bool) -> str:
    """Format validation errors."""
    error_msg = str(error)

    suggestions = [
        "Check that all required fields are provided",
        "Verify field values match expected formats",
        "Review the command help: cum <command> --help",
    ]

    # Add specific suggestions based on error message
    if "status" in error_msg.lower():
        suggestions.insert(0, "Status names are case-sensitive - use exact status name")
        suggestions.insert(1, "View valid statuses: cum hierarchy <list_id>")
    elif "tag" in error_msg.lower():
        suggestions.insert(0, "Tags must already exist in the space before adding to tasks")
        suggestions.insert(1, "Create tags in the ClickUp UI first")
    elif "priority" in error_msg.lower():
        suggestions.insert(0, "Priority must be 1 (urgent), 2 (high), 3 (normal), or 4 (low)")

    return ErrorFormatter.format_error(
        error_type="Validation Error",
        message=error_msg,
        context=context,
        suggestions=suggestions,
        no_color=not use_color,
    )


def _format_timeout_error(error: ClickUpTimeoutError, context: Dict, use_color: bool) -> str:
    """Format timeout errors."""
    suggestions = [
        "Check your internet connection",
        "Try again - this might be a temporary issue",
        "Check ClickUp status: https://status.clickup.com/",
        "Increase timeout if dealing with large datasets",
    ]

    return ErrorFormatter.format_error(
        error_type="Request Timeout",
        message=str(error),
        context=context,
        suggestions=suggestions,
        no_color=not use_color,
    )


def _format_api_error(error: ClickUpAPIError, context: Dict, use_color: bool) -> str:
    """Format generic API errors."""
    error_msg = str(error)
    status_code = getattr(error, 'status_code', 0)

    suggestions = []

    # Parse specific error messages for better suggestions
    if "list id invalid" in error_msg.lower():
        suggestions = [
            "Verify the list ID format is correct (should be numeric)",
            "Get list ID from ClickUp URL: https://app.clickup.com/.../<list_id>/...",
            "List all available lists: cum hierarchy --all",
            "Set current list: cum set list <valid_list_id>",
        ]
    elif "task id invalid" in error_msg.lower():
        suggestions = [
            "Verify the task ID format is correct",
            "Get task ID from ClickUp URL or use cum hierarchy to find it",
            "Task IDs should be alphanumeric (e.g., '86c6ce9gg')",
        ]
    elif status_code == 400:
        suggestions = [
            "Check that all required parameters are provided",
            "Verify parameter formats are correct",
            "Review command usage: cum <command> --help",
        ]
    elif status_code == 403:
        suggestions = [
            "Verify you have permission to access this resource",
            "Check that you're working in the correct workspace",
            "Ensure your API token has the required permissions",
        ]
    elif status_code == 422:
        suggestions = [
            "Check that status names match exactly (case-sensitive)",
            "Verify that tags already exist in the space",
            "Review required fields for this operation",
        ]
    else:
        suggestions = [
            "Check your input parameters",
            "Verify IDs and values are correct",
            "Review the command help: cum <command> --help",
        ]

    # Extract just the API error message, not the full "ClickUp API Error 400: ..." string
    clean_message = error_msg
    if "ClickUp API Error" in error_msg:
        # Extract just the message part after the status code
        match = re.search(r'ClickUp API Error \d+: (.+)', error_msg)
        if match:
            clean_message = match.group(1)

    context_with_status = context.copy()
    if status_code:
        context_with_status['status_code'] = status_code

    return ErrorFormatter.format_error(
        error_type=f"API Error ({status_code})" if status_code else "API Error",
        message=clean_message,
        context=context_with_status,
        suggestions=suggestions,
        no_color=not use_color,
    )


def _format_value_error(error: ValueError, context: Dict, use_color: bool) -> str:
    """Format ValueError exceptions (often from context resolution)."""
    error_msg = str(error)

    suggestions = []

    # Context-related value errors
    if "no current" in error_msg.lower():
        if "workspace" in error_msg.lower():
            suggestions = [
                "Set current workspace: cum set workspace <workspace_id>",
                "List available workspaces: cum hierarchy --all",
                "Or specify workspace explicitly in the command",
            ]
        elif "list" in error_msg.lower():
            suggestions = [
                "Set current list: cum set list <list_id>",
                "View available lists: cum hierarchy --all",
                "Or specify list ID explicitly in the command",
            ]
        elif "task" in error_msg.lower():
            suggestions = [
                "Set current task: cum set task <task_id>",
                "Or specify task ID explicitly in the command",
            ]
        else:
            suggestions = [
                "Set required context: cum set <type> <id>",
                "View current context: cum show",
                "Or specify the ID explicitly in the command",
            ]
    else:
        # Generic value error
        suggestions = [
            "Check your input values",
            "Review command usage: cum <command> --help",
            "Verify all required arguments are provided",
        ]

    return ErrorFormatter.format_error(
        error_type="Invalid Input",
        message=error_msg,
        context=context,
        suggestions=suggestions,
        no_color=not use_color,
    )
