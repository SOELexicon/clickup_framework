"""Custom field management commands for ClickUp Framework CLI."""

import sys
from typing import Dict, Any, Optional, List, Tuple
from clickup_framework import ClickUpClient, get_context_manager
from clickup_framework.resources.custom_fields import CustomFieldsAPI
from clickup_framework.utils.colors import colorize, TextColor, TextStyle
from clickup_framework.utils.animations import ANSIAnimations
from clickup_framework.exceptions import ClickUpAPIError


# Field type color mapping
FIELD_TYPE_COLORS = {
    'short_text': TextColor.BRIGHT_BLUE,
    'text': TextColor.BRIGHT_BLUE,
    'number': TextColor.BRIGHT_GREEN,
    'drop_down': TextColor.BRIGHT_YELLOW,
    'labels': TextColor.BRIGHT_YELLOW,
    'date': TextColor.BRIGHT_MAGENTA,
    'checkbox': TextColor.BRIGHT_CYAN,
    'email': TextColor.BRIGHT_BLUE,
    'url': TextColor.BRIGHT_BLUE,
    'phone': TextColor.BRIGHT_BLUE,
    'currency': TextColor.BRIGHT_GREEN,
    'rating': TextColor.BRIGHT_YELLOW,
    'location': TextColor.BRIGHT_CYAN,
}


def resolve_field_name_to_id(
    client: ClickUpClient,
    task_id: str,
    field_name_or_id: str
) -> Tuple[str, Dict[str, Any]]:
    """
    Resolve a field name or ID to a field ID and field definition.

    Args:
        client: ClickUpClient instance
        task_id: Task ID to get list context from
        field_name_or_id: Field name (case-insensitive) or field ID

    Returns:
        Tuple of (field_id, field_definition)

    Raises:
        ValueError: If field not found or multiple matches
    """
    # Get task to find its list
    try:
        task = client.get_task(task_id)
        list_id = task['list']['id']
    except Exception as e:
        raise ValueError(f"Could not get task: {e}")

    # Get custom fields for the list
    try:
        fields_response = client.get_accessible_custom_fields(list_id)
        fields = fields_response.get('fields', [])
    except Exception as e:
        raise ValueError(f"Could not get custom fields: {e}")

    if not fields:
        raise ValueError(f"No custom fields found for list {list_id}")

    # Try to match by ID first (exact match)
    for field in fields:
        if field['id'] == field_name_or_id:
            return (field['id'], field)

    # Try to match by name (case-insensitive)
    matches = []
    for field in fields:
        if field['name'].lower() == field_name_or_id.lower():
            matches.append(field)

    if len(matches) == 1:
        return (matches[0]['id'], matches[0])
    elif len(matches) > 1:
        field_names = [f"'{f['name']}' ({f['id']})" for f in matches]
        raise ValueError(
            f"Multiple fields match '{field_name_or_id}': {', '.join(field_names)}. "
            "Please use field ID instead."
        )

    # No match found - provide helpful suggestions
    available_fields = [f"{f['name']} ({f['type']})" for f in fields]
    raise ValueError(
        f"Field '{field_name_or_id}' not found. Available fields:\n  " +
        "\n  ".join(available_fields)
    )


def format_field_value(field: Dict[str, Any], value: Any) -> str:
    """
    Format a field value for display based on field type.

    Args:
        field: Field definition dict
        value: Raw field value

    Returns:
        Formatted string
    """
    if value is None or value == "":
        return colorize("(not set)", TextColor.BRIGHT_BLACK)

    field_type = field['type']

    # Checkbox
    if field_type == 'checkbox':
        return "✓" if value else "✗"

    # Date
    elif field_type == 'date':
        # Value is timestamp in milliseconds
        from datetime import datetime
        try:
            dt = datetime.fromtimestamp(int(value) / 1000)
            return dt.strftime('%Y-%m-%d %H:%M')
        except (ValueError, TypeError, OSError) as e:
            return str(value)

    # Dropdown/Labels - value is option ID, need to look up name
    elif field_type in ('drop_down', 'labels'):
        if isinstance(value, dict):
            # Sometimes the API returns the option object
            return value.get('name', str(value))
        else:
            # Look up option name from field type_config
            options = field.get('type_config', {}).get('options', [])
            for option in options:
                if option['id'] == value or option.get('orderindex') == value:
                    return option['name']
            return str(value)

    # Currency
    elif field_type == 'currency':
        return f"${value:,.2f}" if isinstance(value, (int, float)) else str(value)

    # Rating
    elif field_type == 'rating':
        max_rating = field.get('type_config', {}).get('count', 5)
        return f"{'★' * int(value)}{'☆' * (max_rating - int(value))}"

    # Default - just return as string
    return str(value)


