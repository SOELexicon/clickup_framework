"""
Display Options Module

This module handles the processing and validation of display options
for task formatting and visualization.

Task: tsk_1e88842d - Tree Structure Validation
dohcount: 1
"""

from typing import Dict, Any, List, Optional, Set
import logging

# Configure logger
logger = logging.getLogger(__name__)

class DisplayOptions:
    """Class to handle task display options and processing."""
    
    def __init__(self, 
                 args: Optional[Any] = None,
                 show_tags: bool = False,
                 show_score: bool = False,
                 show_descriptions: bool = False,
                 show_comments: int = 0,
                 show_dates: bool = False,
                 show_ids: bool = False,
                 show_priority: bool = True,
                 show_type_emoji: bool = True,
                 tag_style: str = "colored",
                 colorize_output: bool = True):
        """
        Initialize display options for task rendering.
        
        Args:
            args: Optional arguments object to process
            show_tags: Whether to show task tags
            show_score: Whether to show task scores
            show_descriptions: Whether to show task descriptions
            show_comments: Number of comments to show (0 for none)
            show_dates: Whether to show dates (created, updated)
            show_ids: Whether to show task IDs
            show_priority: Whether to show task priority
            show_type_emoji: Whether to show task type emoji
            tag_style: Style for tag display ('colored', 'plain', 'emoji')
            colorize_output: Whether to use colors in output
        """
        # Initialize with default values
        self.show_tags = show_tags
        self.show_score = show_score
        self.show_descriptions = show_descriptions
        self.show_comments = show_comments
        self.show_dates = show_dates
        self.show_ids = show_ids
        self.show_priority = show_priority
        self.show_type_emoji = show_type_emoji
        self.tag_style = tag_style
        self.colorize_output = colorize_output
        
        # Process args if provided
        if args:
            self.process_args(args)
    
    def process_args(self, args: Any) -> None:
        """
        Process command-line arguments into display options.
        
        Args:
            args: Arguments object from argparse
        """
        # Handle legacy arguments
        if hasattr(args, 'show_tags'):
            self.show_tags = args.show_tags
            
        if hasattr(args, 'show_score'):
            self.show_score = args.show_score
            
        if hasattr(args, 'tag_style'):
            self.tag_style = args.tag_style
            
        if hasattr(args, 'show_type_emoji'):
            self.show_type_emoji = args.show_type_emoji
        
        # Check for IDs display settings
        if hasattr(args, 'ids_only') and args.ids_only:
            self.show_ids = True
        elif hasattr(args, 'show_id'):
            self.show_ids = args.show_id
        elif hasattr(args, 'show_ids'):
            self.show_ids = args.show_ids
            
        # Process colorization settings
        if hasattr(args, 'no_color') and args.no_color:
            self.colorize_output = False
        elif hasattr(args, 'color') and args.color is not None:
            self.colorize_output = args.color
            
        # Process descriptions display
        if hasattr(args, 'show_descriptions'):
            self.show_descriptions = args.show_descriptions
            
        # Process comments display
        if hasattr(args, 'show_comments'):
            self.show_comments = args.show_comments
            
        # Process dates display
        if hasattr(args, 'show_dates'):
            self.show_dates = args.show_dates
            
        # Process priority display
        if hasattr(args, 'show_priority'):
            self.show_priority = args.show_priority
        
        # Process the multi-attribute display option
        if hasattr(args, 'display_attrs') and args.display_attrs:
            self._process_display_attributes(args.display_attrs)
    
    def _process_display_attributes(self, attrs: List[str]) -> None:
        """
        Process multi-attribute display options.
        
        Args:
            attrs: List of display attributes to enable
        """
        if 'all' in attrs:
            # Enable all display options
            self.show_tags = True
            self.show_score = True
            self.show_descriptions = True
            self.show_comments = 3  # Show up to 3 comments
            self.show_dates = True
            self.show_ids = True
            self.show_priority = True
            return
            
        # Process individual attributes
        if 'tags' in attrs:
            self.show_tags = True
        if 'scores' in attrs or 'score' in attrs:
            self.show_score = True
        if 'descriptions' in attrs or 'description' in attrs:
            self.show_descriptions = True
        if 'comments' in attrs or 'comment' in attrs:
            self.show_comments = 3  # Show up to 3 comments
        if 'dates' in attrs or 'date' in attrs:
            self.show_dates = True
        if 'ids' in attrs or 'id' in attrs:
            self.show_ids = True
        if 'priority' in attrs:
            self.show_priority = True
    
    def as_dict(self) -> Dict[str, Any]:
        """
        Get display options as a dictionary for passing to formatting functions.
        
        Returns:
            Dictionary of display options
        """
        return {
            'show_tags': self.show_tags,
            'show_score': self.show_score,
            'show_descriptions': self.show_descriptions,
            'show_comments': self.show_comments,
            'show_dates': self.show_dates,
            'show_ids': self.show_ids,
            'show_priority': self.show_priority,
            'show_type_emoji': self.show_type_emoji,
            'tag_style': self.tag_style,
            'colorize_output': self.colorize_output
        }


def process_display_options(args: Any) -> DisplayOptions:
    """
    Process display options from command-line arguments.
    
    Args:
        args: Command-line arguments
        
    Returns:
        DisplayOptions object with processed settings
    """
    return DisplayOptions(args) 