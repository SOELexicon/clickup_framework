#!/usr/bin/env python3
"""
Post GitHub Actions Run Information to ClickUp

Posts detailed GitHub Actions workflow run information to the ClickUp Framework project.
Creates tasks in the Actions list with workflow run details.
"""

import sys
import os
import json
from datetime import datetime

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from clickup_framework import ClickUpClient


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


def create_action_task(client, list_id, run_info):
    """Create a ClickUp task for a GitHub Actions run."""

    status_emoji = determine_status_emoji(run_info['job_status'])
    run_url = get_run_url(run_info)
    commit_url = get_commit_url(run_info)

    # Build task name
    task_name = f"{status_emoji} [{run_info['workflow_name']}] Run #{run_info['run_number']} - {run_info['ref_name']}"

    # Build task description with detailed workflow info
    description = f"""# GitHub Actions Run

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

*Automatically created by GitHub Actions workflow*
"""

    # Determine tags based on status and event
    tags = [{'name': 'github-actions'}, {'name': 'automated'}]

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

    # Create the task
    task = client.create_task(
        list_id,
        name=task_name,
        description=description,
        tags=tags
    )

    return task


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

    # Create task in ClickUp
    try:
        task = create_action_task(client, LIST_ID, run_info)
        print("=" * 80)
        print("SUCCESS")
        print("=" * 80)
        print(f"Task created: {task['id']}")
        print(f"Task name: {task['name']}")
        print(f"URL: {task.get('url', 'N/A')}")
        print()
    except Exception as e:
        print(f"✗ Error creating task: {e}", file=sys.stderr)
        import traceback
        traceback.print_exc()
        return 1

    print("=" * 80)

    return 0


if __name__ == "__main__":
    sys.exit(main())
