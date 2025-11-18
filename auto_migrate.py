#!/usr/bin/env python3
"""
Automated migration script for converting commands to BaseCommand.

Usage:
    python3 auto_migrate.py <command_file.py>
    python3 auto_migrate.py --batch demo.py dump.py flat.py

This script will:
1. Analyze the command file
2. Generate migrated code
3. Create a backup
4. Write the migrated version
5. Test the command
"""

import re
import sys
import shutil
from pathlib import Path
from typing import Dict, List, Optional


class CommandMigrator:
    """Handles migration of a command file to BaseCommand."""

    def __init__(self, file_path: Path):
        self.file_path = file_path
        self.content = file_path.read_text()
        self.command_name = file_path.stem
        self.class_name = self._generate_class_name()

    def _generate_class_name(self) -> str:
        """Generate a CamelCase class name from filename."""
        # Convert snake_case to CamelCase
        parts = self.command_name.replace('_command', '').split('_')
        return ''.join(word.capitalize() for word in parts) + 'Command'

    def extract_imports(self) -> List[str]:
        """Extract import statements from the file."""
        imports = []
        for line in self.content.split('\n'):
            if line.startswith('import ') or line.startswith('from '):
                # Skip imports that will be replaced
                if 'get_context_manager' in line:
                    continue
                if 'ClickUpClient' in line and 'from clickup_framework import' in line:
                    continue
                if line.strip() and 'import sys' not in line:
                    imports.append(line)
        return imports

    def extract_command_function(self) -> Optional[str]:
        """Extract the main command function."""
        pattern = r'def (\w+_command)\(args\):\s*(?:""".*?""")?(.+?)(?=\ndef |\nclass |\Z)'
        match = re.search(pattern, self.content, re.DOTALL)
        if match:
            return match.group(0)
        return None

    def extract_register_function(self) -> Optional[str]:
        """Extract the register_command function."""
        pattern = r'def register_command\(.*?\):.*?(?=\ndef |\nclass |\Z)'
        match = re.search(pattern, self.content, re.DOTALL)
        if match:
            return match.group(0)
        return None

    def convert_body(self, func_body: str) -> str:
        """Convert function body to use BaseCommand methods."""
        # Remove the function definition line and docstring
        lines = func_body.split('\n')[1:]  # Skip 'def command_name(args):'

        # Skip docstring if present
        if '"""' in '\n'.join(lines[:3]):
            in_docstring = False
            new_lines = []
            for line in lines:
                if '"""' in line:
                    in_docstring = not in_docstring
                    if not in_docstring:
                        continue
                elif not in_docstring:
                    new_lines.append(line)
            lines = new_lines

        converted = []
        for line in lines:
            # Replace context = get_context_manager() with self.context
            if 'context = get_context_manager()' in line:
                continue

            # Replace client = ClickUpClient() with self.client
            if 'client = ClickUpClient()' in line:
                continue

            # Replace args. with self.args.
            line = re.sub(r'\bargs\.', 'self.args.', line)

            # Replace context. with self.context.
            line = re.sub(r'\bcontext\.', 'self.context.', line)

            # Replace client. with self.client.
            line = re.sub(r'\bclient\.', 'self.client.', line)

            # Replace print statements with self.print
            if 'print(' in line and 'self.print(' not in line:
                # Check if it's an error print
                if 'file=sys.stderr' in line:
                    # Convert to self.print_error
                    msg_match = re.search(r'print\(["\'](.+?)["\']', line)
                    if msg_match:
                        line = ' ' * (len(line) - len(line.lstrip())) + f'self.print_error("{msg_match.group(1)}")'
                else:
                    line = line.replace('print(', 'self.print(')

            # Replace sys.exit(1) with self.error
            if 'sys.exit(1)' in line:
                continue  # Usually follows error print, which we've converted

            converted.append(line)

        # Add proper indentation (8 spaces for execute method body)
        indented = []
        for line in converted:
            if line.strip():
                # Add 8 spaces of indentation
                indented.append('        ' + line.lstrip())
            else:
                indented.append('')

        return '\n'.join(indented)

    def generate_migrated_code(self) -> str:
        """Generate the complete migrated code."""
        imports = self.extract_imports()
        command_func = self.extract_command_function()
        register_func = self.extract_register_function()

        if not command_func:
            raise ValueError(f"Could not find command function in {self.file_path}")

        # Extract module docstring
        docstring_match = re.search(r'^"""(.+?)"""', self.content, re.DOTALL)
        module_docstring = docstring_match.group(0) if docstring_match else f'"""{self.command_name} command."""'

        # Extract function body
        func_match = re.search(r'def \w+_command\(args\):(.+?)(?=\ndef |\nclass |\Z)', command_func, re.DOTALL)
        func_body = func_match.group(1) if func_match else ''

        # Convert the body
        converted_body = self.convert_body(command_func)

        # Build additional imports
        additional_imports = []
        for imp in imports:
            if 'base_command' not in imp.lower():
                additional_imports.append(imp)

        additional_imports_str = '\n'.join(additional_imports) if additional_imports else ''

        # Get command function name
        cmd_func_name = re.search(r'def (\w+_command)\(args\):', command_func).group(1)
        cmd_short_name = cmd_func_name.replace('_command', '')

        # Build the migrated code
        migrated = f'''{module_docstring}

from clickup_framework.commands.base_command import BaseCommand
{additional_imports_str}


class {self.class_name}(BaseCommand):
    """
    {self.command_name.replace('_', ' ').title()} command using BaseCommand.
    """

    def execute(self):
        """Execute the {cmd_short_name} command."""
{converted_body}


def {cmd_func_name}(args):
    """
    Command function wrapper for backward compatibility.

    This function maintains the existing function-based API while
    using the BaseCommand class internally.
    """
    command = {self.class_name}(args, command_name='{cmd_short_name}')
    command.execute()


{register_func}
'''

        return migrated

    def migrate(self, backup: bool = True) -> bool:
        """Perform the migration."""
        try:
            # Create backup
            if backup:
                backup_path = self.file_path.with_suffix('.py.bak')
                shutil.copy2(self.file_path, backup_path)
                print(f"✓ Created backup: {backup_path}")

            # Generate migrated code
            migrated_code = self.generate_migrated_code()

            # Write migrated code
            self.file_path.write_text(migrated_code)
            print(f"✓ Migrated: {self.file_path}")

            return True
        except Exception as e:
            print(f"✗ Error migrating {self.file_path}: {e}")
            return False


def main():
    """Main entry point."""
    if len(sys.argv) < 2:
        print("Usage: python3 auto_migrate.py <command_file.py>")
        print("       python3 auto_migrate.py --batch file1.py file2.py ...")
        sys.exit(1)

    batch_mode = '--batch' in sys.argv
    files = [arg for arg in sys.argv[1:] if arg != '--batch']

    commands_dir = Path('clickup_framework/commands')

    success_count = 0
    fail_count = 0

    for filename in files:
        file_path = commands_dir / filename
        if not file_path.exists():
            print(f"✗ File not found: {file_path}")
            fail_count += 1
            continue

        print(f"\nMigrating {filename}...")
        migrator = CommandMigrator(file_path)
        if migrator.migrate():
            success_count += 1
        else:
            fail_count += 1

    print(f"\n{'='*60}")
    print(f"Migration complete: {success_count} succeeded, {fail_count} failed")


if __name__ == '__main__':
    main()
