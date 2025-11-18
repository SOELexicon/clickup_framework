#!/usr/bin/env python3
"""
Automated migration script for converting commands to BaseCommand.

This script analyzes a command file and generates a migrated version
that uses the BaseCommand base class.
"""

import re
import sys
from pathlib import Path
from typing import Dict, List, Tuple


def analyze_command_file(file_path: Path) -> Dict[str, any]:
    """Analyze a command file to extract key information."""
    content = file_path.read_text()

    info = {
        'has_client': 'ClickUpClient()' in content,
        'has_context': 'get_context_manager()' in content,
        'has_display': 'DisplayManager' in content,
        'has_format_options': 'create_format_options' in content,
        'has_id_resolution': 'resolve_' in content,
        'has_error_handling': 'sys.stderr' in content or 'sys.exit' in content,
        'uses_print': 'print(' in content,
        'imports': [],
        'command_function': None,
        'register_function': None,
    }

    # Extract command function name
    cmd_func_match = re.search(r'def (\w+_command)\(args\):', content)
    if cmd_func_match:
        info['command_function'] = cmd_func_match.group(1)

    # Extract imports
    import_lines = re.findall(r'^(import .*|from .* import .*)', content, re.MULTILINE)
    info['imports'] = import_lines

    return info


def generate_migrated_command(file_path: Path, class_name: str) -> str:
    """Generate migrated command code."""
    content = file_path.read_text()

    # Extract command function
    cmd_func_match = re.search(
        r'def (\w+_command)\(args\):.*?(?=\ndef |$)',
        content,
        re.DOTALL
    )

    if not cmd_func_match:
        return None

    original_func = cmd_func_match.group(0)
    func_body = cmd_func_match.group(0).split('"""')[-1] if '"""' in cmd_func_match.group(0) else original_func

    # Extract the actual logic (remove function def and docstring)
    body_match = re.search(r'def \w+_command\(args\):(?:\s+""".*?""")?(.+)', original_func, re.DOTALL)
    if body_match:
        func_body = body_match.group(1)

    # Build migrated version
    migrated = f'''"""{{DOCSTRING}}"""

from clickup_framework.commands.base_command import BaseCommand
{{ADDITIONAL_IMPORTS}}


class {class_name}(BaseCommand):
    """
    {{CLASS_DOCSTRING}}
    """

    def execute(self):
        """Execute the {{COMMAND_NAME}} command."""
{{CONVERTED_BODY}}


def {{FUNC_NAME}}(args):
    """
    Command function wrapper for backward compatibility.

    This function maintains the existing function-based API while
    using the BaseCommand class internally.
    """
    command = {class_name}(args, command_name='{{CMD_NAME}}')
    command.execute()


{{REGISTER_FUNCTION}}
'''

    return migrated


def get_command_mapping() -> Dict[str, List[str]]:
    """Return mapping of command files to ClickUp task IDs."""
    return {
        'assigned_command.py': ['86c6jrdqk'],
        'attachment_commands.py': ['86c6jrdrg'],
        'automation_commands.py': ['86c6jrdrv'],
        'checklist_commands.py': ['86c6jrdta'],
        'clear_current.py': ['86c6jrdty', '86c6jrdzz', '86c6jrdw8'],
        'command_sync.py': ['86c6jrdup', '86c6jre12'],
        'comment_commands.py': ['86c6jrdvr', '86c6jre2w'],
        'custom_field_commands.py': ['86c6jrdxe', '86c6jre7k'],
        'demo.py': ['86c6jrdy8', '86c6jre94'],
        'detail.py': ['86c6jrdz8', '86c6jreaq'],
        'diff_command.py': ['86c6jrec0', '86c6jre08'],
        'doc_commands.py': ['86c6jred3', '86c6jre15'],
        'dump.py': ['86c6jreft', '86c6jre32'],
        'filter.py': ['86c6jrejy', '86c6jre4e'],
        'flat.py': ['86c6jrep1', '86c6jre5e'],
        'folder_commands.py': ['86c6jrerk', '86c6jre7x'],
        'git_overflow_command.py': ['86c6jrex5', '86c6jrea1'],
        'git_reauthor_command.py': ['86c6jrey8', '86c6jrecf'],
        'gitpull_command.py': ['86c6jrezh', '86c6jredq'],
        'gitsuck_command.py': ['86c6jrf0x', '86c6jrej0'],
        'hierarchy.py': ['86c6jrf21', '86c6jrema'],
        'horde_command.py': ['86c6jrf3d', '86c6jrerf'],
        'jizz_command.py': ['86c6jrf4h', '86c6jrewz'],
        'list_commands.py': ['86c6jrf54', '86c6jrey3'],
        'mermaid_commands.py': ['86c6jrf5y', '86c6jreyz'],
        'search_command.py': ['86c6jrf6k', '86c6jrf0p'],
        'space_commands.py': ['86c6jrf9v', '86c6jrf3t'],
        'stash_command.py': ['86c6jrfar', '86c6jrf4d'],
        'stats.py': ['86c6jrfbt', '86c6jrf56'],
        'task_commands.py': ['86c6jrfd1', '86c6jrf61'],
        'update_command.py': ['86c6jrfe6', '86c6jrf6q'],
    }


def get_simple_commands() -> List[str]:
    """Return list of simple commands to migrate first."""
    return [
        'demo.py',
        'dump.py',
        'flat.py',
        'filter.py',
        'stats.py',
        'clear_current.py',
    ]


if __name__ == '__main__':
    # Display command mapping
    mapping = get_command_mapping()

    print("Command to Task ID Mapping:")
    print("=" * 70)
    for cmd_file, task_ids in sorted(mapping.items()):
        print(f"{cmd_file:30} → {', '.join(task_ids)}")

    print(f"\nTotal: {len(mapping)} command files")
    print(f"Total: {sum(len(ids) for ids in mapping.values())} ClickUp tasks")
    print(f"\nSimple commands to start with: {', '.join(get_simple_commands())}")
