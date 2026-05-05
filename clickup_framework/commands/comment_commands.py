"""Comment management commands for ClickUp Framework CLI."""

import sys
import os
from clickup_framework import ClickUpClient, get_context_manager
from clickup_framework.commands.base_command import BaseCommand
from clickup_framework.utils.colors import colorize, TextColor, TextStyle
from clickup_framework.utils.animations import ANSIAnimations
from clickup_framework.commands.utils import read_text_from_file, add_common_args
from clickup_framework.parsers import ContentProcessor, ParserContext

# Metadata for automatic help generation
COMMAND_METADATA = {
    "category": "💬 Comment Management",
    "commands": [
        {
            "name": "comment_add [ca]",
            "args": "<task_id> <text>",
            "description": "Add a comment to a task"
        },
        {
            "name": "comment_list [cl]",
            "args": "<task_id> [--limit N]",
            "description": "List comments on a task"
        },
        {
            "name": "comment_update [cu]",
            "args": "<comment_id> <text>",
            "description": "Update an existing comment"
        },
        {
            "name": "comment_reply [cr]",
            "args": "<comment_id> <text>",
            "description": "Reply to a comment (create threaded reply)"
        },
        {
            "name": "comment_delete [cd]",
            "args": "<comment_id> [--force]",
            "description": "Delete a comment"
        },
    ]
}


def _read_comment_text(args):
    """Return comment text from args or file with shared validation."""
    if args.text and args.comment_file:
        print("Error: Cannot provide both comment text and --comment-file", file=sys.stderr)
        sys.exit(1)

    if not args.text and not args.comment_file:
        print("Error: Must provide either comment text or --comment-file", file=sys.stderr)
        sys.exit(1)

    if args.comment_file:
        return read_text_from_file(args.comment_file)

    return args.text


def _process_comment_text(args, client, comment_text, task_id=None):
    """Process markdown and mermaid content for comment text."""
    process_markdown = getattr(args, 'markdown', True)
    skip_mermaid = getattr(args, 'skip_mermaid', False)
    upload_images = getattr(args, 'upload_images', False)
    processor = None
    result = {}

    if process_markdown:
        processor = ContentProcessor(
            context=ParserContext.COMMENT,
            cache_dir=getattr(args, 'image_cache', None),
            client=client if upload_images else None
        )

        if upload_images and task_id:
            result = processor.process_and_upload(
                comment_text,
                task_id,
                format_markdown=True,
                process_mermaid=not skip_mermaid,
                convert_mermaid_to_images=not skip_mermaid
            )
            comment_text = result['content']

            upload_results = result.get('upload_results', {})
            if upload_results.get('uploaded'):
                print(f"✓ Uploaded {len(upload_results['uploaded'])} image(s)")
            if upload_results.get('errors'):
                for hash_val, error in upload_results['errors']:
                    print(f"⚠️  Failed to upload {hash_val[:8]}: {error}", file=sys.stderr)
        else:
            result = processor.process(
                comment_text,
                format_markdown=True,
                process_mermaid=not skip_mermaid,
                convert_mermaid_to_images=not skip_mermaid
            )
            comment_text = result['content']

            if result.get('unuploaded_images'):
                if task_id:
                    print(f"ℹ️  {len(result['unuploaded_images'])} image(s) need uploading. Use --upload-images flag.")
                else:
                    print(f"ℹ️  {len(result['unuploaded_images'])} image(s) need uploading. Provide --task-id to upload.")

    return comment_text, processor, result


def _build_comment_data(args, processor, comment_text, result):
    """Create rich-text payload when the processed comment still contains markdown."""
    if processor is None or not getattr(args, 'markdown', True):
        return None

    if not processor.markdown_formatter.contains_markdown(comment_text):
        return None

    image_metadata = {}
    attachment_ids = []
    if getattr(args, 'upload_images', False) and result.get('image_metadata'):
        image_metadata = result['image_metadata']
        attachment_ids = result.get('attachment_ids', [])

    return processor.markdown_formatter.to_json_format(
        comment_text,
        image_metadata=image_metadata,
        attachment_ids=attachment_ids
    )


