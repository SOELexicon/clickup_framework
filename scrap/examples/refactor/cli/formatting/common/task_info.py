"""
Task Info Formatting Module

This module provides utilities for formatting basic task information.

Task: tsk_1e88842d - Tree Structure Validation
dohcount: 2

Related Tasks:
    - tsk_da3dfe13 - Descriptive Task Display (related)
    - tsk_1e88842d - Implement multi-attribute display with --show parameter

Changes:
    - v1: Initial implementation of basic task info formatting
    - v2: Added support for new display parameters: show_descriptions, show_dates, show_comments
    - v3: Added FormatOptions class for better parameter management
    - v4: Improved content display with proper indentation and emojis
"""

from typing import Dict, Any, List, Optional, Union
import logging
import textwrap
import re
import sys
from dataclasses import dataclass, field
import traceback

# Helper function for escaped newlines
def _convert_escaped_newlines(text: str) -> str:
    """
    Convert escaped newline sequences (\\n) to actual newlines.
    
    This ensures proper processing and indentation of multi-line text
    in tree views and other formatted output.
    
    Args:
        text: The text that may contain escaped newlines
        
    Returns:
        Text with escaped newlines converted to actual newlines
    """
    if text and isinstance(text, str) and '\\n' in text:
        return text.replace('\\n', '\n')
    return text

# Content display constants
DEFAULT_DESCRIPTION_LENGTH = 100  # Default max length for descriptions
MAX_COMMENT_PREVIEW_LENGTH = 50   # Max length for comment previews
MAX_DESCRIPTION_LINES = 3         # Max number of description lines to show

# Section emojis
DESCRIPTION_EMOJI = "📝"  # Document emoji for descriptions
COMMENT_EMOJI = "💬"     # Speech bubble emoji for comments
TAG_EMOJI = "🏷️"         # Tag emoji for tags
DATE_EMOJI = "📅"        # Calendar emoji for dates
SCORE_EMOJI = "📊"       # Chart emoji for scores

# Add a mapping for task types to emojis
TASK_TYPE_EMOJI_MAP = {
    "task": "📝",
    "bug": "🐛",
    "feature": "🚀",
    "refactor": "♻️",
    "documentation": "📚",
    "enhancement": "✨",
    "chore": "🧹",
    "research": "🔬",
    "testing": "🧪",
    "security": "🛡️",
    "project": "📂",
    "milestone": "🏁"
}

# Status color mapping
STATUS_COLOR_MAP = {
    "to do": "37",        # White
    "in progress": "33",  # Yellow
    "complete": "32",     # Green
    "blocked": "31",      # Red
    "default": "37"       # White default
}

# Priority color mapping
PRIORITY_COLOR_MAP = {
    "p1": "31",     # Red for urgent
    "p2": "33",     # Yellow for high
    "p3": "36",     # Cyan for medium
    "p4": "37",     # White for low
    "default": "37" # White default
}

def get_task_status_color(status: str) -> str:
    """
    Get the color code for a task status.
    
    Args:
        status: The task status
        
    Returns:
        The ANSI color code for the status
    """
    logging.debug(f"get_task_status_color called with status: {status} (type: {type(status)})")
    
    if not status:
        return STATUS_COLOR_MAP["default"]
    
    try:
        # Normalize status by converting to lowercase
        normalized_status = str(status).lower().strip()
        logging.debug(f"Normalized status: {normalized_status}")
        
        # Return the corresponding color or default
        return STATUS_COLOR_MAP.get(normalized_status, STATUS_COLOR_MAP["default"])
    except Exception as e:
        logging.error(f"Error in get_task_status_color: {e}")
        return STATUS_COLOR_MAP["default"]

def get_task_priority_color(priority: str) -> str:
    """
    Get the color code for a task priority.
    
    Args:
        priority: The task priority (string or int)
        
    Returns:
        The ANSI color code for the priority
    """
    logging.debug(f"get_task_priority_color called with priority: {priority} (type: {type(priority)})")
    
    if not priority:
        return PRIORITY_COLOR_MAP["default"]
    
    try:
        # Handle integer priority values (convert to string first)
        if isinstance(priority, int):
            priority = f"p{priority}"
            logging.debug(f"Converted int priority to: {priority}")
        
        # Normalize priority by converting to lowercase
        normalized_priority = str(priority).lower().strip()
        logging.debug(f"Normalized priority: {normalized_priority}")
        
        # Return the corresponding color or default
        return PRIORITY_COLOR_MAP.get(normalized_priority, PRIORITY_COLOR_MAP["default"])
    except Exception as e:
        logging.error(f"Error in get_task_priority_color: {e}")
        return PRIORITY_COLOR_MAP["default"]

