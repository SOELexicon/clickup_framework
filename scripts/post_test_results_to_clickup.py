#!/usr/bin/env python3
"""
Post Test Results to ClickUp

Posts detailed test results to the ClickUp Framework Testing list.
Creates tasks with test outcomes, coverage, and failure details.
"""

import sys
import os
import json
import subprocess
from datetime import datetime

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from clickup_framework import ClickUpClient


def run_tests_with_coverage():
    """Run tests and capture results with coverage."""
    print("Running tests with coverage...")

    # Run pytest with JSON report and coverage
    cmd = [
        'python', '-m', 'pytest',
        'tests/',
        '-v',
        '--tb=short',
        '--json-report',
        '--json-report-file=test_report.json',
        '--cov=clickup_framework',
        '--cov-report=json',
        '--cov-report=term'
    ]

    try:
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            timeout=300
        )

        return {
            'exit_code': result.returncode,
            'stdout': result.stdout,
            'stderr': result.stderr
        }
    except subprocess.TimeoutExpired:
        return {
            'exit_code': 124,
            'stdout': '',
            'stderr': 'Tests timed out after 5 minutes'
        }
    except Exception as e:
        return {
            'exit_code': 1,
            'stdout': '',
            'stderr': str(e)
        }


def load_test_report():
    """Load the JSON test report."""
    try:
        with open('test_report.json', 'r') as f:
            return json.load(f)
    except FileNotFoundError:
        print("Warning: test_report.json not found")
        return None


def load_coverage_report():
    """Load the coverage report."""
    try:
        with open('coverage.json', 'r') as f:
            return json.load(f)
    except FileNotFoundError:
        print("Warning: coverage.json not found")
        return None


def create_test_run_task(client, list_id, test_results, coverage_data, repo_name, branch_name, commit_hash):
    """Create a main task for the test run."""

    # Extract summary from test report
    if test_results and 'summary' in test_results:
        summary = test_results['summary']
        total = summary.get('total', 0)
        passed = summary.get('passed', 0)
        failed = summary.get('failed', 0)
        skipped = summary.get('skipped', 0)
        errors = summary.get('error', 0)

        status_emoji = "✅" if failed == 0 and errors == 0 else "❌"
        test_summary = f"{status_emoji} {passed}/{total} passed"
    else:
        test_summary = "Test results unavailable"
        passed = 0
        total = 0
        failed = 0
        skipped = 0
        errors = 0

    # Get coverage percentage
    coverage_pct = 0
    if coverage_data and 'totals' in coverage_data:
        coverage_pct = coverage_data['totals'].get('percent_covered', 0)

    # Build task name
    timestamp = datetime.now().strftime('%Y-%m-%d %H:%M')
    task_name = f"[Test Run {timestamp}] {test_summary} | {coverage_pct:.1f}% coverage"

    # Build task description
    description = f"""# Test Run Results

**Repository:** {repo_name}
**Branch:** {branch_name}
**Commit:** `{commit_hash}`
**Timestamp:** {timestamp}

## Summary

- **Total Tests:** {total}
- **Passed:** {passed} ✅
- **Failed:** {failed} ❌
- **Skipped:** {skipped} ⏭️
- **Errors:** {errors} 🚫
- **Success Rate:** {(passed/total*100) if total > 0 else 0:.1f}%

## Coverage

- **Overall Coverage:** {coverage_pct:.1f}%
"""

    # Add failed tests details if any
    if test_results and failed > 0:
        description += "\n## Failed Tests\n\n"
        for test in test_results.get('tests', []):
            if test.get('outcome') == 'failed':
                description += f"- **{test.get('nodeid', 'Unknown')}**\n"
                if 'call' in test and 'longrepr' in test['call']:
                    error_msg = test['call']['longrepr'][:200]
                    description += f"  ```\n  {error_msg}...\n  ```\n"

    # Add coverage details
    if coverage_data and 'files' in coverage_data:
        description += "\n## Coverage by Module\n\n"
        files = coverage_data['files']
        # Sort by coverage percentage
        sorted_files = sorted(
            files.items(),
            key=lambda x: x[1]['summary'].get('percent_covered', 0)
        )

        for filepath, data in sorted_files[:10]:  # Top 10 files
            pct = data['summary'].get('percent_covered', 0)
            emoji = "✅" if pct >= 80 else "⚠️" if pct >= 50 else "❌"
            description += f"- {emoji} `{filepath}`: {pct:.1f}%\n"

    # Determine task status based on results
    if failed == 0 and errors == 0:
        custom_type = 'milestone'  # Success
        priority = 4  # Low priority
    else:
        custom_type = 'bug'  # Failure
        priority = 1  # High priority

    # Create the task
    task = client.create_task(
        list_id,
        name=task_name,
        description=description,
        priority={'priority': str(priority)},
        tags=[
            {'name': 'automated'},
            {'name': 'test-run'},
            {'name': f'coverage-{int(coverage_pct)}'}
        ]
    )

    return task


