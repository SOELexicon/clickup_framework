"""
Dependency Analyzer Module

Analyzes and visualizes task dependencies with critical path analysis.
Shows upstream (blocking) and downstream (blocked by) dependency chains.
"""

import logging
from typing import Dict, Any, List, Optional, Set, Tuple
from clickup_framework.components.options import FormatOptions
from clickup_framework.components.task_formatter import RichTaskFormatter
from clickup_framework.utils.colors import (
    colorize, status_color, priority_color, get_status_icon,
    TextColor, TextStyle
)
from clickup_framework.utils.datetime import format_timestamp

logger = logging.getLogger(__name__)


class DependencyAnalyzer:
    """
    Analyzes task dependencies and provides critical path analysis.

    Features:
    - Upstream dependency chains (what's blocking this task)
    - Downstream dependency chains (what this task is blocking)
    - Critical path warnings and risk analysis
    - Task link analysis (related, duplicate, etc.)
    - Actionable recommendations
    """

    def __init__(self, client=None):
        """
        Initialize the dependency analyzer.

        Args:
            client: Optional ClickUpClient for fetching task details
        """
        self.client = client
        self.formatter = RichTaskFormatter()

    def analyze_dependencies(
        self,
        task: Dict[str, Any],
        all_tasks: Optional[List[Dict[str, Any]]] = None,
        options: Optional[FormatOptions] = None
    ) -> str:
        """
        Analyze and format complete dependency information for a task.

        Args:
            task: The main task to analyze
            all_tasks: All related tasks (optional, for better context)
            options: Format options

        Returns:
            Formatted dependency analysis string
        """
        if options is None:
            options = FormatOptions()

        sections = []
        task_id = task.get('id')

        # Build task map for lookups
        task_map = {}
        if all_tasks:
            task_map = {t.get('id'): t for t in all_tasks if t.get('id')}

        # Add the current task to the map
        if task_id:
            task_map[task_id] = task

        # Analyze dependencies
        upstream_deps, downstream_deps = self._extract_dependencies(task, task_map)

        # Get task links
        links = task.get('links', [])

        # Only show section if there are dependencies or links
        if not upstream_deps and not downstream_deps and not links:
            return ""

        # Header
        header_lines = []
        separator = "━" * 60
        header = "DEPENDENCY & RELATIONSHIP ANALYSIS"

        if options.colorize_output:
            header = colorize(header, TextColor.BRIGHT_WHITE, TextStyle.BOLD)
        header_lines.append(separator)
        header_lines.append(header)
        header_lines.append(separator)

        sections.append("\n".join(header_lines))

        # Critical path warnings
        warnings = self._generate_warnings(task, upstream_deps, downstream_deps, options)
        if warnings:
            sections.append(warnings)
            sections.append(separator)

        # Upstream dependencies
        if upstream_deps:
            upstream_section = self._format_upstream_dependencies(
                task, upstream_deps, task_map, options
            )
            sections.append(upstream_section)
            sections.append(separator)

        # Downstream dependencies
        if downstream_deps:
            downstream_section = self._format_downstream_dependencies(
                task, downstream_deps, task_map, options
            )
            sections.append(downstream_section)
            sections.append(separator)

        # Other task links
        if links:
            links_section = self._format_task_links(links, task_map, options)
            sections.append(links_section)
            sections.append(separator)

        # Recommendations
        recommendations = self._generate_recommendations(
            task, upstream_deps, downstream_deps, options
        )
        if recommendations:
            sections.append(recommendations)
            sections.append(separator)

        return "\n\n".join(sections)

    def _extract_dependencies(
        self,
        task: Dict[str, Any],
        task_map: Dict[str, Dict[str, Any]]
    ) -> Tuple[List[Dict[str, Any]], List[Dict[str, Any]]]:
        """
        Extract upstream and downstream dependencies.

        Args:
            task: Current task
            task_map: Map of all tasks

        Returns:
            Tuple of (upstream_deps, downstream_deps)
        """
        task_id = task.get('id')
        dependencies = task.get('dependencies', [])

        upstream = []  # Tasks blocking this one
        downstream = []  # Tasks this one blocks

        # Find upstream dependencies (tasks this task depends on)
        for dep in dependencies:
            if not isinstance(dep, dict):
                continue

            dep_task_id = dep.get('task_id')
            depends_on_id = dep.get('depends_on')

            # If this task depends on another (upstream blocker)
            if dep_task_id == task_id and depends_on_id:
                blocking_task = task_map.get(depends_on_id)
                if blocking_task:
                    upstream.append(blocking_task)
                elif self.client:
                    # Try to fetch the task
                    try:
                        blocking_task = self.client.get_task(depends_on_id)
                        if blocking_task:
                            upstream.append(blocking_task)
                            task_map[depends_on_id] = blocking_task
                    except Exception as e:
                        logger.debug(f"Could not fetch blocking task {depends_on_id}: {e}")

        # Find downstream dependencies (tasks that depend on this task)
        # We need to search through ALL tasks to find ones that depend on us
        for other_task_id, other_task in task_map.items():
            if other_task_id == task_id:
                continue  # Skip self

            other_dependencies = other_task.get('dependencies', [])
            for dep in other_dependencies:
                if not isinstance(dep, dict):
                    continue

                dep_task_id = dep.get('task_id')
                depends_on_id = dep.get('depends_on')

                # If the other task depends on this task
                if dep_task_id == other_task_id and depends_on_id == task_id:
                    downstream.append(other_task)
                    break  # Found it, move to next task

        return upstream, downstream

    def _format_upstream_dependencies(
        self,
        task: Dict[str, Any],
        upstream_deps: List[Dict[str, Any]],
        task_map: Dict[str, Dict[str, Any]],
        options: FormatOptions
    ) -> str:
        """Format upstream dependency chain (what's blocking this task)."""
        lines = []

        header = "⬆️  UPSTREAM DEPENDENCIES (what's blocking this task):"
        if options.colorize_output:
            header = colorize(header, TextColor.BRIGHT_YELLOW, TextStyle.BOLD)
        lines.append(header)
        lines.append("")

        # Build chains for each direct blocker
        for blocker in upstream_deps:
            chain_lines = self._build_dependency_chain(
                blocker, task, task_map, options, direction='upstream'
            )
            lines.extend(chain_lines)
            lines.append("")

        # Summary
        summary = self._format_blocking_summary(upstream_deps, options)
        lines.append(summary)

        return "\n".join(lines)

    def _format_downstream_dependencies(
        self,
        task: Dict[str, Any],
        downstream_deps: List[Dict[str, Any]],
        task_map: Dict[str, Dict[str, Any]],
        options: FormatOptions
    ) -> str:
        """Format downstream dependency chain (what depends on this task)."""
        lines = []

        header = "⬇️  DOWNSTREAM DEPENDENCIES (what depends on this task):"
        if options.colorize_output:
            header = colorize(header, TextColor.BRIGHT_CYAN, TextStyle.BOLD)
        lines.append(header)
        lines.append("")

        # Show current task first
        lines.append(self._format_current_task_marker(task, options))

        # Show dependents in a simple tree
        for i, dependent in enumerate(downstream_deps):
            is_last = (i == len(downstream_deps) - 1)
            branch = "  └─" if is_last else "  ├─"

            dep_line = branch + " " + self._format_dependency_task(dependent, options)
            lines.append(dep_line)

            # Recursively show what this dependent blocks (if any)
            further_blocked = self._get_blocked_tasks(dependent, task_map)
            if further_blocked:
                prefix = "    " if is_last else "  │ "
                sub_lines = self._build_downstream_tree(
                    further_blocked, task_map, options, prefix, 0, 3
                )
                lines.extend(sub_lines)

        lines.append("")

        # Impact analysis
        impact = self._format_impact_analysis(downstream_deps, options)
        lines.append(impact)

        return "\n".join(lines)

    def _build_dependency_chain(
        self,
        start_task: Dict[str, Any],
        end_task: Dict[str, Any],
        task_map: Dict[str, Dict[str, Any]],
        options: FormatOptions,
        direction: str = 'upstream',
        indent_level: int = 0,
        visited: Optional[Set[str]] = None,
        max_depth: int = 5
    ) -> List[str]:
        """
        Build a dependency chain recursively.

        Args:
            start_task: Starting task
            end_task: Ending task (where to mark "YOU ARE HERE")
            task_map: Task lookup map
            options: Format options
            direction: 'upstream' or 'downstream'
            indent_level: Current indentation level
            visited: Set of visited task IDs (for cycle detection)
            max_depth: Maximum chain depth

        Returns:
            List of formatted lines
        """
        if visited is None:
            visited = set()

        lines = []
        task_id = start_task.get('id')

        # Cycle detection
        if task_id in visited or indent_level >= max_depth:
            return lines

        visited.add(task_id)

        # Format current task
        indent = "    " + ("  " * indent_level)
        task_line = self._format_dependency_task(start_task, options)

        # Add tree branch character
        if indent_level > 0:
            branch = "└─" if direction == 'downstream' else "├─"
            lines.append(f"{indent}{branch} {task_line}")
        else:
            lines.append(f"{indent}{task_line}")

        # Check if this is the end task (mark as "YOU ARE HERE")
        if task_id == end_task.get('id'):
            marker = "└─ 👉 "
            marker += self._format_current_task_inline(end_task, options)
            marker += " ⬅️ YOU ARE HERE"
            lines.append(f"{indent}  {marker}")
            return lines

        # Recursively build chain
        if direction == 'upstream':
            # Find what blocks this task
            blockers = self._get_blocking_tasks(start_task, task_map)
            for blocker in blockers:
                if blocker.get('id') not in visited:
                    sub_lines = self._build_dependency_chain(
                        blocker, end_task, task_map, options,
                        direction, indent_level + 1, visited, max_depth
                    )
                    lines.extend(sub_lines)
        else:  # downstream
            # Find what this task blocks
            blocked = self._get_blocked_tasks(start_task, task_map)
            for blocked_task in blocked:
                if blocked_task.get('id') not in visited:
                    sub_lines = self._build_dependency_chain(
                        blocked_task, end_task, task_map, options,
                        direction, indent_level + 1, visited, max_depth
                    )
                    lines.extend(sub_lines)

        return lines

    def _get_blocking_tasks(
        self,
        task: Dict[str, Any],
        task_map: Dict[str, Dict[str, Any]]
    ) -> List[Dict[str, Any]]:
        """Get tasks that are blocking this task."""
        task_id = task.get('id')
        dependencies = task.get('dependencies', [])
        blockers = []

        for dep in dependencies:
            if not isinstance(dep, dict):
                continue
            if dep.get('task_id') == task_id:
                blocker_id = dep.get('depends_on')
                if blocker_id and blocker_id in task_map:
                    blockers.append(task_map[blocker_id])

        return blockers

    def _get_blocked_tasks(
        self,
        task: Dict[str, Any],
        task_map: Dict[str, Dict[str, Any]]
    ) -> List[Dict[str, Any]]:
        """Get tasks that are blocked by this task."""
        task_id = task.get('id')
        blocked = []

        # Search through all tasks to find ones that depend on this task
        for other_task in task_map.values():
            dependencies = other_task.get('dependencies', [])
            for dep in dependencies:
                if not isinstance(dep, dict):
                    continue
                if dep.get('depends_on') == task_id:
                    blocked.append(other_task)
                    break

        return blocked

    def _build_downstream_tree(
        self,
        tasks: List[Dict[str, Any]],
        task_map: Dict[str, Dict[str, Any]],
        options: FormatOptions,
        prefix: str = "",
        current_depth: int = 0,
        max_depth: int = 3
    ) -> List[str]:
        """
        Build a simple tree of downstream dependencies.

        Args:
            tasks: List of dependent tasks to display
            task_map: Task lookup map
            options: Format options
            prefix: Current indentation prefix
            current_depth: Current depth
            max_depth: Maximum depth to traverse

        Returns:
            List of formatted lines
        """
        if current_depth >= max_depth:
            return []

        lines = []
        for i, task in enumerate(tasks):
            is_last = (i == len(tasks) - 1)
            branch = "└─" if is_last else "├─"

            task_line = prefix + branch + " " + self._format_dependency_task(task, options)
            lines.append(task_line)

            # Check for further dependencies
            further_blocked = self._get_blocked_tasks(task, task_map)
            if further_blocked:
                child_prefix = prefix + ("  " if is_last else "│ ")
                sub_lines = self._build_downstream_tree(
                    further_blocked, task_map, options,
                    child_prefix, current_depth + 1, max_depth
                )
                lines.extend(sub_lines)

        return lines

    def _format_dependency_task(
        self,
        task: Dict[str, Any],
        options: FormatOptions
    ) -> str:
        """Format a single task in the dependency chain."""
        parts = []

        # ID
        task_id = task.get('id', '')
        if task_id:
            id_str = f"[{task_id}]"
            if options.colorize_output:
                id_str = colorize(id_str, TextColor.BRIGHT_BLACK)
            parts.append(id_str)

        # Emoji
        if options.show_type_emoji:
            from clickup_framework.utils.colors import get_task_emoji
            emoji = get_task_emoji(task.get('custom_type', 'task'))
            parts.append(emoji)

        # Status icon
        status = task.get('status', {})
        status_name = status.get('status') if isinstance(status, dict) else status
        if options.show_status_icon:
            status_icon = get_status_icon(status_name or '')
            if options.colorize_output:
                status_icon = colorize(status_icon, status_color(status_name))
            parts.append(status_icon)

        # Name
        name = task.get('name', 'Untitled')
        if options.colorize_output:
            name = colorize(name, status_color(status_name))
        parts.append(name)

        # Priority
        priority = task.get('priority')
        if priority:
            priority_val = priority.get('priority', '4') if isinstance(priority, dict) else priority
            if priority_val and str(priority_val) != '4':
                priority_str = f"(P{priority_val})"
                if options.colorize_output:
                    priority_str = colorize(priority_str, priority_color(priority_val))
                parts.append(priority_str)

        return " ".join(parts)

    def _format_current_task_marker(
        self,
        task: Dict[str, Any],
        options: FormatOptions
    ) -> str:
        """Format the current task marker for downstream view."""
        line = "    👉 " + self._format_dependency_task(task, options)
        line += " ⬅️ YOU ARE HERE"
        if options.colorize_output:
            line = colorize(line, TextColor.BRIGHT_YELLOW, TextStyle.BOLD)
        return line

    def _format_current_task_inline(
        self,
        task: Dict[str, Any],
        options: FormatOptions
    ) -> str:
        """Format current task inline in chain."""
        parts = [f"[{task.get('id')}]" if task.get('id') else ""]
        parts.append("📝")

        status = task.get('status', {})
        status_name = status.get('status') if isinstance(status, dict) else status
        if options.show_status_icon:
            parts.append(get_status_icon(status_name or ''))

        parts.append(task.get('name', 'Untitled'))

        priority = task.get('priority')
        if priority:
            priority_val = priority.get('priority', '4') if isinstance(priority, dict) else priority
            if str(priority_val) != '4':
                parts.append(f"(P{priority_val})")

        line = " ".join(parts)
        if options.colorize_output:
            line = colorize(line, TextColor.BRIGHT_YELLOW, TextStyle.BOLD)
        return line

    def _generate_warnings(
        self,
        task: Dict[str, Any],
        upstream_deps: List[Dict[str, Any]],
        downstream_deps: List[Dict[str, Any]],
        options: FormatOptions
    ) -> str:
        """Generate critical path warnings."""
        warnings = []

        # Check for blockers
        if upstream_deps:
            not_started = [t for t in upstream_deps
                          if self._is_not_started(t)]
            if not_started:
                msg = f"• Currently blocked by {len(upstream_deps)} task{'s' if len(upstream_deps) != 1 else ''} ({len(not_started)} not started)"
                warnings.append(msg)
            else:
                msg = f"• Currently blocked by {len(upstream_deps)} task{'s' if len(upstream_deps) != 1 else ''}"
                warnings.append(msg)

        # Check downstream high-priority tasks
        if downstream_deps:
            high_pri = [t for t in downstream_deps if self._is_high_priority(t)]
            if high_pri:
                msg = f"• Blocking {len(high_pri)} high-priority task{'s' if len(high_pri) != 1 else ''}"
                warnings.append(msg)

            # Check for at-risk tasks
            at_risk = [t for t in downstream_deps if self._is_at_risk(t)]
            if at_risk:
                msg = f"• {len(at_risk)} dependent task{'s' if len(at_risk) != 1 else ''} at risk of missing deadline"
                warnings.append(msg)

        # Total chain impact
        total_chain = len(upstream_deps) + len(downstream_deps)
        if total_chain > 0:
            msg = f"• Total chain impact: {total_chain} tasks"
            warnings.append(msg)

        if not warnings:
            return ""

        lines = []
        header = "⚠️  CRITICAL PATH WARNINGS:"
        if options.colorize_output:
            header = colorize(header, TextColor.BRIGHT_RED, TextStyle.BOLD)
        lines.append(header)

        for warning in warnings:
            if options.colorize_output:
                warning = colorize(warning, TextColor.BRIGHT_RED)
            lines.append(f"  {warning}")

        return "\n".join(lines)

    def _format_blocking_summary(
        self,
        upstream_deps: List[Dict[str, Any]],
        options: FormatOptions
    ) -> str:
        """Format summary of blocking dependencies."""
        lines = []

        header = "🔍 Blocking Summary:"
        if options.colorize_output:
            header = colorize(header, TextColor.CYAN, TextStyle.BOLD)
        lines.append(header)

        lines.append(f"  • {len(upstream_deps)} direct blocker{'s' if len(upstream_deps) != 1 else ''}")

        # TODO: Calculate upstream chain size and estimated unblock date
        # For now, simple count
        lines.append(f"  • Risk: {'HIGH' if any(self._is_not_started(t) for t in upstream_deps) else 'MEDIUM'}")

        return "\n".join(lines)

    def _format_impact_analysis(
        self,
        downstream_deps: List[Dict[str, Any]],
        options: FormatOptions
    ) -> str:
        """Format impact analysis of downstream dependencies."""
        lines = []

        header = "📊 Impact Analysis:"
        if options.colorize_output:
            header = colorize(header, TextColor.CYAN, TextStyle.BOLD)
        lines.append(header)

        lines.append(f"  • {len(downstream_deps)} direct dependent{'s' if len(downstream_deps) != 1 else ''}")

        at_risk = [t for t in downstream_deps if self._is_at_risk(t)]
        if at_risk:
            msg = f"  • {len(at_risk)} task{'s' if len(at_risk) != 1 else ''} at risk (due soon)"
            if options.colorize_output:
                msg = colorize(msg, TextColor.BRIGHT_RED)
            lines.append(msg)

        return "\n".join(lines)

    def _format_task_links(
        self,
        links: List[Dict[str, Any]],
        task_map: Dict[str, Dict[str, Any]],
        options: FormatOptions
    ) -> str:
        """Format other task links (related, duplicate, etc.)."""
        if not links:
            return ""

        lines = []
        header = f"🔗 OTHER TASK LINKS ({len(links)}):"
        if options.colorize_output:
            header = colorize(header, TextColor.BRIGHT_MAGENTA, TextStyle.BOLD)
        lines.append(header)
        lines.append("")

        # Group by link type
        by_type = {}
        for link in links:
            link_type = link.get('type', 'related')
            if link_type not in by_type:
                by_type[link_type] = []
            by_type[link_type].append(link)

        for link_type, type_links in by_type.items():
            type_header = f"  {link_type.title()}:"
            if options.colorize_output:
                type_header = colorize(type_header, TextColor.MAGENTA, TextStyle.BOLD)
            lines.append(type_header)

            for link in type_links:
                link_task_id = link.get('task_id')
                linked_task = task_map.get(link_task_id)

                if linked_task:
                    task_line = "    ├─ " + self._format_dependency_task(linked_task, options)
                    lines.append(task_line)

            lines.append("")

        return "\n".join(lines)

    def _generate_recommendations(
        self,
        task: Dict[str, Any],
        upstream_deps: List[Dict[str, Any]],
        downstream_deps: List[Dict[str, Any]],
        options: FormatOptions
    ) -> str:
        """Generate actionable recommendations."""
        recommendations = []

        # Check for not started blockers
        not_started = [t for t in upstream_deps if self._is_not_started(t)]
        if not_started:
            for blocker in not_started[:2]:  # Top 2
                rec = {
                    'priority': 'URGENT',
                    'action': f"Follow up on [{blocker.get('id')}] {blocker.get('name', 'Unnamed')}",
                    'reason': 'Task is not started and blocking critical path'
                }
                recommendations.append(rec)

        # Check for at-risk downstream tasks
        at_risk = [t for t in downstream_deps if self._is_at_risk(t)]
        if at_risk:
            for dep_task in at_risk[:2]:
                rec = {
                    'priority': 'HIGH',
                    'action': f"Monitor [{dep_task.get('id')}] {dep_task.get('name', 'Unnamed')} deadline",
                    'reason': 'At risk of missing deadline'
                }
                recommendations.append(rec)

        if not recommendations:
            return ""

        lines = []
        header = "📈 RECOMMENDED ACTIONS:"
        if options.colorize_output:
            header = colorize(header, TextColor.BRIGHT_GREEN, TextStyle.BOLD)
        lines.append(header)
        lines.append("")

        for i, rec in enumerate(recommendations, 1):
            priority = rec['priority']
            priority_str = f"⚠️  {priority}" if priority == 'URGENT' else f"📅 {priority}"
            if options.colorize_output:
                color = TextColor.BRIGHT_RED if priority == 'URGENT' else TextColor.YELLOW
                priority_str = colorize(priority_str, color, TextStyle.BOLD)

            lines.append(f"  {i}. {priority_str}: {rec['action']}")
            reason_line = f"     → {rec['reason']}"
            if options.colorize_output:
                reason_line = colorize(reason_line, TextColor.BRIGHT_BLACK)
            lines.append(reason_line)
            lines.append("")

        return "\n".join(lines)

    # Helper methods for task analysis

    def _is_not_started(self, task: Dict[str, Any]) -> bool:
        """Check if task is not started."""
        status = task.get('status', {})
        status_name = status.get('status') if isinstance(status, dict) else status
        status_lower = str(status_name).lower().strip() if status_name else ''
        return status_lower in ('to do', 'todo', 'open', 'backlog')

    def _is_high_priority(self, task: Dict[str, Any]) -> bool:
        """Check if task is high priority (P1 or P2)."""
        priority = task.get('priority')
        if not priority:
            return False
        priority_val = priority.get('priority', '4') if isinstance(priority, dict) else priority
        try:
            return int(priority_val) <= 2
        except (ValueError, TypeError):
            return False

    def _is_at_risk(self, task: Dict[str, Any]) -> bool:
        """Check if task is at risk of missing deadline."""
        # TODO: Implement actual date comparison with due_date
        # For now, check if has due date and is high priority and not started
        has_due_date = task.get('due_date') is not None
        return has_due_date and self._is_high_priority(task) and self._is_not_started(task)
