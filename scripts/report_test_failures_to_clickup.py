#!/usr/bin/env python3
"""
Report Test Failures to ClickUp

Parses test results and creates ClickUp bug report tasks only for test failures.
Tags each bug with the command/args that failed.
"""

import sys
import os
import json
import subprocess
from datetime import datetime
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from clickup_framework import ClickUpClient


def parse_test_results(test_report_path='test_report.json'):
    """
    Parse pytest JSON report and extract test failures.

    Returns:
        list: List of test failure dictionaries
    """
    if not os.path.exists(test_report_path):
        print(f"⚠️  Test report not found: {test_report_path}")
        return []

    try:
        with open(test_report_path, 'r') as f:
            report = json.load(f)

        failures = []
        tests = report.get('tests', [])

        for test in tests:
            outcome = test.get('outcome', '')
            if outcome in ['failed', 'error']:
                failures.append({
                    'nodeid': test.get('nodeid', ''),
                    'outcome': outcome,
                    'duration': test.get('duration', 0),
                    'call': test.get('call', {}),
                    'lineno': test.get('lineno', 0),
                })

        return failures
    except Exception as e:
        print(f"✗ Error parsing test report: {e}")
        return []


def extract_command_and_args(test_nodeid):
    """
    Extract command and args from test nodeid.

    Example:
        "tests/commands/test_hierarchy.py::test_hierarchy_command"
        Returns: ("hierarchy", "test with basic args")
    """
    # Parse the nodeid
    parts = test_nodeid.split('::')

    if len(parts) < 2:
        return ("unknown", "")

    file_path = parts[0]
    test_name = parts[1]

    # Extract command from file path
    # e.g., "tests/commands/test_hierarchy.py" -> "hierarchy"
    if 'commands/' in file_path:
        command_file = Path(file_path).stem  # test_hierarchy
        command = command_file.replace('test_', '')  # hierarchy
    else:
        # For other tests, use the directory name
        command = Path(file_path).parts[-2] if len(Path(file_path).parts) > 1 else "general"

    # Extract args from test name if present
    # e.g., "test_hierarchy_with_all_flag" -> "with all flag"
    test_args = test_name.replace('test_', '').replace('_', ' ')

    return (command, test_args)


def find_existing_bug_task(client, list_id, test_nodeid, commit_hash):
    """
    Check if a bug task already exists for this test failure.

    Args:
        client: ClickUpClient instance
        list_id: List ID to search in
        test_nodeid: Test node ID
        commit_hash: Short commit hash

    Returns:
        Existing task dictionary or None
    """
    try:
        response = client.get_list_tasks(list_id, include_closed=False)
        tasks = response.get('tasks', [])

        # Look for a bug task with matching test nodeid in the description
        for task in tasks:
            task_name = task.get('name', '')
            # Check if task is a bug for this specific test
            if test_nodeid in task_name and '[Bug]' in task_name:
                return task

        return None
    except Exception as e:
        print(f"  Warning: Could not check for existing bug: {e}")
        return None


def create_bug_task_for_failure(client, list_id, failure, repo_name, branch_name, commit_hash):
    """
    Create a ClickUp bug task for a test failure.

    Args:
        client: ClickUpClient instance
        list_id: List ID to create task in
        failure: Test failure dictionary
        repo_name: Repository name
        branch_name: Branch name
        commit_hash: Short commit hash

    Returns:
        Created task dictionary or None
    """
    try:
        # Extract command and args
        command, args = extract_command_and_args(failure['nodeid'])

        # Create task name
        task_name = f"🐛 [Bug] Test failure: {command} {args}"

        # Extract error information
        call_info = failure.get('call', {})
        longrepr = call_info.get('longrepr', '')
        crash_info = call_info.get('crash', {})

        # Build description
        description = f"""# Test Failure Report

**Status:** {failure['outcome'].upper()}
**Test:** `{failure['nodeid']}`
**Command:** `{command}`
**Args/Scenario:** `{args}`
**Duration:** {failure['duration']:.2f}s
**Repository:** {repo_name}
**Branch:** {branch_name}
**Commit:** `{commit_hash}`

## Error Details

"""

        # Add error traceback
        if longrepr:
            description += f"""### Traceback

```
{longrepr}
```

"""

        # Add crash information if available
        if crash_info:
            crash_message = crash_info.get('message', '')
            if crash_message:
                description += f"""### Crash Info

{crash_message}

"""

        # Add reproduction steps
        description += f"""## Reproduction

To reproduce this failure:

```bash
# Run the specific test
pytest {failure['nodeid']} -v

# Or run all tests for this command
pytest tests/ -k "{command}" -v
```

## Investigation Checklist

- [ ] Reproduce failure locally
- [ ] Identify root cause
- [ ] Write fix
- [ ] Add regression test
- [ ] Verify fix passes all tests
- [ ] Update documentation if needed

---

*Automatically created from test failure*
"""

        # Determine tags based on command
        tags = [
            {'name': 'bug'},
            {'name': 'test-failure'},
            {'name': 'automated'},
            {'name': f'cmd-{command}'},
            {'name': branch_name}
        ]

        # Determine priority based on failure type
        priority = 2  # Default: High priority
        if failure['outcome'] == 'error':
            priority = 1  # Urgent for errors

        # Create task
        task_data = {
            'name': task_name,
            'description': description,
            'priority': priority,
            'tags': tags,
            'status': 'Open'
        }

        task = client.create_task(list_id, **task_data)
        return task

    except Exception as e:
        print(f"✗ Error creating bug task: {e}")
        return None


