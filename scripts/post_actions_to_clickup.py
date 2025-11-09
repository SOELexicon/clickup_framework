#!/usr/bin/env python3
"""
Post GitHub Actions Run Information to ClickUp

Posts detailed GitHub Actions workflow run information to the ClickUp Framework project.
Creates Action Run tasks with Test Result subtasks and attaches test reports.
"""

import sys
import os
import json
import re
from datetime import datetime

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from clickup_framework import ClickUpClient


def contains_markdown(text):
    """
    Detect if text contains markdown formatting.
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


def get_workflow_run_info():
    """Get information about the current GitHub Actions workflow run."""
    return {
        'workflow_name': os.environ.get('GITHUB_WORKFLOW', 'Unknown Workflow'),
        'run_id': os.environ.get('GITHUB_RUN_ID', 'unknown'),
        'run_number': os.environ.get('GITHUB_RUN_NUMBER', 'unknown'),
        'run_attempt': os.environ.get('GITHUB_RUN_ATTEMPT', '1'),
        'repository': os.environ.get('GITHUB_REPOSITORY', 'unknown'),
        'ref': os.environ.get('GITHUB_REF', 'unknown'),
        'ref_name': os.environ.get('GITHUB_REF_NAME', 'unknown'),
        'ref_type': os.environ.get('GITHUB_REF_TYPE', 'unknown'),
        'sha': os.environ.get('GITHUB_SHA', 'unknown'),
        'actor': os.environ.get('GITHUB_ACTOR', 'unknown'),
        'triggering_actor': os.environ.get('GITHUB_TRIGGERING_ACTOR', 'unknown'),
        'event_name': os.environ.get('GITHUB_EVENT_NAME', 'unknown'),
        'server_url': os.environ.get('GITHUB_SERVER_URL', 'https://github.com'),
        'job_status': os.environ.get('JOB_STATUS', 'unknown'),
        'timestamp': datetime.now().strftime('%Y-%m-%d %H:%M:%S UTC')
    }


def get_run_url(info):
    """Generate the URL for the workflow run."""
    return f"{info['server_url']}/{info['repository']}/actions/runs/{info['run_id']}"


def get_commit_url(info):
    """Generate the URL for the commit."""
    return f"{info['server_url']}/{info['repository']}/commit/{info['sha']}"


def determine_status_emoji(job_status):
    """Get emoji for job status."""
    status_map = {
        'success': '✅',
        'failure': '❌',
        'cancelled': '🚫',
        'skipped': '⏭️',
        'unknown': '❓'
    }
    return status_map.get(job_status.lower(), '❓')


def load_test_report():
    """Load the JSON test report if it exists."""
    try:
        if os.path.exists('test_report.json'):
            with open('test_report.json', 'r') as f:
                return json.load(f)
    except Exception as e:
        print(f"Warning: Could not load test_report.json: {e}")
    return None


def load_coverage_report():
    """Load the coverage report if it exists."""
    try:
        if os.path.exists('coverage.json'):
            with open('coverage.json', 'r') as f:
                return json.load(f)
    except Exception as e:
        print(f"Warning: Could not load coverage.json: {e}")
    return None


def create_action_run_task(client, list_id, run_info):
    """Create a ClickUp Action Run task for a GitHub Actions run."""

    status_emoji = determine_status_emoji(run_info['job_status'])
    run_url = get_run_url(run_info)
    commit_url = get_commit_url(run_info)

    # Build task name
    task_name = f"[Run #{run_info['run_number']}] {run_info['workflow_name']} - {run_info['ref_name']}"

    # Build task description with detailed workflow info
    description = f"""# GitHub Actions Run #{run_info['run_number']}

**Status:** {status_emoji} {run_info['job_status'].upper()}
**Workflow:** {run_info['workflow_name']}
**Run ID:** {run_info['run_id']}
**Run Number:** #{run_info['run_number']} (Attempt {run_info['run_attempt']})
**Timestamp:** {run_info['timestamp']}

## Repository Information