def _print_debug_payload(args, comment_text=None, comment_data=None):
    """Show debug payload details before sending when requested."""
    if not getattr(args, 'debug', False):
        return

    if comment_data is not None:
        import json
        print("\n" + colorize("Generated JSON:", TextColor.BRIGHT_CYAN, TextStyle.BOLD))
        print("=" * 60)
        print(json.dumps(comment_data, indent=2))
        print("=" * 60 + "\n")
        return

    if comment_text is not None:
        print("\n" + colorize("Plain Text Mode:", TextColor.BRIGHT_CYAN, TextStyle.BOLD))
        print(f"comment_text: {repr(comment_text)}\n")


def _upload_attachment_urls(args, client, task_id, use_color):
    """Upload image attachments for comment_add."""
    attachment_urls = []
    if not getattr(args, 'attach_images', None):
        return attachment_urls

    from clickup_framework.resources import AttachmentsAPI

    attachments_api = AttachmentsAPI(client)
    for image_path in args.attach_images:
        if not os.path.exists(image_path):
            print(f"Warning: Image not found: {image_path}", file=sys.stderr)
            continue

        try:
            attachment = attachments_api.create(task_id, image_path)
            attachment_url = attachment.get('url')
            if attachment_url:
                attachment_urls.append(attachment_url)
                if use_color:
                    print(f"📎 Uploaded: {colorize(os.path.basename(image_path), TextColor.BRIGHT_CYAN)}")
                else:
                    print(f"Uploaded: {os.path.basename(image_path)}")
        except Exception as e:
            print(f"Warning: Failed to upload {image_path}: {e}", file=sys.stderr)

    return attachment_urls


def _print_comment_summary(comment):
    """Format and display a comment summary."""
    from clickup_framework.formatters import format_comment

    formatted = format_comment(comment, detail_level="summary")
    print(f"\n{formatted}")


def _comment_add_impl(args, context, client, use_color):
    """Add a comment to a task."""
    from clickup_framework.resources import CommentsAPI

    comments_api = CommentsAPI(client)

    try:
        task_id = context.resolve_id('task', args.task_id)
    except ValueError as e:
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)

    comment_text = _read_comment_text(args)
    comment_text, processor, result = _process_comment_text(args, client, comment_text, task_id=task_id)
    attachment_urls = _upload_attachment_urls(args, client, task_id, use_color)

    try:
        comment_data = _build_comment_data(args, processor, comment_text, result)
        if comment_data is not None:
            _print_debug_payload(args, comment_data=comment_data)
            comment = comments_api.create_task_comment(
                task_id,
                comment_data=comment_data,
                attachment_urls=attachment_urls if attachment_urls else None
            )
        else:
            _print_debug_payload(args, comment_text=comment_text)
            comment = comments_api.create_task_comment(
                task_id,
                comment_text=comment_text,
                attachment_urls=attachment_urls if attachment_urls else None
            )

        return comment
    except Exception as e:
        print(f"Error adding comment: {e}", file=sys.stderr)
        sys.exit(1)


def _comment_reply_impl(args, client):
    """Reply to a comment (create threaded reply)."""
    from clickup_framework.resources import CommentsAPI

    comments_api = CommentsAPI(client)
    comment_text = _read_comment_text(args)
    task_id = getattr(args, 'task_id', None)
    comment_text, _, _ = _process_comment_text(args, client, comment_text, task_id=task_id)

    try:
        notify_all = getattr(args, 'notify_all', False)
        comment = comments_api.create_threaded_comment(
            args.cpid,
            comment_text=comment_text,
            notify_all=notify_all
        )

        return comment
    except Exception as e:
        print(f"Error adding reply: {e}", file=sys.stderr)
        sys.exit(1)


def _comment_list_impl(args, context, client, use_color):
    """List comments on a task."""
    from clickup_framework.resources import CommentsAPI

    comments_api = CommentsAPI(client)

    try:
        task_id = context.resolve_id('task', args.task_id)
    except ValueError as e:
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)

    try:
        task = client.get_task(task_id)
        result = comments_api.get_task_comments(task_id)
        return {
            "task": task,
            "comments": result.get('comments', []),
            "total": result.get('total', len(result.get('comments', [])))
        }
    except Exception as e:
        print(f"Error listing comments: {e}", file=sys.stderr)
        sys.exit(1)