def get_task_type_emoji(task_type: str) -> str:
    """
    Get the emoji for a task type.
    
    Args:
        task_type: The task type
        
    Returns:
        The emoji for the task type
    """
    if not task_type:
        return TASK_TYPE_EMOJI_MAP["task"]  # Default to task emoji
    
    # Normalize task type by converting to lowercase and removing spaces
    normalized_type = task_type.lower().strip()
    
    # Return the corresponding emoji or default to task emoji
    return TASK_TYPE_EMOJI_MAP.get(normalized_type, TASK_TYPE_EMOJI_MAP["task"])

def get_task_emoji(task_type: str) -> str:
    """
    Get the emoji for a task type.
    
    This is an alias for get_task_type_emoji for backward compatibility.
    
    Args:
        task_type: The task type
        
    Returns:
        The emoji for the task type
    """
    return get_task_type_emoji(task_type)

@dataclass
class FormatOptions:
    """
    Dataclass to hold all formatting options.
    
    This makes it easier to pass options between functions and
    helps prevent issues with missing or renamed parameters.
    """
    colorize_output: bool = True
    show_ids: bool = False
    show_score: bool = False
    show_tags: bool = False
    tag_style: str = "colored"
    show_type_emoji: bool = True
    show_descriptions: bool = False
    show_dates: bool = False
    show_comments: int = 0
    show_relationships: bool = False
    include_completed: bool = False
    hide_orphaned: bool = False
    description_length: int = DEFAULT_DESCRIPTION_LENGTH
    show_container_diff: bool = True
    trace: bool = False
    
    @classmethod
    def from_dict(cls, options_dict: Dict[str, Any]) -> 'FormatOptions':
        """Create a FormatOptions instance from a dictionary of options."""
        return cls(**{k: v for k, v in options_dict.items() if k in cls.__dataclass_fields__})
    
    @classmethod
    def from_args(cls, args) -> 'FormatOptions':
        """Create a FormatOptions instance from command-line arguments."""
        options = {}
        for field_name in cls.__dataclass_fields__:
            if hasattr(args, field_name):
                options[field_name] = getattr(args, field_name)
            elif field_name == 'show_ids' and hasattr(args, 'show_id'):
                # Handle common naming difference between CLI and functions
                options[field_name] = getattr(args, 'show_id')
                
        return cls.from_dict(options)

