#!/usr/bin/env python3
"""
Script to update ClickUp tasks with command help output and other information.

This script:
1. Reads the JSON file with task IDs and commands
2. Runs `cum <command> --help` for each command
3. Updates each task's description with the help output
"""

import json
import subprocess
import sys
from pathlib import Path
from clickup_framework import ClickUpClient
from clickup_framework.exceptions import ClickUpAPIError

# Get the script directory
SCRIPT_DIR = Path(__file__).parent
JSON_FILE = SCRIPT_DIR / "cum_commands_tasks.json"


def get_command_help(command: str) -> tuple[str, str]:
    """
    Get help output for a command.
    
    Returns:
        tuple: (help_output, error_output)
    """
    try:
        result = subprocess.run(
            ["cum", command, "--help"],
            capture_output=True,
            text=True,
            encoding='utf-8',
            errors='replace',  # Replace invalid characters instead of failing
            timeout=10
        )
        help_output = result.stdout
        error_output = result.stderr
        
        # If no stdout but stderr, use stderr
        if not help_output and error_output:
            help_output = error_output
            error_output = ""
            
        return help_output, error_output
    except subprocess.TimeoutExpired:
        return "", "Command timed out after 10 seconds"
    except FileNotFoundError:
        return "", "Command 'cum' not found in PATH"
    except Exception as e:
        return "", f"Error running command: {str(e)}"


def get_command_version_info() -> str:
    """Get version info from cum."""
    try:
        result = subprocess.run(
            ["cum", "--version"],
            capture_output=True,
            text=True,
            encoding='utf-8',
            errors='replace',
            timeout=5
        )
        return result.stdout.strip()
    except:
        return "Version info unavailable"


def format_description(command: str, category: str, help_output: str, error_output: str, version_info: str) -> str:
    """Format the task description with all command information."""
    
    description = f"""# CUM {command}

## Command Information

**Category:** {category}
**Command:** `cum {command}`

## Version

```
{version_info}
```

## Help Output

"""
    
    if help_output:
        description += f"```\n{help_output}\n```\n\n"
    else:
        description += "*No help output available*\n\n"
    
    if error_output:
        description += f"## Error Output\n\n```\n{error_output}\n```\n\n"
    
    description += """## Usage

Run the command with `--help` for detailed usage information:

```bash
cum {command} --help
```

## Notes

- This task documents the `cum {command}` command
- Help output is automatically generated from the command itself
- For the most up-to-date information, run `cum {command} --help` directly
""".format(command=command)
    
    return description


def main():
    """Main function to update all tasks."""
    # Load JSON file
    if not JSON_FILE.exists():
        print(f"Error: JSON file not found at {JSON_FILE}")
        sys.exit(1)
    
    with open(JSON_FILE, 'r', encoding='utf-8') as f:
        commands = json.load(f)
    
    print(f"Loaded {len(commands)} commands from {JSON_FILE}")
    
    # Initialize ClickUp client
    try:
        client = ClickUpClient()
    except Exception as e:
        print(f"Error initializing ClickUp client: {e}")
        sys.exit(1)
    
    # Get version info once
    version_info = get_command_version_info()
    print(f"CUM Version: {version_info}")
    
    # Process each command
    updated = 0
    failed = 0
    
    for i, cmd_info in enumerate(commands, 1):
        task_id = cmd_info["task_id"]
        command = cmd_info["command"]
        category = cmd_info["category"]
        
        print(f"\n[{i}/{len(commands)}] Processing: {command} (Task: {task_id})")
        
        # Get help output
        help_output, error_output = get_command_help(command)
        
        if not help_output and not error_output:
            print(f"  [WARNING] No output for command '{command}'")
        
        # Format description
        description = format_description(command, category, help_output, error_output, version_info)
        
        # Update task
        try:
            client.update_task(
                task_id=task_id,
                markdown_description=description
            )
            print(f"  [OK] Updated task {task_id}")
            updated += 1
        except ClickUpAPIError as e:
            print(f"  [ERROR] Failed to update task {task_id}: {e}")
            failed += 1
        except Exception as e:
            print(f"  [ERROR] Unexpected error updating task {task_id}: {e}")
            failed += 1
    
    # Summary
    print(f"\n{'='*60}")
    print(f"Summary:")
    print(f"  Total commands: {len(commands)}")
    print(f"  Updated: {updated}")
    print(f"  Failed: {failed}")
    print(f"{'='*60}")


if __name__ == "__main__":
    main()

