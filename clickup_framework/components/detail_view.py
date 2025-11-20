"""
Task Detail View Formatter

Provides comprehensive detailed view of a single task with hierarchical relationships,
showing the task in context of its parent, children, and dependencies in a tree view.
"""

from typing import Dict, Any, Optional, List
from clickup_framework.utils.colors import (
    colorize, status_color, priority_color, TextColor, TextStyle,
    get_task_emoji, get_status_icon, TASK_TYPE_EMOJI, USE_COLORS
)
from clickup_framework.utils.text import strip_markdown, unescape_content
from clickup_framework.utils.markdown_renderer import render_markdown
from clickup_framework.utils.checklist_mapping import get_mapping_manager
from clickup_framework.utils.datetime import format_timestamp
from clickup_framework.components.options import FormatOptions
from clickup_framework.components.tree import TreeFormatter
from clickup_framework.components.task_formatter import RichTaskFormatter
from clickup_framework.components.dependency_analyzer import DependencyAnalyzer


class TaskDetailFormatter:
    """
    Formats comprehensive detailed view of a single task with relationship context.

    This formatter shows a task in context with:
    - Full task details (name, ID, status, priority, description, etc.)
    - Parent task chain (showing ancestry)
    - Sibling tasks (other children of the same parent)
    - Child tasks (subtasks in a tree view)
    - Dependencies (blocking/waiting on)
    - Checklists, attachments, comments
    """

    def __init__(self, client=None):
        """
        Initialize the detail formatter.

        Args:
            client: Optional ClickUpClient for fetching related tasks
        """
        self.client = client
        self.section_separator = "─" * 60
        self.task_formatter = RichTaskFormatter()

    def _colorize(
        self,
        text: str,
        color: Optional[TextColor] = None,
        style: Optional[TextStyle] = None,
        options: Optional[FormatOptions] = None
    ) -> str:
        """
        Apply color and style to text, respecting format options.

        Args:
            text: Text to colorize
            color: Text color to apply
            style: Text style to apply
            options: Format options (uses colorize_output to force colors)

        Returns:
            Colorized text string
        """
        force = options.colorize_output if options else False
        return colorize(text, color, style, force=force)

    def format_with_context(
        self,
        task: Dict[str, Any],
        all_tasks: Optional[List[Dict[str, Any]]] = None,
        options: Optional[FormatOptions] = None
    ) -> str:
        """
        Format a task with full relationship context showing parent chain,
        siblings, children, and dependencies in a tree view.

        Args:
            task: The main task to display
            all_tasks: All tasks (for resolving relationships)
            options: Format options

        Returns:
            Formatted task with relationship tree
        """
        if options is None:
            options = FormatOptions.detailed()

        sections = []

        # Header with task details
        sections.append(self._format_header(task, options))

        # Container/location
        container_info = self._format_container_info(task, options)
        if container_info:
            sections.append(container_info)

        # Metadata
        sections.append(self._format_metadata(task, options))

        # Description - show full description by default
        description = self._format_description(task, options, max_lines=None)
        if description:
            sections.append(description)

        # Tags
        tags = self._format_tags(task, options)
        if tags:
            sections.append(tags)

        # Relationship tree - this is the key section
        if all_tasks:
            relationship_tree = self._format_relationship_tree(task, all_tasks, options)
            if relationship_tree:
                sections.append(relationship_tree)

        # Dependency analysis - comprehensive dependency and relationship analysis
        if all_tasks:
            analyzer = DependencyAnalyzer(self.client)
            dependency_analysis = analyzer.analyze_dependencies(task, all_tasks, options)
            if dependency_analysis:
                sections.append(dependency_analysis)

        # Checklists
        checklists = self._format_checklists(task, options)
        if checklists:
            sections.append(checklists)

        # Attachments
        attachments = self._format_attachments(task, options)
        if attachments:
            sections.append(attachments)

        # Comments
        comments = self._format_comments(task, options)
        if comments:
            sections.append(comments)

        return "\n\n".join(sections)

    def format_detail(
        self,
        task: Dict[str, Any],
        options: Optional[FormatOptions] = None
    ) -> str:
        """
        Format a complete detailed view of a task (without relationship tree).

        Args:
            task: Task dictionary with all available fields
            options: Format options (uses detailed() preset if not provided)

        Returns:
            Formatted detailed task view
        """
        if options is None:
            options = FormatOptions.detailed()

        sections = []

        # Header section
        sections.append(self._format_header(task, options))

        # Container/location section
        container_info = self._format_container_info(task, options)
        if container_info:
            sections.append(container_info)

        # Metadata section (dates, assignees, etc)
        sections.append(self._format_metadata(task, options))

        # Description section
        description = self._format_description(task, options)
        if description:
            sections.append(description)

        # Tags section
        tags = self._format_tags(task, options)
        if tags:
            sections.append(tags)

        # Custom fields section
        custom_fields = self._format_custom_fields(task, options)
        if custom_fields:
            sections.append(custom_fields)

        # Relationships section (parent/children/dependencies)
        relationships = self._format_relationships(task, options)
        if relationships:
            sections.append(relationships)

        # Checklists section
        checklists = self._format_checklists(task, options)
        if checklists:
            sections.append(checklists)

        # Attachments section
        attachments = self._format_attachments(task, options)
        if attachments:
            sections.append(attachments)

        # Linked tasks section
        linked_tasks = self._format_linked_tasks(task, options)
        if linked_tasks:
            sections.append(linked_tasks)

        # Documents section
        documents = self._format_documents(task, options)
        if documents:
            sections.append(documents)

        # Comments section
        comments = self._format_comments(task, options)
        if comments:
            sections.append(comments)

        # Note: Subtasks are shown in format_with_context() method using relationship tree
        # The format_detail() method is for standalone task view without context

        # Time tracking section
        time_tracking = self._format_time_tracking(task, options)
        if time_tracking:
            sections.append(time_tracking)

        return "\n\n".join(sections)

    def _format_header(self, task: Dict[str, Any], options: FormatOptions) -> str:
        """Format the task header with name, status, priority, type."""
        lines = []

        # Title with emoji
        task_type = task.get('custom_type') or task.get('type', 'task')
        task_name = task.get('name', 'Unnamed Task')
        emoji = get_task_emoji(task_type, task_name) if options.show_type_emoji else ""

        title = f"{emoji} {task_name}" if emoji else task_name

        if options.colorize_output:
            title = self._colorize(title, TextColor.BRIGHT_WHITE, TextStyle.BOLD, options)

        lines.append(title)
        lines.append(self.section_separator)

        # ID
        if task.get('id'):
            id_label = "ID:"
            if options.colorize_output:
                id_label = self._colorize(id_label, TextColor.BRIGHT_BLACK, options=options)
            lines.append(f"{id_label} {task['id']}")

        # Status
        if task.get('status'):
            status = task['status'].get('status', '') if isinstance(task['status'], dict) else str(task['status'])
            status_label = "Status:"
            if options.colorize_output:
                status_label = self._colorize(status_label, TextColor.BRIGHT_BLACK, options=options)
                status = self._colorize(status, status_color(status), TextStyle.BOLD, options)
            lines.append(f"{status_label} {status}")

        # Priority
        if task.get('priority'):
            priority = task['priority'].get('priority', '') if isinstance(task['priority'], dict) else str(task['priority'])
            priority_label = "Priority:"
            if options.colorize_output:
                priority_label = self._colorize(priority_label, TextColor.BRIGHT_BLACK, options=options)
                priority = self._colorize(priority, priority_color(priority), options=options)
            lines.append(f"{priority_label} {priority}")

        # Type
        if task_type:
            type_label = "Type:"
            if options.colorize_output:
                type_label = colorize(type_label, TextColor.BRIGHT_BLACK)
            lines.append(f"{type_label} {task_type}")

        # URL
        if task.get('url'):
            url_label = "URL:"
            if options.colorize_output:
                url_label = colorize(url_label, TextColor.BRIGHT_BLACK)
            lines.append(f"{url_label} {task['url']}")

        return "\n".join(lines)

    def _format_container_info(self, task: Dict[str, Any], options: FormatOptions) -> str:
        """Format container hierarchy (Space > Folder > List) with IDs."""
        parts = []
        workspace_id = None
        folder_id = None
        list_id = None

        # Get workspace ID from task's team_id field (not from space)
        workspace_id = task.get('team_id')

        if task.get('space'):
            space = task['space']
            if isinstance(space, dict):
                space_name = space.get('name', '')
                if space_name:
                    parts.append(space_name)
            else:
                parts.append(str(space))

        if task.get('folder'):
            folder = task['folder']
            if isinstance(folder, dict):
                folder_name = folder.get('name', '')
                folder_id = folder.get('id', '')
                if folder_name:
                    parts.append(folder_name)
            else:
                parts.append(str(folder))

        if task.get('list'):
            list_obj = task['list']
            if isinstance(list_obj, dict):
                list_name = list_obj.get('name', '')
                list_id = list_obj.get('id', '')
                if list_name:
                    parts.append(list_name)
            else:
                parts.append(str(list_obj))

        if not parts:
            return ""

        lines = []
        label = "Location:"
        if options.colorize_output:
            label = colorize(label, TextColor.BRIGHT_BLACK)

        hierarchy = " > ".join(parts)
        if options.colorize_output:
            hierarchy = colorize(hierarchy, TextColor.CYAN)

        lines.append(f"{label} {hierarchy}")

        # Add workspace ID, folder ID, and list ID on separate lines if show_ids is enabled
        if options.show_ids:
            if workspace_id:
                ws_label = "Workspace ID:"
                if options.colorize_output:
                    ws_label = colorize(ws_label, TextColor.BRIGHT_BLACK)
                lines.append(f"{ws_label} {workspace_id}")

            if folder_id:
                folder_label = "Folder ID:"
                if options.colorize_output:
                    folder_label = colorize(folder_label, TextColor.BRIGHT_BLACK)
                lines.append(f"{folder_label} {folder_id}")

            if list_id:
                list_label = "List ID:"
                if options.colorize_output:
                    list_label = colorize(list_label, TextColor.BRIGHT_BLACK)
                lines.append(f"{list_label} {list_id}")

        return "\n".join(lines)

    def _format_metadata(self, task: Dict[str, Any], options: FormatOptions) -> str:
        """Format metadata like dates, assignees, creator."""
        lines = []

        # Dates
        if task.get('date_created'):
            label = "Created:"
            value = self._format_date_with_seconds(task['date_created'])
            if options.colorize_output:
                label = colorize(label, TextColor.BRIGHT_BLACK)
                value = colorize(value, TextColor.GREEN)
            lines.append(f"{label} {value}")

        if task.get('date_updated'):
            label = "Updated:"
            value = self._format_date_with_seconds(task['date_updated'])
            if options.colorize_output:
                label = colorize(label, TextColor.BRIGHT_BLACK)
                value = colorize(value, TextColor.YELLOW)
            lines.append(f"{label} {value}")

        if task.get('due_date'):
            label = "Due:"
            value = self._format_date_with_seconds(task['due_date'])
            if options.colorize_output:
                label = colorize(label, TextColor.BRIGHT_BLACK)
                value = colorize(value, TextColor.RED)
            lines.append(f"{label} {value}")

        if task.get('date_closed'):
            label = "Closed:"
            value = self._format_date_with_seconds(task['date_closed'])
            if options.colorize_output:
                label = colorize(label, TextColor.BRIGHT_BLACK)
                value = colorize(value, TextColor.GREEN)
            lines.append(f"{label} {value}")

        # Creator
        if task.get('creator'):
            creator = task['creator']
            creator_name = creator.get('username', '') if isinstance(creator, dict) else str(creator)
            if creator_name:
                label = "Creator:"
                if options.colorize_output:
                    label = colorize(label, TextColor.BRIGHT_BLACK)
                lines.append(f"{label} {creator_name}")

        # Assignees
        if task.get('assignees'):
            assignees = task['assignees']
            if assignees:
                names = [a.get('username', '') if isinstance(a, dict) else str(a) for a in assignees]
                names = [n for n in names if n]  # Filter empty
                if names:
                    label = "Assignees:"
                    value = ", ".join(names)
                    if options.colorize_output:
                        label = colorize(label, TextColor.BRIGHT_BLACK)
                        value = colorize(value, TextColor.BLUE)
                    lines.append(f"{label} {value}")

        # Watchers
        if task.get('watchers'):
            watchers = task['watchers']
            if watchers:
                names = [w.get('username', '') if isinstance(w, dict) else str(w) for w in watchers]
                names = [n for n in names if n]
                if names:
                    label = "Watchers:"
                    value = ", ".join(names)
                    if options.colorize_output:
                        label = colorize(label, TextColor.BRIGHT_BLACK)
                    lines.append(f"{label} {value}")

        return "\n".join(lines) if lines else ""

    def _format_description(self, task: Dict[str, Any], options: FormatOptions, max_lines: Optional[int] = None) -> str:
        """
        Format task description with markdown rendering.

        Args:
            task: Task dictionary
            options: Format options
            max_lines: Maximum number of lines to display (None = all lines)

        Returns:
            Formatted description string
        """
        description = task.get('description') or ''
        description = description.strip()
        if not description:
            return ""

        # Unescape content from ClickUp API (converts \\n to actual newlines)
        description = unescape_content(description)

        lines = []
        header = "📝 Description:"
        if options.colorize_output:
            header = colorize(header, TextColor.BRIGHT_WHITE, TextStyle.BOLD)
        lines.append(header)
        lines.append("")

        # Render markdown to ANSI formatting
        # Use colorization if either option is enabled or USE_COLORS is True
        should_colorize = options.colorize_output or USE_COLORS
        if should_colorize:
            rendered = render_markdown(description, colorize_output=True)
        else:
            rendered = strip_markdown(description)

        # Split into lines and apply max_lines limit if specified
        desc_lines = rendered.split('\n')
        if max_lines is not None and len(desc_lines) > max_lines:
            desc_lines = desc_lines[:max_lines]
            # Add ellipsis to indicate truncation
            if desc_lines:
                desc_lines.append("  ...")

        # Add indentation for readability
        for line in desc_lines:
            lines.append(f"  {line}")

        return "\n".join(lines)

    def _format_tags(self, task: Dict[str, Any], options: FormatOptions) -> str:
        """Format tags section."""
        tags = task.get('tags', [])
        if not tags:
            return ""

        lines = []
        header = "🏷️  Tags:"
        if options.colorize_output:
            header = colorize(header, TextColor.BRIGHT_WHITE, TextStyle.BOLD)
        lines.append(header)

        # Format tags
        tag_names = []
        for tag in tags:
            tag_name = tag.get('name', '') if isinstance(tag, dict) else str(tag)
            if tag_name:
                if options.colorize_output and isinstance(tag, dict) and tag.get('tag_fg'):
                    # Use tag's color if available
                    tag_names.append(f"#{tag_name}")
                else:
                    tag_names.append(f"#{tag_name}")

        if tag_names:
            tags_str = "  " + ", ".join(tag_names)
            if options.colorize_output:
                tags_str = colorize(tags_str, TextColor.MAGENTA)
            lines.append(tags_str)

        return "\n".join(lines)

    def _format_custom_fields(self, task: Dict[str, Any], options: FormatOptions) -> str:
        """Format custom fields with GUIDs."""
        custom_fields = task.get('custom_fields', [])
        if not custom_fields:
            return ""

        lines = []
        header = "⚙️  Custom Fields:"
        if options.colorize_output:
            header = colorize(header, TextColor.BRIGHT_WHITE, TextStyle.BOLD)
        lines.append(header)

        for field in custom_fields:
            if isinstance(field, dict):
                name = field.get('name', 'Unknown')
                value = field.get('value', '')
                field_id = field.get('id', '')  # Get the GUID/field ID

                # Format based on type
                field_type = field.get('type', '')
                if field_type == 'drop_down' and isinstance(value, dict):
                    value = value.get('name', value)

                # Format field name with GUID
                if field_id:
                    if options.colorize_output:
                        field_label = f"  {name} " + colorize(f"[{field_id}]", TextColor.BRIGHT_BLACK) + ":"
                    else:
                        field_label = f"  {name} [{field_id}]:"
                else:
                    field_label = f"  {name}:"

                if options.colorize_output and not field_id:
                    field_label = colorize(field_label, TextColor.BRIGHT_BLACK)

                lines.append(f"{field_label} {value}")

        return "\n".join(lines)

    def _format_relationship_tree(
        self,
        task: Dict[str, Any],
        all_tasks: List[Dict[str, Any]],
        options: FormatOptions
    ) -> str:
        """
        Format a comprehensive relationship tree showing parent chain, siblings, and children.

        This shows the task in its full hierarchical context:
        - Parent chain (grandparent > parent)
        - Current task (highlighted)
        - Siblings (other children of parent)
        - Children (subtasks)
        - Dependencies
        """
        lines = []
        header = "🌳 Task Relationships:"
        if options.colorize_output:
            header = colorize(header, TextColor.BRIGHT_WHITE, TextStyle.BOLD)
        lines.append(header)
        lines.append("")

        task_id = task.get('id')
        parent_id = task.get('parent')

        # Build task lookup map
        task_map = {t.get('id'): t for t in all_tasks if t.get('id')}

        # 1. Show parent chain if exists
        if parent_id:
            parent_chain = self._build_parent_chain(task_id, task_map)
            if parent_chain:
                chain_header = "  📊 Parent Chain:"
                if options.colorize_output:
                    chain_header = colorize(chain_header, TextColor.CYAN, TextStyle.BOLD)
                lines.append(chain_header)

                # Show from top ancestor down to immediate parent
                for depth, parent_task in enumerate(parent_chain):
                    indent = "  " + ("  " * (depth + 1))
                    parent_name = parent_task.get('name', 'Unnamed')
                    parent_status = parent_task.get('status', {})
                    if isinstance(parent_status, dict):
                        parent_status = parent_status.get('status', '')

                    prefix = "└─" if depth == len(parent_chain) - 1 else "├─"
                    line = f"{indent}{prefix} {parent_name}"

                    if parent_status:
                        status_str = f" [{parent_status}]"
                        if options.colorize_output:
                            status_str = colorize(status_str, status_color(parent_status))
                        line += status_str

                    if options.colorize_output:
                        line = colorize(line, TextColor.CYAN)
                    lines.append(line)

                lines.append("")

        # 2. Show current task (highlighted)
        current_header = "  👉 Current Task:"
        if options.colorize_output:
            current_header = colorize(current_header, TextColor.BRIGHT_YELLOW, TextStyle.BOLD)
        lines.append(current_header)

        task_line = f"    • {task.get('name', 'Unnamed')}"
        task_status = task.get('status', {})
        if isinstance(task_status, dict):
            task_status = task_status.get('status', '')

        if task_status:
            status_str = f" [{task_status}]"
            if options.colorize_output:
                status_str = colorize(status_str, status_color(task_status))
            task_line += status_str

        if options.colorize_output:
            task_line = colorize(task_line, TextColor.BRIGHT_YELLOW, TextStyle.BOLD)
        lines.append(task_line)
        lines.append("")

        # 3. Show siblings (other children of same parent)
        if parent_id:
            siblings = [t for t in all_tasks
                       if t.get('parent') == parent_id
                       and t.get('id') != task_id]

            if siblings:
                sibling_header = f"  👥 Siblings ({len(siblings)}):"
                if options.colorize_output:
                    sibling_header = colorize(sibling_header, TextColor.MAGENTA, TextStyle.BOLD)
                lines.append(sibling_header)

                for sibling in siblings[:5]:  # Show first 5
                    sibling_name = sibling.get('name', 'Unnamed')
                    sibling_status = sibling.get('status', {})
                    if isinstance(sibling_status, dict):
                        sibling_status = sibling_status.get('status', '')

                    sibling_line = f"    • {sibling_name}"
                    if sibling_status:
                        status_str = f" [{sibling_status}]"
                        if options.colorize_output:
                            status_str = colorize(status_str, status_color(sibling_status))
                        sibling_line += status_str

                    if options.colorize_output:
                        sibling_line = colorize(sibling_line, TextColor.MAGENTA)
                    lines.append(sibling_line)

                if len(siblings) > 5:
                    more_line = f"    ... and {len(siblings) - 5} more siblings"
                    if options.colorize_output:
                        more_line = colorize(more_line, TextColor.BRIGHT_BLACK)
                    lines.append(more_line)

                lines.append("")

        # 4. Show children (subtasks) in tree view
        children = [t for t in all_tasks if t.get('parent') == task_id]

        if children:
            children_header = f"  📂 Subtasks ({len(children)}):"
            if options.colorize_output:
                children_header = colorize(children_header, TextColor.GREEN, TextStyle.BOLD)
            lines.append(children_header)

            # Build recursive tree of children
            tree_lines = self._build_child_tree(task_id, all_tasks, options, depth=0, max_depth=3)
            lines.extend(tree_lines)
            lines.append("")

        # 5. Show dependencies
        dependencies = task.get('dependencies', [])
        if dependencies:
            dep_header = f"  🔗 Dependencies ({len(dependencies)}):"
            if options.colorize_output:
                dep_header = colorize(dep_header, TextColor.YELLOW, TextStyle.BOLD)
            lines.append(dep_header)

            for dep in dependencies[:5]:
                if isinstance(dep, dict):
                    dep_id = dep.get('depends_on', '')
                    dep_task = task_map.get(dep_id)

                    if dep_task:
                        dep_name = dep_task.get('name', 'Unnamed')
                        dep_status = dep_task.get('status', {})
                        if isinstance(dep_status, dict):
                            dep_status = dep_status.get('status', '')

                        dep_line = f"    • {dep_name}"
                        if dep_status:
                            status_str = f" [{dep_status}]"
                            if options.colorize_output:
                                status_str = colorize(status_str, status_color(dep_status))
                            dep_line += status_str

                        if options.colorize_output:
                            dep_line = colorize(dep_line, TextColor.YELLOW)
                        lines.append(dep_line)

            if len(dependencies) > 5:
                more_line = f"    ... and {len(dependencies) - 5} more dependencies"
                if options.colorize_output:
                    more_line = colorize(more_line, TextColor.BRIGHT_BLACK)
                lines.append(more_line)

        return "\n".join(lines)

    def _build_parent_chain(
        self,
        task_id: str,
        task_map: Dict[str, Dict[str, Any]]
    ) -> List[Dict[str, Any]]:
        """
        Build the chain of parent tasks from root to immediate parent.

        Args:
            task_id: ID of the task
            task_map: Map of task ID to task dict

        Returns:
            List of parent tasks from top ancestor to immediate parent
        """
        chain = []
        current = task_map.get(task_id)

        if not current:
            return chain

        parent_id = current.get('parent')

        # Walk up the parent chain
        seen = set()
        while parent_id and parent_id not in seen:
            seen.add(parent_id)
            parent = task_map.get(parent_id)

            if parent:
                chain.append(parent)
                parent_id = parent.get('parent')
            else:
                break

        # Reverse to get top-down order
        return list(reversed(chain))

    def _get_smart_indicators(self, task: Dict[str, Any], options: FormatOptions) -> List[str]:
        """
        Get smart indicators for a task (dependencies, blockers, linked tasks, assignees, due dates, time tracking).

        Args:
            task: Task dictionary
            options: Format options

        Returns:
            List of indicator strings
        """
        indicators = []

        # Dependencies and blockers
        dependencies = task.get('dependencies', [])
        if dependencies:
            waiting_on = []
            blocking = []

            for dep in dependencies:
                if isinstance(dep, dict):
                    dep_type = dep.get('type', 'waiting_on')
                    if dep_type == 'waiting_on':
                        waiting_on.append(dep.get('task_id'))
                    elif dep_type == 'blocking':
                        blocking.append(dep.get('task_id'))

            if waiting_on:
                count = len(waiting_on)
                if options.colorize_output:
                    indicators.append(colorize(f"⏳{count}", TextColor.YELLOW))
                else:
                    indicators.append(f"D:{count}")

            if blocking:
                count = len(blocking)
                if options.colorize_output:
                    indicators.append(colorize(f"🚫{count}", TextColor.RED))
                else:
                    indicators.append(f"B:{count}")

        # Linked tasks
        linked_tasks = task.get('linked_tasks', [])
        if linked_tasks:
            count = len(linked_tasks)
            if options.colorize_output:
                indicators.append(colorize(f"🔗{count}", TextColor.CYAN))
            else:
                indicators.append(f"L:{count}")

        # Assignees
        assignees = task.get('assignees', [])
        if assignees:
            if options.colorize_output:
                if len(assignees) == 1:
                    assignee = assignees[0]
                    username = assignee.get('username', '')
                    initials = ''.join([c[0].upper() for c in username.split('_')[:2]]) if username else '?'
                    indicators.append(colorize(f"👤{initials}", TextColor.BLUE))
                else:
                    indicators.append(colorize(f"👥{len(assignees)}", TextColor.BLUE))
            else:
                indicators.append(f"A:{len(assignees)}")

        # Due date warnings
        due_date = task.get('due_date')
        if due_date:
            from datetime import datetime, timezone
            try:
                if isinstance(due_date, str):
                    due_timestamp = int(due_date) / 1000
                else:
                    due_timestamp = due_date / 1000

                due_dt = datetime.fromtimestamp(due_timestamp, tz=timezone.utc)
                now = datetime.now(timezone.utc)
                days_until_due = (due_dt - now).days

                if days_until_due < 0:
                    # Overdue
                    if options.colorize_output:
                        indicators.append(colorize(f"🔴{abs(days_until_due)}d", TextColor.RED, TextStyle.BOLD))
                    else:
                        indicators.append(f"OVERDUE:{abs(days_until_due)}d")
                elif days_until_due == 0:
                    # Due today
                    if options.colorize_output:
                        indicators.append(colorize("📅TODAY", TextColor.YELLOW, TextStyle.BOLD))
                    else:
                        indicators.append("DUE:TODAY")
                elif days_until_due <= 3:
                    # Due soon
                    if options.colorize_output:
                        indicators.append(colorize(f"⚠️{days_until_due}d", TextColor.YELLOW))
                    else:
                        indicators.append(f"DUE:{days_until_due}d")
            except (ValueError, TypeError):
                pass

        # Time tracking
        time_estimate = task.get('time_estimate')
        time_spent = task.get('time_spent', 0)
        if time_estimate or time_spent:
            if time_estimate and time_spent:
                hours_estimate = time_estimate / 3600000
                hours_spent = time_spent / 3600000
                if options.colorize_output:
                    if hours_spent > hours_estimate:
                        indicators.append(colorize(f"⏱️{hours_spent:.1f}/{hours_estimate:.1f}h", TextColor.RED))
                    else:
                        indicators.append(colorize(f"⏱️{hours_spent:.1f}/{hours_estimate:.1f}h", TextColor.GREEN))
                else:
                    indicators.append(f"T:{hours_spent:.1f}/{hours_estimate:.1f}h")
            elif time_estimate:
                hours_estimate = time_estimate / 3600000
                if options.colorize_output:
                    indicators.append(colorize(f"⏱️{hours_estimate:.1f}h", TextColor.CYAN))
                else:
                    indicators.append(f"T:{hours_estimate:.1f}h")
            elif time_spent:
                hours_spent = time_spent / 3600000
                if options.colorize_output:
                    indicators.append(colorize(f"⏱️{hours_spent:.1f}h", TextColor.YELLOW))
                else:
                    indicators.append(f"T:{hours_spent:.1f}h")

        return indicators

    def _format_subtask_description(self, task: Dict[str, Any], options: FormatOptions, max_lines: Optional[int] = 9, indent: str = "  ") -> List[str]:
        """
        Format subtask description preview with line limit.

        Args:
            task: Task dictionary
            options: Format options
            max_lines: Maximum number of lines to display (None for no limit)
            indent: Indentation prefix

        Returns:
            List of formatted description lines
        """
        description = task.get('description', '').strip()
        if not description:
            return []

        # Unescape content
        description = unescape_content(description)

        # Render markdown if colorization enabled
        should_colorize = options.colorize_output or USE_COLORS
        if should_colorize:
            rendered = render_markdown(description, colorize_output=True)
        else:
            rendered = strip_markdown(description)

        # Split and limit lines
        desc_lines = rendered.split('\n')
        if max_lines is not None and len(desc_lines) > max_lines:
            desc_lines = desc_lines[:max_lines]
            desc_lines.append("...")

        # Add indentation and dim color
        formatted_lines = []
        for line in desc_lines:
            formatted_line = f"{indent}{line}"
            if options.colorize_output:
                formatted_line = colorize(formatted_line, TextColor.BRIGHT_BLACK)
            formatted_lines.append(formatted_line)

        return formatted_lines

    def _format_subtask_comments(self, task: Dict[str, Any], status_name: str, options: FormatOptions, indent: str = "  ") -> List[str]:
        """
        Format comments for a subtask based on completion status.

        Args:
            task: Task dictionary
            status_name: Status name (to check if complete)
            options: Format options
            indent: Indentation prefix

        Returns:
            List of formatted comment lines
        """
        comments = task.get('comments', [])
        if not comments:
            return []

        # Check if task is completed
        status_lower = str(status_name).lower().strip() if status_name else ""
        is_completed = status_lower in ('complete', 'completed', 'done', 'closed')

        lines = []

        if is_completed:
            # Show comment count only for completed subtasks
            comment_count = len(comments)
            comment_line = f"{indent}💬 {comment_count} comment{'s' if comment_count != 1 else ''}"
            if options.colorize_output:
                comment_line = colorize(comment_line, TextColor.BRIGHT_BLACK)
            lines.append(comment_line)
        else:
            # Show latest 2 comments for incomplete subtasks
            # Sort by date descending (newest first)
            sorted_comments = sorted(
                comments,
                key=lambda c: c.get('date', 0) if isinstance(c.get('date'), (int, float)) else 0,
                reverse=True
            )
            latest_comments = sorted_comments[:2]

            for comment in latest_comments:
                user = comment.get('user', {})
                username = user.get('username', 'Unknown') if isinstance(user, dict) else 'Unknown'
                comment_text = comment.get('comment_text', '')

                # Truncate long comments
                if len(comment_text) > 60:
                    comment_text = comment_text[:60] + "..."

                comment_line = f"{indent}💬 {username}: {comment_text}"
                if options.colorize_output:
                    comment_line = colorize(comment_line, TextColor.CYAN)
                lines.append(comment_line)

        return lines

    def _build_child_tree(
        self,
        parent_id: str,
        all_tasks: List[Dict[str, Any]],
        options: FormatOptions,
        depth: int = 0,
        max_depth: int = 3
    ) -> List[str]:
        """
        Recursively build a tree view of child tasks with enhanced details.

        Args:
            parent_id: Parent task ID
            all_tasks: All tasks
            options: Format options
            depth: Current depth
            max_depth: Maximum depth to traverse

        Returns:
            List of formatted tree lines
        """
        if depth >= max_depth:
            return []

        lines = []
        children = [t for t in all_tasks if t.get('parent') == parent_id]

        if not children:
            return lines

        for i, child in enumerate(children):
            is_last = i == len(children) - 1
            prefix = "    " + ("  " * depth)
            branch = "└─" if is_last else "├─"

            # For continuation lines (descriptions, comments), use │ for non-last items
            if is_last:
                continuation_prefix = prefix + "   "  # 3 spaces to match └─ indent
            else:
                continuation_prefix = prefix + "│  "  # vertical pipe + 2 spaces

            # Get child details
            child_name = child.get('name', 'Unnamed')
            child_status = child.get('status', {})
            if isinstance(child_status, dict):
                child_status_name = child_status.get('status', '')
            else:
                child_status_name = child_status

            # Build task line with smart indicators
            child_line_parts = [f"{prefix}{branch}"]

            # Add task ID if enabled
            if options.show_ids and child.get('id'):
                child_id_str = f"[{child['id']}]"
                if options.colorize_output:
                    child_id_str = colorize(child_id_str, TextColor.BRIGHT_BLACK)
                child_line_parts.append(child_id_str)

            # Add smart indicators using RichTaskFormatter logic
            child_line_parts.extend(self._get_smart_indicators(child, options))

            # Add task type emoji
            if options.show_type_emoji:
                task_type = child.get('custom_type') or 'task'
                emoji = get_task_emoji(task_type, child_name)
                child_line_parts.append(emoji)

            # Add status icon
            status_icon = get_status_icon(child_status_name or '', fallback_to_code=True)
            if options.colorize_output:
                status_icon = colorize(status_icon, status_color(child_status_name))
            child_line_parts.append(status_icon)

            # Add task name
            if options.colorize_output:
                child_name_colored = colorize(child_name, status_color(child_status_name))
                child_line_parts.append(child_name_colored)
            else:
                child_line_parts.append(child_name)

            line = " ".join(child_line_parts)
            lines.append(line)

            # Add description preview (full description, no line limit)
            child_description = child.get('description', '').strip()
            if child_description:
                desc_lines = self._format_subtask_description(child, options, max_lines=None, indent=continuation_prefix)
                lines.extend(desc_lines)

            # Add comments based on completion status
            comment_lines = self._format_subtask_comments(child, child_status_name, options, indent=continuation_prefix)
            if comment_lines:
                lines.extend(comment_lines)

            # Recursively add grandchildren
            child_id = child.get('id')
            if child_id:
                grandchildren_lines = self._build_child_tree(
                    child_id, all_tasks, options, depth + 1, max_depth
                )
                lines.extend(grandchildren_lines)

        return lines

    def _format_relationships(self, task: Dict[str, Any], options: FormatOptions) -> str:
        """Format parent/child and dependency relationships."""
        lines = []
        has_relationships = False

        # Parent
        if task.get('parent'):
            has_relationships = True
            parent = task['parent']
            parent_name = parent.get('name', parent.get('id', 'Unknown')) if isinstance(parent, dict) else str(parent)

            label = "  Parent:"
            if options.colorize_output:
                label = colorize(label, TextColor.BRIGHT_BLACK)
                parent_name = colorize(parent_name, TextColor.CYAN)
            lines.append(f"{label} {parent_name}")

        # Children
        if task.get('children'):
            children = task['children']
            if children:
                has_relationships = True
                child_count = len(children)
                label = f"  Children ({child_count}):"
                if options.colorize_output:
                    label = colorize(label, TextColor.BRIGHT_BLACK)
                lines.append(label)

                for child in children[:5]:  # Show first 5
                    child_name = child.get('name', child.get('id', 'Unknown')) if isinstance(child, dict) else str(child)
                    child_line = f"    • {child_name}"
                    if options.colorize_output:
                        child_line = colorize(child_line, TextColor.CYAN)
                    lines.append(child_line)

                if len(children) > 5:
                    more_line = f"    ... and {len(children) - 5} more"
                    if options.colorize_output:
                        more_line = colorize(more_line, TextColor.BRIGHT_BLACK)
                    lines.append(more_line)

        # Dependencies
        if task.get('dependencies'):
            dependencies = task['dependencies']
            if dependencies:
                has_relationships = True
                dep_count = len(dependencies)
                label = f"  Dependencies ({dep_count}):"
                if options.colorize_output:
                    label = colorize(label, TextColor.BRIGHT_BLACK)
                lines.append(label)

                for dep in dependencies[:5]:
                    dep_name = dep.get('name', dep.get('depends_on', 'Unknown')) if isinstance(dep, dict) else str(dep)
                    dep_line = f"    • {dep_name}"
                    if options.colorize_output:
                        dep_line = colorize(dep_line, TextColor.YELLOW)
                    lines.append(dep_line)

                if len(dependencies) > 5:
                    more_line = f"    ... and {len(dependencies) - 5} more"
                    if options.colorize_output:
                        more_line = colorize(more_line, TextColor.BRIGHT_BLACK)
                    lines.append(more_line)

        if not has_relationships:
            return ""

        header = "🔗 Relationships:"
        if options.colorize_output:
            header = colorize(header, TextColor.BRIGHT_WHITE, TextStyle.BOLD)

        return header + "\n" + "\n".join(lines)

    def _format_checklists(self, task: Dict[str, Any], options: FormatOptions) -> str:
        """Format checklists with completion status and numeric indices."""
        checklists = task.get('checklists', [])
        if not checklists:
            return ""

        # Get mapping manager and task ID
        mapping_manager = get_mapping_manager()
        task_id = task.get('id')

        # Update mappings from task data to ensure all checklists/items are mapped
        if task_id:
            mapping_manager.update_mappings_from_task(task_id, task)

        lines = []
        header = "☑️  Checklists:"
        if options.colorize_output:
            header = colorize(header, TextColor.BRIGHT_WHITE, TextStyle.BOLD)
        lines.append(header)

        for checklist in checklists:
            if isinstance(checklist, dict):
                name = checklist.get('name', 'Unnamed Checklist')
                checklist_id = checklist.get('id')
                items = checklist.get('items', [])

                completed = sum(1 for item in items if isinstance(item, dict) and item.get('resolved'))
                total = len(items)

                # Get checklist index
                checklist_index = ""
                if task_id and checklist_id:
                    index = mapping_manager.get_checklist_index(task_id, checklist_id)
                    if index:
                        checklist_index = f"[{index}] "

                checklist_header = f"\n  {checklist_index}{name} ({completed}/{total})"
                if options.colorize_output:
                    completion_pct = (completed / total * 100) if total > 0 else 0
                    color = TextColor.GREEN if completion_pct == 100 else TextColor.YELLOW if completion_pct >= 50 else TextColor.RED
                    checklist_header = colorize(checklist_header, color, TextStyle.BOLD)
                lines.append(checklist_header)

                for item in items:
                    if isinstance(item, dict):
                        item_name = item.get('name', '')
                        item_id = item.get('id')
                        is_resolved = item.get('resolved', False)
                        checkbox = "✓" if is_resolved else "○"

                        # Get item index
                        item_index = ""
                        if task_id and checklist_id and item_id:
                            index = mapping_manager.get_item_index(task_id, checklist_id, item_id)
                            if index:
                                item_index = f"[{index}] "

                        item_line = f"    {checkbox} {item_index}{item_name}"
                        if options.colorize_output:
                            if is_resolved:
                                item_line = colorize(item_line, TextColor.BRIGHT_BLACK)
                            lines.append(item_line)
                        else:
                            lines.append(item_line)

        return "\n".join(lines)

    def _format_attachments(self, task: Dict[str, Any], options: FormatOptions) -> str:
        """Format attachments list."""
        attachments = task.get('attachments', [])
        if not attachments:
            return ""

        lines = []
        header = f"📎 Attachments ({len(attachments)}):"
        if options.colorize_output:
            header = colorize(header, TextColor.BRIGHT_WHITE, TextStyle.BOLD)
        lines.append(header)

        for attachment in attachments:
            if isinstance(attachment, dict):
                name = attachment.get('title') or attachment.get('name', 'Unnamed')
                url = attachment.get('url', '')
                size = attachment.get('size', 0)

                # Format size
                size_str = self._format_file_size(size) if size else ""

                attachment_line = f"  • {name}"
                if size_str:
                    attachment_line += f" ({size_str})"

                if options.colorize_output:
                    attachment_line = colorize(attachment_line, TextColor.CYAN)
                lines.append(attachment_line)

                if url:
                    url_line = f"    {url}"
                    if options.colorize_output:
                        url_line = colorize(url_line, TextColor.BRIGHT_BLACK)
                    lines.append(url_line)

        return "\n".join(lines)

    def _format_linked_tasks(self, task: Dict[str, Any], options: FormatOptions) -> str:
        """
        Format linked tasks with task type and title (no description).

        Args:
            task: Task dictionary
            options: Format options

        Returns:
            Formatted linked tasks section
        """
        linked_tasks = task.get('linked_tasks', [])
        if not linked_tasks:
            return ""

        lines = []
        header = f"🔗 Linked Tasks ({len(linked_tasks)}):"
        if options.colorize_output:
            header = colorize(header, TextColor.BRIGHT_WHITE, TextStyle.BOLD)
        lines.append(header)

        for linked in linked_tasks:
            if isinstance(linked, dict):
                # Extract task info
                task_id = linked.get('task_id', '')
                task_name = linked.get('name', 'Unnamed Task')
                task_type = linked.get('custom_type') or linked.get('type', 'task')

                # Build task line with type emoji and title
                task_emoji = get_task_emoji(task_type, task_name) if options.show_type_emoji else ""

                if task_emoji:
                    task_line = f"  {task_emoji} {task_name}"
                else:
                    task_line = f"  • {task_name}"

                # Add task type label
                if task_type and task_type != 'task':
                    type_label = f" ({task_type})"
                    if options.colorize_output:
                        type_label = colorize(type_label, TextColor.BRIGHT_BLACK)
                    task_line += type_label

                # Add task ID if enabled
                if options.show_ids and task_id:
                    id_str = f" [{task_id}]"
                    if options.colorize_output:
                        id_str = colorize(id_str, TextColor.BRIGHT_BLACK)
                    task_line += id_str

                if options.colorize_output:
                    task_line = colorize(task_line, TextColor.CYAN)

                lines.append(task_line)

        return "\n".join(lines)

    def _format_documents(self, task: Dict[str, Any], options: FormatOptions) -> str:
        """Format linked documents with page treeview."""
        from clickup_framework.components.tree import TreeFormatter
        from clickup_framework.apis.docs import DocsAPI

        # Check if task has linked docs
        linked_docs = task.get('linked_docs', [])
        if not linked_docs and not self.client:
            return ""

        # If no linked docs in task data, try to fetch from relationships
        if not linked_docs:
            return ""

        lines = []
        header = f"📄 Documents ({len(linked_docs)}):"
        if options.colorize_output:
            header = colorize(header, TextColor.BRIGHT_WHITE, TextStyle.BOLD)
        lines.append(header)

        # Fetch and display each document with its pages
        if self.client:
            docs_api = DocsAPI(self.client)
            workspace_id = task.get('team_id', '')

            for doc_ref in linked_docs:
                if isinstance(doc_ref, dict):
                    doc_id = doc_ref.get('doc_id', '')
                    doc_name = doc_ref.get('name', 'Unnamed Document')
                elif isinstance(doc_ref, str):
                    doc_id = doc_ref
                    doc_name = 'Document'
                else:
                    continue

                # Format document header
                if options.colorize_output:
                    doc_header = colorize(f"\n  📘 {doc_name}", TextColor.BRIGHT_CYAN, TextStyle.BOLD)
                else:
                    doc_header = f"\n  📘 {doc_name}"
                lines.append(doc_header)

                # Fetch pages for this document
                if workspace_id and doc_id:
                    try:
                        pages_result = docs_api.get_doc_pages(workspace_id, doc_id)
                        pages = pages_result.get('pages', [])

                        if pages:
                            # Build page tree
                            def format_page_node(page):
                                page_name = page.get('name', 'Unnamed Page')
                                if options.colorize_output:
                                    return colorize(f"📄 {page_name}", TextColor.CYAN)
                                return f"📄 {page_name}"

                            def get_page_children(page):
                                # Placeholder for nested pages
                                return []

                            # Display pages in tree format
                            for page in pages:
                                page_lines = TreeFormatter.build_tree(
                                    [page],
                                    format_page_node,
                                    get_page_children,
                                    prefix="    ",
                                    is_last=True
                                )
                                lines.extend(page_lines)
                        else:
                            no_pages = "    (No pages)"
                            if options.colorize_output:
                                no_pages = colorize(no_pages, TextColor.BRIGHT_BLACK)
                            lines.append(no_pages)

                    except Exception:
                        # If fetching pages fails, just show the document
                        error_msg = "    (Unable to fetch pages)"
                        if options.colorize_output:
                            error_msg = colorize(error_msg, TextColor.BRIGHT_BLACK)
                        lines.append(error_msg)

        return "\n".join(lines) if len(lines) > 1 else ""

    def _format_comments(self, task: Dict[str, Any], options: FormatOptions) -> str:
        """Format comments section in threaded treeview format - shows all comments by default."""
        from clickup_framework.components.tree import TreeFormatter
        from clickup_framework.resources import CommentsAPI

        all_comments = task.get('comments', [])
        if not all_comments:
            return ""

        lines = []
        header = f"💬 Comments ({len(all_comments)}):"
        if options.colorize_output:
            header = colorize(header, TextColor.BRIGHT_WHITE, TextStyle.BOLD)
        lines.append(header)

        # Sort by date descending (newest first) - show all comments (not just 5)
        sorted_comments = sorted(
            all_comments,
            key=lambda c: c.get('date', 0) if isinstance(c.get('date'), (int, float)) else 0,
            reverse=True
        )

        # Fetch threaded replies for each comment if we have a client
        if self.client:
            comments_api = CommentsAPI(self.client)
            comments_with_replies = []

            for comment in sorted_comments:
                comment_copy = comment.copy()
                comment_copy['_replies'] = []

                # Check if comment has replies
                reply_count = comment.get('reply_count', 0)
                if reply_count and int(reply_count) > 0:
                    try:
                        # Fetch threaded replies
                        replies_result = comments_api.get_threaded_comments(comment['id'])
                        replies = replies_result.get('comments', [])
                        comment_copy['_replies'] = replies
                    except Exception:
                        # If fetching replies fails, just skip them
                        pass

                comments_with_replies.append(comment_copy)
        else:
            comments_with_replies = sorted_comments

        # Format comments using TreeFormatter
        def format_comment_node(comment):
            """Format a comment for tree display."""
            user = comment.get('user', {})
            username = user.get('username', 'Unknown') if isinstance(user, dict) else 'Unknown'
            comment_text = comment.get('comment_text', '')
            reply_count = comment.get('reply_count', 0)

            # Format comment header
            if options.colorize_output:
                header_text = colorize(f"{username}", TextColor.BLUE, TextStyle.BOLD)
                if reply_count and int(reply_count) > 0:
                    header_text += colorize(f" ({reply_count} replies)", TextColor.BRIGHT_BLACK)
            else:
                header_text = f"{username}"
                if reply_count and int(reply_count) > 0:
                    header_text += f" ({reply_count} replies)"

            # Truncate comment text for tree display
            if comment_text:
                max_len = 80
                if len(comment_text) > max_len:
                    text_preview = comment_text[:max_len] + "..."
                else:
                    text_preview = comment_text

                if options.colorize_output:
                    text_preview = colorize(text_preview, TextColor.WHITE)

                return f"{header_text}: {text_preview}"
            else:
                return header_text

        def get_comment_children(comment):
            """Get replies for a comment."""
            return comment.get('_replies', [])

        # Display using TreeFormatter
        lines.append("")
        for comment in comments_with_replies:
            tree_lines = TreeFormatter.build_tree(
                [comment],
                format_comment_node,
                get_comment_children,
                prefix="  ",
                is_last=True
            )
            lines.extend(tree_lines)

        return "\n".join(lines)

    def _format_subtasks(self, task: Dict[str, Any], all_tasks: List[Dict[str, Any]], options: FormatOptions) -> str:
        """Format subtasks in treeview with comment and attachment counts."""
        from clickup_framework.components.tree import TreeFormatter

        # Get subtasks from all_tasks if available
        if not all_tasks:
            return ""

        task_id = task.get('id')
        if not task_id:
            return ""

        # Find all subtasks (tasks where parent is this task)
        subtasks = [t for t in all_tasks if t.get('parent') == task_id]

        if not subtasks:
            return ""

        lines = []
        header = f"📋 Subtasks ({len(subtasks)}):"
        if options.colorize_output:
            header = colorize(header, TextColor.BRIGHT_WHITE, TextStyle.BOLD)
        lines.append(header)

        # Format subtasks using TreeFormatter
        def format_subtask_node(subtask):
            """Format a subtask for tree display."""
            name = subtask.get('name', 'Unnamed Task')
            status = subtask.get('status', {})
            status_name = status.get('status', 'Unknown') if isinstance(status, dict) else 'Unknown'

            # Get counts
            comment_count = len(subtask.get('comments', []))
            attachment_count = len(subtask.get('attachments', []))

            # Build display string
            parts = []
            if options.colorize_output:
                parts.append(colorize(name, TextColor.CYAN))
                parts.append(colorize(f"[{status_name}]", TextColor.BRIGHT_BLACK))
            else:
                parts.append(name)
                parts.append(f"[{status_name}]")

            # Add counts if present
            counts = []
            if comment_count > 0:
                count_str = f"💬 {comment_count}"
                if options.colorize_output:
                    count_str = colorize(count_str, TextColor.BLUE)
                counts.append(count_str)

            if attachment_count > 0:
                count_str = f"📎 {attachment_count}"
                if options.colorize_output:
                    count_str = colorize(count_str, TextColor.GREEN)
                counts.append(count_str)

            if counts:
                parts.append("(" + " ".join(counts) + ")")

            return " ".join(parts)

        def get_subtask_children(subtask):
            """Get child subtasks."""
            subtask_id = subtask.get('id')
            if not subtask_id:
                return []
            return [t for t in all_tasks if t.get('parent') == subtask_id]

        # Display using TreeFormatter
        lines.append("")
        tree_lines = TreeFormatter.build_tree(
            subtasks,
            format_subtask_node,
            get_subtask_children,
            prefix="  ",
            is_last=True
        )
        lines.extend(tree_lines)

        return "\n".join(lines)

    def _format_time_tracking(self, task: Dict[str, Any], options: FormatOptions) -> str:
        """Format time tracking information."""
        time_estimate = task.get('time_estimate')
        time_spent = task.get('time_spent')

        if not time_estimate and not time_spent:
            return ""

        lines = []
        header = "⏱️  Time Tracking:"
        if options.colorize_output:
            header = colorize(header, TextColor.BRIGHT_WHITE, TextStyle.BOLD)
        lines.append(header)

        if time_estimate:
            estimate_str = self._format_duration(time_estimate)
            label = "  Estimate:"
            if options.colorize_output:
                label = colorize(label, TextColor.BRIGHT_BLACK)
            lines.append(f"{label} {estimate_str}")

        if time_spent:
            spent_str = self._format_duration(time_spent)
            label = "  Spent:"
            if options.colorize_output:
                label = colorize(label, TextColor.BRIGHT_BLACK)
            lines.append(f"{label} {spent_str}")

        # Calculate progress if both are available
        if time_estimate and time_spent:
            try:
                progress = (int(time_spent) / int(time_estimate) * 100)
                label = "  Progress:"
                value = f"{progress:.1f}%"
                if options.colorize_output:
                    label = colorize(label, TextColor.BRIGHT_BLACK)
                    color = TextColor.RED if progress > 100 else TextColor.YELLOW if progress > 75 else TextColor.GREEN
                    value = colorize(value, color)
                lines.append(f"{label} {value}")
            except (ValueError, ZeroDivisionError):
                pass

        return "\n".join(lines)

    def _format_file_size(self, size_bytes: int) -> str:
        """Format file size in human-readable format."""
        for unit in ['B', 'KB', 'MB', 'GB']:
            if size_bytes < 1024.0:
                return f"{size_bytes:.1f} {unit}"
            size_bytes /= 1024.0
        return f"{size_bytes:.1f} TB"

    def _format_date_with_seconds(self, timestamp: Optional[str]) -> str:
        """
        Format ClickUp timestamp with seconds for detail view.

        Handles both Unix timestamps (milliseconds) and ISO format strings.

        Args:
            timestamp: Unix timestamp in milliseconds or ISO format string

        Returns:
            Formatted date string in yyyy-MM-dd hh:mm:ss format
        """
        if not timestamp:
            return "No date"

        try:
            from datetime import datetime
            # First try to parse as integer (Unix timestamp in milliseconds)
            if isinstance(timestamp, str) and timestamp.isdigit():
                ts = int(timestamp)
                dt = datetime.fromtimestamp(ts / 1000)
            elif isinstance(timestamp, int):
                dt = datetime.fromtimestamp(timestamp / 1000)
            else:
                # Try to parse as ISO format string
                from dateutil import parser
                dt = parser.parse(timestamp)

            return dt.strftime("%Y-%m-%d %H:%M:%S")
        except (ValueError, OSError, ImportError):
            # If dateutil is not available, try basic ISO parsing
            try:
                if isinstance(timestamp, str) and 'T' in timestamp:
                    # Basic ISO format parsing (YYYY-MM-DDTHH:MM:SSZ)
                    dt = datetime.fromisoformat(timestamp.replace('Z', '+00:00'))
                    return dt.strftime("%Y-%m-%d %H:%M:%S")
            except (ValueError, OSError):
                pass
            return "Invalid date"

    def _format_duration(self, milliseconds: int) -> str:
        """Format duration in human-readable format."""
        try:
            ms = int(milliseconds)
            seconds = ms // 1000
            minutes = seconds // 60
            hours = minutes // 60

            if hours > 0:
                return f"{hours}h {minutes % 60}m"
            elif minutes > 0:
                return f"{minutes}m"
            else:
                return f"{seconds}s"
        except (ValueError, TypeError):
            return str(milliseconds)
