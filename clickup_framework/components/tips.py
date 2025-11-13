"""
Tips system for ClickUp Framework CLI.

Provides context-aware, rotating tips that help users discover features
and improve their workflow efficiency.
"""

import os
import json
from pathlib import Path
from typing import Dict, Optional
from clickup_framework.utils.colors import colorize, TextColor, TextStyle


# Tips organized by command category
TIPS = {
    'hierarchy': [
        "Use 'cum h --all' to see all workspace tasks, or 'cum h <task_id>' to focus on one task and its subtasks",
        "Smart indicators show dependencies (⏳), blockers (🚫), assignees (👤), and due dates (📅)",
        "Tree lines show parent-child relationships - follow the └─ and ├─ branches to understand task structure",
        "Pipe to grep to find tasks: 'cum h --all | grep keyword' or 'cum h <list_id> | grep \"in progress\"'",
        "Use --preset for different detail levels: 'cum h --preset minimal' for quick overview",
        "Filter tasks by status: 'cum filter <list_id> --status \"in progress\"' to see active work",
        "Set current task context with 'cum set task <id>' then use 'cum h current' to view it",
        "Attachments show with 📎 icon - use 'cum attach <task_id> <file>' to upload files",
    ],
    'list': [
        "Use 'cum h --all' to see all workspace tasks, or 'cum h <task_id>' to focus on one task and its subtasks",
        "Smart indicators show dependencies (⏳), blockers (🚫), assignees (👤), and due dates (📅)",
        "Tree lines show parent-child relationships - follow the └─ and ├─ branches to understand task structure",
        "Pipe to grep to find tasks: 'cum h --all | grep keyword' or 'cum h <list_id> | grep \"in progress\"'",
        "Use --preset for different detail levels: 'cum h --preset minimal' for quick overview",
    ],
    'task_create': [
        "Assign tasks with --assignee <user_id> or use 'cum ta <task_id> <user_id>' later",
        "Set due dates with --due-date YYYY-MM-DD format",
        "Create subtasks with --parent <task_id> to nest under existing tasks",
        "Set priority with --priority: 1=urgent, 2=high, 3=normal, 4=low",
        "Add to specific list with --list-id or set default: 'cum set list <id>'",
        "Use --description to add detailed task info during creation",
        "Add tags during creation: --tags 'tag1,tag2,tag3'",
    ],
    'task_update': [
        "Update multiple fields at once: 'cum tu <task_id> --name \"New\" --priority 1 --status \"in progress\"'",
        "Use --description to replace full description or see 'cum ca' to add comments",
        "Change task status: 'cum tss <task_id> \"status\"' (faster than full update)",
        "Set priority quickly: 'cum tsp <task_id> 1' for urgent tasks",
        "Manage tags: 'cum tst <task_id> --add tag1 --remove tag2'",
    ],
    'task_status': [
        "Status changes auto-update parent tasks if automation is enabled",
        "Check automation: 'cum pau status' and enable with 'cum pau enable'",
        "Update multiple tasks: 'cum tss <task_id1> <task_id2> <task_id3> \"Complete\"'",
        "View available statuses: 'cum detail <task_id>' shows status options",
    ],
    'doc': [
        "Create docs with pages: 'cum dc <workspace> \"Doc Name\" --pages \"Page 1:Content here\"'",
        "Export docs to markdown: 'cum de <workspace> --doc-id <id> --output-dir ./docs'",
        "Import markdown files: 'cum di <workspace> ./docs --nested' to preserve folder structure",
        "List all docs: 'cum dl <workspace>' to see workspace documentation",
        "Update pages: 'cum pu <workspace> <doc_id> <page_id> --content \"New content\"'",
        "View doc structure: 'cum dg <workspace> <doc_id>' shows all pages hierarchically",
    ],
    'comment': [
        "Add comments quickly: 'cum ca <task_id> \"Your comment here\"'",
        "Read from file: 'cum ca <task_id> --comment-file notes.txt' for longer comments",
        "List comments: 'cum cl <task_id>' to see task discussion history",
        "Update comments: 'cum cu <comment_id> \"Updated text\"'",
    ],
    'attachment': [
        "Upload files: 'cum attach <task_id> <file_path>' to add attachments",
        "Attachments appear in task details and hierarchy views with 📎 icon",
        "Use 'current' for task_id if you've set context: 'cum attach current file.pdf'",
        "View attachments: 'cum detail <task_id>' shows all attached files with URLs",
    ],
    'context': [
        "Set current workspace: 'cum set workspace <id>' to avoid typing it repeatedly",
        "Set current list: 'cum set list <id>' for quick task creation",
        "Set current task: 'cum set task <id>' to use 'current' in commands",
        "View context: 'cum show' displays all current settings",
        "Clear context: 'cum clear' or 'cum clear task' to reset",
    ],
    'filter': [
        "Filter by status: 'cum filter <list_id> --status \"in progress\"'",
        "Filter by priority: 'cum filter <list_id> --priority urgent'",
        "Filter by assignee: 'cum filter <list_id> --assignee <user_id>'",
        "Combine filters: 'cum filter <list_id> --status open --priority high'",
        "Filter by tags: 'cum filter <list_id> --tags \"bug,urgent\"'",
    ],
    'custom_field': [
        "Set custom field: 'cum cf set <task_id> \"Field Name\" \"value\"'",
        "Get field value: 'cum cf get <task_id> \"Field Name\"'",
        "List available fields: 'cum cf list --task <task_id>'",
        "Remove field value: 'cum cf remove <task_id> \"Field Name\"'",
    ],
    'checklist': [
        "Create checklist: 'cum chk create <task_id> \"Checklist Name\"'",
        "Add items: 'cum chk item-add <checklist_id> \"Item name\" --assignee <user_id>'",
        "List checklists: 'cum chk list <task_id>' to see all checklists on task",
        "Use templates: 'cum chk template list' to see available templates",
        "Clone checklists: 'cum chk clone <source_task> <target_task>' to copy",
    ],
    'general': [
        "Enable colors: 'cum ansi enable' for beautiful colored output",
        "View all commands: 'cum --help' or just 'cum' for command tree",
        "Get command help: 'cum <command> --help' for detailed usage",
        "Update cum tool: 'cum update cum' to get latest features",
        "Disable tips: Set CLICKUP_NO_TIPS=1 environment variable or use --no-tips flag",
        "Set current context to avoid typing IDs: 'cum set list <id>' then 'cum tc \"Task Name\"'",
        "Check tool version: 'cum --version' to see current version",
    ],
}


