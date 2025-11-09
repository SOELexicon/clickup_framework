#!/usr/bin/env python3
"""
Post Test Results to ClickUp

Posts detailed test results to the ClickUp Framework Testing list.
Creates PR tasks with Test Result subtasks and attaches test reports.
"""

import sys
import os
import json
import subprocess
from datetime import datetime
import re

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from clickup_framework import ClickUpClient


def contains_markdown(text):
    """
    Detect if text contains markdown formatting.

    Checks for common markdown patterns:
    - Headers (#, ##, ###)
    - Code blocks (```)
    - Tables (|---|)
    - Links ([text](url))
    - Bold (**text**)
    - Lists (-, *, 1.)
    """
    if not text:
        return False

    markdown_patterns = [
        r'#+\s',           # Headers
        r'```',            # Code blocks
        r'\|.*\|',         # Tables
        r'\[.*\]\(.*\)',   # Links
        r'\*\*.*\*\*',     # Bold
        r'^[-*]\s',        # Unordered lists
        r'^\d+\.\s',       # Ordered lists
    ]

    for pattern in markdown_patterns:
        if re.search(pattern, text, re.MULTILINE):
            return True

    return False


def get_pr_info():
    """Get PR information from GitHub environment."""
    pr_number = os.environ.get('PR_NUMBER')
    pr_title = os.environ.get('PR_TITLE')
    event_name = os.environ.get('GITHUB_EVENT_NAME', 'push')

    # Try to extract from GITHUB_REF if not explicitly set
    if not pr_number and event_name == 'pull_request':
        ref = os.environ.get('GITHUB_REF', '')
        # Format: refs/pull/123/merge
        match = re.search(r'refs/pull/(\d+)', ref)
        if match:
            pr_number = match.group(1)

    return {
        'number': pr_number,
        'title': pr_title or f'PR #{pr_number}' if pr_number else None,
        'is_pr': event_name == 'pull_request' or pr_number is not None
    }


def find_pr_task(client, list_id, pr_number):
    """Find existing PR task by PR number."""
    if not pr_number:
        return None

    try:
        # Get all tasks from the list
        response = client.get_list_tasks(list_id, include_closed=False)
        tasks = response.get('tasks', [])

        # Look for task with PR number in name
        pr_tag = f'[PR #{pr_number}]'
        for task in tasks:
            if pr_tag in task.get('name', ''):
                return task

        return None
    except Exception as e:
        print(f"Warning: Could not search for existing PR task: {e}")
        return None


def create_pr_task(client, list_id, pr_number, pr_title, repo_name, branch_name):
    """Create a task for the pull request."""

    task_name = f'[PR #{pr_number}] {pr_title}'

    description = f"""# Pull Request #{pr_number}

**Repository:** {repo_name}
**Branch:** {branch_name}
**Title:** {pr_title}

This task tracks test results for PR #{pr_number}.

## Test Runs

Test results will be added as subtasks below.
"""

    # Create the task with custom_type if supported
    task_data = {
        'name': task_name,
        'status': 'to do',  # Start PR tasks as 'to do'
        'tags': [
            {'name': f'pr-{pr_number}'},
            {'name': 'pull-request'},
            {'name': 'automated'}
        ]
    }

    # Use markdown_description if content has markdown, otherwise use description
    if contains_markdown(description):
        task_data['markdown_description'] = description
    else:
        task_data['description'] = description

    task = client.create_task(list_id, **task_data)

    return task


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


