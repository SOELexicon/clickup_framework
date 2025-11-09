"""
Tree Validation Module

This module provides functions for validating and fixing tree structure formatting.

Task: tsk_1e88842d - Tree Structure Validation
dohcount: 1
"""

from typing import List, Dict, Any, Optional, Set, Tuple
import logging
import re

# Add tag emoji reference
TAG_EMOJI = "🏷️"

def validate_tree_structure(tree_lines: List[str]) -> Tuple[bool, List[str]]:
    """
    Validates the consistency of the tree structure,
    particularly focusing on vertical pipe characters.
    
    Task: tsk_fa92b435 - Tree Structure Validation
    dohcount: 3
    
    Parameters:
        tree_lines: List of rendered tree lines
    
    Returns:
        Tuple of (is_valid, error_messages)
    """
    errors = []
    pipe_positions = {}
    
    # First pass: Find expected pipe positions
    for i, line in enumerate(tree_lines):
        # Skip empty lines
        if not isinstance(line, str) or not line.strip():
            continue
            
        # Skip tag lines from validation requirements
        if TAG_EMOJI in line and line.strip().startswith(TAG_EMOJI):
            continue
            
        # Track indent level and pipe positions
        indent_level = 0
        j = 0
        while j < len(line):
            char = line[j]
            
            if char == '│':
                if indent_level not in pipe_positions:
                    pipe_positions[indent_level] = set()
                pipe_positions[indent_level].add(j)
                j += 1  # Move past the pipe
            elif char in ('├', '└'):
                # This position indicates a branch, which means
                # there should be pipes at this position in other lines
                if indent_level not in pipe_positions:
                    pipe_positions[indent_level] = set()
                pipe_positions[indent_level].add(j)
                
                # Next level's indentation starts after branch character
                indent_level += 1
                j += 2  # Skip the branch character and the dash
            else:
                j += 1  # Move to next character
    
    # Second pass: Verify pipe consistency
    for i, line in enumerate(tree_lines):
        if not isinstance(line, str) or not line.strip():
            continue
            
        # Skip tag lines from validation
        if TAG_EMOJI in line and line.strip().startswith(TAG_EMOJI):
            continue
            
        # Check each level's pipe positions
        for level, positions in sorted(pipe_positions.items()):
            for pos in sorted(positions):
                # Skip if position is beyond this line
                if pos >= len(line):
                    continue
                    
                # If we expect a pipe at this position
                expected_chars = ('│', '├', '└', ' ')
                
                # Check if the character is not a pipe or branch and it should be
                if (line[pos] not in expected_chars and 
                    # Only validate if this line should have a pipe at this position
                    # based on its indentation level and structure
                    _should_have_pipe_at_position(line, pos, level)):
                    errors.append(f"Line {i+1}: Expected vertical pipe or branch at position {pos+1}, found '{line[pos]}'")
    
    return len(errors) == 0, errors