**Repository:** {run_info['repository']}
**Branch/Tag:** {run_info['ref_name']} ({run_info['ref_type']})
**Commit:** [`{run_info['sha'][:8]}`]({commit_url})
**Triggered by:** {run_info['triggering_actor']}
**Event:** {run_info['event_name']}

## Links

- 🔗 [View Workflow Run]({run_url})
- 📝 [View Commit]({commit_url})

---

## Test Results

Test result tasks will be added as subtasks below.

---

*Automatically created by GitHub Actions workflow*
"""

    # Determine tags based on status and event
    tags = [
        {'name': 'github-actions'},
        {'name': 'automated'},
        {'name': f'run-{run_info["run_number"]}'},
        {'name': run_info['ref_name']}
    ]

    # Add status tag
    if run_info['job_status'].lower() == 'success':
        tags.append({'name': 'success'})
    elif run_info['job_status'].lower() == 'failure':
        tags.append({'name': 'failure'})
    elif run_info['job_status'].lower() == 'cancelled':
        tags.append({'name': 'cancelled'})

    # Add event type tag
    if run_info['event_name']:
        tags.append({'name': run_info['event_name']})

    # Determine task status based on job status
    if run_info['job_status'].lower() == 'success':
        status = 'complete'
    elif run_info['job_status'].lower() == 'failure':
        status = 'failed'
    else:
        status = 'to do'

    # Create the task with Action Run type
    task_data = {
        'name': task_name,
        'status': status,
        'custom_type': 'Action Run',  # Set task type to Action Run
        'tags': tags
    }

    if contains_markdown(description):
        task_data['markdown_description'] = description
    else:
        task_data['description'] = description

    task = client.create_task(list_id, **task_data)

    return task


def create_test_result_task(client, list_id, test_report, coverage_report,
                            run_info, parent_task_id):
    """Create a Test Result subtask with test data."""

    # Extract summary from test report
    if test_report and 'summary' in test_report:
        summary = test_report['summary']
        total = summary.get('total', 0)
        passed = summary.get('passed', 0)
        failed = summary.get('failed', 0)
        skipped = summary.get('skipped', 0)
        errors = summary.get('error', 0)
        duration = test_report.get('duration', 0)

        status_emoji = "✅" if failed == 0 and errors == 0 else "❌"
        test_summary = f"{status_emoji} {passed}/{total} passed"
    else:
        test_summary = "No test data available"
        passed = 0
        total = 0
        failed = 0
        skipped = 0
        errors = 0
        duration = 0

    # Get coverage percentage
    coverage_pct = 0
    if coverage_report and 'totals' in coverage_report:
        coverage_pct = coverage_report['totals'].get('percent_covered', 0)

    # Build task name
    task_name = f"Test Results - {test_summary} | {coverage_pct:.1f}% coverage"

    # Build comprehensive markdown test report description
    description = f"""# Test Run Results Report

**Repository:** {run_info['repository']}
**Branch:** {run_info['ref_name']}
**Commit:** `{run_info['sha'][:8]}`
**Timestamp:** {run_info['timestamp']}
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

    # Add failed tests details if any
    if test_report and failed > 0:
        description += "\n### ❌ Failed Tests\n\n"
        for test in test_report.get('tests', []):
            if test.get('outcome') == 'failed':
                nodeid = test.get('nodeid', 'Unknown')
                duration_test = test.get('duration', 0)
                description += f"\n#### {nodeid}\n\n"
                description += f"**Duration:** {duration_test:.2f}s\n\n"

                if 'call' in test and 'longrepr' in test['call']:
                    error_msg = test['call']['longrepr']
                    # Truncate very long error messages
                    if len(error_msg) > 500:
                        error_msg = error_msg[:500] + "...\n\n*(Error truncated. See full report attachment)*"
                    description += f"**Error:**\n```python\n{error_msg}\n```\n"

    # Add detailed coverage breakdown
    if coverage_report and 'files' in coverage_report:
        description += "\n---\n\n## 📁 Coverage by Module\n\n"
        description += "| File | Coverage | Missing Lines |\n"
        description += "|------|----------|---------------|\n"

        files = coverage_report['files']
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
        'parent': parent_task_id,  # Make it a subtask
        'priority': {'priority': str(priority)},
        'status': status,
        'custom_type': 'Test Result',  # Set task type to Test Result
        'tags': [
            {'name': 'automated'},
            {'name': 'test-results'},
            {'name': f'coverage-{int(coverage_pct)}'},
            {'name': f'run-{run_info["run_number"]}'}
        ]
    }

    if contains_markdown(description):
        task_data['markdown_description'] = description
    else:
        task_data['description'] = description

    task = client.create_task(list_id, **task_data)

    return task