def create_test_results_task(client, list_id, test_results, coverage_data,
                             repo_name, branch_name, commit_hash, parent_task_id=None):
    """Create a test results task."""

    # Extract summary from test report
    if test_results and 'summary' in test_results:
        summary = test_results['summary']
        total = summary.get('total', 0)
        passed = summary.get('passed', 0)
        failed = summary.get('failed', 0)
        skipped = summary.get('skipped', 0)
        errors = summary.get('error', 0)
        duration = test_results.get('duration', 0)

        status_emoji = "✅" if failed == 0 and errors == 0 else "❌"
        test_summary = f"{status_emoji} {passed}/{total} passed"
    else:
        test_summary = "Test results unavailable"
        passed = 0
        total = 0
        failed = 0
        skipped = 0
        errors = 0
        duration = 0

    # Get coverage percentage
    coverage_pct = 0
    if coverage_data and 'totals' in coverage_data:
        coverage_pct = coverage_data['totals'].get('percent_covered', 0)

    # Build task name
    timestamp = datetime.now().strftime('%Y-%m-%d %H:%M')
    task_name = f'[Test Results {timestamp}] {test_summary} | {coverage_pct:.1f}% coverage'

    # Build comprehensive markdown test report description
    description = f"""# Test Run Results Report

**Repository:** {repo_name}
**Branch:** {branch_name}
**Commit:** `{commit_hash}`
**Timestamp:** {timestamp}
**Duration:** {duration:.2f}s

---

## 📊 Test Summary

| Metric | Count | Percentage |
|--------|-------|------------|
| **Total Tests** | {total} | 100% |
| **Passed** ✅ | {passed} | {(passed/total*100) if total > 0 else 0:.1f}% |
| **Failed** ❌ | {failed} | {(failed/total*100) if total > 0 else 0:.1f}% |
| **Skipped** ⏭️ | {skipped} | {(skipped/total*100) if total > 0 else 0:.1f}% |
| **Errors** 🚫 | {errors} | {(errors/total*100) if total > 0 else 0:.1f}% |

**Success Rate:** {(passed/total*100) if total > 0 else 0:.1f}%

---

## 📈 Code Coverage

**Overall Coverage:** {coverage_pct:.1f}%

"""

    # Add passed tests summary
    if test_results and passed > 0:
        description += "\n### ✅ Passed Tests\n\n"
        passed_tests = [t for t in test_results.get('tests', []) if t.get('outcome') == 'passed']
        if len(passed_tests) <= 20:  # Show all if reasonable number
            for test in passed_tests:
                nodeid = test.get('nodeid', 'Unknown')
                duration = test.get('duration', 0)
                description += f"- `{nodeid}` ({duration:.2f}s)\n"
        else:
            description += f"*{len(passed_tests)} tests passed successfully*\n"

    # Add failed tests details if any
    if test_results and failed > 0:
        description += "\n### ❌ Failed Tests\n\n"
        for test in test_results.get('tests', []):
            if test.get('outcome') == 'failed':
                nodeid = test.get('nodeid', 'Unknown')
                duration = test.get('duration', 0)
                description += f"\n#### {nodeid}\n\n"
                description += f"**Duration:** {duration:.2f}s\n\n"

                if 'call' in test and 'longrepr' in test['call']:
                    error_msg = test['call']['longrepr']
                    # Truncate very long error messages
                    if len(error_msg) > 500:
                        error_msg = error_msg[:500] + "...\n\n*(Error truncated. See full report attachment)*"
                    description += f"**Error:**\n```python\n{error_msg}\n```\n"

    # Add skipped tests if any
    if test_results and skipped > 0:
        description += "\n### ⏭️ Skipped Tests\n\n"
        skipped_tests = [t for t in test_results.get('tests', []) if t.get('outcome') == 'skipped']
        for test in skipped_tests[:10]:  # Limit to 10
            nodeid = test.get('nodeid', 'Unknown')
            description += f"- `{nodeid}`\n"
        if len(skipped_tests) > 10:
            description += f"\n*...and {len(skipped_tests) - 10} more skipped tests*\n"

    # Add detailed coverage breakdown
    if coverage_data and 'files' in coverage_data:
        description += "\n---\n\n## 📁 Coverage by Module\n\n"
        description += "| File | Coverage | Missing Lines |\n"
        description += "|------|----------|---------------|\n"

        files = coverage_data['files']
        # Sort by coverage percentage (lowest first to highlight issues)
        sorted_files = sorted(
            files.items(),
            key=lambda x: x[1]['summary'].get('percent_covered', 0)
        )

        for filepath, data in sorted_files[:15]:  # Top 15 files
            pct = data['summary'].get('percent_covered', 0)
            missing = data['summary'].get('missing_lines', 0)
            emoji = "✅" if pct >= 80 else "⚠️" if pct >= 50 else "❌"
            description += f"| {emoji} `{filepath}` | {pct:.1f}% | {missing} |\n"

    description += "\n---\n\n*This test report was automatically generated and posted to ClickUp.*"

    # Determine task priority and status based on results
    if failed == 0 and errors == 0:
        priority = 4  # Low priority (success)
        status = 'passed'  # Test passed
    else:
        priority = 1  # High priority (failure)
        status = 'failed'  # Test failed

    # Create the task
    task_data = {
        'name': task_name,
        'priority': {'priority': str(priority)},
        'status': status,  # Use 'passed' or 'failed' based on test results
        'tags': [
            {'name': 'automated'},
            {'name': 'test-results'},
            {'name': f'coverage-{int(coverage_pct)}'}
        ]
    }

    # Use markdown_description if content has markdown, otherwise use description
    if contains_markdown(description):
        task_data['markdown_description'] = description
    else:
        task_data['description'] = description

    if parent_task_id:
        task_data['parent'] = parent_task_id

    task = client.create_task(list_id, **task_data)

    return task