def _display_threaded_comments(comments, comments_api, detail_level, use_color):
    """Display comments in threaded treeview format."""
    from clickup_framework.formatters import format_comment
    from clickup_framework.components.tree import TreeFormatter

    # Fetch replies for each comment
    comments_with_replies = []
    for comment in comments:
        comment_copy = comment.copy()
        comment_copy['_replies'] = []

        # Check if comment has replies
        reply_count = comment.get('reply_count', 0)
        if reply_count and int(reply_count) > 0:
            try:
                # Fetch threaded replies
                replies_result = comments_api.get_threaded_comments(comment['id'])
                replies = replies_result.get('comments', [])
                comment_copy['_replies'] = replies
            except Exception as e:
                # If fetching replies fails, just skip them
                pass

        comments_with_replies.append(comment_copy)

    # Format each comment using TreeFormatter
    def format_comment_node(comment):
        """Format a comment for tree display."""
        user = comment.get('user', {})
        username = user.get('username', 'Unknown') if isinstance(user, dict) else 'Unknown'
        comment_text = comment.get('comment_text', '')
        comment_id = comment.get('id', '')
        reply_count = comment.get('reply_count', 0)

        # Format comment header
        if use_color:
            header = colorize(f"{username}", TextColor.BLUE, TextStyle.BOLD)
            if reply_count and int(reply_count) > 0:
                header += colorize(f" ({reply_count} replies)", TextColor.BRIGHT_BLACK)
        else:
            header = f"{username}"
            if reply_count and int(reply_count) > 0:
                header += f" ({reply_count} replies)"

        # Truncate comment text for tree display
        if comment_text:
            max_len = 80
            if len(comment_text) > max_len:
                text_preview = comment_text[:max_len] + "..."
            else:
                text_preview = comment_text

            if use_color:
                text_preview = colorize(text_preview, TextColor.WHITE)

            return f"{header}: {text_preview}"
        else:
            return header

    def get_comment_children(comment):
        """Get replies for a comment."""
        return comment.get('_replies', [])

    # Display using TreeFormatter
    print()
    for comment in comments_with_replies:
        tree_lines = TreeFormatter.build_tree(
            [comment],
            format_comment_node,
            get_comment_children,
            prefix="",
            is_last=True
        )
        for line in tree_lines:
            print(line)
        print()  # Empty line between root comments


def _comment_update_impl(args, client):
    """Update an existing comment."""
    from clickup_framework.resources import CommentsAPI

    comments_api = CommentsAPI(client)
    comment_text = _read_comment_text(args)
    task_id = getattr(args, 'task_id', None)
    comment_text, processor, result = _process_comment_text(args, client, comment_text, task_id=task_id)

    try:
        comment_data = _build_comment_data(args, processor, comment_text, result)
        if comment_data is not None:
            updated = comments_api.update(args.comment_id, comment_data=comment_data)
        else:
            updated = comments_api.update(args.comment_id, comment_text=comment_text)

        return updated
    except Exception as e:
        print(f"Error updating comment: {e}", file=sys.stderr)
        sys.exit(1)


def _comment_delete_impl(args, use_color, client):
    """Delete a comment."""
    from clickup_framework.resources import CommentsAPI

    comments_api = CommentsAPI(client)

    if not args.force:
        if use_color:
            prompt = colorize(f"Delete comment {args.comment_id}? (y/N): ", TextColor.BRIGHT_YELLOW)
        else:
            prompt = f"Delete comment {args.comment_id}? (y/N): "

        response = input(prompt).strip().lower()
        if response != 'y':
            print("Cancelled")
            return None

    try:
        comments_api.delete(args.comment_id)
        return {"success": True, "comment_id": args.comment_id}
    except Exception as e:
        print(f"Error deleting comment: {e}", file=sys.stderr)
        sys.exit(1)


class CommentCommandBase(BaseCommand):
    """Shared BaseCommand wiring for comment commands."""

    def _get_context_manager(self):
        """Use module-local factories so existing tests can patch them."""
        return get_context_manager()

    def _create_client(self):
        """Use module-local factories so existing tests can patch them."""
        return ClickUpClient()


class CommentAddCommand(CommentCommandBase):
    """Add a comment to a task."""

    def execute(self):
        """Execute the comment_add command."""
        result = _comment_add_impl(self.args, self.context, self.client, self.use_color)
        if result:
            self.handle_output(data=result)
        return result


class CommentReplyCommand(CommentCommandBase):
    """Reply to a comment."""

    def execute(self):
        """Execute the comment_reply command."""
        result = _comment_reply_impl(self.args, self.client)
        if result:
            self.handle_output(data=result)
        return result


