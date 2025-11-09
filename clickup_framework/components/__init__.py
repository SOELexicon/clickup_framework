"""
ClickUp Framework Components Module

This module provides high-level wrapper components for displaying ClickUp data
in beautiful, hierarchical tree views similar to ClickupCLI.

Components:
    - FormatOptions: Dataclass for managing display options
    - TreeFormatter: Renders hierarchical tree structures with box-drawing characters
    - TaskHierarchyFormatter: Organizes tasks by parent-child relationships
    - ContainerHierarchyFormatter: Organizes tasks by workspace/space/folder/list containers
    - TaskFilter: Filters tasks by various criteria
    - RichTaskFormatter: Enhanced task formatting with emojis, colors, and styling
    - DisplayManager: High-level component combining filtering, organizing, and rendering

Example Usage:
    ```python
    from clickup_framework import ClickUpClient
    from clickup_framework.components import DisplayManager, FormatOptions

    client = ClickUpClient()
    display = DisplayManager(client)

    # Get tasks and display in hierarchical tree view
    tasks = client.get_list_tasks("list_id")
    options = FormatOptions(
        colorize_output=True,
        show_ids=True,
        show_tags=True,
        show_descriptions=True
    )

    output = display.format_container_hierarchy(tasks, options)
    print(output)
    ```
"""

from clickup_framework.components.options import FormatOptions
from clickup_framework.components.tree import TreeFormatter
from clickup_framework.components.hierarchy import TaskHierarchyFormatter
from clickup_framework.components.container import ContainerHierarchyFormatter
from clickup_framework.components.filters import TaskFilter
from clickup_framework.components.task_formatter import RichTaskFormatter
from clickup_framework.components.detail_view import TaskDetailFormatter
from clickup_framework.components.display import DisplayManager

__all__ = [
    'FormatOptions',
    'TreeFormatter',
    'TaskHierarchyFormatter',
    'ContainerHierarchyFormatter',
    'TaskFilter',
    'RichTaskFormatter',
    'TaskDetailFormatter',
    'DisplayManager',
]
