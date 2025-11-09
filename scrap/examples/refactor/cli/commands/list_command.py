"""
List Command Module for ClickUp JSON Manager

This module implements the 'list' command to display tasks and other entities.

Task: tsk_1e88842d - Tree Structure Validation
dohcount: 3

Changes:
- v3: Added multi-attribute display with new --show argument
- v4: Added support for default template in .project directory
"""

from typing import List, Dict, Any, Optional
import argparse
import json
import sys
import os
import re

from refactor.core.core_manager import CoreManager
from refactor.utils.config import Config
from refactor.cli.commands.base_command import BaseCommand
from refactor.cli.formatters import format_output
from refactor.utils.colors import colorize, TextColor, TextStyle
from refactor.utils.template_finder import get_template_path

class ListCommand(BaseCommand):
    """Command to list tasks in a template file with various display options."""
    
    def get_parser(self, subparsers):
        """
        Create the parser for the 'list' command.
        
        Args:
            subparsers: Subparsers object from argparse
            
        Returns:
            Parser for the 'list' command
        """
        parser = subparsers.add_parser(
            'list',
            help='List all tasks in a template file'
        )
        
        # Optional template file argument
        parser.add_argument(
            'template_file',
            nargs='?',
            help='Path to the template file (defaults to .project/clickup_tasks.json if exists)'
        )
        
        # Optional arguments
        parser.add_argument(
            '--tree',
            action='store_true',
            help='Display tasks in a tree structure'
        )
        
        parser.add_argument(
            '--organize-by-container',
            action='store_true',
            help='Organize tasks by their container (space, folder, list)'
        )
        
        parser.add_argument(
            '--filter',
            help='Filter tasks by name, use quotation marks'
        )
        
        parser.add_argument(
            '--status',
            help='Filter tasks by status'
        )
        
        parser.add_argument(
            '--include-completed',
            action='store_true',
            help='Include completed tasks in the output'
        )
        
        parser.add_argument(
            '--hide-orphaned',
            action='store_true',
            help='Hide orphaned tasks when using organize-by-container'
        )
        
        parser.add_argument(
            '--assignee',
            help='Filter tasks by assignee name'
        )
        
        parser.add_argument(
            '--tags',
            nargs='+',
            help='Filter tasks by tags (can provide multiple tags)'
        )
        
        parser.add_argument(
            '--color',
            action='store_true',
            default=None,
            help='Enable colorized output'
        )
        
        parser.add_argument(
            '--no-color',
            action='store_true',
            help='Disable colorized output'
        )
        
        parser.add_argument(
            '--json',
            action='store_true',
            help='Output in JSON format'
        )
        
        # Display options - legacy arguments
        parser.add_argument(
            '--show-tags',
            action='store_true',
            help='[DEPRECATED] Display task tags. Use --show tags instead.'
        )
        
        parser.add_argument(
            '--tag-style',
            choices=['colored', 'plain', 'emoji'],
            default='colored',
            help='Style for displaying tags'
        )
        
        parser.add_argument(
            '--show-score',
            action='store_true',
            help='[DEPRECATED] Display task scores. Use --show scores instead.'
        )
        
        # New multi-attribute display option
        parser.add_argument(
            '--show',
            nargs='+',
            choices=['tags', 'descriptions', 'comments', 'dates', 'scores', 'ids', 'all'],
            help='Display additional task attributes (can provide multiple attributes)'
        )
        
        parser.add_argument(
            '--sort-by',
            choices=['name', 'status', 'priority', 'created', 'updated'],
            default='priority',
            help='Sort tasks by this field'
        )
        
        parser.add_argument(
            '--reverse',
            action='store_true',
            help='Reverse the sort order'
        )
        
        # New parameter for displaying ID in square brackets with the task name
        parser.add_argument(
            '--show-id',
            action='store_true',
            help='Display task IDs in square brackets'
        )
        
        parser.add_argument(
            '--ids-only',
            action='store_true',
            help='Display only task IDs'
        )
        
        parser.add_argument(
            '--names-only',
            action='store_true',
            help='Display only task names'
        )
        
        return parser
    
    def execute(self, args):
        """
        Execute the 'list' command with the given arguments.
        
        Args:
            args: Parsed arguments
            
        Returns:
            Command execution result
        """
        # Find the template file to use
        template_file = get_template_path(args.template_file)
        
        if not template_file:
            print("Error: No template file specified and no default template found.", file=sys.stderr)
            print("Please specify a template file or run './cujm init' to create a default template.", file=sys.stderr)
            return 1
        
        # Load the template file
        try:
            with open(template_file, 'r', encoding='utf-8') as f:
                template_data = json.load(f)
        except Exception as e:
            print(f"Error: {e}", file=sys.stderr)
            return 1
        
        # Create a core manager instance for accessing the data
        core_manager = CoreManager()
        core_manager.load_data(template_data)
        
        # Get the tasks from the template data
        tasks = template_data.get('tasks', [])
        
        # Process the display flags to set appropriate display options
        show_tags = True  # Default to showing tags
        if hasattr(args, 'show_tags'):
            show_tags = args.show_tags
            
        show_score = args.show_score if hasattr(args, 'show_score') else False
        show_descriptions = False
        show_comments = 0
        show_dates = False
        show_ids = args.show_id if hasattr(args, 'show_id') else False
        
        # Handle the new --show argument
        if hasattr(args, 'show') and args.show:
            if 'all' in args.show:
                show_tags = True
                show_score = True
                show_descriptions = True
                show_comments = 3  # Show up to 3 comments
                show_dates = True
                show_ids = True
            else:
                if 'tags' in args.show:
                    show_tags = True
                if 'scores' in args.show:
                    show_score = True
                if 'descriptions' in args.show:
                    show_descriptions = True
                if 'comments' in args.show:
                    show_comments = 3  # Show up to 3 comments
                if 'dates' in args.show:
                    show_dates = True
                if 'ids' in args.show:
                    show_ids = True
        
        # Apply filters
        if args.filter:
            tasks = [t for t in tasks if re.search(args.filter, t.get('name', ''), re.IGNORECASE)]
        
        if args.status:
            tasks = [t for t in tasks if t.get('status', '').lower() == args.status.lower()]
        
        if not args.include_completed:
            tasks = [t for t in tasks if t.get('status', '').lower() != 'complete']
        
        if args.assignee:
            tasks = [t for t in tasks if args.assignee.lower() in [a.lower() for a in t.get('assignees', [])]]
        
        if args.tags:
            tasks = [
                t for t in tasks 
                if set([tag.lower() for tag in args.tags]).issubset(
                    set([tag.lower() for tag in t.get('tags', [])])
                )
            ]
        
        # Determine colorization preference
        colorize_output = True
        if hasattr(args, 'no_color') and args.no_color:
            colorize_output = False
        elif hasattr(args, 'color') and args.color is not None:
            colorize_output = args.color
        elif 'NO_COLOR' in os.environ:
            colorize_output = False
        
        # Format and display tasks
        if args.json:
            # JSON output
            print(json.dumps(tasks, indent=2))
        elif args.ids_only:
            # IDs only
            for task in tasks:
                print(task.get('id', ''))
        elif args.names_only:
            # Names only
            for task in tasks:
                print(task.get('name', ''))
        elif args.tree:
            # Tree display
            if args.organize_by_container:
                from refactor.cli.formatting.tree.container import format_container_hierarchy
                
                result = format_container_hierarchy(
                    tasks=tasks,
                    colorize_output=colorize_output,
                    include_completed=args.include_completed,
                    hide_orphaned=getattr(args, 'hide_orphaned', False),
                    show_score=show_score,
                    show_tags=show_tags,
                    tag_style=args.tag_style,
                    show_ids=show_ids,
                    show_descriptions=show_descriptions,
                    show_dates=show_dates,
                    show_comments=show_comments
                )
            else:
                from refactor.cli.formatting.tree.hierarchy import format_task_hierarchy
                
                result = format_task_hierarchy(
                    tasks=tasks,
                    colorize_output=colorize_output,
                    show_score=show_score,
                    show_tags=show_tags,
                    tag_style=args.tag_style,
                    show_ids=show_ids,
                    show_descriptions=show_descriptions,
                    show_dates=show_dates,
                    show_comments=show_comments,
                    organize_by_container=args.organize_by_container
                )
            print(result)
        else:
            # Flat list display
            for task in tasks:
                task_id = task.get('id', '')
                task_name = task.get('name', '')
                task_status = task.get('status', '')
                
                # Format the task line
                if colorize_output:
                    status_color = TextColor.GREEN if task_status.lower() == 'complete' else TextColor.YELLOW
                    line = f"{task_id}: {colorize(task_name, status_color)}"
                else:
                    line = f"{task_id}: {task_name}"
                
                print(line)
                
                # Add tags if requested
                if show_tags and task.get('tags'):
                    tags_str = ', '.join(task.get('tags', []))
                    if colorize_output:
                        print(f"  Tags: {colorize(tags_str, TextColor.BLUE)}")
                    else:
                        print(f"  Tags: {tags_str}")
                
                # Add descriptions if requested
                if show_descriptions and task.get('description'):
                    desc = task.get('description', '').strip()
                    if desc:
                        print(f"  Description: {desc[:80]}{'...' if len(desc) > 80 else ''}")
        
        return 0 