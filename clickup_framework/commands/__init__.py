"""
CLI Commands Package

This package provides a plugin-based command system for the ClickUp Framework CLI.
Each command is defined in its own Python module with a register_command() function.

Command files are automatically discovered and loaded by the CLI.
"""

import os
import importlib
import inspect
from pathlib import Path


def discover_and_register_commands(subparsers, add_common_args):
    """
    Automatically discover and register all command modules.

    Args:
        subparsers: The argparse subparsers object to register commands with
        add_common_args: Function to add common arguments to a parser

    This function scans the commands directory for Python files and imports
    each module. If the module has a register_command() function, it calls it
    to register the command with argparse.
    """
    commands_dir = Path(__file__).parent

    # Get all .py files in the commands directory
    command_files = [
        f.stem for f in commands_dir.glob('*.py')
        if f.is_file()
        and f.stem not in ['__init__', 'utils']  # Skip special files
        and not f.stem.startswith('_')  # Skip private modules
    ]

    registered_commands = []

    for module_name in sorted(command_files):
        try:
            # Import the module
            module = importlib.import_module(f'clickup_framework.commands.{module_name}')

            # Check if module has register_command function
            if hasattr(module, 'register_command') and callable(module.register_command):
                # Get the function signature to see what parameters it expects
                sig = inspect.signature(module.register_command)
                params = list(sig.parameters.keys())

                # Call register_command with appropriate arguments
                if 'add_common_args' in params:
                    module.register_command(subparsers, add_common_args)
                else:
                    module.register_command(subparsers)

                registered_commands.append(module_name)
        except Exception as e:
            # Log error but continue loading other commands
            import sys
            print(f"Warning: Failed to load command module '{module_name}': {e}", file=sys.stderr)

    return registered_commands
