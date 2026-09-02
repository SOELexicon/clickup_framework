"""Attachment management commands for ClickUp Framework CLI."""

import os
import re
import requests
from clickup_framework.commands.base_command import BaseCommand
from clickup_framework.resources import AttachmentsAPI
from clickup_framework.utils.colors import colorize, TextColor, TextStyle
from clickup_framework.utils.animations import ANSIAnimations
from clickup_framework.commands.utils import add_common_args


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
            
            # Display attachment details
            lines = [success_msg, ""]
            if use_color:
                lines.append(f"📄 File: {colorize(result.get('title', file_name), TextColor.BRIGHT_CYAN)}")
                lines.append(f"🆔 ID: {colorize(result.get('id', 'N/A'), TextColor.BRIGHT_GREEN)}")
                if result.get('url'):
                    lines.append(f"🔗 URL: {colorize(result['url'], TextColor.BRIGHT_BLUE)}")
            else:
                lines.append(f"File: {result.get('title', file_name)}")
                lines.append(f"ID: {result.get('id', 'N/A')}")
                if result.get('url'):
                    lines.append(f"URL: {result['url']}")
            
            console_out = "\n".join(lines)
            self.handle_output(data=result, console_output=console_out)

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


class AttachmentDownloadCommand(BaseCommand):
    """
    Attachment Download Command using BaseCommand.
    """

    def execute(self):
        """Download attachment(s) from a task to the local filesystem."""
        task_id = self.resolve_id('task', self.args.task_id)
        use_color = self.context.get_ansi_output()

        try:
            task = self.client.get_task(task_id)
        except Exception as e:
            error_msg = str(e)
            if "404" in error_msg:
                self.error(f"Task not found: {task_id}")
            elif "403" in error_msg or "401" in error_msg:
                self.error("Permission denied. Check your API token and task access.")
            else:
                self.error(f"Error fetching task: {error_msg}")
            return

        attachments = task.get('attachments') or []

        if self.args.id:
            attachments = [a for a in attachments if str(a.get('id')) == str(self.args.id)]
            if not attachments:
                self.error(f"No attachment with ID {self.args.id} found on task {task_id}")
        elif self.args.index is not None:
            if self.args.index < 1 or self.args.index > len(attachments):
                self.error(
                    f"Attachment index {self.args.index} out of range "
                    f"(task has {len(attachments)} attachment(s))"
                )
            attachments = [attachments[self.args.index - 1]]

        if not attachments:
            self.error(f"Task {task_id} has no attachments")

        output_dir = self.args.output or "."
        os.makedirs(output_dir, exist_ok=True)

        saved = []
        for attachment in attachments:
            url = attachment.get('url')
            if not url:
                continue

            title = attachment.get('title') or f"attachment_{attachment.get('id', 'unknown')}"
            file_name = self._safe_filename(title)
            dest_path = os.path.join(output_dir, file_name)

            if use_color:
                self.print(f"⬇️  Downloading: {colorize(file_name, TextColor.BRIGHT_CYAN, TextStyle.BOLD)}")
            else:
                self.print(f"Downloading: {file_name}")

            try:
                response = requests.get(url, stream=True, timeout=60)
                response.raise_for_status()
                with open(dest_path, 'wb') as f:
                    for chunk in response.iter_content(chunk_size=8192):
                        f.write(chunk)
            except Exception as e:
                self.print_error(f"Failed to download {file_name}: {e}")
                continue

            size = os.path.getsize(dest_path)
            saved.append({'id': attachment.get('id'), 'title': title, 'path': dest_path, 'size': size})

        if not saved:
            self.error("No attachments were downloaded")

        lines = [ANSIAnimations.success_message(f"Downloaded {len(saved)} attachment(s)"), ""]
        for item in saved:
            if use_color:
                size_str = f"{item['size']:,}"
                lines.append(
                    f"📄 {colorize(item['title'], TextColor.BRIGHT_CYAN)} "
                    f"({colorize(size_str, TextColor.BRIGHT_YELLOW)} bytes) "
                    f"-> {colorize(item['path'], TextColor.BRIGHT_BLUE)}"
                )
            else:
                lines.append(f"{item['title']} ({item['size']:,} bytes) -> {item['path']}")

        console_out = "\n".join(lines)
        self.handle_output(data={'task_id': task_id, 'attachments': saved}, console_output=console_out)

    @staticmethod
    def _safe_filename(name: str) -> str:
        """Strip path separators and unsafe characters from an attachment title."""
        name = os.path.basename(name)
        name = re.sub(r'[\\/:*?"<>|]', '_', name).strip()
        return name or "attachment"


def attachment_download_command(args):
    """
    Command function wrapper for backward compatibility.

    This function maintains the existing function-based API while
    using the BaseCommand class internally.
    """
    command = AttachmentDownloadCommand(args, command_name='attachment_download')
    command.execute()


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
    add_common_args(attach_parser)
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
    add_common_args(create_parser)
    create_parser.set_defaults(func=attachment_create_command)

    # attachment download
    download_parser = attachment_subparsers.add_parser(
        'download',
        help='Download attachment(s) from a task'
    )
    download_parser.add_argument(
        'task_id',
        help='Task ID (or "current" to use context)'
    )
    download_parser.add_argument(
        '--output', '-o',
        help='Directory to save downloaded file(s) into (default: current directory)'
    )
    download_group = download_parser.add_mutually_exclusive_group()
    download_group.add_argument(
        '--id',
        help='Download only the attachment with this ID'
    )
    download_group.add_argument(
        '--index',
        type=int,
        help='Download only the Nth attachment on the task (1-based, in task order)'
    )
    add_common_args(download_parser)
    download_parser.set_defaults(func=attachment_download_command)
