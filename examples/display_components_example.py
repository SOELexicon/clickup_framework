"""
Display Components Example

Demonstrates how to use the wrapper components to display ClickUp tasks
in beautiful, hierarchical tree views.
"""

import os
import sys

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from clickup_framework import ClickUpClient
from clickup_framework.components import (
    DisplayManager,
    FormatOptions,
    TaskFilter,
    RichTaskFormatter,
    TaskHierarchyFormatter,
    ContainerHierarchyFormatter
)


def example_1_basic_hierarchy():
    """Example 1: Display tasks in hierarchical view."""
    print("=" * 60)
    print("Example 1: Hierarchical View")
    print("=" * 60)

    client = ClickUpClient()
    display = DisplayManager(client)

    # Replace with your list ID
    list_id = os.getenv('CLICKUP_LIST_ID', 'your_list_id_here')

    try:
        tasks = client.get_list_tasks(list_id)

        # Display with default options
        output = display.hierarchy_view(tasks)
        print(output)
    except Exception as e:
        print(f"Error: {e}")
        print("\nTip: Set CLICKUP_API_TOKEN and CLICKUP_LIST_ID environment variables")


def example_2_container_hierarchy():
    """Example 2: Display tasks organized by containers."""
    print("\n" + "=" * 60)
    print("Example 2: Container Hierarchy View")
    print("=" * 60)

    client = ClickUpClient()
    display = DisplayManager(client)

    list_id = os.getenv('CLICKUP_LIST_ID', 'your_list_id_here')

    try:
        tasks = client.get_list_tasks(list_id)

        # Display with container organization
        output = display.container_view(tasks)
        print(output)
    except Exception as e:
        print(f"Error: {e}")


def example_3_custom_formatting():
    """Example 3: Custom formatting options."""
    print("\n" + "=" * 60)
    print("Example 3: Custom Formatting Options")
    print("=" * 60)

    client = ClickUpClient()
    display = DisplayManager(client)

    list_id = os.getenv('CLICKUP_LIST_ID', 'your_list_id_here')

    try:
        tasks = client.get_list_tasks(list_id)

        # Create custom format options
        options = FormatOptions(
            colorize_output=True,
            show_ids=True,
            show_tags=True,
            show_descriptions=True,
            show_dates=True,
            show_comments=2,
            description_length=100
        )

        output = display.hierarchy_view(tasks, options)
        print(output)
    except Exception as e:
        print(f"Error: {e}")


def example_4_filtered_view():
    """Example 4: Filtered task view."""
    print("\n" + "=" * 60)
    print("Example 4: Filtered View")
    print("=" * 60)

    client = ClickUpClient()
    display = DisplayManager(client)

    list_id = os.getenv('CLICKUP_LIST_ID', 'your_list_id_here')

    try:
        tasks = client.get_list_tasks(list_id)

        # Display only high priority tasks
        output = display.filtered_view(
            tasks,
            priority=1,  # Urgent priority
            include_completed=False,
            view_mode='hierarchy'
        )
        print(output)
    except Exception as e:
        print(f"Error: {e}")


def example_5_detail_levels():
    """Example 5: Different detail levels."""
    print("\n" + "=" * 60)
    print("Example 5: Detail Levels")
    print("=" * 60)

    client = ClickUpClient()
    display = DisplayManager(client)

    list_id = os.getenv('CLICKUP_LIST_ID', 'your_list_id_here')

    try:
        tasks = client.get_list_tasks(list_id)

        print("\n--- Minimal View ---")
        minimal_output = display.hierarchy_view(tasks, FormatOptions.minimal())
        print(minimal_output)

        print("\n--- Summary View ---")
        summary_output = display.hierarchy_view(tasks, FormatOptions.summary())
        print(summary_output)

        print("\n--- Detailed View ---")
        detailed_output = display.hierarchy_view(tasks, FormatOptions.detailed())
        print(detailed_output)

    except Exception as e:
        print(f"Error: {e}")


def example_6_task_statistics():
    """Example 6: Task statistics."""
    print("\n" + "=" * 60)
    print("Example 6: Task Statistics")
    print("=" * 60)

    client = ClickUpClient()
    display = DisplayManager(client)

    list_id = os.getenv('CLICKUP_LIST_ID', 'your_list_id_here')

    try:
        tasks = client.get_list_tasks(list_id)

        # Display statistics
        stats = display.summary_stats(tasks)
        print(stats)
    except Exception as e:
        print(f"Error: {e}")


def example_7_individual_formatters():
    """Example 7: Using individual formatters directly."""
    print("\n" + "=" * 60)
    print("Example 7: Individual Formatters")
    print("=" * 60)

    client = ClickUpClient()

    list_id = os.getenv('CLICKUP_LIST_ID', 'your_list_id_here')

    try:
        tasks = client.get_list_tasks(list_id)

        # Use RichTaskFormatter directly
        formatter = RichTaskFormatter()
        print("\n--- Single Task (Detailed) ---")
        if tasks:
            task_output = formatter.format_task_detailed(tasks[0])
            print(task_output)

        # Use TaskHierarchyFormatter directly
        print("\n--- Hierarchy Formatter ---")
        hierarchy_formatter = TaskHierarchyFormatter()
        hierarchy_output = hierarchy_formatter.format_hierarchy(
            tasks,
            FormatOptions.summary(),
            header="My Tasks"
        )
        print(hierarchy_output)

    except Exception as e:
        print(f"Error: {e}")


def main():
    """Run all examples."""
    print("\n")
    print("╔" + "=" * 58 + "╗")
    print("║  ClickUp Framework - Display Components Examples        ║")
    print("╚" + "=" * 58 + "╝")
    print("\n")

    # Run examples
    example_1_basic_hierarchy()
    example_2_container_hierarchy()
    example_3_custom_formatting()
    example_4_filtered_view()
    example_5_detail_levels()
    example_6_task_statistics()
    example_7_individual_formatters()

    print("\n" + "=" * 60)
    print("Examples Complete!")
    print("=" * 60)


if __name__ == "__main__":
    main()
