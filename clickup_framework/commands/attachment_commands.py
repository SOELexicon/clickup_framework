"""Attachment management commands for ClickUp Framework CLI."""

import sys
import os
from pathlib import Path
from clickup_framework import ClickUpClient, get_context_manager
from clickup_framework.resources import AttachmentsAPI
from clickup_framework.utils.colors import colorize, TextColor, TextStyle
from clickup_framework.utils.animations import ANSIAnimations


def attachment_create_command(args):
    """Upload a file attachment to a task."""
    context = get_context_manager()
    client = ClickUpClient()
    attachments_api = AttachmentsAPI(client)

    # Resolve "current" to actual task ID
    try:
        task_id = context.resolve_id('task', args.task_id)
    except ValueError as e:
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)

    file_path = args.file_path

    # Validate file exists
    if not os.path.exists(file_path):
        print(f"Error: File not found: {file_path}", file=sys.stderr)
        sys.exit(1)

    # Check if it's a file (not a directory)
    if not os.path.isfile(file_path):
        print(f"Error: Not a file: {file_path}", file=sys.stderr)
        sys.exit(1)

    # Get file info
    file_size = os.path.getsize(file_path)
    file_name = os.path.basename(file_path)
    use_color = context.get_ansi_output()

    # Display upload info
    if use_color:
        print(f"📎 Uploading: {colorize(file_name, TextColor.BRIGHT_CYAN, TextStyle.BOLD)} "
              f"({colorize(f'{file_size:,}', TextColor.BRIGHT_YELLOW)} bytes)")
    else:
        print(f"Uploading: {file_name} ({file_size:,} bytes)")

    # Upload with error handling
    try:
        result = attachments_api.create(task_id, file_path)

        # Show success message
        success_msg = ANSIAnimations.success_message("Attachment uploaded successfully")
        print(success_msg)

        # Display attachment details
        if use_color:
            print(f"\n📄 File: {colorize(result.get('title', file_name), TextColor.BRIGHT_CYAN)}")
            print(f"🆔 ID: {colorize(result.get('id', 'N/A'), TextColor.BRIGHT_GREEN)}")
            if result.get('url'):
                print(f"🔗 URL: {colorize(result['url'], TextColor.BRIGHT_BLUE)}")
        else:
            print(f"\nFile: {result.get('title', file_name)}")
            print(f"ID: {result.get('id', 'N/A')}")
            if result.get('url'):
                print(f"URL: {result['url']}")

        # Show helpful tip
        from clickup_framework.components.tips import show_tip
        show_tips_enabled = getattr(args, 'show_tips', True)
        show_tip('attachment', use_color=use_color, enabled=show_tips_enabled)

    except Exception as e:
        error_msg = str(e)
        if "404" in error_msg:
            print(f"Error: Task not found: {task_id}", file=sys.stderr)
        elif "403" in error_msg or "401" in error_msg:
            print(f"Error: Permission denied. Check your API token and task access.", file=sys.stderr)
        elif "413" in error_msg:
            print(f"Error: File too large. Maximum file size may be exceeded.", file=sys.stderr)
        else:
            print(f"Error uploading attachment: {error_msg}", file=sys.stderr)
        sys.exit(1)


def register_command(subparsers):
    """Register attachment management commands."""
    # Main 'attach' command (short form)
    attach_parser = subparsers.add_parser(
        'attach',
        help='Upload file attachment to task'
    )
    attach_parser.add_argument(
        'task_id',
        help='Task ID (or "current" to use context)'
    )
    attach_parser.add_argument(
        'file_path',
        help='Path to file to upload'
    )
    attach_parser.set_defaults(func=attachment_create_command)

    # Verbose 'attachment' command with subcommands
    attachment_parser = subparsers.add_parser(
        'attachment',
        help='Manage task attachments'
    )
    attachment_subparsers = attachment_parser.add_subparsers(
        dest='attachment_command',
        help='Attachment command to execute'
    )

    # attachment create
    create_parser = attachment_subparsers.add_parser(
        'create',
        help='Upload file to task'
    )
    create_parser.add_argument(
        'task_id',
        help='Task ID (or "current" to use context)'
    )
    create_parser.add_argument(
        'file_path',
        help='Path to file to upload'
    )
    create_parser.set_defaults(func=attachment_create_command)
