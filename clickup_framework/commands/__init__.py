"""
Drop-in plugin command loader for CLI.

Each command module in this directory should define a `register_command(subparsers)` function
that configures its own argument parser and sets the command function.

Example command module structure:
    def my_command(args):
        '''Command implementation'''
        pass

    def register_command(subparsers):
        parser = subparsers.add_parser('mycommand', help='Description')
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

__all__ = ['discover_commands', 'register_all_commands', 'discover_and_register_commands',
           'create_format_options', 'get_list_statuses']
