"""
Drop-in plugin command loader for CLI.

Each command module in this directory should define:
1. A `register_command(subparsers)` function that configures argparse
2. A `COMMAND_METADATA` dict for automatic help generation (optional but recommended)

Example command module structure:
    # Metadata for automatic help generation
    COMMAND_METADATA = {
        "category": "📊 View Commands",
        "commands": [
            {
                "name": "mycommand [alias1, alias2]",
                "args": "<arg1> [options]",
                "description": "Command description shown in help"
            }
        ]
    }

    def my_command(args):
        '''Command implementation'''
        pass

    def register_command(subparsers):
        parser = subparsers.add_parser('mycommand', aliases=['alias1', 'alias2'],
                                       help='Description')
        parser.add_argument('arg1', help='Argument 1')
        parser.set_defaults(func=my_command)
"""

import os
import importlib
import pkgutil
from pathlib import Path


def discover_commands():
    """
    Discover all command modules in this directory.

    Returns:
        List of module objects that have a register_command function
    """
    commands = []
    package_dir = Path(__file__).parent

    # Iterate through all .py files in the commands directory
    for importer, module_name, ispkg in pkgutil.iter_modules([str(package_dir)]):
        # Skip utils and private modules
        if module_name.startswith('_') or module_name == 'utils':
            continue

        try:
            # Import the module
            module = importlib.import_module(f'.{module_name}', package=__name__)

            # Check if it has a register_command function
            if hasattr(module, 'register_command'):
                commands.append(module)
        except Exception as e:
            print(f"Warning: Failed to load command module '{module_name}': {e}")

    return commands


def collect_command_metadata():
    """
    Collect COMMAND_METADATA from all command modules for help generation.

    Returns:
        dict: Dictionary mapping categories to lists of command definitions
              Format: {category: [(name, args, description), ...]}
    """
    from collections import defaultdict

    metadata_by_category = defaultdict(list)
    commands = discover_commands()

    for module in commands:
        # Check if module has COMMAND_METADATA
        if hasattr(module, 'COMMAND_METADATA'):
            metadata = module.COMMAND_METADATA
            category = metadata.get('category', '🔧 Other Commands')
            cmd_list = metadata.get('commands', [])

            for cmd in cmd_list:
                name = cmd.get('name', 'unknown')
                args = cmd.get('args', '')
                desc = cmd.get('description', '')
                metadata_by_category[category].append((name, args, desc))

    # Sort categories to ensure consistent output
    # Keep emoji categories in a specific order
    category_order = [
        "📊 View Commands",
        "🎯 Context Management",
        "✅ Task Management",
        "💬 Comment Management",
        "☑️  Checklist Management",
        "🏷️  Custom Fields",
        "🤖 Parent Task Automation",
        "📄 Docs Management",
        "📦 Export/Dump",
        "🏗️  Workspace Hierarchy",
        "🔄 Git Workflow",
        "🛠️  Utility Commands",
        "🎨 Configuration",
    ]

    # Build ordered dict
    ordered_metadata = {}
    for cat in category_order:
        if cat in metadata_by_category:
            ordered_metadata[cat] = metadata_by_category[cat]

    # Add any remaining categories
    for cat in sorted(metadata_by_category.keys()):
        if cat not in ordered_metadata:
            ordered_metadata[cat] = metadata_by_category[cat]

    return ordered_metadata


def register_all_commands(subparsers):
    """
    Register all discovered commands with the argument parser.

    Args:
        subparsers: The argparse subparsers object to register commands with
    """
    commands = discover_commands()

    for module in commands:
        try:
            module.register_command(subparsers)
        except Exception as e:
            module_name = module.__name__.split('.')[-1]
            print(f"Warning: Failed to register command from '{module_name}': {e}")


def discover_and_register_commands(subparsers, add_common_args=None):
    """
    Discover and register all command plugins.

    This is a wrapper function for backward compatibility with cli.py.
    The add_common_args parameter is accepted but not used since command
    modules import and use add_common_args from utils directly.

    Args:
        subparsers: The argparse subparsers object to register commands with
        add_common_args: (Optional) Common args function (for compatibility)
    """
    register_all_commands(subparsers)


# Export utility functions for use by command modules
from .utils import create_format_options, get_list_statuses

__all__ = ['discover_commands', 'collect_command_metadata', 'register_all_commands',
           'discover_and_register_commands', 'create_format_options', 'get_list_statuses']