def parse_field_value(field: Dict[str, Any], value_str: str) -> Any:
    """
    Parse a string value according to field type.

    Args:
        field: Field definition dict
        value_str: String value from command line

    Returns:
        Parsed value appropriate for field type

    Raises:
        ValueError: If value cannot be parsed for field type
    """
    field_type = field['type']

    # Checkbox - accept various boolean representations
    if field_type == 'checkbox':
        lower_val = value_str.lower()
        if lower_val in ('true', 'yes', '1', 'on', 'checked'):
            return True
        elif lower_val in ('false', 'no', '0', 'off', 'unchecked'):
            return False
        else:
            raise ValueError(
                f"Invalid checkbox value '{value_str}'. "
                "Use: true/false, yes/no, 1/0, on/off, checked/unchecked"
            )

    # Number - parse as int or float
    elif field_type in ('number', 'currency', 'rating'):
        try:
            # Try int first
            if '.' not in value_str:
                return int(value_str)
            else:
                return float(value_str)
        except ValueError:
            raise ValueError(f"Invalid number value '{value_str}'")

    # Date - accept various formats
    elif field_type == 'date':
        from datetime import datetime
        # Try common date formats
        for fmt in ('%Y-%m-%d', '%Y/%m/%d', '%m/%d/%Y', '%d/%m/%Y', '%Y-%m-%d %H:%M:%S'):
            try:
                dt = datetime.strptime(value_str, fmt)
                # Return timestamp in milliseconds
                return int(dt.timestamp() * 1000)
            except ValueError:
                continue
        raise ValueError(
            f"Invalid date format '{value_str}'. "
            "Supported formats: YYYY-MM-DD, YYYY/MM/DD, MM/DD/YYYY"
        )

    # Dropdown - match option by name
    elif field_type == 'drop_down':
        options = field.get('type_config', {}).get('options', [])
        for option in options:
            if option['name'].lower() == value_str.lower():
                return option['orderindex']  # ClickUp expects orderindex for dropdowns

        # No match - show available options
        option_names = [opt['name'] for opt in options]
        raise ValueError(
            f"Invalid option '{value_str}'. Available options: {', '.join(option_names)}"
        )

    # Labels - can be multiple, comma-separated
    elif field_type == 'labels':
        options = field.get('type_config', {}).get('options', [])
        values = [v.strip() for v in value_str.split(',')]
        result = []

        for val in values:
            matched = False
            for option in options:
                if option['label'].lower() == val.lower():
                    result.append(option['id'])
                    matched = True
                    break
            if not matched:
                option_names = [opt['label'] for opt in options]
                raise ValueError(
                    f"Invalid label '{val}'. Available labels: {', '.join(option_names)}"
                )

        return result

    # Text fields - return as-is
    return value_str


def custom_field_set_command(args):
    """Set a custom field value on a task."""
    context = get_context_manager()
    client = ClickUpClient()

    # Resolve task ID
    try:
        task_id = context.resolve_id('task', args.task_id)
    except ValueError as e:
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)

    # Resolve field name to ID
    try:
        field_id, field = resolve_field_name_to_id(client, task_id, args.field_name_or_id)
    except ValueError as e:
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)

    # Parse value according to field type
    try:
        parsed_value = parse_field_value(field, args.value)
    except ValueError as e:
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)

    # Show field info and current value
    field_color = FIELD_TYPE_COLORS.get(field['type'], TextColor.WHITE)
    print(f"\nField: {colorize(field['name'], TextStyle.BOLD)} ({colorize(field['type'], field_color)})")
    print(f"New value: {format_field_value(field, parsed_value)}")

    # Set the field value
    try:
        client.set_custom_field_value(task_id, field_id, parsed_value)
        success_msg = ANSIAnimations.success_message(
            f"Custom field '{field['name']}' updated successfully"
        )
        print(f"\n{success_msg}")
    except ClickUpAPIError as e:
        print(f"Error setting custom field: {e}", file=sys.stderr)
        sys.exit(1)