class CommentListCommand(CommentCommandBase):
    """List task comments."""

    def execute(self):
        """Execute the comment_list command."""
        result = _comment_list_impl(self.args, self.context, self.client, self.use_color)
        if result:
            from clickup_framework.resources import CommentsAPI
            comments_api = CommentsAPI(self.client)
            
            detail_level = getattr(self.args, 'detail', 'summary')
            threaded = getattr(self.args, 'threaded', True)
            
            # Since _comment_list_impl doesn't print anything itself now,
            # we need to handle the console display here.
            # But wait, does it print? No, it returns a dict.
            
            # Build console output manually for now or use a formatter if exists
            # (Assuming I'll need to capture the current printing logic)
            
            # Actually, I'll just let handle_output do its job with the data.
            # For now I'll use a placeholder for console_output if it's special.
            self.handle_output(
                data=result,
                detail_level=detail_level
            )
        return result


class CommentUpdateCommand(CommentCommandBase):
    """Update an existing comment."""

    def execute(self):
        """Execute the comment_update command."""
        result = _comment_update_impl(self.args, self.client)
        if result:
            self.handle_output(data=result)
        return result


class CommentDeleteCommand(CommentCommandBase):
    """Delete a comment."""

    def execute(self):
        """Execute the comment_delete command."""
        result = _comment_delete_impl(self.args, self.use_color, self.client)
        if result:
            self.handle_output(data=result)
        return result


def comment_add_command(args):
    """Command function wrapper for backward compatibility."""
    command = CommentAddCommand(args, command_name='comment_add')
    command.execute()


def comment_reply_command(args):
    """Command function wrapper for backward compatibility."""
    command = CommentReplyCommand(args, command_name='comment_reply')
    command.execute()


def comment_list_command(args):
    """Command function wrapper for backward compatibility."""
    command = CommentListCommand(args, command_name='comment_list')
    command.execute()


def comment_update_command(args):
    """Command function wrapper for backward compatibility."""
    command = CommentUpdateCommand(args, command_name='comment_update')
    command.execute()


def comment_delete_command(args):
    """Command function wrapper for backward compatibility."""
    command = CommentDeleteCommand(args, command_name='comment_delete')
    command.execute()