def _should_have_pipe_at_position(line: str, pos: int, level: int) -> bool:
    """
    Determines if a line should have a pipe character at a specific position
    based on the line's structure and indentation level.
    
    Task: tsk_fa92b435 - Tree Structure Validation
    dohcount: 3
    
    Parameters:
        line: The line to check
        pos: The position to check for a pipe
        level: The indentation level
    
    Returns:
        True if the line should have a pipe at the position, False otherwise
    """
    # Skip if position is at the beginning of the line or beyond the end
    if pos <= 0 or pos >= len(line):
        return False
    
    # Content display indicators (descriptions, relationships, comments, tags)
    content_display_indicators = ['📝', '🔄', '💬', TAG_EMOJI]
    
    # Get the stripped content to check for indicators
    line_content = line.strip()
    
    # Count leading spaces to determine this line's level
    leading_spaces = len(line) - len(line.lstrip())
    line_level = leading_spaces // 2  # Assuming 2-space indentation
    
    # Check if this is a continued line from multiline content (no emoji indicator but deeply indented)
    is_continued_line = False
    
    # Look for patterns that suggest this is a continuation line from a multiline comment/description
    # Typically these have extra indentation without content indicators
    if leading_spaces > 0 and all(indicator not in line for indicator in content_display_indicators):
        # Check if indentation is deeper than normal tree indentation pattern
        # Continuation lines have additional indentation beyond the normal pattern
        if leading_spaces % 2 != 0 or leading_spaces >= 6:  # Either odd spacing or very deep indent
            is_continued_line = True
        # Check if line contains typical content found in comment sections
        elif any(marker in line for marker in ["From:", "─────", "  ∟", "  -"]):
            is_continued_line = True
    
    if is_continued_line:
        # For content continuation lines, follow the same pipe rules as their parent
        # Just check valid pipe positions for the base levels
        parent_level = max(1, leading_spaces // 2)  # Estimate parent level from continuation indent
        
        # Only want pipes at even positions (0, 2, 4...)
        if pos % 2 != 0:
            return False
            
        # Only draw pipes for levels before the parent level
        if level >= parent_level:
            return False
            
        # Check if this position corresponds to a valid pipe position at this level
        pipe_pos_for_level = level * 2
        if pos != pipe_pos_for_level:
            return False
            
        # Make sure the position has proper spacing around it
        has_space_after = (pos < len(line)-1 and line[pos+1] == ' ')
        
        # Special case for end of line
        if pos == len(line)-1:
            has_space_after = True
            
        return has_space_after
    
    # For content display lines (indicated by emoji at start of content),
    # they should follow the same pipe structure as their parent line
    is_content_display_line = False
    
    # More robust content line detection
    first_indicator_pos = -1
    
    # Check each indicator more carefully
    for indicator in content_display_indicators:
        indicator_pos = line.find(indicator)
        
        # Skip if indicator not found
        if indicator_pos == -1:
            continue
            
        # Check if this is a properly positioned indicator
        if line_content.startswith(indicator) or (
            indicator_pos > 0 and 
            # Ensure there's a space or tree character before the indicator
            (line[indicator_pos-1] == ' ' or 
             line[indicator_pos-1] in ['│', '├', '└', '─'])
        ):
            is_content_display_line = True
            first_indicator_pos = indicator_pos
            break
    
    if is_content_display_line:
        # For content display lines in any mode
        
        # First check: Pipes should be at even positions only (0, 2, 4, etc.)
        if pos % 2 != 0:
            return False
        
        # If we have found the indicator position, use it to determine parent level
        if first_indicator_pos != -1:
            # Only draw pipes before the indicator
            if pos >= first_indicator_pos:
                return False
                
            # Calculate the parent level based on indicator position
            # The parent level is determined by how far the indicator is indented
            parent_level = max(0, (first_indicator_pos // 2))
            
            # We need pipes at all levels up to the parent's level
            # Check if this position corresponds to a valid pipe position at this level
            pipe_pos_for_level = level * 2
            
            # For all content display lines, ensure pipes appear at all levels before the content
            return pos == pipe_pos_for_level and level < parent_level
        
        # If we couldn't determine the indicator position (unlikely but possible),
        # fall back to using the indentation level
        parent_level = leading_spaces // 2
        
        # Only check levels before the parent's level
        if level >= parent_level:
            return False
            
        # Check if this position corresponds to a valid pipe position at this level
        pipe_pos_for_level = level * 2
        return pos == pipe_pos_for_level
    
    # Special case for content lines that might not have emoji indicators
    # Check for common patterns in content display without emoji
    if any(marker in line_content for marker in ["Recent Comments:", "From:", "Description:", "|", ">"]):
        # Only check for pipes at even positions
        if pos % 2 != 0:
            return False
        
        # Calculate parent level based on indentation
        parent_level = max(1, leading_spaces // 2)
        
        # Only allow pipes for levels before the parent
        if level >= parent_level:
            return False
        
        # Check position matches the level
        pipe_pos_for_level = level * 2
        if pos != pipe_pos_for_level:
            return False
        
        # Verify spacing
        has_space_after = (pos < len(line)-1 and line[pos+1] == ' ')
        if pos == len(line)-1:
            has_space_after = True
            
        return has_space_after
    
    # For regular tree nodes (not content display lines)
    
    # Only expect pipes for levels that this line should display
    if level >= line_level:
        return False
    
    # Check if the character is within a properly indented section
    # Pipes should appear at positions 0, 2, 4, etc.
    if pos % 2 != 0:
        return False
    
    # Make sure this position corresponds to the expected pipe position for this level
    if pos != level * 2:
        return False
    
    # Check surrounding characters
    # Pipes typically have spaces before/after them in tree structures
    has_space_before = pos > 0 and line[pos-1] == ' '
    has_space_after = pos < len(line)-1 and line[pos+1] == ' '
    
    # Special case: line might end with a pipe
    if pos == len(line)-1:
        has_space_after = True
    
    return has_space_before and has_space_after

def fix_tree_structure(tree_output: str) -> str:
    """
    Attempt to fix the tree structure by correcting vertical pipe character
    alignment and connections.
    
    Task: tsk_fa92b435 - Tree Structure Validation
    dohcount: 2
    
    Parameters:
        tree_output: The tree output to fix
    
    Returns:
        The fixed tree output
    """
    lines = tree_output.split('\n')
    if not lines:
        return tree_output
    
    # Process line by line
    fixed_lines = []
    
    # Track the positions where we should have pipes for each line
    # This maps line index -> set of positions requiring pipes
    line_pipe_positions = {}
    
    # First pass: collect expected pipe positions and identify line types
    line_types = {}  # Maps line index -> "content", "node", or "continuation"
    content_parent_map = {}  # Maps content line index -> parent node line index
    
    # Track the last non-content line and content line
    last_node_line_idx = -1
    last_content_line_idx = -1
    
    # Content display indicators
    content_display_indicators = ['📝', '🔄', '💬', TAG_EMOJI]
    
    for i, line in enumerate(lines):
        # Skip empty lines
        if not line.strip():
            fixed_lines.append(line)
            continue
        
        # Get leading spaces to determine indentation level
        leading_spaces = len(line) - len(line.lstrip())
        
        # Check if this is a continuation of a multiline comment/description
        # Continuation lines have deeper indentation and no content indicators
        is_continuation = False
        if last_content_line_idx >= 0 and all(indicator not in line for indicator in content_display_indicators):
            # Check if indentation suggests this is a continuation
            # Typically 6+ spaces or odd number of spaces indicating special indentation
            if leading_spaces % 2 != 0 or leading_spaces >= 6:
                is_continuation = True
        
        if is_continuation:
            line_types[i] = "continuation"
            # Link this continuation to the previous content line
            content_parent_map[i] = content_parent_map.get(last_content_line_idx, last_node_line_idx)
            fixed_lines.append(line)
            continue
        
        # Check if this is a content display line
        is_content_line = False
        for indicator in content_display_indicators:
            if indicator in line and (
                line.strip().startswith(indicator) or
                (line.find(indicator) > 0 and line[line.find(indicator)-1] == ' ')
            ):
                is_content_line = True
                break
        
        if is_content_line:
            line_types[i] = "content"
            last_content_line_idx = i
            # Link this content line to the most recent node line
            if last_node_line_idx >= 0:
                content_parent_map[i] = last_node_line_idx
            fixed_lines.append(line)
            continue
        
        # This is a regular node line
        line_types[i] = "node"
        last_node_line_idx = i
        last_content_line_idx = -1  # Reset content line tracking
        
        # Calculate the level based on indentation
        level = leading_spaces // 2  # Assuming 2-space indentation
        
        # For each level, record the expected pipe position
        line_pipe_positions[i] = set()
        for l in range(level):
            # Pipes appear at positions 0, 2, 4, etc.
            line_pipe_positions[i].add(l * 2)
        
        fixed_lines.append(line)
    
    # Consolidate all pipe positions across all node lines
    all_pipe_positions = set()
    for positions in line_pipe_positions.values():
        all_pipe_positions.update(positions)
    
    # If no pipe positions were found, return the original output
    if not all_pipe_positions:
        return tree_output
    
    # Second pass: fix the pipes in all lines
    for i, line in enumerate(fixed_lines):
        # Skip empty lines
        if not line.strip():
            continue
        
        line_chars = list(line)
        
        if i in line_types:
            if line_types[i] == "content":
                # This is a content line - match pipe structure with parent
                if i in content_parent_map:
                    parent_idx = content_parent_map[i]
                    parent_pipes = line_pipe_positions.get(parent_idx, set())
                    
                    # Leading spaces determine level
                    leading_spaces = len(line) - len(line.lstrip())
                    
                    # Identify the first content indicator if any
                    first_indicator_pos = -1
                    for indicator in content_display_indicators:
                        pos = line.find(indicator)
                        if pos != -1 and (first_indicator_pos == -1 or pos < first_indicator_pos):
                            first_indicator_pos = pos
                    
                    # Only fix pipes up to the content indicator
                    for pos in sorted(all_pipe_positions):
                        # Only process positions before the first indicator and within line length
                        if pos < len(line) and (first_indicator_pos == -1 or pos < first_indicator_pos):
                            # Check if this position should have a pipe based on parent structure
                            if pos in parent_pipes and pos % 2 == 0 and pos // 2 < leading_spaces // 2:
                                # Replace with pipe only if not already a tree character
                                if line[pos] not in ['│', '├', '└', '─']:
                                    line_chars[pos] = '│'
            
            elif line_types[i] == "continuation":
                # This is a continuation line - match pipe structure with its parent content line
                if i in content_parent_map:
                    parent_idx = content_parent_map[i]
                    # Get pipes from the ultimate parent (the node, not the content line)
                    while parent_idx in line_types and line_types[parent_idx] in ["content", "continuation"]:
                        if parent_idx in content_parent_map:
                            parent_idx = content_parent_map[parent_idx]
                        else:
                            break
                    
                    parent_pipes = line_pipe_positions.get(parent_idx, set())
                    
                    # For continuation lines, we need to estimate what level they're at
                    # They're typically more indented than content lines
                    leading_spaces = len(line) - len(line.lstrip())
                    estimated_parent_level = leading_spaces // 3  # Rough estimate
                    
                    # Only fix pipes up to where content might start
                    content_start = leading_spaces
                    for pos in sorted(all_pipe_positions):
                        # Only process positions before content starts and within line length
                        if pos < len(line) and pos < content_start:
                            # Only draw pipes for positions in the parent's structure
                            # and at levels below the estimated parent level
                            if pos in parent_pipes and pos % 2 == 0 and pos // 2 < estimated_parent_level:
                                # Replace with pipe only if not already a tree character
                                if line[pos] not in ['│', '├', '└', '─']:
                                    line_chars[pos] = '│'
            
            else:  # "node" type
                # For regular node lines, use the collected pipe positions
                for pos in sorted(all_pipe_positions):
                    if pos < len(line) and _should_have_pipe_at_position(line, pos, pos // 2):
                        # Replace with pipe only if not already a tree character
                        if line[pos] not in ['│', '├', '└', '─']:
                            line_chars[pos] = '│'
        
        fixed_lines[i] = ''.join(line_chars)
    
    return '\n'.join(fixed_lines) 