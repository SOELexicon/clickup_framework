"""Comment management commands for ClickUp Framework CLI."""

import sys
from clickup_framework import ClickUpClient, get_context_manager
from clickup_framework.utils.colors import colorize, TextColor, TextStyle
from clickup_framework.utils.animations import ANSIAnimations


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

    try:
        # Create the comment
        comment = comments_api.create_task_comment(task_id, args.comment_text)

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

    try:
        # Update the comment
        updated = comments_api.update(args.comment_id, args.comment_text)

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
    comment_add_parser = subparsers.add_parser('comment_add', aliases=['ca'],
                                                help='Add a comment to a task')
    comment_add_parser.add_argument('task_id', help='Task ID (or "current")')
    comment_add_parser.add_argument('comment_text', help='Comment text')
    comment_add_parser.set_defaults(func=comment_add_command)

    # Comment list
    comment_list_parser = subparsers.add_parser('comment_list', aliases=['cl'],
                                                 help='List comments on a task')
    comment_list_parser.add_argument('task_id', help='Task ID (or "current")')
    comment_list_parser.add_argument('--limit', type=int, help='Limit number of comments shown')
    comment_list_parser.add_argument('--detail', choices=['minimal', 'summary', 'detailed', 'full'],
                                     default='summary', help='Detail level for comment display')
    comment_list_parser.set_defaults(func=comment_list_command)

    # Comment update
    comment_update_parser = subparsers.add_parser('comment_update', aliases=['cu'],
                                                   help='Update an existing comment')
    comment_update_parser.add_argument('comment_id', help='Comment ID')
    comment_update_parser.add_argument('comment_text', help='New comment text')
    comment_update_parser.set_defaults(func=comment_update_command)

    # Comment delete
    comment_delete_parser = subparsers.add_parser('comment_delete', aliases=['cd'],
                                                   help='Delete a comment')
    comment_delete_parser.add_argument('comment_id', help='Comment ID')
    comment_delete_parser.add_argument('--force', '-f', action='store_true',
                                       help='Skip confirmation prompt')
    comment_delete_parser.set_defaults(func=comment_delete_command)
