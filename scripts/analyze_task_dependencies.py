#!/usr/bin/env python3
"""
Task Dependency Analyzer

Analyzes ClickUp task dependencies to show:
- What blocks each task (dependencies)
- What each task blocks (dependents)
- Sorted execution order (topological sort)
- Critical path identification

Usage:
    python clickup_framework/scripts/analyze_task_dependencies.py <task_id>
    python clickup_framework/scripts/analyze_task_dependencies.py --all <list_id>
    python clickup_framework/scripts/analyze_task_dependencies.py --project <project_task_id>

    # Or from anywhere if clickup_framework is installed:
    python -m clickup_framework.scripts.analyze_task_dependencies <task_id>
"""

import argparse
import sys
from pathlib import Path
from collections import defaultdict, deque
from typing import Dict, List, Set, Tuple

# Add parent directories to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from clickup_framework import ClickUpClient


def get_task_dependencies(client: ClickUpClient, task_id: str) -> Tuple[List[str], List[str]]:
    """
    Get dependencies for a task.

    Returns:
        (blockers, dependents) - Lists of task IDs
    """
    task = client.get_task(task_id)
    dependencies = task.get('dependencies', [])

    blockers = []  # Tasks this task waits for
    dependents = []  # Tasks waiting for this task

    for dep in dependencies:
        if dep.get('task_id') == task_id:
            # This task waits for depends_on task
            blockers.append(dep.get('depends_on'))
        if dep.get('depends_on') == task_id:
            # depends_on task waits for this task
            dependents.append(dep.get('task_id'))

    return blockers, dependents


def build_dependency_graph(client: ClickUpClient, task_ids: List[str]) -> Dict:
    """Build complete dependency graph for all tasks."""
    graph = {}

    for task_id in task_ids:
        try:
            task = client.get_task(task_id)
            blockers, dependents = get_task_dependencies(client, task_id)

            graph[task_id] = {
                'name': task.get('name'),
                'status': task['status']['status'],
                'blockers': blockers,
                'dependents': dependents
            }
        except Exception as e:
            print(f"Warning: Could not fetch {task_id}: {str(e)[:50]}", file=sys.stderr)

    return graph


def topological_sort(graph: Dict) -> List[str]:
    """
    Sort tasks in dependency order (what must be completed first).
    Returns list of task IDs in execution order.
    """
    # Build adjacency list and in-degree count
    adj = defaultdict(list)
    in_degree = defaultdict(int)

    # Initialize all nodes
    for task_id in graph:
        in_degree[task_id] = 0

    # Build graph
    for task_id, info in graph.items():
        for blocker in info['blockers']:
            if blocker in graph:  # Only include tasks in our set
                adj[blocker].append(task_id)
                in_degree[task_id] += 1

    # Kahn's algorithm for topological sort
    queue = deque([task_id for task_id in graph if in_degree[task_id] == 0])
    sorted_tasks = []

    while queue:
        task_id = queue.popleft()
        sorted_tasks.append(task_id)

        for dependent in adj[task_id]:
            in_degree[dependent] -= 1
            if in_degree[dependent] == 0:
                queue.append(dependent)

    # Check for cycles
    if len(sorted_tasks) != len(graph):
        print("Warning: Circular dependencies detected!", file=sys.stderr)

    return sorted_tasks


def find_critical_path(graph: Dict, sorted_tasks: List[str]) -> List[str]:
    """Find the critical path (longest chain of dependencies)."""
    # Calculate longest path to each task
    longest_path = {}
    predecessor = {}

    for task_id in sorted_tasks:
        max_length = 0
        max_pred = None

        for blocker in graph[task_id]['blockers']:
            if blocker in longest_path:
                if longest_path[blocker] + 1 > max_length:
                    max_length = longest_path[blocker] + 1
                    max_pred = blocker

        longest_path[task_id] = max_length
        predecessor[task_id] = max_pred

    # Find task with longest path
    if not longest_path:
        return []

    end_task = max(longest_path, key=longest_path.get)

    # Reconstruct path
    path = []
    current = end_task
    while current is not None:
        path.append(current)
        current = predecessor.get(current)

    return list(reversed(path))


def print_task_info(task_id: str, graph: Dict):
    """Print detailed information about a single task."""
    if task_id not in graph:
        print(f"Task {task_id} not found in graph")
        return

    info = graph[task_id]

    print(f"\n{'='*80}")
    print(f"Task: {task_id}")
    print(f"Name: {info['name']}")
    print(f"Status: {info['status']}")
    print(f"{'='*80}")

    print(f"\nBLOCKERS ({len(info['blockers'])}):")
    if info['blockers']:
        print("This task is BLOCKED BY and cannot proceed until these complete:")
        for blocker in info['blockers']:
            if blocker in graph:
                print(f"  ← {blocker}: {graph[blocker]['name']} [{graph[blocker]['status']}]")
            else:
                print(f"  ← {blocker}: (external task)")
    else:
        print("  ✓ No blockers - can start immediately!")

    print(f"\nDEPENDENTS ({len(info['dependents'])}):")
    if info['dependents']:
        print("These tasks are BLOCKED BY this task and waiting for it to complete:")
        for dependent in info['dependents']:
            if dependent in graph:
                print(f"  → {dependent}: {graph[dependent]['name']} [{graph[dependent]['status']}]")
            else:
                print(f"  → {dependent}: (external task)")
    else:
        print("  ✓ No dependents - no other tasks waiting")