def custom_field_get_command(args):
    """Get a custom field value from a task."""
    context = get_context_manager()
    client = ClickUpClient()

    # Resolve task ID
    try:
        task_id = context.resolve_id('task', args.task_id)
    except ValueError as e:
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)

    # Resolve field name to ID
    try:
        field_id, field = resolve_field_name_to_id(client, task_id, args.field_name_or_id)
    except ValueError as e:
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)

    # Get task to retrieve field value
    try:
        task = client.get_task(task_id)
        custom_fields = task.get('custom_fields', [])

        # Find the field value
        field_value = None
        for cf in custom_fields:
            if cf['id'] == field_id:
                field_value = cf.get('value')
                break

        # Display field info
        field_color = FIELD_TYPE_COLORS.get(field['type'], TextColor.WHITE)
        print(f"\n{colorize(field['name'], TextStyle.BOLD)} ({colorize(field['type'], field_color)})")
        print(f"Value: {format_field_value(field, field_value)}")

    except ClickUpAPIError as e:
        print(f"Error getting custom field: {e}", file=sys.stderr)
        sys.exit(1)


def custom_field_list_command(args):
    """List custom fields."""
    context = get_context_manager()
    client = ClickUpClient()
    fields_api = CustomFieldsAPI(client)

    # Determine context and get fields
    try:
        if args.task:
            # List fields on a specific task with values
            task_id = context.resolve_id('task', args.task)
            task = client.get_task(task_id)
            list_id = task['list']['id']

            # Get field definitions
            fields_response = client.get_accessible_custom_fields(list_id)
            field_defs = {f['id']: f for f in fields_response.get('fields', [])}

            # Get task custom field values
            task_fields = task.get('custom_fields', [])

            print(f"\n{colorize('Custom Fields for Task', TextStyle.BOLD)} {task['id']}")
            print(f"Task: {task['name']}\n")

            if not task_fields:
                print("No custom fields set on this task.")
                return

            for cf in task_fields:
                field_def = field_defs.get(cf['id'], {})
                field_type = field_def.get('type', 'unknown')
                field_name = field_def.get('name', cf.get('name', 'Unknown'))
                field_value = cf.get('value')

                field_color = FIELD_TYPE_COLORS.get(field_type, TextColor.WHITE)
                print(f"  {colorize(field_name, TextStyle.BOLD)} ({colorize(field_type, field_color)})")
                print(f"    Value: {format_field_value(field_def, field_value)}")
                print()

        elif args.list:
            # List available fields for a list
            list_id = context.resolve_id('list', args.list)
            response = fields_api.get_for_list(list_id)
            fields = response.get('fields', [])

            print(f"\n{colorize('Custom Fields for List', TextStyle.BOLD)} {list_id}\n")
            _print_field_definitions(fields)

        elif args.space:
            # List available fields for a space
            space_id = context.resolve_id('space', args.space)
            response = fields_api.get_for_space(space_id)
            fields = response.get('fields', [])

            print(f"\n{colorize('Custom Fields for Space', TextStyle.BOLD)} {space_id}\n")
            _print_field_definitions(fields)

        elif args.workspace:
            # List all workspace custom fields
            workspace_id = context.resolve_id('workspace', args.workspace)
            response = fields_api.get_for_workspace(workspace_id)
            fields = response.get('fields', [])

            print(f"\n{colorize('Custom Fields for Workspace', TextStyle.BOLD)} {workspace_id}\n")
            _print_field_definitions(fields)

        else:
            print("Error: Must specify one of: --task, --list, --space, or --workspace", file=sys.stderr)
            sys.exit(1)

    except ValueError as e:
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)
    except ClickUpAPIError as e:
        print(f"Error listing custom fields: {e}", file=sys.stderr)
        sys.exit(1)


