"""
Task Detail View Formatter

Provides comprehensive detailed view of a single task with hierarchical relationships,
showing the task in context of its parent, children, and dependencies in a tree view.
"""

from typing import Dict, Any, Optional, List
from clickup_framework.utils.colors import (
    colorize, status_color, priority_color, TextColor, TextStyle,
    get_task_emoji, TASK_TYPE_EMOJI
)
from clickup_framework.components.options import FormatOptions
from clickup_framework.components.tree import TreeFormatter
from clickup_framework.components.task_formatter import RichTaskFormatter


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

    def __init__(self):
        """Initialize the detail formatter."""
        self.section_separator = "─" * 60
        self.task_formatter = RichTaskFormatter()

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

        # Description
        description = self._format_description(task, options)
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

        # Comments section
        comments = self._format_comments(task, options)
        if comments:
            sections.append(comments)

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
        emoji = get_task_emoji(task_type) if options.show_type_emoji else ""
        task_name = task.get('name', 'Unnamed Task')

        title = f"{emoji} {task_name}" if emoji else task_name

        if options.colorize_output:
            title = colorize(title, TextColor.BRIGHT_WHITE, TextStyle.BOLD)

        lines.append(title)
        lines.append(self.section_separator)

        # ID
        if task.get('id'):
            id_label = "ID:"
            if options.colorize_output:
                id_label = colorize(id_label, TextColor.BRIGHT_BLACK)
            lines.append(f"{id_label} {task['id']}")

        # Status
        if task.get('status'):
            status = task['status'].get('status', '') if isinstance(task['status'], dict) else str(task['status'])
            status_label = "Status:"
            if options.colorize_output:
                status_label = colorize(status_label, TextColor.BRIGHT_BLACK)
                status = colorize(status, status_color(status), TextStyle.BOLD)
            lines.append(f"{status_label} {status}")

        # Priority
        if task.get('priority'):
            priority = task['priority'].get('priority', '') if isinstance(task['priority'], dict) else str(task['priority'])
            priority_label = "Priority:"
            if options.colorize_output:
                priority_label = colorize(priority_label, TextColor.BRIGHT_BLACK)
                priority = colorize(priority, priority_color(priority))
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
        """Format container hierarchy (Space > Folder > List)."""
        parts = []

        if task.get('space'):
            space_name = task['space'].get('name') if isinstance(task['space'], dict) else str(task['space'])
            if space_name:
                parts.append(space_name)

        if task.get('folder'):
            folder_name = task['folder'].get('name') if isinstance(task['folder'], dict) else str(task['folder'])
            if folder_name:
                parts.append(folder_name)

        if task.get('list'):
            list_name = task['list'].get('name') if isinstance(task['list'], dict) else str(task['list'])
            if list_name:
                parts.append(list_name)

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

        return "\n".join(lines)

    def _format_metadata(self, task: Dict[str, Any], options: FormatOptions) -> str:
        """Format metadata like dates, assignees, creator."""
        lines = []

        # Dates
        if task.get('date_created'):
            label = "Created:"
            value = task['date_created']
            if options.colorize_output:
                label = colorize(label, TextColor.BRIGHT_BLACK)
                value = colorize(value, TextColor.GREEN)
            lines.append(f"{label} {value}")

        if task.get('date_updated'):
            label = "Updated:"
            value = task['date_updated']
            if options.colorize_output:
                label = colorize(label, TextColor.BRIGHT_BLACK)
                value = colorize(value, TextColor.YELLOW)
            lines.append(f"{label} {value}")

        if task.get('due_date'):
            label = "Due:"
            value = task['due_date']
            if options.colorize_output:
                label = colorize(label, TextColor.BRIGHT_BLACK)
                value = colorize(value, TextColor.RED)
            lines.append(f"{label} {value}")

        if task.get('date_closed'):
            label = "Closed:"
            value = task['date_closed']
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

    def _format_description(self, task: Dict[str, Any], options: FormatOptions) -> str:
        """Format full task description."""
        description = task.get('description', '').strip()
        if not description:
            return ""

        lines = []
        header = "📝 Description:"
        if options.colorize_output:
            header = colorize(header, TextColor.BRIGHT_WHITE, TextStyle.BOLD)
        lines.append(header)
        lines.append("")

        # Show full description (not truncated)
        # Add indentation for readability
        for line in description.split('\n'):
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
        """Format custom fields."""
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

                # Format based on type
                field_type = field.get('type', '')
                if field_type == 'drop_down' and isinstance(value, dict):
                    value = value.get('name', value)

                field_label = f"  {name}:"
                if options.colorize_output:
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

    def _build_child_tree(
        self,
        parent_id: str,
        all_tasks: List[Dict[str, Any]],
        options: FormatOptions,
        depth: int = 0,
        max_depth: int = 3
    ) -> List[str]:
        """
        Recursively build a tree view of child tasks.

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

            child_name = child.get('name', 'Unnamed')
            child_status = child.get('status', {})
            if isinstance(child_status, dict):
                child_status = child_status.get('status', '')

            line = f"{prefix}{branch} {child_name}"

            if child_status:
                status_str = f" [{child_status}]"
                if options.colorize_output:
                    status_str = colorize(status_str, status_color(child_status))
                line += status_str

            if options.colorize_output:
                line = colorize(line, TextColor.GREEN)
            lines.append(line)

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
        """Format checklists with completion status."""
        checklists = task.get('checklists', [])
        if not checklists:
            return ""

        lines = []
        header = "☑️  Checklists:"
        if options.colorize_output:
            header = colorize(header, TextColor.BRIGHT_WHITE, TextStyle.BOLD)
        lines.append(header)

        for checklist in checklists:
            if isinstance(checklist, dict):
                name = checklist.get('name', 'Unnamed Checklist')
                items = checklist.get('items', [])

                completed = sum(1 for item in items if isinstance(item, dict) and item.get('resolved'))
                total = len(items)

                checklist_header = f"\n  {name} ({completed}/{total})"
                if options.colorize_output:
                    completion_pct = (completed / total * 100) if total > 0 else 0
                    color = TextColor.GREEN if completion_pct == 100 else TextColor.YELLOW if completion_pct >= 50 else TextColor.RED
                    checklist_header = colorize(checklist_header, color, TextStyle.BOLD)
                lines.append(checklist_header)

                for item in items:
                    if isinstance(item, dict):
                        item_name = item.get('name', '')
                        is_resolved = item.get('resolved', False)
                        checkbox = "✓" if is_resolved else "○"

                        item_line = f"    {checkbox} {item_name}"
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

    def _format_comments(self, task: Dict[str, Any], options: FormatOptions) -> str:
        """Format comments section."""
        comments = task.get('comments', [])
        if not comments:
            return ""

        lines = []
        header = f"💬 Comments ({len(comments)}):"
        if options.colorize_output:
            header = colorize(header, TextColor.BRIGHT_WHITE, TextStyle.BOLD)
        lines.append(header)

        # Show up to 5 most recent comments
        for comment in comments[:5]:
            if isinstance(comment, dict):
                author = comment.get('user', {}).get('username', 'Unknown') if isinstance(comment.get('user'), dict) else comment.get('user', 'Unknown')
                date = comment.get('date', '')
                text = comment.get('comment_text') or comment.get('text', '')

                comment_header = f"\n  {author}"
                if date:
                    comment_header += f" • {date}"

                if options.colorize_output:
                    comment_header = colorize(comment_header, TextColor.BLUE, TextStyle.BOLD)
                lines.append(comment_header)

                # Show comment text with indentation
                if text:
                    for line in text.split('\n'):
                        lines.append(f"  {line}")

        if len(comments) > 5:
            more_line = f"\n  ... and {len(comments) - 5} more comments"
            if options.colorize_output:
                more_line = colorize(more_line, TextColor.BRIGHT_BLACK)
            lines.append(more_line)

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