class TipManager:
    """
    Manages tip rotation and display for CLI commands.

    Stores state in ~/.config/clickup/tip_state.json to track
    which tip was last shown for each category, ensuring fair
    rotation through all tips.
    """

    def __init__(self):
        """Initialize TipManager with state file."""
        self.config_dir = Path.home() / '.config' / 'clickup'
        self.state_file = self.config_dir / 'tip_state.json'
        self.state = self._load_state()

    def _load_state(self) -> Dict[str, int]:
        """Load tip state from file."""
        if self.state_file.exists():
            try:
                with open(self.state_file, 'r') as f:
                    return json.load(f)
            except (json.JSONDecodeError, IOError):
                # If file is corrupted, start fresh
                return {}
        return {}

    def _save_state(self):
        """Save tip state to file."""
        try:
            # Ensure config directory exists
            self.config_dir.mkdir(parents=True, exist_ok=True)

            with open(self.state_file, 'w') as f:
                json.dump(self.state, f, indent=2)
        except IOError:
            # If we can't save state, just continue without it
            pass

    def get_tip(self, category: str) -> Optional[str]:
        """
        Get next tip for given category.

        Args:
            category: Tip category (e.g., 'hierarchy', 'task_create', 'general')

        Returns:
            Next tip string, or None if category doesn't exist or tips disabled
        """
        # Check if tips are disabled
        if self._tips_disabled():
            return None

        # Get tips for category, fallback to general if category not found
        tips = TIPS.get(category, TIPS.get('general', []))

        if not tips:
            return None

        # Get current index for this category
        current_index = self.state.get(category, 0)

        # Get the tip
        tip = tips[current_index]

        # Update index for next time (wrap around)
        next_index = (current_index + 1) % len(tips)
        self.state[category] = next_index
        self._save_state()

        return tip

    def _tips_disabled(self) -> bool:
        """Check if tips are disabled via environment variable."""
        return os.getenv('CLICKUP_NO_TIPS', '').lower() in ('1', 'true', 'yes')

    def format_tip(self, tip: str, use_color: bool = True) -> str:
        """
        Format tip for display.

        Args:
            tip: Tip text to format
            use_color: Whether to use ANSI colors

        Returns:
            Formatted tip string
        """
        if use_color:
            icon = "💡"
            label = colorize("TIP:", TextColor.BRIGHT_YELLOW, TextStyle.BOLD)
            tip_text = colorize(tip, TextColor.BRIGHT_CYAN)
            return f"\n{icon} {label} {tip_text}\n"
        else:
            return f"\nTIP: {tip}\n"


# Global tip manager instance
_tip_manager = None


def get_tip_manager() -> TipManager:
    """Get the global TipManager instance."""
    global _tip_manager
    if _tip_manager is None:
        _tip_manager = TipManager()
    return _tip_manager


def show_tip(category: str, use_color: bool = True, enabled: bool = True):
    """
    Show a tip for the given category.

    Args:
        category: Tip category
        use_color: Whether to use ANSI colors
        enabled: Whether tips are enabled (from --no-tips flag)
    """
    if not enabled:
        return

    manager = get_tip_manager()
    tip = manager.get_tip(category)

    if tip:
        formatted = manager.format_tip(tip, use_color)
        print(formatted)
