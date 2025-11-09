from .commands import (
    list_cmd, show, comment, append_desc, create_subtask, create_task,
    create_space, create_folder, create_list, create_checklist,
    update_status, update_tags, dashboard, interactive_dashboard,
    find, checklist, relationship, fix_newlines, validate
)

def setup_subparsers(subparsers):
    """Set up all command subparsers."""
    # ... existing code ...
    relationship.setup_args(subparsers)
    fix_newlines.setup_args(subparsers)
    validate.setup_args(subparsers)
    
    return subparsers

# ... existing code ... 