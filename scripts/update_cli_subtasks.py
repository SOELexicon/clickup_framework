#!/usr/bin/env python3
"""
Update CLI command subtasks with detailed descriptions.
Includes failsafe to prevent duplicates by checking existing tasks first.
"""

from clickup_framework import ClickUpClient

# Task hierarchy for CLI commands with detailed descriptions
CLI_COMMANDS = [
    {
        "name": "Task Management Commands",
        "description": """# Task Management Commands

Comprehensive task management functionality for the ClickUp Framework CLI.

## Commands to Implement

### task create
Create new tasks with support for:
- Task name and description
- Priority levels (1-4)
- Status assignment
- Tags
- Assignees
- Due dates
- Parent task assignment

### task update
Update existing tasks with ability to modify:
- Task name
- Description
- Status
- Priority
- Tags (add/remove)
- Assignees (add/remove)
- Due dates
- Custom fields

### task delete
Delete tasks with:
- Confirmation prompt
- Optional force flag
- Cascade deletion of subtasks (optional)

### task assign / task unassign
Manage task assignees:
- Add assignees by user ID or email
- Remove assignees
- List current assignees

### task set-status
Quick status updates:
- Set task status by name
- Show available statuses for the list
- Validate status exists before updating

### task set-priority
Priority management:
- Set priority (1-4 or urgent/high/normal/low)
- Clear priority

### task set-tags
Tag management:
- Add tags
- Remove tags
- Replace all tags
- List current tags

## Implementation Details

All task commands should:
- Support "current" keyword to use context
- Show colored, formatted output
- Display success/error messages clearly
- Validate inputs before API calls
- Handle API errors gracefully
"""
    },
    {
        "name": "Comment Commands",
        "description": """# Comment Commands

Manage task comments and discussions.

## Commands to Implement

### comment add
Add comments to tasks:
- Comment text (required)
- Notify assignees (optional)
- Attach files (optional)
- Mention users with @username

### comment list
List comments on a task:
- Show all comments or limit count
- Display commenter name and timestamp
- Show threaded replies
- Include reactions

### comment update
Edit existing comments:
- Update comment text
- Preserve original metadata (author, timestamp)

### comment delete
Remove comments:
- Delete by comment ID
- Confirmation prompt
- Optional force flag

## Implementation Details

- Support rich text formatting in comments
- Handle @ mentions properly
- Show timestamps in user-friendly format
- Support pagination for large comment threads
- Use colors for different comment types
"""
    },
    {
        "name": "Checklist Commands",
        "description": """# Checklist Commands

Manage task checklists and checklist items.

## Commands to Implement

### checklist create
Create new checklists on tasks:
- Checklist name
- Initial checklist items
- Assignees per item
- Parent task specification

### checklist add-item
Add items to existing checklists:
- Item text
- Assignee (optional)
- Position in list

### checklist check / checklist uncheck
Toggle checklist item completion:
- Mark items as checked/unchecked
- Update completion percentage
- Show visual progress

### checklist delete
Remove checklists or items:
- Delete entire checklist
- Delete specific items
- Confirmation prompts

### checklist list
Show all checklists for a task:
- Display completion status
- Show assignees
- Format with checkboxes (☑/☐)
- Calculate progress percentages

## Implementation Details

- Use Unicode checkbox symbols (☑☐)
- Show progress bars for checklist completion
- Support bulk operations (check all, uncheck all)
- Color-code completed vs pending items
"""
    },
    {
        "name": "Relationship Commands",
        "description": """# Relationship Commands

Manage task relationships and dependencies.

## Commands to Implement

### relationship add
Create relationships between tasks:
- Dependency types (blocking, waiting on, related)
- Link to other tasks
- Bidirectional relationship setup

### relationship remove
Remove task relationships:
- Remove by relationship ID
- Remove all relationships
- Confirmation prompts

### relationship list
Show all relationships for a task:
- Display relationship type
- Show related task details
- Use arrows to indicate direction (→, ←, ↔)
- Color-code by relationship type

### relationship blocking / relationship waiting-on
Quick shortcuts for common relationships:
- Mark task as blocking another
- Mark task as waiting on another
- Show dependency chains

## Implementation Details

- Visualize dependency chains with tree view
- Detect circular dependencies and warn
- Show impact of relationship changes
- Use intuitive symbols (🔒 for blocking, ⏳ for waiting)
"""
    },
    {
        "name": "Custom Field Commands",
        "description": """# Custom Field Commands

Manage custom fields on tasks.

## Commands to Implement

### customfield set
Set custom field values:
- Field name or ID
- Field value (typed correctly)
- Validation before setting
- Support for all field types (text, number, dropdown, date, etc.)

### customfield get
Get custom field value:
- Retrieve by field name or ID
- Format output based on field type
- Show field type and metadata

### customfield list
List all custom fields for a task/list:
- Show field names and values
- Display field types
- Format based on field type
- Color-code different field types

### customfield clear
Clear custom field value:
- Remove field value
- Confirmation if required field

## Implementation Details

- Detect field type automatically
- Validate values before setting
- Support field type-specific formatting:
  - Dates: human-readable format
  - Numbers: proper number formatting
  - Dropdowns: show available options
  - Labels: color-coded display
- Handle required vs optional fields
"""
    },
    {
        "name": "List Commands",
        "description": """# List Commands

Manage ClickUp lists.

## Commands to Implement

### list get
Get list details:
- List name and ID
- Status options
- Custom fields
- Folder/space hierarchy
- Task count

### list create
Create new lists:
- List name (required)
- Parent folder
- Status options
- Due date settings
- Time tracking enabled/disabled

### list update
Update list settings:
- Rename list
- Change status options
- Update due date settings
- Modify time tracking settings

### list delete
Delete lists:
- Confirmation prompt
- Optional force flag
- Archive instead of delete (option)

### list tasks
List all tasks in a list:
- Use existing hierarchy/flat/container views
- Apply filters
- Support presets

## Implementation Details

- Show list hierarchy (Space > Folder > List)
- Display status workflow visually
- Show custom field definitions
- Include task count and completion stats
"""
    },
    {
        "name": "Workspace/Space/Folder Commands",
        "description": """# Workspace, Space, and Folder Commands

Manage ClickUp organizational hierarchy.

## Workspace Commands

### workspace list
List all workspaces:
- Show workspace IDs
- Show members count
- Display workspace color

### workspace get
Get workspace details:
- Workspace name and ID
- Members
- Spaces
- Settings

## Space Commands

### space list
List spaces in workspace:
- Space names and IDs
- Folder count
- Private vs shared

### space get
Get space details:
- Space name and ID
- Folders
- Lists
- Members

### space create
Create new space:
- Space name
- Private/shared setting
- Multiple assignees option

### space update
Update space settings:
- Rename
- Change privacy
- Update settings

### space delete
Delete space:
- Confirmation required
- Archive option

## Folder Commands

### folder list
List folders in space:
- Folder names and IDs
- List count

### folder get
Get folder details:
- Folder name and ID
- Lists
- Statuses

### folder create
Create new folder:
- Folder name
- Parent space
- Hidden option

### folder update
Update folder:
- Rename
- Change hidden status

### folder delete
Delete folder:
- Confirmation required

## Implementation Details

- Show full hierarchy path for context
- Use tree view for nested structures
- Color-code by organizational level
- Support bulk operations where applicable
"""
    },
    {
        "name": "Docs Commands",
        "description": """# Docs Commands

Manage ClickUp Docs (if API supports it).

## Commands to Implement

### doc list
List docs in workspace:
- Doc names and IDs
- Last modified
- Author
- Sharing settings

### doc get
Get doc content:
- Doc name and ID
- Content (formatted)
- Metadata
- Sharing info

### doc create
Create new doc:
- Doc name
- Initial content
- Parent workspace/folder
- Sharing settings

### doc update
Update doc:
- Update content
- Change name
- Modify sharing

### doc delete
Delete doc:
- Confirmation required

## Implementation Details

- Format doc content for terminal display
- Support markdown output
- Handle rich text appropriately
- Show doc hierarchy
"""
    },
    {
        "name": "Time Tracking Commands",
        "description": """# Time Tracking Commands

Manage time entries on tasks.

## Commands to Implement

### time start
Start time tracking:
- Task ID
- Description (optional)
- Billable flag

### time stop
Stop active time tracking:
- Save time entry
- Show duration
- Add description

### time add
Manually add time entry:
- Task ID
- Duration or start/end time
- Description
- Billable flag
- Date

### time list
List time entries:
- For specific task
- For date range
- Show duration, description, user
- Total time summary

### time update
Update time entry:
- Change duration
- Update description
- Toggle billable

### time delete
Delete time entry:
- Confirmation required

## Implementation Details

- Show duration in human-readable format (2h 30m)
- Display active timer in colored output
- Support time format parsing (2h30m, 2.5h, 150m)
- Show billable vs non-billable time
- Calculate totals and summaries
"""
    },
    {
        "name": "View Management Commands",
        "description": """# View Management Commands

Manage ClickUp views (List, Board, Calendar, etc).

## Commands to Implement

### view list
List available views:
- View names and IDs
- View types (list, board, calendar, etc)
- Filters and grouping

### view get
Get view configuration:
- View settings
- Filters
- Grouping
- Sorting

### view create
Create custom view:
- View name and type
- Filters
- Grouping options
- Sorting rules

### view update
Update view configuration:
- Change filters
- Modify grouping
- Update sorting

### view delete
Delete custom view:
- Confirmation required

## Implementation Details

- Preview view configuration
- Validate filter syntax
- Show visual representation of view settings
- Support view templates
"""
    },
    {
        "name": "Attachment Commands",
        "description": """# Attachment Commands

Manage file attachments on tasks.

## Commands to Implement

### attachment upload
Upload file to task:
- File path
- Task ID
- Optional description

### attachment list
List task attachments:
- Filename and size
- Upload date and user
- URL for download

### attachment download
Download attachment:
- Attachment ID
- Destination path
- Show progress bar

### attachment delete
Delete attachment:
- Attachment ID
- Confirmation required

## Implementation Details

- Show file size in human-readable format (KB, MB, GB)
- Display file type icons/indicators
- Support bulk upload
- Show upload/download progress
- Validate file exists before upload
"""
    }
]


