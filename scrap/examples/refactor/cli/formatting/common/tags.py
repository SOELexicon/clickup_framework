"""
Tags Formatting Module

This module provides utilities for formatting task tags in various styles.

Task: tsk_1e88842d - Tree Structure Validation
dohcount: 1
"""

from typing import List, Dict, Any, Optional, Set, Tuple
import logging
import sys

# Add tag emoji
TAG_EMOJI = "🏷️"

def format_tags(
    tags: List[str],
    tag_style: str = "colored",
    indent: str = "",
    colorize_output: bool = True
) -> str:
    """
    Format a list of tags in the specified style.
    
    Task: tsk_1e88842d - Tree Structure Validation
    dohcount: 1
    
    Args:
        tags: List of tag strings
        tag_style: Style for tag display ('colored', 'brackets', 'hash')
        indent: Indentation string to prepend
        colorize_output: Whether to use colors for tags
        
    Returns:
        Formatted tags string
    """
    if not tags:
        return ""
        
    # Import colors if needed
    if colorize_output and tag_style == "colored":
        try:
            from refactor.utils.colors import TextColor, colorize
            color_map = {
                # High priority tags
                "blocker": TextColor.BRIGHT_RED,
                "critical": TextColor.BRIGHT_RED,
                "urgent": TextColor.BRIGHT_RED,
                "high-priority": TextColor.BRIGHT_RED,
                
                # Medium priority tags
                "medium-priority": TextColor.YELLOW,
                "moderate": TextColor.YELLOW,
                "important": TextColor.YELLOW,
                
                # Low priority tags
                "low-priority": TextColor.GREEN,
                "minor": TextColor.GREEN,
                
                # Status tags
                "blocked": TextColor.RED,
                "in-progress": TextColor.BLUE,
                "ready": TextColor.GREEN,
                "approved": TextColor.GREEN,
                "review": TextColor.CYAN,
                "testing": TextColor.MAGENTA,
                
                # Type tags
                "bug": TextColor.BRIGHT_RED,
                "feature": TextColor.BRIGHT_GREEN,
                "enhancement": TextColor.BRIGHT_CYAN,
                "refactor": TextColor.BRIGHT_YELLOW,
                "documentation": TextColor.BRIGHT_BLUE,
                "ui": TextColor.BRIGHT_MAGENTA,
                "api": TextColor.CYAN,
                "backend": TextColor.BLUE,
                "frontend": TextColor.MAGENTA,
                
                # Component tags - custom colors for each component
                "core": TextColor.BRIGHT_WHITE,
                "cli": TextColor.BRIGHT_CYAN,
                "dashboard": TextColor.BRIGHT_MAGENTA,
                "storage": TextColor.BRIGHT_YELLOW,
                "utils": TextColor.BRIGHT_GREEN,
                "plugins": TextColor.BRIGHT_BLUE,
                "display": TextColor.CYAN,
                
                # Other tags - default color
                "default": TextColor.WHITE
            }
        except ImportError:
            # Fall back to brackets if colors aren't available
            tag_style = "brackets"
    
    # Format each tag based on style
    formatted_tags = []
    
    for tag in tags:
        if tag_style == "colored" and colorize_output:
            from refactor.utils.colors import TextColor, colorize
            # Get color for this tag or default color
            color = color_map.get(tag.lower(), color_map["default"])
            formatted_tags.append(f"[{colorize(tag, color)}]")
        elif tag_style == "brackets":
            formatted_tags.append(f"[{tag}]")
        elif tag_style == "hash":
            formatted_tags.append(f"#{tag}")
        else:
            # Default to brackets if style not recognized
            formatted_tags.append(f"[{tag}]")
    
    # Join tags with spaces and prepend emoji
    tag_result = f"{TAG_EMOJI} {' '.join(formatted_tags)}"
    
    # Add indentation if provided
    if indent:
        tag_result = f"{indent}{tag_result}"
        
    return tag_result

def format_tag_line(
    tags: List[str],
    tag_style: str = "colored",
    indent: str = "",
    colorize_output: bool = True,
    is_last: bool = True
) -> str:
    """
    Format tags as a separate line with proper indentation for tree displays.
    
    Task: tsk_1e88842d - Tree Structure Validation
    dohcount: 1
    
    Args:
        tags: List of tag strings
        tag_style: Style for tag display
        indent: Base indentation for the parent task
        colorize_output: Whether to use colors
        is_last: Whether this is the last item at its level
        
    Returns:
        Formatted tag line with proper indentation
    """
    if not tags:
        return ""
    
    # Calculate tag line indent (should align with subtask level)
    # Add two spaces or vertical pipe + space depending on if last
    tag_indent = indent + ("  " if is_last else "│ ")
    
    # Format tags and add indentation
    return format_tags(tags, tag_style, tag_indent, colorize_output) 