def create_failed_test_tasks(client, list_id, test_results, parent_task_id):
    """Create individual tasks for failed tests."""
    if not test_results or 'tests' not in test_results:
        return []

    created_tasks = []

    for test in test_results['tests']:
        if test.get('outcome') != 'failed':
            continue

        nodeid = test.get('nodeid', 'Unknown Test')
        test_name = nodeid.split('::')[-1] if '::' in nodeid else nodeid

        # Build task description
        description = f"""# Failed Test Details

**Test:** `{nodeid}`
**File:** `{test.get('nodeid', '').split('::')[0]}`
**Duration:** {test.get('duration', 0):.2f}s

## Error

"""

        # Add error details
        if 'call' in test:
            call_info = test['call']
            if 'longrepr' in call_info:
                description += f"```python\n{call_info['longrepr']}\n```"
            if 'crash' in call_info:
                description += f"\n\n**Crash Info:**\n```\n{call_info['crash']}\n```"

        # Create task
        task = client.create_task(
            list_id,
            name=f"[Test Failure] {test_name}",
            description=description,
            parent=parent_task_id,
            priority={'priority': '1'},
            tags=[
                {'name': 'test-failure'},
                {'name': 'automated'}
            ]
        )

        created_tasks.append(task)

    return created_tasks


def main():
    """Main entry point."""
    # Configuration
    LIST_ID = "901517404278"  # Testing list
    REPO_NAME = os.environ.get('GITHUB_REPOSITORY', 'clickup_framework')
    BRANCH_NAME = os.environ.get('GITHUB_REF_NAME', 'unknown')
    COMMIT_HASH = os.environ.get('GITHUB_SHA', 'unknown')[:8]

    print("=" * 80)
    print(f"Posting Test Results to ClickUp")
    print("=" * 80)
    print(f"Repository: {REPO_NAME}")
    print(f"Branch: {BRANCH_NAME}")
    print(f"Commit: {COMMIT_HASH}")
    print()

    # Initialize client
    try:
        client = ClickUpClient()
    except Exception as e:
        print(f"✗ Error initializing ClickUp client: {e}", file=sys.stderr)
        print("Make sure CLICKUP_API_TOKEN environment variable is set.", file=sys.stderr)
        return 1

    # Run tests
    test_run_result = run_tests_with_coverage()

    # Load reports
    test_report = load_test_report()
    coverage_report = load_coverage_report()

    # Create main test run task
    try:
        main_task = create_test_run_task(
            client,
            LIST_ID,
            test_report,
            coverage_report,
            REPO_NAME,
            BRANCH_NAME,
            COMMIT_HASH
        )
        print(f"✓ Test run task created: {main_task['id']}")
        print(f"  URL: {main_task.get('url', 'N/A')}")
        print()

        # Create tasks for failed tests
        if test_report:
            failed_tasks = create_failed_test_tasks(
                client,
                LIST_ID,
                test_report,
                main_task['id']
            )

            if failed_tasks:
                print(f"✓ Created {len(failed_tasks)} failed test tasks")
                for task in failed_tasks:
                    print(f"  - {task['name']}")
                print()

    except Exception as e:
        print(f"✗ Error creating tasks: {e}")
        import traceback
        traceback.print_exc()
        return 1

    # Summary
    print("=" * 80)
    print("SUMMARY")
    print("=" * 80)
    print(f"Test run: {test_run_result['exit_code'] == 0 and '✅ PASSED' or '❌ FAILED'}")
    if test_report and 'summary' in test_report:
        summary = test_report['summary']
        print(f"Tests: {summary.get('passed', 0)}/{summary.get('total', 0)} passed")
    if coverage_report and 'totals' in coverage_report:
        pct = coverage_report['totals'].get('percent_covered', 0)
        print(f"Coverage: {pct:.1f}%")
    print("=" * 80)

    return test_run_result['exit_code']


if __name__ == "__main__":
    sys.exit(main())
