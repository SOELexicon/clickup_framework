"""Attachment management commands for ClickUp Framework CLI."""

import os
from clickup_framework.commands.base_command import BaseCommand
from clickup_framework.resources import AttachmentsAPI
from clickup_framework.utils.colors import colorize, TextColor, TextStyle
from clickup_framework.utils.animations import ANSIAnimations


class AttachmentCreateCommand(BaseCommand):
    """
    Attachment Create Command using BaseCommand.
    """

    def execute(self):
        """Upload a file attachment to a task."""
        attachments_api = AttachmentsAPI(self.client)

        # Resolve "current" to actual task ID
        task_id = self.resolve_id('task', self.args.task_id)

        file_path = self.args.file_path

        # Validate file exists
        if not os.path.exists(file_path):
            self.error(f"File not found: {file_path}")

        # Check if it's a file (not a directory)
        if not os.path.isfile(file_path):
            self.error(f"Not a file: {file_path}")

        # Get file info
        file_size = os.path.getsize(file_path)
        file_name = os.path.basename(file_path)
        use_color = self.context.get_ansi_output()

        # Display upload info
        if use_color:
            self.print(f"📎 Uploading: {colorize(file_name, TextColor.BRIGHT_CYAN, TextStyle.BOLD)} "
                      f"({colorize(f'{file_size:,}', TextColor.BRIGHT_YELLOW)} bytes)")
        else:
            self.print(f"Uploading: {file_name} ({file_size:,} bytes)")

        # Upload with error handling
        try:
            result = attachments_api.create(task_id, file_path)

            # Show success message
            success_msg = ANSIAnimations.success_message("Attachment uploaded successfully")
            self.print(success_msg)

            # Display attachment details
            if use_color:
                self.print(f"\n📄 File: {colorize(result.get('title', file_name), TextColor.BRIGHT_CYAN)}")
                self.print(f"🆔 ID: {colorize(result.get('id', 'N/A'), TextColor.BRIGHT_GREEN)}")
                if result.get('url'):
                    self.print(f"🔗 URL: {colorize(result['url'], TextColor.BRIGHT_BLUE)}")
            else:
                self.print(f"\nFile: {result.get('title', file_name)}")
                self.print(f"ID: {result.get('id', 'N/A')}")
                if result.get('url'):
                    self.print(f"URL: {result['url']}")

            # Show helpful tip
            from clickup_framework.components.tips import show_tip
            show_tips_enabled = getattr(self.args, 'show_tips', True)
            show_tip('attachment', use_color=use_color, enabled=show_tips_enabled)

        except Exception as e:
            error_msg = str(e)
            if "404" in error_msg:
                self.error(f"Task not found: {task_id}")
            elif "403" in error_msg or "401" in error_msg:
                self.error("Permission denied. Check your API token and task access.")
            elif "413" in error_msg:
                self.error("File too large. Maximum file size may be exceeded.")
            else:
                self.error(f"Error uploading attachment: {error_msg}")


def attachment_create_command(args):
    """
    Command function wrapper for backward compatibility.

    This function maintains the existing function-based API while
    using the BaseCommand class internally.
    """
    command = AttachmentCreateCommand(args, command_name='attach')
    command.execute()


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
