"""Show current context command."""

import os
from clickup_framework import get_context_manager
from clickup_framework.utils.colors import colorize, TextColor, TextStyle
from clickup_framework.utils.animations import ANSIAnimations


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


def register_command(subparsers, add_common_args=None):
    """Register the show_current command with argparse."""
    parser = subparsers.add_parser(
        'show_current',
        aliases=['show'],
        help='Show current resource context',
        description='Display the current context configuration with all set resources'
    )
    parser.set_defaults(func=show_current_command)
