from typing import Dict, List, Any, Optional, Tuple, Set

def format_task_basic_info(
    task: Dict[str, Any],
    colorize_output: bool = False,
    show_ids: bool = False,
    show_score: bool = False,
    show_tags: bool = False,
    show_description: bool = False,
    show_comments: int = 0,
    show_dates: bool = False,
    truncate_description: bool = True,
    truncate_length: int = 100,
    truncate_comments: bool = True,
    truncate_comment_length: int = 100,
    indent_spaces: int = 2
) -> str:
    """
    Format basic task information into a string.
    
    Args:
        task: Task dictionary to format
        colorize_output: Whether to colorize the output
        show_ids: Whether to show task IDs
        show_score: Whether to show task scores
        show_tags: Whether to show task tags under the task with tag emoji
        show_description: Whether to show task descriptions indented under the task
        show_comments: Number of comments to show (0 = none, negative = all)
        show_dates: Whether to show task dates
        truncate_description: Whether to truncate long descriptions
        truncate_length: Maximum length for descriptions before truncating
        truncate_comments: Whether to truncate long comments
        truncate_comment_length: Maximum length for comments before truncating
        indent_spaces: Number of spaces to use for indentation
        
    Returns:
        Formatted string representation of the task.
    """
    import logging
    from refactor.cli.formatting.common.task_info import (
        format_task_dates, format_task_score, get_task_emoji,
        format_task_status, format_task_priority
    )
    from refactor.utils.colors import colorize, TextColor, task_status_color
    
    # Create indent string based on specified spaces
    indent = ' ' * indent_spaces
    
    # Get task components
    task_id = task.get('id', '')
    task_name = task.get('name', 'Unnamed Task')
    # Ensure status is always a string before calling .lower()
    task_status = str(task.get('status', '')).lower() if task.get('status') is not None else ''
    task_type = task.get('custom_type', task.get('type', ''))
    task_priority = task.get('priority')
    
    # Debug logs
    logging.debug(f"Show IDs: {show_ids}")
    logging.debug(f"Task ID: {task_id}")
    
    # Start building the output with task emoji and name
    task_emoji = get_task_emoji(task_type)
    output = f"{task_emoji} "
    
    # Add ID if requested
    if show_ids and task_id:
        id_str = f"[{task_id}] "
        if colorize_output:
            id_str = colorize(id_str, TextColor.BRIGHT_BLACK)
        output += id_str
        logging.debug(f"Added task ID to output: {id_str}")
    
    # Add task name and status
    output += task_name
    
    # Add status
    status_str = format_task_status(task_status, colorize_output)
    if status_str:
        output += f" [{status_str}]"
    
    # Add priority
    priority_str = format_task_priority(task_priority, colorize_output)
    if priority_str:
        output += f" {priority_str}"
    
    # Add score if requested
    if show_score:
        score_str = format_task_score(task, colorize_output)
        if score_str:
            output += f" {score_str}"
    
    # Add dates if requested
    if show_dates:
        dates_str = format_task_dates(task, colorize_output)
        if dates_str:
            output += f" {dates_str}"
    
    # Create a new line with indentation for tags if requested
    if show_tags and task.get('tags'):
        tags_list = task.get('tags', [])
        if tags_list:
            tags_str = "🏷️ Tags: "
            
            # Format each tag
            formatted_tags = []
            for tag in tags_list:
                if colorize_output:
                    formatted_tag = colorize(f"[{tag}]", TextColor.BRIGHT_CYAN)
                else:
                    formatted_tag = f"[{tag}]"
                formatted_tags.append(formatted_tag)
            
            # Join tags and add to output on a new line with indentation
            tags_str += " ".join(formatted_tags)
            output += f"\n{indent}{tags_str}"
    
    # Add description if requested
    if show_description and task.get('description'):
        desc = task.get('description', '')
        
        if desc:
            # Format description with truncation if needed
            if truncate_description and len(desc) > truncate_length:
                visible_desc = desc[:truncate_length] + "..."
            else:
                visible_desc = desc
                
            # Replace newlines with newline + indentation to maintain structure
            visible_desc = visible_desc.replace('\n', f'\n{indent}{indent}')
            
            # Add description header and content on a new line with indentation
            desc_header = "📝 Description:"
            if colorize_output:
                desc_header = colorize(desc_header, TextColor.BRIGHT_BLUE)
                
            output += f"\n{indent}{desc_header}"
            output += f"\n{indent}{indent}{visible_desc}"
    
    # Add comments if requested
    if show_comments and task.get('comments'):
        comments = task.get('comments', [])
        
        # Determine how many comments to show
        if show_comments < 0:
            # Show all comments
            comments_to_show = comments
        else:
            # Show at most show_comments
            comments_to_show = comments[:show_comments]
            
        if comments_to_show:
            # Add comments header
            comments_header = "💬 Comments:"
            if colorize_output:
                comments_header = colorize(comments_header, TextColor.BRIGHT_GREEN)
                
            output += f"\n{indent}{comments_header}"
            
            # Process each comment
            for comment in comments_to_show:
                comment_text = comment.get('text', '')
                comment_user = comment.get('user', {}).get('username', 'Unknown User')
                
                if comment_text:
                    # Format comment with truncation if needed
                    if truncate_comments and len(comment_text) > truncate_comment_length:
                        visible_comment = comment_text[:truncate_comment_length] + "..."
                    else:
                        visible_comment = comment_text
                        
                    # Replace newlines with newline + indentation to maintain structure
                    visible_comment = visible_comment.replace('\n', f'\n{indent}{indent}{indent}')
                    
                    # Add user attribution and comment text with proper indentation
                    comment_user_str = f"@{comment_user}:"
                    if colorize_output:
                        comment_user_str = colorize(comment_user_str, TextColor.BRIGHT_MAGENTA)
                        
                    output += f"\n{indent}{indent}{comment_user_str}"
                    output += f"\n{indent}{indent}{indent}{visible_comment}"
    
    # Return formatted output
    return output 