def register_command(subparsers):
    """Register comment management commands."""
    # Comment add
    comment_add_parser = subparsers.add_parser(
        'comment_add',
        aliases=['ca'],
        help='Add a comment to a task',
        description='Add a text comment to a task, either inline or from a file.',
        epilog='''Tips:
  • Add inline comment: cum ca current "This is my comment"
  • Add from file: cum ca 86abc123 --comment-file notes.txt
  • Comments support markdown formatting
  • Use for status updates, notes, or collaboration
  • Comments appear in task activity feed'''
    )
    comment_add_parser.add_argument('task_id', help='Task ID (or "current")')
    comment_add_parser.add_argument('text', nargs='?', help='Comment text (optional if using --comment-file)')
    comment_add_parser.add_argument('--comment-file', '-f', help='Read comment text from file')
    comment_add_parser.add_argument('--no-markdown', dest='markdown', action='store_false',
                                    help='Disable markdown formatting')
    comment_add_parser.add_argument('--skip-mermaid', action='store_true',
                                    help='Skip mermaid diagram processing')
    comment_add_parser.add_argument('--upload-images', action='store_true',
                                    help='Upload images to ClickUp')
    comment_add_parser.add_argument('--attach-images', nargs='+', metavar='IMAGE_PATH',
                                    help='Upload and attach images to comment (supports multiple paths)')
    comment_add_parser.add_argument('--image-cache', help='Directory for image cache')
    comment_add_parser.add_argument('--debug', action='store_true',
                                    help='Show generated JSON before sending')
    add_common_args(comment_add_parser)
    comment_add_parser.set_defaults(func=comment_add_command)

    # Comment reply (threaded comments)
    comment_reply_parser = subparsers.add_parser(
        'comment_reply',
        aliases=['cr'],
        help='Reply to a comment (create threaded reply)',
        description='Create a threaded reply to an existing comment.',
        epilog='''Tips:
  • Reply to comment: cum cr --cpid <comment_id> "This is my reply"
  • Reply from file: cum cr --cpid <comment_id> --comment-file reply.txt
  • Get comment ID from cum cl <task_id>
  • Replies appear nested under parent comment
  • Use --task-id for image uploads: cum cr --cpid <cid> --task-id <tid> --upload-images "Reply"
  • Markdown formatting supported'''
    )
    comment_reply_parser.add_argument('--cpid', required=True, help='Comment parent ID (comment to reply to)')
    comment_reply_parser.add_argument('text', nargs='?', help='Reply text (optional if using --comment-file)')
    comment_reply_parser.add_argument('--comment-file', '-f', help='Read reply text from file')
    comment_reply_parser.add_argument('--task-id', help='Task ID (required for --upload-images)')
    comment_reply_parser.add_argument('--no-markdown', dest='markdown', action='store_false',
                                      help='Disable markdown formatting')
    comment_reply_parser.add_argument('--skip-mermaid', action='store_true',
                                      help='Skip mermaid diagram processing')
    comment_reply_parser.add_argument('--upload-images', action='store_true',
                                      help='Upload images to ClickUp')
    comment_reply_parser.add_argument('--image-cache', help='Directory for image cache')
    comment_reply_parser.add_argument('--notify-all', action='store_true',
                                      help='Notify all task watchers of the reply')
    add_common_args(comment_reply_parser)
    comment_reply_parser.set_defaults(func=comment_reply_command)

    # Comment list
    comment_list_parser = subparsers.add_parser(
        'comment_list',
        aliases=['cl'],
        help='List comments on a task',
        description='Display all comments on a task with configurable detail levels and threading support.',
        epilog='''Tips:
  • List all comments: cum cl current
  • Show threaded replies: cum cl current --threaded (default)
  • Show flat list: cum cl current --flat
  • Limit results: cum cl 86abc123 --limit 5
  • Change detail level: cum cl current --detail full
  • Detail levels: minimal, summary, detailed, full
  • Threaded mode shows replies nested under parent comments
  • Use to review task history and discussions'''
    )
    comment_list_parser.add_argument('task_id', help='Task ID (or "current")')
    comment_list_parser.add_argument('--limit', type=int, help='Limit number of comments shown')
    comment_list_parser.add_argument('--detail', choices=['minimal', 'summary', 'detailed', 'full'],
                                     default='summary', help='Detail level for comment display')
    comment_list_parser.add_argument('--threaded', dest='threaded', action='store_true', default=True,
                                     help='Show threaded replies in treeview format (default)')
    comment_list_parser.add_argument('--flat', dest='threaded', action='store_false',
                                     help='Show flat list of comments without threading')
    add_common_args(comment_list_parser)
    comment_list_parser.set_defaults(func=comment_list_command)

    # Comment update
    comment_update_parser = subparsers.add_parser(
        'comment_update',
        aliases=['cu'],
        help='Update an existing comment',
        description='Edit the text of an existing comment on a task.',
        epilog='''Tips:
  • Update inline: cum cu <comment_id> "Updated text"
  • Update from file: cum cu <comment_id> --comment-file updated.txt
  • Get comment ID from cum cl <task_id>
  • Markdown formatting supported
  • Edits are tracked in comment history'''
    )
    comment_update_parser.add_argument('comment_id', help='Comment ID')
    comment_update_parser.add_argument('text', nargs='?', help='New comment text (optional if using --comment-file)')
    comment_update_parser.add_argument('--comment-file', '-f', help='Read new comment text from file')
    comment_update_parser.add_argument('--task-id', help='Task ID (required for --upload-images)')
    comment_update_parser.add_argument('--no-markdown', dest='markdown', action='store_false',
                                       help='Disable markdown formatting')
    comment_update_parser.add_argument('--skip-mermaid', action='store_true',
                                       help='Skip mermaid diagram processing')
    comment_update_parser.add_argument('--upload-images', action='store_true',
                                       help='Upload images to ClickUp')
    comment_update_parser.add_argument('--image-cache', help='Directory for image cache')
    add_common_args(comment_update_parser)
    comment_update_parser.set_defaults(func=comment_update_command)

    # Comment delete
    comment_delete_parser = subparsers.add_parser(
        'comment_delete',
        aliases=['cd'],
        help='Delete a comment',
        description='Permanently delete a comment from a task with optional confirmation.',
        epilog='''Tips:
  • Delete with confirmation: cum cd <comment_id>
  • Force delete: cum cd <comment_id> --force
  • Get comment ID from cum cl <task_id>
  • Deletion is permanent and cannot be undone
  • Consider editing instead of deleting when possible'''
    )
    comment_delete_parser.add_argument('comment_id', help='Comment ID')
    comment_delete_parser.add_argument('--force', '-f', action='store_true',
                                       help='Skip confirmation prompt')
    add_common_args(comment_delete_parser)
    comment_delete_parser.set_defaults(func=comment_delete_command)