def format_task_basic_info(
    task: Dict[str, Any],
    colorize: bool = True,
    show_id: bool = False,
    show_score: bool = False,
    show_type_emoji: bool = True,
    show_tags: bool = False,
    tag_style: str = "colored",
    show_description: bool = False,
    description_length: int = 100,
    show_relationships: bool = False,
    show_comments: int = 0,
    show_dates: bool = False,
    options: Optional[FormatOptions] = None,
    indent_level: int = 0,
    trace: bool = False
) -> str:
    """
    Format basic information about a task.
    
    Args:
        task: The task dictionary to format.
        colorize: Whether to colorize the output.
        show_id: Whether to show task IDs.
        show_score: Whether to show task scores.
        show_type_emoji: Whether to show task type emojis.
        show_tags: Whether to show task tags.
        tag_style: The style for displaying tags.
        show_description: Whether to show task descriptions.
        description_length: The max length for task descriptions.
        show_relationships: Whether to show task relationships.
        show_comments: The number of comments to show.
        show_dates: Whether to show task dates.
        options: Additional format options.
        indent_level: The indentation level for the task.
        trace: Whether to show detailed stack traces on error
        
    Returns:
        Formatted string with task information
    """
    try:
        # Use options object if provided, otherwise use individual parameters
        if options:
            colorize = options.colorize_output
            show_id = options.show_ids
            show_score = options.show_score
            show_type_emoji = options.show_type_emoji
            show_tags = options.show_tags
            tag_style = options.tag_style
            show_description = options.show_descriptions
            description_length = options.description_length
            show_relationships = options.show_relationships
            show_comments = options.show_comments
            show_dates = options.show_dates
            
        if trace:
            # Log parameters to aid debugging
            logging.debug(f"format_task_basic_info called for task {task.get('id')}")
            logging.debug(f"  show_id={show_id}")
            logging.debug(f"  colorize={colorize}")
            logging.debug(f"  options={options.__dict__ if options else None}")
            
        # Get basic task info
        task_id = task.get('id', '')
        task_name = task.get('name', '')
        task_status = task.get('status', '')
        task_type = task.get('type', '')
        task_priority = task.get('priority', 'P4')
        
        base_indent = '  ' * indent_level
        content_indent = base_indent + '│ '
        last_item_indent = base_indent + '└─'
        
        # Format basic task line
        output = []
        basic_info = []
        
        if trace and show_id:
            task_id = task.get('id', '')
            logging.debug(f"Adding ID {task_id} to formatted output")

        # Add task ID if requested
        if show_id and task_id:
            id_str = f"[{task_id}]"
            if colorize:
                id_str = f"\033[38;5;8m{id_str}\033[0m"  # Dark gray
            basic_info.append(id_str)
        
        # Add task emoji based on type
        type_emoji = get_task_type_emoji(task_type)
        basic_info.append(type_emoji)
        
        # Add task name
        name_str = task_name
        if colorize:
            status_color = get_task_status_color(task_status)
            name_str = f"\033[{status_color}m{name_str}\033[0m"
        basic_info.append(name_str)
        
        # Add task status if not "to do"
        try:
            # Ensure status is a string and do a case-insensitive comparison
            status_str = str(task_status).lower()
            if status_str != "to do":
                status_display = f"[{task_status}]"
                if colorize:
                    status_color = get_task_status_color(task_status)
                    status_display = f"\033[{status_color}m{status_display}\033[0m"
                basic_info.append(status_display)
        except Exception as e:
            logging.error(f"Error processing task status: {e} (status value: {task_status}, type: {type(task_status)})")
            # Add a fallback display that won't break
            basic_info.append(f"[Status: {str(task_status)}]")
        
        # Add priority if not default
        try:
            # Ensure priority is a string and do a case-insensitive comparison
            priority_str = str(task_priority).lower() 
            if priority_str != 'p4':
                priority_display = f"({task_priority})"
                if colorize:
                    priority_color = get_task_priority_color(task_priority)
                    priority_display = f"\033[{priority_color}m{priority_display}\033[0m"
                basic_info.append(priority_display)
        except Exception as e:
            logging.error(f"Error processing task priority: {e} (priority value: {task_priority}, type: {type(task_priority)})")
            # Add a fallback display that won't break
            basic_info.append(f"(Priority: {str(task_priority)})")
        
        # Add scores if requested
        if show_score:
            score_str = format_task_score(task, colorize)
            if score_str:
                basic_info.append(score_str)
        
        # Combine basic info into a single line
        output.append(' '.join(basic_info))
        
        # Add additional content if requested
        has_additional_content = False
        
        # Add dates section if requested
        if show_dates:
            dates_str = format_task_dates(task, colorize)
            if dates_str:
                has_additional_content = True
                date_header = f"{content_indent}{DATE_EMOJI} Dates:"
                if colorize:
                    date_header = f"\033[1m{date_header}\033[0m"  # Bold
                output.append(date_header)
                
                # Format each date on its own line with indentation
                date_lines = _convert_escaped_newlines(dates_str).split('\n')
                for date_line in date_lines:
                    output.append(f"{content_indent}  {date_line}")
        
        # Add tags section if requested and tags exist
        if show_tags and task.get('tags'):
            has_additional_content = True
            tags_header = f"{content_indent}{TAG_EMOJI} Tags:"
            if colorize:
                tags_header = f"\033[1m{tags_header}\033[0m"  # Bold
            output.append(tags_header)
            
            tags_str = ', '.join(task.get('tags', []))
            output.append(f"{content_indent}  {tags_str}")
        
        # Add description if requested
        if show_description and task.get('description'):
            description = _convert_escaped_newlines(task.get('description', ''))
            if description:
                has_additional_content = True
                desc_header = f"{content_indent}{DESCRIPTION_EMOJI} Description:"
                if colorize:
                    desc_header = f"\033[1m{desc_header}\033[0m"  # Bold
                output.append(desc_header)
                
                # Handle multi-line descriptions
                desc_lines = description.split('\n')
                desc_to_show = desc_lines[:MAX_DESCRIPTION_LINES]
                
                for line in desc_to_show:
                    if len(line) > description_length:
                        line = line[:description_length] + "..."
                    output.append(f"{content_indent}  {line}")
                    
                # Show count of additional lines if truncated
                if len(desc_lines) > MAX_DESCRIPTION_LINES:
                    more_lines = len(desc_lines) - MAX_DESCRIPTION_LINES
                    output.append(f"{content_indent}  ... and {more_lines} more line(s)")
        
        # Add comments if requested
        if show_comments and task.get('comments'):
            comments = task.get('comments', [])
            if comments:
                has_additional_content = True
                comments_header = f"{content_indent}{COMMENT_EMOJI} Comments:"
                if colorize:
                    comments_header = f"\033[1m{comments_header}\033[0m"  # Bold
                output.append(comments_header)
                
                # Show only the first comment with preview
                first_comment = comments[0]
                comment_author = first_comment.get('author', 'Unknown')
                comment_time = first_comment.get('timestamp', '')
                comment_text = _convert_escaped_newlines(first_comment.get('text', ''))
                
                # Create a preview of the comment
                if comment_text:
                    comment_preview = comment_text.split('\n')[0]
                    if len(comment_preview) > MAX_COMMENT_PREVIEW_LENGTH:
                        comment_preview = comment_preview[:MAX_COMMENT_PREVIEW_LENGTH] + "..."
                    
                    output.append(f"{content_indent}  {comment_author} ({comment_time}): {comment_preview}")
                
                # Show count of additional comments
                if len(comments) > 1:
                    output.append(f"{content_indent}  ... and {len(comments) - 1} more comment(s)")
        
        # Add scores in detailed view if requested
        if show_score:
            # Get individual score components
            impact = task.get('impact_score', 0)
            effort = task.get('effort_score', 0)
            risk = task.get('risk_score', 0)
            value = task.get('value_score', 0)
            
            # Only show scores section if any score > 0
            if impact > 0 or effort > 0 or risk > 0 or value > 0:
                has_additional_content = True
                score_header = f"{content_indent}{SCORE_EMOJI} Scores:"
                if colorize:
                    score_header = f"\033[1m{score_header}\033[0m"  # Bold
                output.append(score_header)
                
                if impact > 0:
                    output.append(f"{content_indent}  Impact: {impact}")
                if effort > 0:
                    output.append(f"{content_indent}  Effort: {effort}")
                if risk > 0:
                    output.append(f"{content_indent}  Risk: {risk}")
                if value > 0:
                    output.append(f"{content_indent}  Value: {value}")
        
        # If we have additional content, use a different final indentation
        if has_additional_content:
            # Change the indentation of the last line to indicate end of this task
            final_indent = last_item_indent
            output.append(f"{final_indent}")
        
        return '\n'.join(output)
    except Exception as e:
        error_msg = f"Error in format_task_basic_info for task {task.get('id', 'unknown')}: {e}"
        if trace:
            error_msg += f"\n{traceback.format_exc()}"
        logging.error(error_msg)
        return f"Error formatting task: {e}"