def upload_test_report_attachments(client, task_id):
    """
    Upload test report files as attachments.

    Args:
        client: ClickUpClient instance
        task_id: Task ID to attach files to

    Returns:
        List of uploaded attachment info
    """
    attachments = []

    files_to_attach = [
        ('test_report.json', 'Test Report (JSON)'),
        ('coverage.json', 'Coverage Report (JSON)'),
        ('.coverage', 'Coverage Data File')
    ]

    for filename, description in files_to_attach:
        if os.path.exists(filename):
            try:
                print(f"  Uploading {filename}...")

                # Upload using ClickUp API (takes file path directly)
                attachment = client.create_task_attachment(task_id, filename)

                print(f"  ✓ {filename} uploaded successfully")
                attachments.append({
                    'filename': filename,
                    'description': description,
                    'attachment': attachment
                })
            except Exception as e:
                print(f"  ✗ Error uploading {filename}: {e}")

    return attachments


def upload_screenshot_attachments(client, task_id):
    """
    Upload display component screenshot files as attachments.

    Args:
        client: ClickUpClient instance
        task_id: Task ID to attach files to

    Returns:
        List of uploaded attachment info
    """
    attachments = []
    screenshots_dir = 'screenshots'

    # Check if screenshots directory exists
    if not os.path.exists(screenshots_dir):
        print(f"  No {screenshots_dir}/ directory found")
        return attachments

    # Get all JPG files from screenshots directory
    try:
        screenshot_files = [
            f for f in os.listdir(screenshots_dir)
            if f.endswith('.jpg')
        ]

        if not screenshot_files:
            print(f"  No screenshot files found in {screenshots_dir}/")
            return attachments

        print(f"  Found {len(screenshot_files)} screenshot(s) to upload")

        for filename in sorted(screenshot_files):
            file_path = os.path.join(screenshots_dir, filename)
            try:
                print(f"  Uploading {filename}...")

                # Upload using ClickUp API (takes file path directly)
                attachment = client.create_task_attachment(task_id, file_path)

                print(f"  ✓ {filename} uploaded successfully")
                attachments.append({
                    'filename': filename,
                    'description': f'Display Component Screenshot: {filename}',
                    'attachment': attachment
                })
            except Exception as e:
                print(f"  ✗ Error uploading {filename}: {e}")

    except Exception as e:
        print(f"  Error reading screenshots directory: {e}")

    return attachments


