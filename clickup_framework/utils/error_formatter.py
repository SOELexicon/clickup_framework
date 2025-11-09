"""
Formatted Error Output Utilities

Provides beautiful, user-friendly error formatting for ClickUp API operations.
"""

from typing import Optional, Dict, Any, List
from datetime import datetime
import json


class ErrorFormatter:
    """Format errors with context and helpful suggestions."""

    # Color codes for terminal output
    COLORS = {
        'red': '\033[91m',
        'yellow': '\033[93m',
        'blue': '\033[94m',
        'green': '\033[92m',
        'cyan': '\033[96m',
        'white': '\033[97m',
        'reset': '\033[0m',
        'bold': '\033[1m',
        'dim': '\033[2m',
    }

    # Emoji/symbols
    SYMBOLS = {
        'error': '❌',
        'warning': '⚠️',
        'info': 'ℹ️',
        'tip': '💡',
        'docs': '📚',
        'link': '🔗',
        'check': '✓',
        'cross': '✗',
    }

    @classmethod
    def format_error(
        cls,
        error_type: str,
        message: str,
        context: Optional[Dict[str, Any]] = None,
        suggestions: Optional[List[str]] = None,
        docs_link: Optional[str] = None,
        technical_details: Optional[str] = None,
        no_color: bool = False,
    ) -> str:
        """
        Format an error message with context and suggestions.

        Args:
            error_type: Type of error (e.g., "Authentication Failed", "Rate Limited")
            message: Main error message
            context: Current context/state information
            suggestions: List of suggested fixes (1-3 items)
            docs_link: URL to relevant documentation
            technical_details: Optional technical error details
            no_color: Disable colored output

        Returns:
            Formatted error string
        """
        output = []

        # Helper functions
        def color(text: str, color_name: str) -> str:
            if no_color:
                return text
            return f"{cls.COLORS.get(color_name, '')}{text}{cls.COLORS['reset']}"

        def symbol(name: str) -> str:
            return cls.SYMBOLS.get(name, '')

        # Error header
        header_line = f"{symbol('error')} {color(error_type, 'red')}"
        output.append(header_line)
        output.append("═" * 80)
        output.append("")

        # Main message
        output.append(color(message, 'white'))
        output.append("")

        # Context section
        if context:
            output.append(f"{color('📋 Current Context:', 'cyan')}")
            for key, value in context.items():
                # Format the key nicely
                display_key = key.replace('_', ' ').title()
                if value is None:
                    value_str = color("None", 'dim')
                elif isinstance(value, bool):
                    value_str = color(str(value), 'green' if value else 'red')
                else:
                    value_str = str(value)
                output.append(f"   {display_key}: {value_str}")
            output.append("")

        # Suggestions section
        if suggestions:
            output.append(f"{symbol('tip')} {color('To fix this:', 'yellow')}")
            for i, suggestion in enumerate(suggestions, 1):
                output.append(f"   {i}. {suggestion}")
            output.append("")

        # Documentation link
        if docs_link:
            output.append(f"{symbol('docs')} {color('Documentation:', 'blue')}")
            output.append(f"   {docs_link}")
            output.append("")

        # Technical details (collapsible)
        if technical_details:
            output.append(f"{color('Technical Details:', 'dim')}")
            for line in technical_details.split('\n'):
                output.append(f"   {color(line, 'dim')}")
            output.append("")

        return '\n'.join(output)

    @classmethod
    def format_api_error(
        cls,
        status_code: int,
        error_response: Dict[str, Any],
        endpoint: str,
        context: Optional[Dict[str, Any]] = None,
        no_color: bool = False,
    ) -> str:
        """
        Format a ClickUp API error response.

        Args:
            status_code: HTTP status code
            error_response: API error response JSON
            endpoint: API endpoint that failed
            context: Additional context
            no_color: Disable colored output

        Returns:
            Formatted error string
        """
        # Determine error type and suggestions based on status code
        error_types = {
            400: ("Bad Request", [
                "Check that all required parameters are provided",
                "Verify parameter types and formats",
                "Review the API documentation for this endpoint"
            ]),
            401: ("Authentication Failed", [
                "Verify your CLICKUP_API_TOKEN environment variable is set",
                "Check that your API token is valid and not expired",
                "Ensure you're using the token directly (not 'Bearer TOKEN')"
            ], "https://docs.clickup.com/en/articles/1367130-getting-started-with-the-clickup-api"),
            403: ("Forbidden", [
                "Verify you have permission to access this resource",
                "Check that the workspace/task IDs are correct",
                "Ensure your API token has the required permissions"
            ]),
            404: ("Not Found", [
                "Verify the task/list/workspace ID is correct",
                "Check that the resource hasn't been deleted",
                "Ensure you have access to this workspace"
            ]),
            422: ("Validation Error", [
                "Check that status names match exactly (case-sensitive)",
                "Verify that tags already exist in the space",
                "Review required fields for this operation"
            ]),
            429: ("Rate Limited", [
                "Wait before retrying (check Retry-After header)",
                "Implement exponential backoff in your script",
                "Consider caching results to reduce API calls"
            ]),
            500: ("Server Error", [
                "This is a ClickUp server issue, not your fault",
                "Wait a few minutes and retry",
                "Check ClickUp status page: https://status.clickup.com/"
            ]),
        }

        error_type, suggestions, *docs = error_types.get(
            status_code,
            (f"HTTP {status_code}", ["Check the ClickUp API documentation"])
        )
        docs_link = docs[0] if docs else None

        # Extract error message from response
        error_msg = error_response.get('err',
                    error_response.get('error',
                    error_response.get('message', 'Unknown error')))

        # Build context
        error_context = {
            'endpoint': endpoint,
            'status_code': status_code,
            **(context or {})
        }

        # Technical details
        technical = json.dumps(error_response, indent=2)

        return cls.format_error(
            error_type=error_type,
            message=error_msg,
            context=error_context,
            suggestions=suggestions,
            docs_link=docs_link,
            technical_details=technical,
            no_color=no_color,
        )

    @classmethod
    def format_missing_context_error(
        cls,
        missing_field: str,
        current_context: Dict[str, Any],
        no_color: bool = False,
    ) -> str:
        """
        Format a missing context error.

        Args:
            missing_field: Name of the missing field
            current_context: Current context state
            no_color: Disable colored output

        Returns:
            Formatted error string
        """
        field_suggestions = {
            'task_id': [
                "Specify task ID: cu get-task 86c6d5j11",
                "Select from recent: cu context recent-tasks",
                "Search for task: cu search \"task name\""
            ],
            'workspace_id': [
                "Initialize context: cu init --workspace YOUR_WORKSPACE_ID",
                "List workspaces: cu list-workspaces",
                "Set workspace: cu context set-workspace WORKSPACE_ID"
            ],
            'list_id': [
                "Specify list: cu get-list LIST_ID",
                "Browse lists: cu list-lists --workspace WORKSPACE_ID",
                "Set current list: cu context set-list LIST_ID"
            ],
        }

        suggestions = field_suggestions.get(
            missing_field,
            [f"Provide {missing_field} as a command-line argument"]
        )

        return cls.format_error(
            error_type=f"Missing {missing_field.replace('_', ' ').title()}",
            message=f"No {missing_field} provided and no current {missing_field} in context",
            context=current_context,
            suggestions=suggestions,
            no_color=no_color,
        )

    @classmethod
    def format_known_limitation(
        cls,
        limitation_type: str,
        workarounds: List[str],
        docs_link: Optional[str] = None,
        no_color: bool = False,
    ) -> str:
        """
        Format a known API limitation error.

        Args:
            limitation_type: Type of limitation (e.g., "OAuth Required", "Tags Must Pre-exist")
            workarounds: List of workaround suggestions
            docs_link: Link to documentation
            no_color: Disable colored output

        Returns:
            Formatted error string
        """
        limitations = {
            'oauth_time_tracking': (
                "Time tracking operations require OAuth authentication which is not available through standard MCP authentication.",
                "https://docs.clickup.com/en/articles/time-tracking"
            ),
            'tag_pre_existence': (
                "Tags cannot be created via API - they must already exist in the space before you can add them to tasks.",
                "https://docs.clickup.com/en/articles/tags"
            ),
            'status_validation': (
                "Status names are case-sensitive and must exactly match the list's configured status names.",
                None
            ),
        }

        message, default_docs = limitations.get(
            limitation_type,
            (f"Known limitation: {limitation_type}", None)
        )

        return cls.format_error(
            error_type=f"⚠️  Known Limitation",
            message=message,
            context=None,
            suggestions=workarounds,
            docs_link=docs_link or default_docs,
            no_color=no_color,
        )


def format_error(*args, **kwargs) -> str:
    """Convenience function for ErrorFormatter.format_error()."""
    return ErrorFormatter.format_error(*args, **kwargs)


def format_api_error(*args, **kwargs) -> str:
    """Convenience function for ErrorFormatter.format_api_error()."""
    return ErrorFormatter.format_api_error(*args, **kwargs)


def format_missing_context_error(*args, **kwargs) -> str:
    """Convenience function for ErrorFormatter.format_missing_context_error()."""
    return ErrorFormatter.format_missing_context_error(*args, **kwargs)


def format_known_limitation(*args, **kwargs) -> str:
    """Convenience function for ErrorFormatter.format_known_limitation()."""
    return ErrorFormatter.format_known_limitation(*args, **kwargs)