def get_existing_subtasks(client, parent_task_id, list_id):
    """
    Get all existing subtasks under a parent task.

    Returns a dictionary mapping task names to task objects.
    """
    result = client.get_list_tasks(list_id, subtasks='true', include_closed='true')

    tasks = result.get('tasks', [])
    subtasks = [t for t in tasks if t.get('parent') == parent_task_id]

    # Create a name->task mapping for easy lookup
    name_map = {task['name']: task for task in subtasks}

    return name_map


def create_or_update_subtask(client, parent_task_id, list_id, category, existing_tasks):
    """
    Create a new subtask or update existing one if it already exists.

    Failsafe: Checks if a task with the same name already exists before creating.
    """
    task_name = category['name']

    # Check if task already exists
    if task_name in existing_tasks:
        # Task exists - update it
        existing_task = existing_tasks[task_name]
        task_id = existing_task['id']

        print(f"  Task exists: {task_name} [{task_id}]")
        print(f"    Updating description...")

        try:
            client.update_task(task_id, description=category['description'])
            print(f"    ✓ Updated")
            return {'id': task_id, 'name': task_name, 'action': 'updated'}
        except Exception as e:
            print(f"    ✗ Error updating: {e}")
            return None
    else:
        # Task doesn't exist - create it
        print(f"  Creating new task: {task_name}")

        task_data = {
            'name': task_name,
            'description': category['description'],
            'parent': parent_task_id,
            'status': 'Open'
        }

        try:
            task = client.create_task(list_id, **task_data)
            task_id = task['id']
            print(f"    ✓ Created [{task_id}]")
            return {'id': task_id, 'name': task_name, 'action': 'created'}
        except Exception as e:
            print(f"    ✗ Error creating: {e}")
            return None


