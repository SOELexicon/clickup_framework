"""Automation management commands for ClickUp Framework CLI."""

import sys
from clickup_framework.automation.config import (
    load_automation_config,
    save_automation_config,
    update_config_value
)
from clickup_framework.utils.colors import colorize, TextColor, TextStyle
from clickup_framework.utils.animations import ANSIAnimations


def parent_auto_update_status_command(args):
    """Display current automation configuration status."""
    config = load_automation_config()

    print("\n" + colorize("Parent Task Auto-Update Configuration", TextColor.BRIGHT_CYAN, TextStyle.BOLD))
    print("=" * 50)
    print()

    # Status
    status_text = "✅ Enabled" if config.enabled else "❌ Disabled"
    print(f"Status: {status_text}")
    print(f"Post Comments: {'✅ Yes' if config.post_comment else '❌ No'}")
    print(f"Update Delay: {config.update_delay_seconds} seconds")
    print(f"Retry on Failure: {'✅ Yes' if config.retry_on_failure else '❌ No'} (max {config.max_retries} attempts)")
    print()

    # Trigger statuses
    print(colorize(f"Trigger Statuses ({len(config.trigger_statuses)}):", TextColor.BRIGHT_WHITE, TextStyle.BOLD))
    for status in config.trigger_statuses:
        print(f"  • {status}")
    print()

    # Parent inactive statuses
    print(colorize(f"Parent Inactive Statuses ({len(config.parent_inactive_statuses)}):", TextColor.BRIGHT_WHITE, TextStyle.BOLD))
    for status in config.parent_inactive_statuses:
        print(f"  • {status}")
    print()

    print(f"Target Status for Parent: \"{config.parent_target_status}\"")
    print()


def parent_auto_update_enable_command(args):
    """Enable parent task auto-update automation."""
    update_config_value('enabled', True)

    success_msg = ANSIAnimations.success_message("Parent task auto-update enabled")
    print(success_msg)
    print("\nSubtasks set to 'in progress' will now automatically update parent tasks.")


def parent_auto_update_disable_command(args):
    """Disable parent task auto-update automation."""
    update_config_value('enabled', False)

    print(ANSIAnimations.warning_message("Parent task auto-update disabled"))
    print("\nYou will need to manually update parent tasks when starting subtasks.")


def parent_auto_update_config_command(args):
    """Configure automation settings."""
    key = args.key
    value = args.value

    # Type conversion for boolean and int values
    if value.lower() in ['true', 'false']:
        value = value.lower() == 'true'
    elif value.isdigit():
        value = int(value)

    try:
        update_config_value(key, value)

        success_msg = ANSIAnimations.success_message(f"Configuration updated")
        print(success_msg)
        print(f"\n{key} = {value}")

    except ValueError as e:
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)


def parent_auto_update_add_trigger_command(args):
    """Add a status to the trigger list."""
    config = load_automation_config()

    if args.status not in config.trigger_statuses:
        config.trigger_statuses.append(args.status)
        save_automation_config(config)

        success_msg = ANSIAnimations.success_message(f"Added trigger status")
        print(success_msg)
        print(f"\nStatus '{args.status}' will now trigger parent updates.")
    else:
        print(f"Status '{args.status}' is already in the trigger list.")


def parent_auto_update_remove_trigger_command(args):
    """Remove a status from the trigger list."""
    config = load_automation_config()

    if args.status in config.trigger_statuses:
        config.trigger_statuses.remove(args.status)
        save_automation_config(config)

        success_msg = ANSIAnimations.success_message(f"Removed trigger status")
        print(success_msg)
        print(f"\nStatus '{args.status}' will no longer trigger parent updates.")
    else:
        print(f"Status '{args.status}' is not in the trigger list.")


def parent_auto_update_list_triggers_command(args):
    """List all trigger statuses."""
    config = load_automation_config()

    print(colorize("Trigger Statuses:", TextColor.BRIGHT_CYAN, TextStyle.BOLD))
    print()
    for i, status in enumerate(config.trigger_statuses, 1):
        print(f"  {i}. {status}")
    print()


def register_command(subparsers):
    """Register automation management commands."""

    # Parent auto-update command with subcommands
    parent_auto_update_parser = subparsers.add_parser(
        'parent_auto_update',
        aliases=['pau'],
        help='Manage parent task auto-update automation'
    )

    parent_auto_update_subparsers = parent_auto_update_parser.add_subparsers(
        dest='subcommand',
        help='Automation management subcommands'
    )

    # Status subcommand
    status_parser = parent_auto_update_subparsers.add_parser(
        'status',
        help='Show current automation configuration'
    )
    status_parser.set_defaults(func=parent_auto_update_status_command)

    # Enable subcommand
    enable_parser = parent_auto_update_subparsers.add_parser(
        'enable',
        help='Enable parent task auto-update'
    )
    enable_parser.set_defaults(func=parent_auto_update_enable_command)

    # Disable subcommand
    disable_parser = parent_auto_update_subparsers.add_parser(
        'disable',
        help='Disable parent task auto-update'
    )
    disable_parser.set_defaults(func=parent_auto_update_disable_command)

    # Config subcommand
    config_parser = parent_auto_update_subparsers.add_parser(
        'config',
        help='Update a configuration value'
    )
    config_parser.add_argument('key', help='Configuration key to update')
    config_parser.add_argument('value', help='New value')
    config_parser.set_defaults(func=parent_auto_update_config_command)

    # Add trigger subcommand
    add_trigger_parser = parent_auto_update_subparsers.add_parser(
        'add-trigger',
        help='Add a status to the trigger list'
    )
    add_trigger_parser.add_argument('status', help='Status to add')
    add_trigger_parser.set_defaults(func=parent_auto_update_add_trigger_command)

    # Remove trigger subcommand
    remove_trigger_parser = parent_auto_update_subparsers.add_parser(
        'remove-trigger',
        help='Remove a status from the trigger list'
    )
    remove_trigger_parser.add_argument('status', help='Status to remove')
    remove_trigger_parser.set_defaults(func=parent_auto_update_remove_trigger_command)

    # List triggers subcommand
    list_triggers_parser = parent_auto_update_subparsers.add_parser(
        'list-triggers',
        help='List all trigger statuses'
    )
    list_triggers_parser.set_defaults(func=parent_auto_update_list_triggers_command)

    # If no subcommand provided, default to status
    parent_auto_update_parser.set_defaults(func=parent_auto_update_status_command)