def format_task_dates(
    task: Dict[str, Any],
    colorize_output: bool = True
) -> str:
    """
    Format task dates.
    
    Task: tsk_1e88842d - Tree Structure Validation
    dohcount: 1
    
    Args:
        task: Task dictionary
        colorize_output: Whether to use ANSI colors
        
    Returns:
        Formatted dates string
    """
    # Extract dates
    created_date = task.get('date_created', '')
    updated_date = task.get('date_updated', '')
    due_date = task.get('due_date', '')
    
    # If no dates, return empty string
    if not any([created_date, updated_date, due_date]):
        return ""
    
    # Format dates with colors if enabled
    date_parts = []
    
    if created_date:
        if colorize_output:
            from refactor.utils.colors import TextColor, colorize
            date_parts.append(f"Created: {colorize(created_date, TextColor.BRIGHT_GREEN)}")
        else:
            date_parts.append(f"Created: {created_date}")
    
    if updated_date:
        if colorize_output:
            from refactor.utils.colors import TextColor, colorize
            date_parts.append(f"Updated: {colorize(updated_date, TextColor.BRIGHT_YELLOW)}")
        else:
            date_parts.append(f"Updated: {updated_date}")
    
    if due_date:
        if colorize_output:
            from refactor.utils.colors import TextColor, colorize
            date_parts.append(f"Due: {colorize(due_date, TextColor.BRIGHT_RED)}")
        else:
            date_parts.append(f"Due: {due_date}")
    
    return " | ".join(date_parts)

