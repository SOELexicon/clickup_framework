"""Context management CLI commands."""

import sys
import os
from clickup_framework import get_context_manager
from clickup_framework.utils.colors import colorize, TextColor, TextStyle
from clickup_framework.utils.animations import ANSIAnimations


def set_current_command(args):
    """Set current resource context."""
    context = get_context_manager()

    resource_type = args.resource_type.lower()
    resource_id = args.resource_id

    # Map resource types to setter methods
    setters = {
        'task': context.set_current_task,
        'list': context.set_current_list,
        'space': context.set_current_space,
        'folder': context.set_current_folder,
        'workspace': context.set_current_workspace,
        'team': context.set_current_workspace,  # Alias
        'assignee': lambda aid: context.set_default_assignee(int(aid)),
        'token': context.set_api_token,
    }

    setter = setters.get(resource_type)
    if not setter:
        print(f"Error: Unknown resource type '{resource_type}'", file=sys.stderr)
        print(f"Valid types: {', '.join(setters.keys())}", file=sys.stderr)
        sys.exit(1)

    try:
        setter(resource_id)
        # Mask token in output for security
        if resource_type == 'token':
            masked_token = f"{resource_id[:15]}...{resource_id[-4:]}" if len(resource_id) > 20 else "********"
            print(f"✓ API token validated and saved successfully: {masked_token}")
        else:
            print(f"✓ Set current {resource_type} to: {resource_id}")
    except ValueError as e:
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)


def clear_current_command(args):
    """Clear current resource context."""
    context = get_context_manager()

    if args.resource_type:
        resource_type = args.resource_type.lower()

        # Map resource types to clear methods
        clearers = {
            'task': context.clear_current_task,
            'list': context.clear_current_list,
            'space': context.clear_current_space,
            'folder': context.clear_current_folder,
            'workspace': context.clear_current_workspace,
            'team': context.clear_current_workspace,  # Alias
            'token': context.clear_api_token,
        }

        clearer = clearers.get(resource_type)
        if not clearer:
            print(f"Error: Unknown resource type '{resource_type}'", file=sys.stderr)
            print(f"Valid types: {', '.join(clearers.keys())}", file=sys.stderr)
            sys.exit(1)

        clearer()
        print(f"✓ Cleared current {resource_type}")
    else:
        # Clear all context
        context.clear_all()
        print("✓ Cleared all context")


def show_current_command(args):
    """Show current resource context with animated display."""
    context = get_context_manager()
    all_context = context.get_all()

    if not all_context or all(v is None for v in [
        context.get_current_task(),
        context.get_current_list(),
        context.get_current_space(),
        context.get_current_folder(),
        context.get_current_workspace(),
        context.get_api_token(),
        context.get_default_assignee()
    ]):
        print(ANSIAnimations.warning_message("No context set"))
        return

    # Build content lines for the box
    content_lines = []

    # Show current values with highlighted IDs
    items = [
        ('Workspace', context.get_current_workspace(), TextColor.BRIGHT_MAGENTA),
        ('Space', context.get_current_space(), TextColor.BRIGHT_BLUE),
        ('Folder', context.get_current_folder(), TextColor.BRIGHT_CYAN),
        ('List', context.get_current_list(), TextColor.BRIGHT_YELLOW),
        ('Task', context.get_current_task(), TextColor.BRIGHT_GREEN),
    ]

    for label, value, color in items:
        if value:
            content_lines.append(ANSIAnimations.highlight_id(label, value, id_color=color))

    # Show API token status (without revealing the token)
    api_token = context.get_api_token()
    if api_token:
        # Mask token but show first 15 and last 4 chars for verification
        masked = f"{api_token[:15]}...{api_token[-4:]}" if len(api_token) > 20 else "********"
        content_lines.append(
            colorize("API Token: ", TextColor.BRIGHT_WHITE) +
            colorize(masked, TextColor.BRIGHT_GREEN) +
            colorize(" (set)", TextColor.BRIGHT_BLACK)
        )

        # Warn if environment variable might override
        env_token = os.environ.get('CLICKUP_API_TOKEN')
        if env_token and env_token != api_token:
            content_lines.append(
                colorize("⚠ Warning: CLICKUP_API_TOKEN env var is set and differs from stored token!",
                        TextColor.BRIGHT_RED, TextStyle.BOLD)
            )
            env_masked = f"{env_token[:15]}...{env_token[-4:]}" if len(env_token) > 20 else "********"
            content_lines.append(
                colorize(f"  Env token: {env_masked} (this will be used instead)",
                        TextColor.BRIGHT_YELLOW)
            )

    # Show default assignee
    default_assignee = context.get_default_assignee()
    if default_assignee:
        content_lines.append(ANSIAnimations.highlight_id("Default Assignee", str(default_assignee), id_color=TextColor.BRIGHT_CYAN))

    # Show last updated with gradient
    if 'last_updated' in all_context:
        last_updated = all_context['last_updated']
        content_lines.append("")  # Empty line for spacing
        content_lines.append(
            colorize("Last Updated: ", TextColor.BRIGHT_BLACK) +
            colorize(last_updated, TextColor.BRIGHT_WHITE)
        )

    # Create animated box
    box = ANSIAnimations.animated_box(
        ANSIAnimations.gradient_text("Current Context", ANSIAnimations.GRADIENT_RAINBOW),
        content_lines,
        color=TextColor.BRIGHT_CYAN
    )

    print("\n" + box + "\n")


def ansi_command(args):
    """Enable or disable ANSI color output."""
    context = get_context_manager()

    if args.action == 'enable':
        context.set_ansi_output(True)
        print("✓ ANSI color output enabled")
    elif args.action == 'disable':
        context.set_ansi_output(False)
        print("✓ ANSI color output disabled")
    elif args.action == 'status':
        enabled = context.get_ansi_output()
        status = "enabled" if enabled else "disabled"
        print(f"ANSI color output is currently: {status}")