def update_all_subtasks(parent_task_id, list_id):
    """Update all CLI command subtasks with detailed descriptions."""
    client = ClickUpClient()

    print(f"Fetching existing subtasks under {parent_task_id}...")
    existing_tasks = get_existing_subtasks(client, parent_task_id, list_id)
    print(f"Found {len(existing_tasks)} existing subtasks\n")

    results = {'created': [], 'updated': [], 'errors': []}

    for i, category in enumerate(CLI_COMMANDS, 1):
        print(f"\n{i}/{len(CLI_COMMANDS)}:")
        result = create_or_update_subtask(client, parent_task_id, list_id, category, existing_tasks)

        if result:
            if result['action'] == 'created':
                results['created'].append(result)
            elif result['action'] == 'updated':
                results['updated'].append(result)
        else:
            results['errors'].append(category['name'])

    return results


if __name__ == "__main__":
    parent_task_id = "86c6e0q06"
    list_id = "901517404274"  # Development Tasks list

    print(f"Updating CLI command subtasks under task {parent_task_id}...")
    print("=" * 60)

    results = update_all_subtasks(parent_task_id, list_id)

    print("\n" + "=" * 60)
    print(f"\nSummary:")
    print(f"  Created: {len(results['created'])} tasks")
    print(f"  Updated: {len(results['updated'])} tasks")
    print(f"  Errors: {len(results['errors'])} tasks")

    if results['created']:
        print("\n  Created tasks:")
        for task in results['created']:
            print(f"    • [{task['id']}] {task['name']}")

    if results['updated']:
        print("\n  Updated tasks:")
        for task in results['updated']:
            print(f"    • [{task['id']}] {task['name']}")

    if results['errors']:
        print("\n  Errors:")
        for name in results['errors']:
            print(f"    • {name}")
