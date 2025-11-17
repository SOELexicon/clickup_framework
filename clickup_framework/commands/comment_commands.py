"""Comment management commands for ClickUp Framework CLI."""

import sys
from clickup_framework import ClickUpClient, get_context_manager
from clickup_framework.utils.colors import colorize, TextColor, TextStyle
from clickup_framework.utils.animations import ANSIAnimations
from clickup_framework.commands.utils import read_text_from_file
from clickup_framework.parsers import ContentProcessor, ParserContext


def comment_add_command(args):
    """Add a comment to a task."""
    from clickup_framework.resources import CommentsAPI
    from clickup_framework.formatters import format_comment

    context = get_context_manager()
    client = ClickUpClient()
    comments_api = CommentsAPI(client)

    # Resolve "current" to actual task ID
    try:
        task_id = context.resolve_id('task', args.task_id)
    except ValueError as e:
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)

    # Validate that either text or comment_file is provided, but not both
    if args.text and args.comment_file:
        print("Error: Cannot provide both comment text and --comment-file", file=sys.stderr)
        sys.exit(1)

    if not args.text and not args.comment_file:
        print("Error: Must provide either comment text or --comment-file", file=sys.stderr)
        sys.exit(1)

    # Get comment text from argument or file
    if args.comment_file:
        comment_text = read_text_from_file(args.comment_file)
    else:
        comment_text = args.text

    # Process markdown and mermaid diagrams if enabled
    process_markdown = getattr(args, 'markdown', True)  # Default to True
    skip_mermaid = getattr(args, 'skip_mermaid', False)
    upload_images = getattr(args, 'upload_images', False)

    if process_markdown:
        processor = ContentProcessor(
            context=ParserContext.COMMENT,
            cache_dir=getattr(args, 'image_cache', None),
            client=client if upload_images else None
        )

        # Process content
        if upload_images:
            # Process and upload images in one step
            result = processor.process_and_upload(
                comment_text,
                task_id,
                format_markdown=True,
                process_mermaid=not skip_mermaid,
                convert_mermaid_to_images=not skip_mermaid
            )
            comment_text = result['content']

            # Show upload results
            upload_results = result.get('upload_results', {})
            if upload_results.get('uploaded'):
                print(f"✓ Uploaded {len(upload_results['uploaded'])} image(s)")
            if upload_results.get('errors'):
                for hash_val, error in upload_results['errors']:
                    print(f"⚠️  Failed to upload {hash_val[:8]}: {error}", file=sys.stderr)
        else:
            # Just process without uploading
            result = processor.process(
                comment_text,
                format_markdown=True,
                process_mermaid=not skip_mermaid,
                convert_mermaid_to_images=not skip_mermaid
            )
            comment_text = result['content']

            # Inform about unuploaded images
            if result.get('unuploaded_images'):
                print(f"ℹ️  {len(result['unuploaded_images'])} image(s) need uploading. Use --upload-images flag.")

    try:
        # Create the comment with rich text formatting
        # ClickUp supports both:
        # - comment_text: Plain text (no formatting)
        # - comment: Rich text JSON array (formatted content)
        if process_markdown and processor.markdown_formatter.contains_markdown(comment_text):
            # Use rich text JSON format for markdown
            comment_data = processor.markdown_formatter.to_json_format(comment_text)

            # Show debug output if requested
            if getattr(args, 'debug', False):
                import json
                print("\n" + colorize("Generated JSON:", TextColor.BRIGHT_CYAN, TextStyle.BOLD))
                print("=" * 60)
                print(json.dumps(comment_data, indent=2))
                print("=" * 60 + "\n")

            comment = comments_api.create_task_comment(task_id, comment_data=comment_data)
        else:
            # Plain text
            if getattr(args, 'debug', False):
                print("\n" + colorize("Plain Text Mode:", TextColor.BRIGHT_CYAN, TextStyle.BOLD))
                print(f"comment_text: {repr(comment_text)}\n")

            comment = comments_api.create_task_comment(task_id, comment_text=comment_text)

        # Show success message
        success_msg = ANSIAnimations.success_message("Comment added")
        print(success_msg)

        # Format and display the comment
        formatted = format_comment(comment, detail_level="summary")
        print(f"\n{formatted}")

    except Exception as e:
        print(f"Error adding comment: {e}", file=sys.stderr)
        sys.exit(1)


def comment_list_command(args):
    """List comments on a task."""
    from clickup_framework.resources import CommentsAPI
    from clickup_framework.formatters import format_comment_list

    context = get_context_manager()
    client = ClickUpClient()
    comments_api = CommentsAPI(client)

    # Resolve "current" to actual task ID
    try:
        task_id = context.resolve_id('task', args.task_id)
    except ValueError as e:
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)

    try:
        # Get task to display task name
        task = client.get_task(task_id)

        # Get comments
        result = comments_api.get_task_comments(task_id)
        comments = result.get('comments', [])

        # Display header
        use_color = context.get_ansi_output()
        if use_color:
            header = colorize(f"Comments for: {task['name']}", TextColor.BRIGHT_CYAN, TextStyle.BOLD)
        else:
            header = f"Comments for: {task['name']}"
        print(f"\n{header}")
        print(colorize("─" * 60, TextColor.BRIGHT_BLACK) if use_color else "─" * 60)

        if not comments:
            print(colorize("\nNo comments found", TextColor.BRIGHT_BLACK) if use_color else "\nNo comments found")
            return

        # Limit comments if specified
        if hasattr(args, 'limit') and args.limit:
            comments = comments[:args.limit]

        # Format and display comments
        detail_level = getattr(args, 'detail', 'summary')
        formatted = format_comment_list(comments, detail_level=detail_level)
        print(f"\n{formatted}")

        # Show total count
        total = len(result.get('comments', []))
        shown = len(comments)
        if shown < total:
            msg = f"\nShowing {shown} of {total} comments"
            print(colorize(msg, TextColor.BRIGHT_BLACK) if use_color else msg)
        else:
            msg = f"\nTotal: {total} comment(s)"
            print(colorize(msg, TextColor.BRIGHT_BLACK) if use_color else msg)

    except Exception as e:
        print(f"Error listing comments: {e}", file=sys.stderr)
        sys.exit(1)


