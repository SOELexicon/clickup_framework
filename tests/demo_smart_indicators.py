#!/usr/bin/env python3
"""
Demo script showing smart indicators in hierarchy view.

This creates mock tasks with various relationships to demonstrate
all the smart indicators.
"""

from clickup_framework.components.task_formatter import RichTaskFormatter
from clickup_framework.components.options import FormatOptions


def create_demo_tasks():
    """Create demo tasks with various indicators."""

    # Task 1: Has everything
    task1 = {
        'id': 'task001',
        'name': 'Implement user authentication system',
        'status': {'status': 'in development'},
        'custom_type': 'task',
        'dependencies': [
            {'task_id': 'dep1', 'type': 'waiting_on'},
            {'task_id': 'dep2', 'type': 'waiting_on'},
            {'task_id': 'block1', 'type': 'blocking'},
        ],
        'linked_tasks': [
            {'task_id': 'link1'},
            {'task_id': 'link2'},
            {'task_id': 'link3'},
        ],
        'assignees': [
            {'username': 'john_doe', 'email': 'john@example.com'}
        ],
        'due_date': str(int(__import__('time').time() * 1000) + 2 * 24 * 3600 * 1000),  # 2 days from now
        'time_estimate': 8 * 3600 * 1000,  # 8 hours
        'time_spent': 4.5 * 3600 * 1000,   # 4.5 hours spent
    }

    # Task 2: Overdue and over budget
    task2 = {
        'id': 'task002',
        'name': 'Fix critical production bug',
        'status': {'status': 'in development'},
        'custom_type': 'task',
        'dependencies': [
            {'task_id': 'block2', 'type': 'blocking'},
            {'task_id': 'block3', 'type': 'blocking'},
            {'task_id': 'block4', 'type': 'blocking'},
        ],
        'assignees': [
            {'username': 'jane_smith'},
            {'username': 'bob_jones'},
        ],
        'due_date': str(int(__import__('time').time() * 1000) - 5 * 24 * 3600 * 1000),  # 5 days ago
        'time_estimate': 8 * 3600 * 1000,   # 8 hours
        'time_spent': 12 * 3600 * 1000,     # 12 hours spent (over budget!)
    }

    # Task 3: Due today
    task3 = {
        'id': 'task003',
        'name': 'Write documentation for API',
        'status': {'status': 'Open'},
        'custom_type': 'task',
        'linked_tasks': [
            {'task_id': 'doc1'},
        ],
        'assignees': [
            {'username': 'alice_brown'}
        ],
        'due_date': str(int(__import__('time').time() * 1000)),  # Today
    }

    # Task 4: Just time estimate
    task4 = {
        'id': 'task004',
        'name': 'Refactor database queries',
        'status': {'status': 'Open'},
        'custom_type': 'task',
        'assignees': [
            {'username': 'charlie_wilson'}
        ],
        'time_estimate': 6 * 3600 * 1000,  # 6 hours estimated
    }

    # Task 5: Completed task
    task5 = {
        'id': 'task005',
        'name': 'Setup CI/CD pipeline',
        'status': {'status': 'Complete'},
        'custom_type': 'task',
        'assignees': [
            {'username': 'david_lee'}
        ],
        'time_estimate': 4 * 3600 * 1000,  # 4 hours
        'time_spent': 3.5 * 3600 * 1000,   # 3.5 hours (under budget!)
    }

    # Task 6: Waiting on multiple dependencies
    task6 = {
        'id': 'task006',
        'name': 'Deploy to production',
        'status': {'status': 'Open'},
        'custom_type': 'task',
        'dependencies': [
            {'task_id': 'dep3', 'type': 'waiting_on'},
            {'task_id': 'dep4', 'type': 'waiting_on'},
            {'task_id': 'dep5', 'type': 'waiting_on'},
            {'task_id': 'dep6', 'type': 'waiting_on'},
        ],
        'assignees': [
            {'username': 'ops_team'},
            {'username': 'security_team'},
            {'username': 'dev_team'},
        ],
    }

    return [task1, task2, task3, task4, task5, task6]


def demo_colored_output():
    """Show colored indicators."""
    print("=" * 80)
    print("SMART INDICATORS - COLORED OUTPUT")
    print("=" * 80)
    print()

    tasks = create_demo_tasks()
    options = FormatOptions(
        colorize_output=True,
        show_ids=True,
        show_type_emoji=True,
        show_status_icon=True,
    )

    for i, task in enumerate(tasks, 1):
        formatted = RichTaskFormatter.format_task(task, options)
        print(f"{i}. {formatted}")
        print()

    print("\n")


def demo_plain_output():
    """Show plain text indicators."""
    print("=" * 80)
    print("SMART INDICATORS - PLAIN TEXT OUTPUT")
    print("=" * 80)
    print()

    tasks = create_demo_tasks()
    options = FormatOptions(
        colorize_output=False,
        show_ids=True,
        show_type_emoji=True,
        show_status_icon=True,
    )

    for i, task in enumerate(tasks, 1):
        formatted = RichTaskFormatter.format_task(task, options)
        print(f"{i}. {formatted}")
        print()

    print("\n")


def demo_indicator_legend():
    """Show legend of all indicators."""
    print("=" * 80)
    print("INDICATOR LEGEND")
    print("=" * 80)
    print()

    print("DEPENDENCIES & BLOCKERS")
    print("  ⏳N or D:N  = Depends on N tasks (waiting for)")
    print("  🚫N or B:N  = Blocking N tasks (others waiting on this)")
    print()

    print("RELATIONSHIPS")
    print("  🔗N or L:N  = Linked to N related tasks")
    print()

    print("ASSIGNEES")
    print("  👤XX       = Assigned to user with initials XX")
    print("  👥N or A:N  = Assigned to N people")
    print()

    print("DUE DATES")
    print("  🔴Nd or OVERDUE:Nd  = N days overdue (RED, BOLD)")
    print("  📅TODAY or DUE:TODAY = Due today (YELLOW, BOLD)")
    print("  ⚠️Nd or DUE:Nd       = Due in N days (YELLOW)")
    print()

    print("TIME TRACKING")
    print("  ⏱️X.X/Y.Yh or T:X.X/Y.Yh = X hours spent / Y hours estimated")
    print("    - RED if over budget (spent > estimated)")
    print("    - GREEN if under budget (spent ≤ estimated)")
    print("  ⏱️X.Xh or T:X.Xh         = Estimate only (CYAN)")
    print("  ⏱️X.Xh or T:X.Xh         = Tracked time only (YELLOW)")
    print()

    print("STATUS")
    print("  ⚙️ = In development")
    print("  ⬜ = Open/Not started")
    print("  ✓ = Complete")
    print()


def main():
    """Run the demo."""
    demo_indicator_legend()
    print("\n\n")
    demo_colored_output()
    print("\n\n")
    demo_plain_output()

    print("=" * 80)
    print("USING IN HIERARCHY VIEW")
    print("=" * 80)
    print()
    print("Run: cum h <task_id>")
    print()
    print("All indicators appear automatically when task data is available:")
    print("  - Dependencies from task.dependencies field")
    print("  - Linked tasks from task.linked_tasks field")
    print("  - Assignees from task.assignees field")
    print("  - Due dates from task.due_date field")
    print("  - Time tracking from task.time_estimate and task.time_spent fields")
    print()
    print("See DOCS_SMART_INDICATORS.md for full documentation.")
    print()


if __name__ == "__main__":
    main()
