# BaseCommand Migration Guide

## Overview

This guide explains how to migrate commands from function-based to BaseCommand class-based implementation.

## Automated Migration

### Scripts Available

1. **migrate_to_basecommand.py** - Shows command-to-task mapping
2. **auto_migrate.py** - Automatically migrates command files
3. **update_clickup_tasks.sh** - Updates ClickUp tasks after migration

### Quick Start

```bash
# 1. See the command mapping
python3 migrate_to_basecommand.py

# 2. Migrate a single command
python3 auto_migrate.py demo.py

# 3. Migrate multiple commands in batch
python3 auto_migrate.py --batch demo.py dump.py flat.py

# 4. Test the migrated command
cum <command> --help
cum <command> <args>

# 5. Commit the changes
git add clickup_framework/commands/<file>.py
git commit -m "Refactor: Migrate <file> to BaseCommand (ClickUp: #<task_ids>)"
git push origin <branch>

# 6. Update ClickUp tasks
./update_clickup_tasks.sh <commit_sha> demo.py dump.py
```

## Command-to-Task Mapping

| Command File | ClickUp Task IDs |
|--------------|------------------|
| demo.py | 86c6jrdy8, 86c6jre94 |
| dump.py | 86c6jreft, 86c6jre32 |
| flat.py | 86c6jrep1, 86c6jre5e |
| filter.py | 86c6jrejy, 86c6jre4e |
| stats.py | 86c6jrfbt, 86c6jrf56 |
| clear_current.py | 86c6jrdty, 86c6jrdzz, 86c6jrdw8 |
| assigned_command.py | 86c6jrdqk |
| attachment_commands.py | 86c6jrdrg |
| automation_commands.py | 86c6jrdrv |
| checklist_commands.py | 86c6jrdta |
| command_sync.py | 86c6jrdup, 86c6jre12 |
| comment_commands.py | 86c6jrdvr, 86c6jre2w |
| custom_field_commands.py | 86c6jrdxe, 86c6jre7k |
| detail.py | 86c6jrdz8, 86c6jreaq |
| diff_command.py | 86c6jrec0, 86c6jre08 |
| doc_commands.py | 86c6jred3, 86c6jre15 |
| folder_commands.py | 86c6jrerk, 86c6jre7x |
| git_overflow_command.py | 86c6jrex5, 86c6jrea1 |
| git_reauthor_command.py | 86c6jrey8, 86c6jrecf |
| gitpull_command.py | 86c6jrezh, 86c6jredq |
| gitsuck_command.py | 86c6jrf0x, 86c6jrej0 |
| hierarchy.py | 86c6jrf21, 86c6jrema |
| horde_command.py | 86c6jrf3d, 86c6jrerf |
| jizz_command.py | 86c6jrf4h, 86c6jrewz |
| list_commands.py | 86c6jrf54, 86c6jrey3 |
| mermaid_commands.py | 86c6jrf5y, 86c6jreyz |
| search_command.py | 86c6jrf6k, 86c6jrf0p |
| space_commands.py | 86c6jrf9v, 86c6jrf3t |
| stash_command.py | 86c6jrfar, 86c6jrf4d |
| task_commands.py | 86c6jrfd1, 86c6jrf61 |
| update_command.py | 86c6jrfe6, 86c6jrf6q |

## Manual Migration Pattern

### Before (Function-based)

```python
"""Command description."""

from clickup_framework import ClickUpClient, get_context_manager

def my_command(args):
    """Execute the command."""
    context = get_context_manager()
    client = ClickUpClient()

    # Command logic
    result = client.do_something(args.id)
    print(f"Result: {result}")

def register_command(subparsers):
    """Register the command."""
    parser = subparsers.add_parser('mycommand')
    parser.add_argument('id')
    parser.set_defaults(func=my_command)
```

### After (BaseCommand)

```python
"""Command description."""

from clickup_framework.commands.base_command import BaseCommand

class MyCommand(BaseCommand):
    """My command using BaseCommand."""

    def execute(self):
        """Execute the command."""
        # self.context and self.client are already initialized
        result = self.client.do_something(self.args.id)
        self.print(f"Result: {result}")

def my_command(args):
    """Command function wrapper for backward compatibility."""
    command = MyCommand(args, command_name='mycommand')
    command.execute()

def register_command(subparsers):
    """Register the command."""
    parser = subparsers.add_parser('mycommand')
    parser.add_argument('id')
    parser.set_defaults(func=my_command)
```

## Key Changes

### 1. Context & Client
- **Before:** `context = get_context_manager()`, `client = ClickUpClient()`
- **After:** Use `self.context` and `self.client` (automatically initialized)

### 2. Arguments
- **Before:** `args.something`
- **After:** `self.args.something`

### 3. Print Statements
- **Before:** `print("message")`
- **After:** `self.print("message")` or `self.print_success()`, `self.print_error()`, `self.print_warning()`

### 4. Error Handling
- **Before:** `print(f"Error: {msg}", file=sys.stderr)` + `sys.exit(1)`
- **After:** `self.error(msg)` (prints error and exits)

### 5. ID Resolution
- **Before:** `resolve_list_id(client, id_or_current, context)`
- **After:** `self.resolve_list(id_or_current)` (or `resolve_id()`, `resolve_container()`)

## Migration Priority

### Simple Commands (Start Here)
1. demo.py
2. dump.py
3. flat.py
4. filter.py
5. stats.py
6. clear_current.py

### Medium Complexity
- assigned_command.py
- attachment_commands.py
- automation_commands.py
- checklist_commands.py
- comment_commands.py
- custom_field_commands.py
- folder_commands.py
- list_commands.py
- search_command.py
- space_commands.py
- task_commands.py
- update_command.py

### Complex Commands (Do Last)
- detail.py (large, lots of formatting)
- hierarchy.py (large, complex logic)
- mermaid_commands.py (complex processing)

## Testing Checklist

After migrating a command:

- [ ] Command class extends BaseCommand
- [ ] All common initialization moved to base class
- [ ] ID resolution uses base class methods
- [ ] Output uses base class print methods
- [ ] No regression in functionality
- [ ] Error handling uses base class methods
- [ ] Function wrapper maintains backward compatibility
- [ ] Command tested and working

## Progress

- **Completed:** 4 commands (8 tasks) - 12%
- **Remaining:** 31 commands (59 tasks)
- **Total:** 35 commands (67 tasks)

### Completed Commands
1. ✅ ansi.py
2. ✅ set_current.py
3. ✅ container.py
4. ✅ show_current.py
