"""
Init Command Module for ClickUp JSON Manager

This module implements the 'init' command to create a new template file with a basic structure.

Task: tsk_init_template - Initialize Template Structure
"""

import os
import json
import logging
import argparse
import uuid
from datetime import datetime
from pathlib import Path
from typing import Dict, Any, List, Optional

from refactor.cli.commands.base import SimpleCommand
from refactor.cli.error_handling import handle_cli_error
from refactor.utils.colors import colorize, TextColor
from refactor.utils.template_finder import create_project_directory
from refactor.cli.commands.project_templates import get_template, get_template_names, TEMPLATES

logger = logging.getLogger(__name__)


class InitCommand(SimpleCommand):
    """Command to initialize a new project template with a basic structure."""
    
    def __init__(self, core_manager=None):
        """Initialize the init command.
        
        Args:
            core_manager: Core manager instance
        """
        super().__init__("init", "Initialize a new project template with spaces, folders, and lists", core_manager)
    
    def configure_parser(self, parser):
        """Configure command line parser for the init command.
        
        Args:
            parser: ArgumentParser instance to configure
        """
        # Create a template group for template options
        template_group = parser.add_argument_group('template options')
        
        template_source = parser.add_mutually_exclusive_group()
        template_source.add_argument(
            "--template",
            help=f"Use a predefined template structure (options: {', '.join(get_template_names())})",
            choices=get_template_names(),
            type=str,
        )
        template_source.add_argument(
            "--custom",
            help="Create a custom template with specified number of spaces, folders, and lists",
            action="store_true",
        )
        
        parser.add_argument(
            "--name",
            help="Project name to use in the template",
            default="ClickUp Project",
            type=str,
        )
        
        # Custom template options
        template_group.add_argument(
            "--spaces",
            help="Number of spaces to create (for custom template)",
            default=1,
            type=int,
        )
        template_group.add_argument(
            "--folders-per-space",
            help="Number of folders to create per space (for custom template)",
            default=2,
            type=int,
        )
        template_group.add_argument(
            "--lists-per-folder",
            help="Number of lists to create per folder (for custom template)",
            default=2,
            type=int,
        )
        
        # Output options
        parser.add_argument(
            "--output",
            help="Output file path for the generated template",
            default=".project/clickup_tasks.json",
            type=str,
        )
        parser.add_argument(
            "--force",
            help="Overwrite existing template file if it exists",
            action="store_true",
        )
        parser.add_argument(
            "--list-templates",
            help="List available predefined templates",
            action="store_true",
        )
        
    def execute(self, args):
        """Execute the init command.
        
        Args:
            args: Command arguments
            
        Returns:
            int: Return code
        """
        # Handle listing available templates
        if args.list_templates:
            self._list_templates()
            return 0
            
        logger.debug(f"Creating project template with name: {args.name}")
        
        # Create output directory if it doesn't exist
        output_dir = os.path.dirname(args.output)
        if output_dir and not os.path.exists(output_dir):
            if output_dir == ".project":
                create_project_directory()
            else:
                os.makedirs(output_dir)
        
        # Check if output file exists and --force is not specified
        if os.path.exists(args.output) and not args.force:
            print(f"Error: Output file {args.output} already exists. Use --force to overwrite.")
            return 1
        
        # Create template structure
        if args.template:
            template = self._create_from_predefined_template(args.template, args.name)
            template_type = f"predefined '{args.template}'"
        else:
            template = self._create_custom_template(
                args.name,
                args.spaces,
                args.folders_per_space,
                args.lists_per_folder,
            )
            template_type = "custom"
        
        # Save template to file
        with open(args.output, "w") as f:
            json.dump(template, f, indent=2)
        
        print(f"Template created at {args.output} using {template_type} structure")
        print(f"You can now use this template with other commands, e.g.:")
        print(f"  ./cujm list {args.output} --tree")
        
        return 0
    
    def _list_templates(self):
        """List all available predefined templates."""
        print("\nAvailable predefined templates:\n")
        for name, template in TEMPLATES.items():
            space_count = len(template["spaces"])
            print(f"  {colorize(name, TextColor.CYAN)}: {template['name']} ({space_count} spaces)")
            
            # Show first 2 spaces for each template as a preview
            for i, space in enumerate(template["spaces"][:2]):
                print(f"    ├─ {colorize(space['name'], TextColor.GREEN)}")
                
                # Show a sample of folders
                if "folders" in space:
                    for j, folder in enumerate(space["folders"][:2]):
                        is_last_folder = j == len(space["folders"][:2]) - 1 and i == len(template["spaces"][:2]) - 1
                        folder_prefix = "    │  └─" if is_last_folder else "    │  ├─"
                        print(f"{folder_prefix} {folder['name']}")
                        
                        # Show a sample of lists
                        if "lists" in folder:
                            for k, lst in enumerate(folder["lists"][:2]):
                                is_last_list = k == len(folder["lists"][:2]) - 1
                                list_prefix = "    │     └─" if is_last_list else "    │     ├─"
                                print(f"{list_prefix} {lst['name']}")
                            
                            # Show ellipsis if there are more lists
                            if len(folder["lists"]) > 2:
                                print(f"    │     └─ ...")
            
            # Show ellipsis if there are more spaces
            if len(template["spaces"]) > 2:
                print(f"    └─ ...")
            print()
        
        print(f"Use --template NAME to create a project with one of these templates.")
        print(f"Example: ./cujm init --template simple --output my_project.json")
    
    def _create_from_predefined_template(self, template_name, project_name):
        """Create a template from a predefined structure.
        
        Args:
            template_name: Name of predefined template to use
            project_name: Name to use for the project
            
        Returns:
            dict: Template structure
        """
        template_data = get_template(template_name)
        
        # Base structure
        template = {
            "name": project_name,
            "description": f"Project based on {template_data['name']} template, created on {datetime.now().strftime('%Y-%m-%d')}",
            "spaces": [],
            "folders": [],
            "lists": [],
            "tasks": [],
            "tags": [],
            "version": "1.0"
        }
        
        # Create spaces, folders, and lists based on template
        for i, space_template in enumerate(template_data["spaces"]):
            space_id = f"space_{uuid.uuid4().hex[:8]}"
            space = {
                "id": space_id,
                "name": space_template["name"],
                "color": self._get_color_for_index(i)
            }
            template["spaces"].append(space)
            
            # Create folders for this space
            for j, folder_template in enumerate(space_template.get("folders", [])):
                folder_id = f"folder_{uuid.uuid4().hex[:8]}"
                folder = {
                    "id": folder_id,
                    "name": folder_template["name"],
                    "space_id": space_id
                }
                template["folders"].append(folder)
                
                # Create lists for this folder
                for k, list_template in enumerate(folder_template.get("lists", [])):
                    list_id = f"list_{uuid.uuid4().hex[:8]}"
                    task_list = {
                        "id": list_id,
                        "name": list_template["name"],
                        "folder_id": folder_id
                    }
                    template["lists"].append(task_list)
                    
                    # Create a sample task in each list
                    task_id = f"task_{uuid.uuid4().hex[:8]}"
                    task = {
                        "id": task_id,
                        "name": f"Sample task in {space_template['name']} - {folder_template['name']} - {list_template['name']}",
                        "description": "This is a sample task created by the init command",
                        "status": "to do",
                        "priority": 3,
                        "assignees": [],
                        "tags": [],
                        "due_date": None,
                        "time_estimate": None,
                        "list_id": list_id,
                        "task_type": "task"
                    }
                    template["tasks"].append(task)
        
        return template
    
    def _create_custom_template(self, name, num_spaces, folders_per_space, lists_per_folder):
        """Create a custom template structure with the specified hierarchy.
        
        Args:
            name: Project name
            num_spaces: Number of spaces to create
            folders_per_space: Number of folders per space
            lists_per_folder: Number of lists per folder
            
        Returns:
            dict: Template structure
        """
        template = {
            "name": name,
            "description": f"Custom project template created on {datetime.now().strftime('%Y-%m-%d')}",
            "spaces": [],
            "folders": [],
            "lists": [],
            "tasks": [],
            "tags": [],
            "version": "1.0"
        }
        
        # Create spaces
        for i in range(1, num_spaces + 1):
            space_id = f"space_{uuid.uuid4().hex[:8]}"
            space = {
                "id": space_id,
                "name": f"Space {i}",
                "color": self._get_color_for_index(i-1)
            }
            template["spaces"].append(space)
            
            # Create folders for this space
            for j in range(1, folders_per_space + 1):
                folder_id = f"folder_{uuid.uuid4().hex[:8]}"
                folder = {
                    "id": folder_id,
                    "name": f"Folder {j}",
                    "space_id": space_id
                }
                template["folders"].append(folder)
                
                # Create lists for this folder
                for k in range(1, lists_per_folder + 1):
                    list_id = f"list_{uuid.uuid4().hex[:8]}"
                    task_list = {
                        "id": list_id,
                        "name": f"List {k}",
                        "folder_id": folder_id
                    }
                    template["lists"].append(task_list)
                    
                    # Create a sample task in each list
                    task_id = f"task_{uuid.uuid4().hex[:8]}"
                    task = {
                        "id": task_id,
                        "name": f"Sample task in Space {i} - Folder {j} - List {k}",
                        "description": "This is a sample task created by the init command",
                        "status": "to do",
                        "priority": 3,
                        "assignees": [],
                        "tags": [],
                        "due_date": None,
                        "time_estimate": None,
                        "list_id": list_id,
                        "task_type": "task"
                    }
                    template["tasks"].append(task)
        
        return template
    
    def _get_color_for_index(self, index: int) -> str:
        """
        Get a color for the given index.
        
        Args:
            index: Index to get color for
            
        Returns:
            Color string
        """
        colors = ["#7B68EE", "#3498DB", "#2ECC71", "#F1C40F", "#E74C3C", 
                  "#9B59B6", "#1ABC9C", "#F39C12", "#D35400", "#C0392B"]
        return colors[index % len(colors)] 