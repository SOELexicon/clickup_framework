"""Automation management commands for ClickUp Framework CLI."""

from clickup_framework.commands.base_command import BaseCommand
from clickup_framework.automation.config import (
    load_automation_config,
    save_automation_config,
    update_config_value
)
from clickup_framework.utils.colors import colorize, TextColor, TextStyle
from clickup_framework.utils.animations import ANSIAnimations


class ParentAutoUpdateStatusCommand(BaseCommand):
    """Display current automation configuration status."""

    def execute(self):
        """Execute the status command."""
        config = load_automation_config()

        self.print("\n" + colorize("Parent Task Auto-Update Configuration", TextColor.BRIGHT_CYAN, TextStyle.BOLD))
        self.print("=" * 50)
        self.print()

        # Status
        status_text = "✅ Enabled" if config.enabled else "❌ Disabled"
        self.print(f"Status: {status_text}")
        self.print(f"Post Comments: {'✅ Yes' if config.post_comment else '❌ No'}")
        self.print(f"Update Delay: {config.update_delay_seconds} seconds")
        self.print(f"Retry on Failure: {'✅ Yes' if config.retry_on_failure else '❌ No'} (max {config.max_retries} attempts)")
        self.print()

        # Trigger statuses
        self.print(colorize(f"Trigger Statuses ({len(config.trigger_statuses)}):", TextColor.BRIGHT_WHITE, TextStyle.BOLD))
        for status in config.trigger_statuses:
            self.print(f"  • {status}")
        self.print()

        # Parent inactive statuses
        self.print(colorize(f"Parent Inactive Statuses ({len(config.parent_inactive_statuses)}):", TextColor.BRIGHT_WHITE, TextStyle.BOLD))
        for status in config.parent_inactive_statuses:
            self.print(f"  • {status}")
        self.print()

        self.print(f"Target Status for Parent: \"{config.parent_target_status}\"")
        self.print()


class ParentAutoUpdateEnableCommand(BaseCommand):
    """Enable parent task auto-update automation."""

    def execute(self):
        """Execute the enable command."""
        update_config_value('enabled', True)

        success_msg = ANSIAnimations.success_message("Parent task auto-update enabled")
        self.print(success_msg)
        self.print("\nSubtasks set to 'in progress' will now automatically update parent tasks.")


class ParentAutoUpdateDisableCommand(BaseCommand):
    """Disable parent task auto-update automation."""

    def execute(self):
        """Execute the disable command."""
        update_config_value('enabled', False)

        self.print(ANSIAnimations.warning_message("Parent task auto-update disabled"))
        self.print("\nYou will need to manually update parent tasks when starting subtasks.")


class ParentAutoUpdateConfigCommand(BaseCommand):
    """Configure automation settings."""

    def execute(self):
        """Execute the config command."""
        key = self.args.key
        value = self.args.value

        # Type conversion for boolean and int values
        if value.lower() in ['true', 'false']:
            value = value.lower() == 'true'
        elif value.isdigit():
            value = int(value)

        try:
            update_config_value(key, value)

            success_msg = ANSIAnimations.success_message("Configuration updated")
            self.print(success_msg)
            self.print(f"\n{key} = {value}")

        except ValueError as e:
            self.error(str(e))


class ParentAutoUpdateAddTriggerCommand(BaseCommand):
    """Add a status to the trigger list."""

    def execute(self):
        """Execute the add-trigger command."""
        config = load_automation_config()

        if self.args.status not in config.trigger_statuses:
            config.trigger_statuses.append(self.args.status)
            save_automation_config(config)

            success_msg = ANSIAnimations.success_message("Added trigger status")
            self.print(success_msg)
            self.print(f"\nStatus '{self.args.status}' will now trigger parent updates.")
        else:
            self.print(f"Status '{self.args.status}' is already in the trigger list.")


class ParentAutoUpdateRemoveTriggerCommand(BaseCommand):
    """Remove a status from the trigger list."""

    def execute(self):
        """Execute the remove-trigger command."""
        config = load_automation_config()

        if self.args.status in config.trigger_statuses:
            config.trigger_statuses.remove(self.args.status)
            save_automation_config(config)

            success_msg = ANSIAnimations.success_message("Removed trigger status")
            self.print(success_msg)
            self.print(f"\nStatus '{self.args.status}' will no longer trigger parent updates.")
        else:
            self.print(f"Status '{self.args.status}' is not in the trigger list.")


class ParentAutoUpdateListTriggersCommand(BaseCommand):
    """List all trigger statuses."""

    def execute(self):
        """Execute the list-triggers command."""
        config = load_automation_config()

        self.print(colorize("Trigger Statuses:", TextColor.BRIGHT_CYAN, TextStyle.BOLD))
        self.print()
        for i, status in enumerate(config.trigger_statuses, 1):
            self.print(f"  {i}. {status}")
        self.print()


# Backward compatibility wrappers
def parent_auto_update_status_command(args):
    """Command wrapper for status."""
    command = ParentAutoUpdateStatusCommand(args, command_name='parent_auto_update')
    command.execute()


def parent_auto_update_enable_command(args):
    """Command wrapper for enable."""
    command = ParentAutoUpdateEnableCommand(args, command_name='parent_auto_update')
    command.execute()


def parent_auto_update_disable_command(args):
    """Command wrapper for disable."""
    command = ParentAutoUpdateDisableCommand(args, command_name='parent_auto_update')
    command.execute()


def parent_auto_update_config_command(args):
    """Command wrapper for config."""
    command = ParentAutoUpdateConfigCommand(args, command_name='parent_auto_update')
    command.execute()


def parent_auto_update_add_trigger_command(args):
    """Command wrapper for add-trigger."""
    command = ParentAutoUpdateAddTriggerCommand(args, command_name='parent_auto_update')
    command.execute()


def parent_auto_update_remove_trigger_command(args):
    """Command wrapper for remove-trigger."""
    command = ParentAutoUpdateRemoveTriggerCommand(args, command_name='parent_auto_update')
    command.execute()


def parent_auto_update_list_triggers_command(args):
    """Command wrapper for list-triggers."""
    command = ParentAutoUpdateListTriggersCommand(args, command_name='parent_auto_update')
    command.execute()


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