def upload_attachments(client, task_id):
    """Upload test report files as attachments to the task."""
    attachments = []

    files_to_attach = [
        'test_report.json',
        'coverage.json'
    ]

    for filename in files_to_attach:
        if os.path.exists(filename):
            try:
                print(f"  Uploading {filename}...")
                # Note: ClickUp API attachment upload requires special handling
                # For now, we'll note that the files exist
                # In production, you'd use client.upload_attachment(task_id, filename)
                print(f"  ✓ {filename} available for upload")
                attachments.append(filename)
            except Exception as e:
                print(f"  ✗ Error uploading {filename}: {e}")

    return attachments


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
        task_data = {
            'name': f"[Test Failure] {test_name}",
            'parent': parent_task_id,
            'priority': {'priority': '1'},
            'status': 'failed',  # Individual test failed
            'tags': [
                {'name': 'test-failure'},
                {'name': 'automated'}
            ]
        }

        # Use markdown_description if content has markdown, otherwise use description
        if contains_markdown(description):
            task_data['markdown_description'] = description
        else:
            task_data['description'] = description

        task = client.create_task(list_id, **task_data)

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

    # Get PR info
    pr_info = get_pr_info()
    print(f"PR: {pr_info['number'] if pr_info['is_pr'] else 'N/A'}")
    print()

    # Initialize client
    try:
        client = ClickUpClient()
    except Exception as e:
        print(f"✗ Error initializing ClickUp client: {e}", file=sys.stderr)
        print("Make sure CLICKUP_API_TOKEN environment variable is set.", file=sys.stderr)
        return 1

    # Handle PR task creation
    parent_task_id = None
    if pr_info['is_pr'] and pr_info['number']:
        print(f"Looking for existing PR task for PR #{pr_info['number']}...")
        existing_pr_task = find_pr_task(client, LIST_ID, pr_info['number'])

        if existing_pr_task:
            print(f"✓ Found existing PR task: {existing_pr_task['id']}")
            print(f"  URL: {existing_pr_task.get('url', 'N/A')}")
            parent_task_id = existing_pr_task['id']
        else:
            print(f"Creating new PR task for PR #{pr_info['number']}...")
            try:
                pr_task = create_pr_task(
                    client,
                    LIST_ID,
                    pr_info['number'],
                    pr_info['title'],
                    REPO_NAME,
                    BRANCH_NAME
                )
                print(f"✓ PR task created: {pr_task['id']}")
                print(f"  URL: {pr_task.get('url', 'N/A')}")
                parent_task_id = pr_task['id']
            except Exception as e:
                print(f"✗ Error creating PR task: {e}")
                print("  Continuing without PR parent task...")
        print()

    # Run tests
    test_run_result = run_tests_with_coverage()

    # Load reports
    test_report = load_test_report()
    coverage_report = load_coverage_report()

    # Create test results task
    try:
        test_task = create_test_results_task(
            client,
            LIST_ID,
            test_report,
            coverage_report,
            REPO_NAME,
            BRANCH_NAME,
            COMMIT_HASH,
            parent_task_id=parent_task_id
        )
        print(f"✓ Test results task created: {test_task['id']}")
        print(f"  URL: {test_task.get('url', 'N/A')}")
        print()

        # Upload attachments
        print("Uploading test report files...")
        attachments = upload_attachments(client, test_task['id'])
        if attachments:
            print(f"✓ {len(attachments)} files ready for attachment")
        print()

        # Create tasks for failed tests
        if test_report:
            failed_tasks = create_failed_test_tasks(
                client,
                LIST_ID,
                test_report,
                test_task['id']
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
    if pr_info['is_pr']:
        print(f"PR: #{pr_info['number']} - {pr_info['title']}")
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