def _print_field_definitions(fields: List[Dict[str, Any]]):
    """Helper to print field definitions."""
    if not fields:
        print("No custom fields found.")
        return

    # Group by type
    by_type = {}
    for field in fields:
        field_type = field.get('type', 'unknown')
        if field_type not in by_type:
            by_type[field_type] = []
        by_type[field_type].append(field)

    for field_type, type_fields in sorted(by_type.items()):
        field_color = FIELD_TYPE_COLORS.get(field_type, TextColor.WHITE)
        print(f"{colorize(field_type.upper(), field_color)}:")

        for field in sorted(type_fields, key=lambda f: f.get('name', '')):
            required = field.get('required', False)
            required_marker = colorize('*', TextColor.BRIGHT_RED) if required else ' '
            print(f"  {required_marker} {colorize(field['name'], TextStyle.BOLD)}")
            print(f"      ID: {colorize(field['id'], TextColor.BRIGHT_BLACK)}")

            # Show additional type-specific info
            if field_type in ('drop_down', 'labels'):
                options = field.get('type_config', {}).get('options', [])
                if options:
                    option_names = [opt.get('name') or opt.get('label', '') for opt in options]
                    print(f"      Options: {', '.join(option_names)}")
            elif field_type == 'rating':
                count = field.get('type_config', {}).get('count', 5)
                print(f"      Max: {count}")

            print()


def custom_field_remove_command(args):
    """Remove a custom field value from a task."""
    context = get_context_manager()
    client = ClickUpClient()

    # Resolve task ID
    try:
        task_id = context.resolve_id('task', args.task_id)
    except ValueError as e:
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)

    # Resolve field name to ID
    try:
        field_id, field = resolve_field_name_to_id(client, task_id, args.field_name_or_id)
    except ValueError as e:
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)

    # Get current value
    try:
        task = client.get_task(task_id)
        custom_fields = task.get('custom_fields', [])

        field_value = None
        for cf in custom_fields:
            if cf['id'] == field_id:
                field_value = cf.get('value')
                break

        # Show current value
        field_color = FIELD_TYPE_COLORS.get(field['type'], TextColor.WHITE)
        print(f"\nField: {colorize(field['name'], TextStyle.BOLD)} ({colorize(field['type'], field_color)})")
        print(f"Current value: {format_field_value(field, field_value)}")

        # Confirm if required field
        if field.get('required', False):
            print(colorize("\nWarning: This is a required field!", TextColor.BRIGHT_YELLOW))

        # Remove the field value
        client.remove_custom_field_value(task_id, field_id)
        success_msg = ANSIAnimations.success_message(
            f"Custom field '{field['name']}' removed from task"
        )
        print(f"\n{success_msg}")

    except ClickUpAPIError as e:
        print(f"Error removing custom field: {e}", file=sys.stderr)
        sys.exit(1)


def register_command(subparsers):
    """Register custom field commands."""
    # Create custom-field subcommand group
    cf_parser = subparsers.add_parser(
        'custom-field',
        aliases=['cf'],
        help='Manage custom fields on tasks',
        description='Manage custom fields on tasks'
    )

    cf_subparsers = cf_parser.add_subparsers(dest='cf_command', help='Custom field command')

    # custom-field set
    set_parser = cf_subparsers.add_parser(
        'set',
        help='Set custom field value on a task',
        description='Set a custom field value. Accepts field name or ID.'
    )
    set_parser.add_argument('task_id', help='Task ID (or "current")')
    set_parser.add_argument('field_name_or_id', help='Custom field name or ID')
    set_parser.add_argument('value', help='Field value')
    set_parser.set_defaults(func=custom_field_set_command)

    # custom-field get
    get_parser = cf_subparsers.add_parser(
        'get',
        help='Get custom field value from a task',
        description='Get a custom field value. Accepts field name or ID.'
    )
    get_parser.add_argument('task_id', help='Task ID (or "current")')
    get_parser.add_argument('field_name_or_id', help='Custom field name or ID')
    get_parser.set_defaults(func=custom_field_get_command)

    # custom-field list
    list_parser = cf_subparsers.add_parser(
        'list',
        help='List custom fields',
        description='List custom fields at different hierarchy levels or show values on a task.'
    )
    list_group = list_parser.add_mutually_exclusive_group(required=True)
    list_group.add_argument('--task', help='List fields on a task with values')
    list_group.add_argument('--list', help='List available fields for a list')
    list_group.add_argument('--space', help='List available fields for a space')
    list_group.add_argument('--workspace', help='List available fields for a workspace')
    list_parser.set_defaults(func=custom_field_list_command)

    # custom-field remove
    remove_parser = cf_subparsers.add_parser(
        'remove',
        aliases=['rm'],
        help='Remove custom field value from a task',
        description='Remove/clear a custom field value from a task.'
    )
    remove_parser.add_argument('task_id', help='Task ID (or "current")')
    remove_parser.add_argument('field_name_or_id', help='Custom field name or ID')
    remove_parser.set_defaults(func=custom_field_remove_command)
