"""Assigned tasks command for ClickUp Framework CLI."""

import sys
from collections import defaultdict, deque
from clickup_framework import ClickUpClient, get_context_manager
from clickup_framework.utils.colors import colorize, TextColor, TextStyle
from clickup_framework.utils.animations import ANSIAnimations


def assigned_tasks_command(args):
    """Display tasks assigned to a user, sorted by dependency difficulty."""
    context = get_context_manager()
    client = ClickUpClient()

    # Get user ID from args or use default assignee
    if args.user_id:
        user_id = args.user_id
    else:
        user_id = context.get_default_assignee()
        if not user_id:
            print("Error: No user ID specified and no default assignee configured.", file=sys.stderr)
            print("Use --user-id <user_id> or set default: set_current assignee <user_id>", file=sys.stderr)
            sys.exit(1)

    # Get workspace/team ID
    try:
        team_id = context.resolve_id('workspace', args.team_id if hasattr(args, 'team_id') and args.team_id else 'current')
    except ValueError:
        # No workspace configured - show list and let user select
        try:
            workspaces = client.get_authorized_workspaces()
            teams = workspaces.get('teams', [])

            if not teams:
                print("Error: No workspaces found in your account.", file=sys.stderr)
                sys.exit(1)

            # Display workspaces
            print(colorize("\nAvailable Workspaces:", TextColor.BRIGHT_CYAN, TextStyle.BOLD))
            for i, team in enumerate(teams, 1):
                team_name = team.get('name', 'Unnamed')
                team_id_val = team.get('id', 'Unknown')
                print(f"  {colorize(str(i), TextColor.BRIGHT_YELLOW)}. {team_name} {colorize(f'[{team_id_val}]', TextColor.BRIGHT_BLACK)}")

            print()
            selection = input(colorize("Select workspace number (or press any letter to cancel): ", TextColor.BRIGHT_WHITE))

            # Check if input is a letter (cancel)
            if selection.isalpha():
                print("Cancelled.")
                sys.exit(0)

            # Try to parse as number
            try:
                workspace_num = int(selection)
                if 1 <= workspace_num <= len(teams):
                    team_id = teams[workspace_num - 1]['id']
                    print(colorize(f"✓ Using workspace: {teams[workspace_num - 1]['name']}", TextColor.BRIGHT_GREEN))
                    print()
                else:
                    print(f"Error: Invalid selection. Please choose 1-{len(teams)}", file=sys.stderr)
                    sys.exit(1)
            except ValueError:
                print("Error: Invalid input. Please enter a number or letter to cancel.", file=sys.stderr)
                sys.exit(1)

        except Exception as e:
            print(f"Error fetching workspaces: {e}", file=sys.stderr)
            sys.exit(1)

    # Fetch tasks assigned to user
    try:
        result = client.get_team_tasks(
            team_id,
            assignees=[user_id],
            subtasks=True,
            include_closed=False
        )
        tasks = result.get('tasks', [])
    except Exception as e:
        print(f"Error fetching tasks: {e}", file=sys.stderr)
        sys.exit(1)

    if not tasks:
        print(f"No tasks found assigned to user {user_id}")
        return

    # Build dependency graph
    task_map = {task['id']: task for task in tasks}
    task_info = {}

    for task in tasks:
        task_id = task['id']
        dependencies = task.get('dependencies', [])

        # Count blockers (tasks this task is waiting on)
        blockers = []
        open_blockers = []

        for dep in dependencies:
            # Type 0 means this task waits for another task
            if dep.get('type') == 0:
                blocker_id = dep.get('depends_on')
                if blocker_id:
                    blockers.append(blocker_id)
                    # Check if blocker is completed
                    if blocker_id in task_map:
                        blocker_status = task_map[blocker_id].get('status', {})
                        if isinstance(blocker_status, dict):
                            blocker_status = blocker_status.get('status', '').lower()
                        else:
                            blocker_status = str(blocker_status).lower()

                        if blocker_status not in ['closed', 'complete', 'completed']:
                            open_blockers.append(blocker_id)

        # Count dependents (tasks waiting on this task)
        dependents = []
        for dep in dependencies:
            # Type 1 means this task blocks another task
            if dep.get('type') == 1:
                dependent_id = dep.get('task_id')
                if dependent_id:
                    dependents.append(dependent_id)

        task_info[task_id] = {
            'task': task,
            'blockers': blockers,
            'open_blockers': open_blockers,
            'dependents': dependents,
            'difficulty': len(open_blockers),  # Difficulty score = number of open blockers
        }

    # Calculate dependency depth using topological sort
    def calculate_depth():
        depths = {}
        in_degree = defaultdict(int)

        # Initialize
        for task_id in task_info:
            in_degree[task_id] = 0

        # Build in-degree count
        for task_id, info in task_info.items():
            for blocker in info['blockers']:
                if blocker in task_info:
                    in_degree[task_id] += 1

        # BFS to calculate depth
        queue = deque()
        for task_id in task_info:
            if in_degree[task_id] == 0:
                queue.append((task_id, 0))
                depths[task_id] = 0

        while queue:
            task_id, depth = queue.popleft()

            # Find tasks that depend on this one
            for tid, info in task_info.items():
                if task_id in info['blockers']:
                    in_degree[tid] -= 1
                    new_depth = depth + 1
                    if tid not in depths or new_depth > depths[tid]:
                        depths[tid] = new_depth
                    if in_degree[tid] == 0:
                        queue.append((tid, depths[tid]))

        return depths

    depths = calculate_depth()
    for task_id in task_info:
        task_info[task_id]['depth'] = depths.get(task_id, 0)

    # Separate parent tasks from subtasks
    parent_tasks = []
    subtasks_by_parent = defaultdict(list)
    orphaned_subtasks = []  # Subtasks whose parent is not in the assigned list

    for task in tasks:
        task_id = task['id']
        parent_id = task.get('parent')

        if parent_id:
            # This is a subtask
            subtasks_by_parent[parent_id].append(task_id)
        else:
            # This is a parent task
            parent_tasks.append(task_id)

    # Identify orphaned subtasks (parent not in our task list)
    for parent_id, subtask_ids in subtasks_by_parent.items():
        if parent_id not in task_map:
            # Parent is not assigned to user, these subtasks are "orphaned" in this view
            orphaned_subtasks.extend(subtask_ids)

    # Sort tasks by difficulty (ascending) then by depth (ascending)
    sorted_task_ids = sorted(
        parent_tasks,
        key=lambda tid: (task_info[tid]['difficulty'], task_info[tid]['depth'])
    )

    # Sort orphaned subtasks the same way
    sorted_orphaned = sorted(
        orphaned_subtasks,
        key=lambda tid: (task_info[tid]['difficulty'], task_info[tid]['depth'])
    )

    # Display header
    print(ANSIAnimations.gradient_text(f"Tasks Assigned to User {user_id}", ANSIAnimations.GRADIENT_RAINBOW))
    print(f"Total: {len(tasks)} tasks\n")

    # Get colorize setting
    use_color = context.get_ansi_output()

    # Display tasks
    from clickup_framework.utils.colors import status_color as get_status_color

    def display_task(task_id, indent_level=0):
        """Display a task with optional indentation for subtasks."""
        info = task_info[task_id]
        task = info['task']

        indent = "   " * indent_level

        # Task name and ID
        task_name = task.get('name', 'Unnamed')
        status = task.get('status', {})
        if isinstance(status, dict):
            status_name = status.get('status', 'Unknown')
        else:
            status_name = str(status)

        # Format status with color
        if use_color:
            status_colored = colorize(status_name, get_status_color(status_name), TextStyle.BOLD)
            task_name_colored = colorize(task_name, TextColor.BRIGHT_WHITE)
        else:
            status_colored = status_name
            task_name_colored = task_name

        # Difficulty indicator
        difficulty = info['difficulty']
        if difficulty == 0:
            difficulty_indicator = colorize("✓ Ready", TextColor.BRIGHT_GREEN) if use_color else "✓ Ready"
        elif difficulty <= 2:
            difficulty_indicator = colorize(f"⚠ {difficulty} blocker(s)", TextColor.BRIGHT_YELLOW) if use_color else f"⚠ {difficulty} blocker(s)"
        else:
            difficulty_indicator = colorize(f"🚫 {difficulty} blocker(s)", TextColor.BRIGHT_RED) if use_color else f"🚫 {difficulty} blocker(s)"

        # Add subtask indicator if this is a subtask
        prefix = f"{indent}   ↳ " if indent_level > 0 else ""

        print(f"{prefix}{task_name_colored}")
        print(f"{indent}   Status: {status_colored}")
        print(f"{indent}   Difficulty: {difficulty_indicator}")
        print(f"{indent}   Depth: {info['depth']} | Relationships: {len(info['blockers'])} blockers, {len(info['dependents'])} dependents")
        print(f"{indent}   ID: {colorize(task_id, TextColor.BRIGHT_BLACK) if use_color else task_id}")

        # Show blocker details if any
        if info['open_blockers']:
            print(f"{indent}   Blocked by:")
            for blocker_id in info['open_blockers'][:3]:  # Show first 3
                if blocker_id in task_map:
                    blocker_task = task_map[blocker_id]
                    blocker_name = blocker_task.get('name', 'Unknown')
                    print(f"{indent}     - {blocker_name} [{blocker_id}]")

        print()  # Blank line between tasks

    # Display parent tasks with their subtasks
    task_number = 1
    for task_id in sorted_task_ids:
        print(f"{task_number}.", end=" ")
        display_task(task_id, indent_level=0)
        task_number += 1

        # Display subtasks for this parent (only those assigned to user)
        if task_id in subtasks_by_parent:
            # Sort subtasks by difficulty and depth
            sorted_subtasks = sorted(
                subtasks_by_parent[task_id],
                key=lambda tid: (task_info[tid]['difficulty'], task_info[tid]['depth'])
            )
            for subtask_id in sorted_subtasks:
                display_task(subtask_id, indent_level=1)

    # Display orphaned subtasks (assigned to user but parent not assigned)
    if sorted_orphaned:
        print(colorize("\n━━━ Subtasks (parent not assigned to you) ━━━\n", TextColor.BRIGHT_CYAN, TextStyle.BOLD) if use_color else "\n━━━ Subtasks (parent not assigned to you) ━━━\n")
        for task_id in sorted_orphaned:
            print(f"{task_number}.", end=" ")
            display_task(task_id, indent_level=0)
            task_number += 1

    # Summary stats
    ready_tasks = sum(1 for info in task_info.values() if info['difficulty'] == 0)
    blocked_tasks = sum(1 for info in task_info.values() if info['difficulty'] > 0)

    print(f"{colorize('Summary:', TextColor.BRIGHT_WHITE, TextStyle.BOLD) if use_color else 'Summary:'}")
    print(f"  Parent tasks: {len(parent_tasks)}")
    print(f"  Subtasks (under assigned parents): {sum(len(v) for k, v in subtasks_by_parent.items() if k in task_map)}")
    if orphaned_subtasks:
        print(f"  Subtasks (parent not assigned): {len(orphaned_subtasks)}")
    print(f"  Ready to start: {ready_tasks} task(s)")
    print(f"  Blocked: {blocked_tasks} task(s)")


def register_command(subparsers):
    """Register assigned tasks command."""
    assigned_parser = subparsers.add_parser('assigned', aliases=['a'],
                                            help='Show tasks assigned to user, sorted by dependency difficulty')
    assigned_parser.add_argument('--user-id', dest='user_id',
                                help='User ID to filter tasks (defaults to configured default assignee)')
    assigned_parser.add_argument('--team-id', dest='team_id',
                                help='Team/workspace ID (defaults to current workspace)')
    assigned_parser.set_defaults(func=assigned_tasks_command)