def get_task_type_breakdown(client, list_id):
    """
    Get breakdown of tasks by type from the list.

    Args:
        client: ClickUpClient instance
        list_id: List ID to analyze

    Returns:
        Dictionary with task type statistics
    """
    try:
        print("Fetching tasks for type breakdown...")
        response = client.get_list_tasks(list_id, include_closed=True)
        tasks = response.get('tasks', [])

        # Count by task type
        type_counts = {}
        type_status_counts = {}
        type_emojis = {
            'Bug': '🐛',
            'Feature': '🚀',
            'Test': '🧪',
            'Test Result': '📊',
            'Action Run': '⚙️',
            'Documentation': '📚',
            'Refactor': '♻️',
            'Enhancement': '✨',
            'Chore': '🧹',
            'Security': '🛡️',
            'Merge': '🔀',
            'Task': '📝',
            'Commit': '💾'
        }

        for task in tasks:
            task_type = task.get('custom_type') or 'Task'
            status = task.get('status', {}).get('status', 'unknown')

            # Count by type
            if task_type not in type_counts:
                type_counts[task_type] = 0
            type_counts[task_type] += 1

            # Count by type and status
            if task_type not in type_status_counts:
                type_status_counts[task_type] = {
                    'open': 0,
                    'in_progress': 0,
                    'complete': 0,
                    'failed': 0,
                    'other': 0
                }

            # Categorize status
            status_lower = status.lower()
            if status_lower in ['open', 'to do', 'todo', 'backlog']:
                type_status_counts[task_type]['open'] += 1
            elif status_lower in ['in progress', 'in review', 'testing']:
                type_status_counts[task_type]['in_progress'] += 1
            elif status_lower in ['complete', 'closed', 'done', 'passed']:
                type_status_counts[task_type]['complete'] += 1
            elif status_lower in ['failed', 'blocked']:
                type_status_counts[task_type]['failed'] += 1
            else:
                type_status_counts[task_type]['other'] += 1

        return {
            'total_tasks': len(tasks),
            'type_counts': type_counts,
            'type_status_counts': type_status_counts,
            'type_emojis': type_emojis
        }

    except Exception as e:
        print(f"Warning: Could not fetch task breakdown: {e}")
        return None


def format_task_type_report(breakdown):
    """
    Format task type breakdown as markdown.

    Args:
        breakdown: Dictionary from get_task_type_breakdown

    Returns:
        Markdown formatted report
    """
    if not breakdown:
        return "_Task breakdown unavailable_"

    type_counts = breakdown['type_counts']
    type_status_counts = breakdown['type_status_counts']
    type_emojis = breakdown['type_emojis']
    total_tasks = breakdown['total_tasks']

    # Sort by count descending
    sorted_types = sorted(type_counts.items(), key=lambda x: x[1], reverse=True)

    report = f"## 📊 Task Type Breakdown\n\n"
    report += f"**Total Tasks in List:** {total_tasks}\n\n"
    report += "| Type | Total | Open | In Progress | Complete | Failed |\n"
    report += "|------|-------|------|-------------|----------|--------|\n"

    for task_type, count in sorted_types:
        emoji = type_emojis.get(task_type, '📝')
        status_counts = type_status_counts.get(task_type, {})
        open_count = status_counts.get('open', 0)
        in_progress = status_counts.get('in_progress', 0)
        complete = status_counts.get('complete', 0)
        failed = status_counts.get('failed', 0)

        report += f"| {emoji} **{task_type}** | {count} | {open_count} | {in_progress} | {complete} | {failed} |\n"

    # Add summary stats
    total_open = sum(counts.get('open', 0) for counts in type_status_counts.values())
    total_in_progress = sum(counts.get('in_progress', 0) for counts in type_status_counts.values())
    total_complete = sum(counts.get('complete', 0) for counts in type_status_counts.values())
    total_failed = sum(counts.get('failed', 0) for counts in type_status_counts.values())

    report += f"| **TOTAL** | **{total_tasks}** | **{total_open}** | **{total_in_progress}** | **{total_complete}** | **{total_failed}** |\n\n"

    # Calculate completion rate
    if total_tasks > 0:
        completion_rate = (total_complete / total_tasks) * 100
        report += f"**Completion Rate:** {completion_rate:.1f}%\n"
        if total_failed > 0:
            failure_rate = (total_failed / total_tasks) * 100
            report += f"**Failure Rate:** {failure_rate:.1f}%\n"

    return report