def print_execution_order(sorted_tasks: List[str], graph: Dict):
    """Print tasks in execution order."""
    print(f"\n{'='*80}")
    print("EXECUTION ORDER (What Must Be Completed First)")
    print(f"{'='*80}\n")

    current_level = []
    last_blockers_count = -1
    level_num = 1

    for task_id in sorted_tasks:
        info = graph[task_id]
        blockers_count = len([b for b in info['blockers'] if b in graph])

        if blockers_count != last_blockers_count:
            if current_level:
                print(f"\nLevel {level_num} - Can start in parallel:")
                for tid in current_level:
                    tinfo = graph[tid]
                    status_marker = "✓" if tinfo['status'] in ['comitted', 'Closed'] else " "
                    print(f"  [{status_marker}] {tid}: {tinfo['name']} [{tinfo['status']}]")
                level_num += 1
                current_level = []
            last_blockers_count = blockers_count

        current_level.append(task_id)

    # Print last level
    if current_level:
        print(f"\nLevel {level_num} - Can start after all others:")
        for tid in current_level:
            tinfo = graph[tid]
            status_marker = "✓" if tinfo['status'] in ['comitted', 'Closed'] else " "
            print(f"  [{status_marker}] {tid}: {tinfo['name']} [{tinfo['status']}]")


def print_critical_path(path: List[str], graph: Dict):
    """Print the critical path."""
    print(f"\n{'='*80}")
    print("CRITICAL PATH (Longest Dependency Chain)")
    print(f"{'='*80}\n")

    print(f"Length: {len(path)} tasks\n")

    for i, task_id in enumerate(path, 1):
        info = graph[task_id]
        status_marker = "✓" if info['status'] in ['comitted', 'Closed'] else " "
        arrow = "  ↓" if i < len(path) else ""
        print(f"{i}. [{status_marker}] {task_id}: {info['name']} [{info['status']}]{arrow}")


def main():
    parser = argparse.ArgumentParser(description='Analyze ClickUp task dependencies')
    parser.add_argument('task_id', nargs='?', help='Task ID to analyze')
    parser.add_argument('--all', metavar='LIST_ID', help='Analyze all tasks in a list')
    parser.add_argument('--project', metavar='TASK_ID', help='Analyze project and subtasks')
    parser.add_argument('--tasks', nargs='+', help='Specific task IDs to analyze')

    args = parser.parse_args()

    if not any([args.task_id, args.all, args.project, args.tasks]):
        parser.print_help()
        sys.exit(1)

    client = ClickUpClient()

    # Collect task IDs
    task_ids = []

    if args.task_id:
        task_ids = [args.task_id]
    elif args.tasks:
        task_ids = args.tasks
    elif args.all:
        # Get all tasks from list
        list_tasks = client.get_list_tasks(args.all, subtasks=True, include_closed=True)
        task_ids = [t['id'] for t in list_tasks.get('tasks', [])]
    elif args.project:
        # Get project and look for related tasks
        task_ids = [args.project]
        # You could expand this to find subtasks, linked tasks, etc.

    if not task_ids:
        print("No tasks found")
        sys.exit(1)

    print(f"Analyzing {len(task_ids)} tasks...")

    # Build dependency graph
    graph = build_dependency_graph(client, task_ids)

    # Single task analysis
    if len(task_ids) == 1 and args.task_id:
        print_task_info(task_ids[0], graph)
        return

    # Multiple task analysis
    sorted_tasks = topological_sort(graph)
    critical_path = find_critical_path(graph, sorted_tasks)

    print_execution_order(sorted_tasks, graph)
    print_critical_path(critical_path, graph)

    # Summary statistics
    completed = sum(1 for t in graph.values() if t['status'] in ['comitted', 'Closed'])
    total = len(graph)

    print(f"\n{'='*80}")
    print("SUMMARY")
    print(f"{'='*80}")
    print(f"Total tasks: {total}")
    print(f"Completed: {completed} ({completed/total*100:.1f}%)")
    print(f"Remaining: {total - completed}")
    print(f"Critical path length: {len(critical_path)} tasks")
    print(f"Parallel opportunities: {len([t for t in graph.values() if not t['blockers']])} tasks can start now")


if __name__ == '__main__':
    main()