def format_task_score(
    task: Dict[str, Any],
    colorize_output: bool = True
) -> str:
    """
    Format task scores.
    
    Task: tsk_1e88842d - Tree Structure Validation
    dohcount: 1
    
    Args:
        task: Task dictionary
        colorize_output: Whether to use ANSI colors
        
    Returns:
        Formatted score string
    """
    # Extract scores
    total_score = task.get('total_score', 0)
    effort_score = task.get('effort_score', 0)
    effectiveness_score = task.get('effectiveness_score', 0)
    risk_score = task.get('risk_score', 0)
    urgency_score = task.get('urgency_score', 0)
    
    # If no scores, return empty string
    if all(score == 0 for score in [total_score, effort_score, effectiveness_score, risk_score, urgency_score]):
        return ""
    
    # Format scores with colors if enabled
    if colorize_output:
        from refactor.utils.colors import TextColor, colorize
        
        # Define color thresholds
        def get_score_color(score, inverse=False):
            if inverse:
                # For effort (lower is better)
                if score >= 8: return TextColor.BRIGHT_RED
                if score >= 5: return TextColor.YELLOW
                return TextColor.GREEN
            else:
                # For other metrics (higher is better)
                if score >= 8: return TextColor.BRIGHT_GREEN
                if score >= 5: return TextColor.YELLOW
                return TextColor.BRIGHT_RED
        
        # Apply colors
        total_colored = colorize(f"{total_score:.1f}", get_score_color(total_score))
        effort_colored = colorize(f"{effort_score:.1f}", get_score_color(effort_score, True))
        effectiveness_colored = colorize(f"{effectiveness_score:.1f}", get_score_color(effectiveness_score))
        risk_colored = colorize(f"{risk_score:.1f}", get_score_color(risk_score))
        urgency_colored = colorize(f"{urgency_score:.1f}", get_score_color(urgency_score))
        
        return f"[Score: {total_colored} | Eff: {effort_colored} | Impact: {effectiveness_colored} | Risk: {risk_colored} | Urg: {urgency_colored}]"
    else:
        # Plain text formatting
        return f"[Score: {total_score:.1f} | Eff: {effort_score:.1f} | Impact: {effectiveness_score:.1f} | Risk: {risk_score:.1f} | Urg: {urgency_score:.1f}]"

def format_task_status(status: str, colorize_output: bool = True) -> str:
    """
    Format a task status string, optionally with coloring.
    
    Args:
        status: The task status string
        colorize_output: Whether to colorize the output
        
    Returns:
        Formatted status string
    """
    import logging
    logging.debug(f"format_task_status called with: {status} (type: {type(status)})")
    
    try:
        if not status:
            return ""
            
        # Ensure status is a string
        status = str(status)
            
        # Simple formatting if no colors
        if not colorize_output:
            return status
            
        # Get the color for this status
        color_code = get_task_status_color(status)
        
        # Format with color
        return f"\033[{color_code}m{status}\033[0m"
    except Exception as e:
        logging.error(f"Error in format_task_status: {e}")
        return str(status) if status else ""

def format_task_priority(priority: str, colorize_output: bool = True) -> str:
    """
    Format a task priority string, optionally with coloring.
    
    Args:
        priority: The task priority (string or int)
        colorize_output: Whether to colorize the output
        
    Returns:
        Formatted priority string
    """
    import logging
    logging.debug(f"format_task_priority called with: {priority} (type: {type(priority)})")
    
    try:
        if not priority:
            return ""
            
        # Handle integer priority values (convert to string first)
        if isinstance(priority, int):
            priority = f"P{priority}"
        elif not isinstance(priority, str):
            priority = str(priority)
            
        # Simple formatting if no colors
        if not colorize_output:
            return priority
            
        # Get the color for this priority
        color_code = get_task_priority_color(priority)
        
        # Format with color
        return f"\033[{color_code}m{priority}\033[0m"
    except Exception as e:
        logging.error(f"Error in format_task_priority: {e}")
        return str(priority) if priority else "" 