def main():
    """Main entry point."""
    # Configuration
    LIST_ID = "901517404278"  # Actions list

    print("=" * 80)
    print(f"Posting GitHub Actions Run to ClickUp")
    print("=" * 80)

    # Get workflow run information
    run_info = get_workflow_run_info()

    print(f"Workflow: {run_info['workflow_name']}")
    print(f"Run: #{run_info['run_number']} (ID: {run_info['run_id']})")
    print(f"Status: {run_info['job_status']}")
    print(f"Repository: {run_info['repository']}")
    print(f"Branch: {run_info['ref_name']}")
    print(f"Triggered by: {run_info['triggering_actor']}")
    print(f"Event: {run_info['event_name']}")
    print()

    # Initialize client
    try:
        client = ClickUpClient()
    except Exception as e:
        print(f"✗ Error initializing ClickUp client: {e}", file=sys.stderr)
        print("Make sure CLICKUP_API_TOKEN environment variable is set.", file=sys.stderr)
        return 1

    # Get task type breakdown
    print()
    task_breakdown = get_task_type_breakdown(client, LIST_ID)
    if task_breakdown:
        print(f"✓ Task breakdown retrieved: {task_breakdown['total_tasks']} tasks analyzed")
        print()

    # Create Action Run task in ClickUp
    print(f"Creating Action Run task for run #{run_info['run_number']}...")
    try:
        action_run_task = create_action_run_task(client, LIST_ID, run_info)
        print(f"✓ Action Run task created: {action_run_task['id']}")
        print(f"  Name: {action_run_task['name']}")
        print(f"  URL: {action_run_task.get('url', 'N/A')}")
        print()

        # Add task type breakdown as a comment
        if task_breakdown:
            print("Adding task type breakdown report as comment...")
            try:
                breakdown_report = format_task_type_report(task_breakdown)
                comment_text = f"""# 📊 Project Status Report

{breakdown_report}

---

*Report generated at workflow run #{run_info['run_number']}*
"""
                client.create_task_comment(
                    action_run_task['id'],
                    comment_text=comment_text,
                    notify_all=False
                )
                print("✓ Task breakdown report added to Action Run task")
                print()
            except Exception as e:
                print(f"Warning: Could not add breakdown report: {e}")
                print()

    except Exception as e:
        print(f"✗ Error creating Action Run task: {e}", file=sys.stderr)
        import traceback
        traceback.print_exc()
        return 1

    # Check for test reports
    print("Checking for test reports...")
    test_report = load_test_report()
    coverage_report = load_coverage_report()

    # Create Test Result subtask if test reports exist
    if test_report or coverage_report:
        print("Test reports found. Creating Test Result subtask...")
        try:
            test_result_task = create_test_result_task(
                client,
                LIST_ID,
                test_report,
                coverage_report,
                run_info,
                action_run_task['id']
            )
            print(f"✓ Test Result task created: {test_result_task['id']}")
            print(f"  Name: {test_result_task['name']}")
            print(f"  URL: {test_result_task.get('url', 'N/A')}")
            print()

            # Upload attachments
            print("Uploading test report attachments...")
            attachments = upload_test_report_attachments(client, test_result_task['id'])
            if attachments:
                print(f"✓ {len(attachments)} file(s) uploaded successfully")
            else:
                print("No attachment files found to upload")
            print()

        except Exception as e:
            print(f"✗ Error creating Test Result task: {e}", file=sys.stderr)
            import traceback
            traceback.print_exc()
            # Don't return error - Action Run task was created successfully
    else:
        print("No test reports found. Skipping Test Result subtask creation.")
        print()

    # Upload screenshot attachments to the Action Run task
    print("Checking for display component screenshots...")
    screenshot_attachments = upload_screenshot_attachments(client, action_run_task['id'])
    if screenshot_attachments:
        print(f"✓ {len(screenshot_attachments)} screenshot(s) uploaded to Action Run task")
        print()
    else:
        print("No screenshots found to upload")
        print()

    # Summary
    print("=" * 80)
    print("SUCCESS")
    print("=" * 80)
    print(f"Action Run Task: {action_run_task.get('url', 'N/A')}")
    if test_report and 'summary' in test_report:
        summary = test_report['summary']
        print(f"Tests: {summary.get('passed', 0)}/{summary.get('total', 0)} passed")
    if coverage_report and 'totals' in coverage_report:
        pct = coverage_report['totals'].get('percent_covered', 0)
        print(f"Coverage: {pct:.1f}%")
    print("=" * 80)

    return 0


if __name__ == "__main__":
    sys.exit(main())