def get_current_commit_hash():
    """Get current commit hash."""
    try:
        commit_hash = subprocess.check_output(
            ['git', 'rev-parse', '--short', 'HEAD'],
            encoding='utf-8'
        ).strip()
        return commit_hash
    except subprocess.CalledProcessError:
        return 'unknown'


def main():
    """Main entry point."""
    # Configuration
    LIST_ID = os.environ.get('CLICKUP_BUG_LIST_ID', '901517412318')  # Default: Development Tasks
    REPO_NAME = os.environ.get('GITHUB_REPOSITORY', 'clickup_framework')
    BRANCH_NAME = os.environ.get('GITHUB_REF_NAME', subprocess.check_output(
        ['git', 'rev-parse', '--abbrev-ref', 'HEAD'], encoding='utf-8'
    ).strip())
    COMMIT_HASH = os.environ.get('GITHUB_SHA', get_current_commit_hash())[:8]
    TEST_REPORT_PATH = os.environ.get('TEST_REPORT_PATH', 'test_report.json')

    print("=" * 80)
    print("📋 Test Failure Report to ClickUp")
    print("=" * 80)
    print(f"Repository: {REPO_NAME}")
    print(f"Branch: {BRANCH_NAME}")
    print(f"Commit: {COMMIT_HASH}")
    print(f"Report: {TEST_REPORT_PATH}")
    print()

    # Parse test results
    print("🔍 Parsing test results...")
    failures = parse_test_results(TEST_REPORT_PATH)

    if not failures:
        print("✓ No test failures found!")
        return 0

    print(f"⚠️  Found {len(failures)} test failure(s)")
    print()

    # Initialize client
    try:
        client = ClickUpClient()
    except Exception as e:
        print(f"✗ Error initializing ClickUp client: {e}", file=sys.stderr)
        print("Make sure CLICKUP_API_TOKEN environment variable is set.", file=sys.stderr)
        return 1

    # Create bug tasks for failures
    created_tasks = []
    skipped_tasks = []

    for failure in failures:
        print(f"Processing: {failure['nodeid']}")

        # Extract command info
        command, args = extract_command_and_args(failure['nodeid'])
        print(f"  Command: {command}")
        print(f"  Args: {args}")
        print(f"  Outcome: {failure['outcome']}")

        # Check if bug task already exists
        existing_task = find_existing_bug_task(client, LIST_ID, failure['nodeid'], COMMIT_HASH)

        if existing_task:
            print(f"  ⏭️  Bug task already exists: {existing_task['id']}")
            print(f"    URL: {existing_task.get('url', 'N/A')}")
            skipped_tasks.append(existing_task)
        else:
            # Create bug task
            task = create_bug_task_for_failure(
                client, LIST_ID, failure, REPO_NAME, BRANCH_NAME, COMMIT_HASH
            )

            if task:
                created_tasks.append(task)
                print(f"  ✓ Bug task created: {task['id']}")
                print(f"    URL: {task.get('url', 'N/A')}")
            else:
                print(f"  ✗ Failed to create bug task")

        print()

    # Summary
    print("=" * 80)
    print("SUMMARY")
    print("=" * 80)
    print(f"Test failures found: {len(failures)}")
    print(f"Bug tasks created: {len(created_tasks)}")
    print(f"Bug tasks skipped (already exist): {len(skipped_tasks)}")
    print()

    if created_tasks:
        print("Created bug tasks:")
        for task in created_tasks:
            print(f"  🐛 {task['name']}")
            print(f"     ID: {task['id']}")
            print(f"     URL: {task.get('url', 'N/A')}")
        print()

    if skipped_tasks:
        print("Skipped bug tasks (already existed):")
        for task in skipped_tasks:
            print(f"  🐛 {task['name']}")
            print(f"     ID: {task['id']}")
            print(f"     URL: {task.get('url', 'N/A')}")
        print()

    print("=" * 80)

    return 0


if __name__ == "__main__":
    sys.exit(main())