def comment_update_command(args):
    """Update an existing comment."""
    from clickup_framework.resources import CommentsAPI
    from clickup_framework.formatters import format_comment

    context = get_context_manager()
    client = ClickUpClient()
    comments_api = CommentsAPI(client)

    # Validate that either text or comment_file is provided, but not both
    if args.text and args.comment_file:
        print("Error: Cannot provide both comment text and --comment-file", file=sys.stderr)
        sys.exit(1)

    if not args.text and not args.comment_file:
        print("Error: Must provide either comment text or --comment-file", file=sys.stderr)
        sys.exit(1)

    # Get comment text from argument or file
    if args.comment_file:
        comment_text = read_text_from_file(args.comment_file)
    else:
        comment_text = args.text

    # Process markdown and mermaid diagrams if enabled
    process_markdown = getattr(args, 'markdown', True)  # Default to True
    skip_mermaid = getattr(args, 'skip_mermaid', False)
    upload_images = getattr(args, 'upload_images', False)

    # Get task_id for uploads (needed to attach images)
    task_id = getattr(args, 'task_id', None)

    if process_markdown:
        processor = ContentProcessor(
            context=ParserContext.COMMENT,
            cache_dir=getattr(args, 'image_cache', None),
            client=client if upload_images else None
        )

        # Process content
        if upload_images and task_id:
            # Process and upload images in one step
            result = processor.process_and_upload(
                comment_text,
                task_id,
                format_markdown=True,
                process_mermaid=not skip_mermaid,
                convert_mermaid_to_images=not skip_mermaid
            )
            comment_text = result['content']

            # Show upload results
            upload_results = result.get('upload_results', {})
            if upload_results.get('uploaded'):
                print(f"✓ Uploaded {len(upload_results['uploaded'])} image(s)")
            if upload_results.get('errors'):
                for hash_val, error in upload_results['errors']:
                    print(f"⚠️  Failed to upload {hash_val[:8]}: {error}", file=sys.stderr)
        else:
            # Just process without uploading
            result = processor.process(
                comment_text,
                format_markdown=True,
                process_mermaid=not skip_mermaid,
                convert_mermaid_to_images=not skip_mermaid
            )
            comment_text = result['content']

            # Inform about unuploaded images
            if result.get('unuploaded_images'):
                if task_id:
                    print(f"ℹ️  {len(result['unuploaded_images'])} image(s) need uploading. Use --upload-images flag.")
                else:
                    print(f"ℹ️  {len(result['unuploaded_images'])} image(s) need uploading. Provide --task-id to upload.")

    try:
        # Update the comment
        # ClickUp comments support markdown directly via comment_text field
        # (not rich text JSON like some other platforms)
        updated = comments_api.update(args.comment_id, comment_text=comment_text)

        # Show success message
        success_msg = ANSIAnimations.success_message("Comment updated")
        print(success_msg)

        # Format and display the updated comment
        formatted = format_comment(updated, detail_level="summary")
        print(f"\n{formatted}")

    except Exception as e:
        print(f"Error updating comment: {e}", file=sys.stderr)
        sys.exit(1)


def comment_delete_command(args):
    """Delete a comment."""
    from clickup_framework.resources import CommentsAPI

    context = get_context_manager()
    client = ClickUpClient()
    comments_api = CommentsAPI(client)

    # Confirmation prompt unless --force is specified
    if not args.force:
        use_color = context.get_ansi_output()
        if use_color:
            prompt = colorize(f"Delete comment {args.comment_id}? (y/N): ", TextColor.BRIGHT_YELLOW)
        else:
            prompt = f"Delete comment {args.comment_id}? (y/N): "

        response = input(prompt).strip().lower()
        if response != 'y':
            print("Cancelled")
            return

    try:
        # Delete the comment
        comments_api.delete(args.comment_id)

        # Show success message
        success_msg = ANSIAnimations.success_message("Comment deleted")
        print(success_msg)

    except Exception as e:
        print(f"Error deleting comment: {e}", file=sys.stderr)
        sys.exit(1)


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
    comment_add_parser.add_argument('--image-cache', help='Directory for image cache')
    comment_add_parser.add_argument('--debug', action='store_true',
                                    help='Show generated JSON before sending')
    comment_add_parser.set_defaults(func=comment_add_command)

    # Comment list
    comment_list_parser = subparsers.add_parser(
        'comment_list',
        aliases=['cl'],
        help='List comments on a task',
        description='Display all comments on a task with configurable detail levels.',
        epilog='''Tips:
  • List all comments: cum cl current
  • Limit results: cum cl 86abc123 --limit 5
  • Change detail level: cum cl current --detail full
  • Detail levels: minimal, summary, detailed, full
  • Use to review task history and discussions'''
    )
    comment_list_parser.add_argument('task_id', help='Task ID (or "current")')
    comment_list_parser.add_argument('--limit', type=int, help='Limit number of comments shown')
    comment_list_parser.add_argument('--detail', choices=['minimal', 'summary', 'detailed', 'full'],
                                     default='summary', help='Detail level for comment display')
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
    comment_delete_parser.set_defaults(func=comment_delete_command)
