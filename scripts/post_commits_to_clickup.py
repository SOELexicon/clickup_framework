#!/usr/bin/env python3
"""
Post Commit Information to ClickUp

Posts detailed commit information to the ClickUp Framework project folder.
Creates tasks in the Development Tasks list with commit details.
"""

import sys
import os
import subprocess
import json
from datetime import datetime

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from clickup_framework import ClickUpClient


def get_commit_info(commit_hash):
    """Get detailed information about a commit."""
    try:
        # Get commit details
        commit_info = subprocess.check_output(
            ['git', 'show', '--format=%H%n%an%n%ae%n%at%n%s%n%b', '--stat', commit_hash],
            encoding='utf-8'
        ).strip()

        lines = commit_info.split('\n')

        # Parse commit info
        full_hash = lines[0]
        author_name = lines[1]
        author_email = lines[2]
        timestamp = int(lines[3])
        subject = lines[4]

        # Find where body starts and stats start
        body_lines = []
        stats_start = -1
        for i in range(5, len(lines)):
            if lines[i].strip() and ('|' in lines[i] or 'file' in lines[i]):
                stats_start = i
                break
            body_lines.append(lines[i])

        body = '\n'.join(body_lines).strip()

        # Get file changes
        stats_lines = lines[stats_start:] if stats_start > 0 else []

        # Get changed files list
        changed_files = subprocess.check_output(
            ['git', 'diff-tree', '--no-commit-id', '--name-only', '-r', commit_hash],
            encoding='utf-8'
        ).strip().split('\n')

        return {
            'hash': full_hash[:8],
            'full_hash': full_hash,
            'author_name': author_name,
            'author_email': author_email,
            'timestamp': timestamp,
            'date': datetime.fromtimestamp(timestamp).strftime('%Y-%m-%d %H:%M:%S'),
            'subject': subject,
            'body': body,
            'stats': '\n'.join(stats_lines),
            'changed_files': changed_files,
            'changed_files_count': len(changed_files)
        }
    except subprocess.CalledProcessError as e:
        print(f"Error getting commit info: {e}", file=sys.stderr)
        return None


def get_recent_commits(count=5):
    """Get recent commits."""
    try:
        commit_hashes = subprocess.check_output(
            ['git', 'log', f'-{count}', '--format=%H'],
            encoding='utf-8'
        ).strip().split('\n')
        return commit_hashes
    except subprocess.CalledProcessError as e:
        print(f"Error getting commits: {e}", file=sys.stderr)
        return []


def detect_commit_type(subject, body, changed_files):
    """
    Detect the type of commit based on commit message and changed files.

    Returns: (task_type, emoji)
    """
    subject_lower = subject.lower()
    body_lower = body.lower() if body else ""
    combined = f"{subject_lower} {body_lower}"

    # Check for keywords in commit message
    if any(word in combined for word in ['fix', 'bug', 'bugfix', 'patch', 'repair', 'resolve']):
        return ('Bug', '🐛')
    elif any(word in combined for word in ['feat', 'feature', 'add', 'implement', 'new']):
        return ('Feature', '🚀')
    elif any(word in combined for word in ['refactor', 'restructure', 'rewrite', 'cleanup']):
        return ('Refactor', '♻️')
    elif any(word in combined for word in ['doc', 'docs', 'documentation', 'readme']):
        return ('Documentation', '📚')
    elif any(word in combined for word in ['test', 'testing', 'spec']):
        return ('Test', '🧪')
    elif any(word in combined for word in ['chore', 'maintain', 'deps', 'dependency', 'dependencies']):
        return ('Chore', '🧹')
    elif any(word in combined for word in ['security', 'vuln', 'vulnerability', 'cve']):
        return ('Security', '🛡️')
    elif any(word in combined for word in ['perf', 'performance', 'optimize', 'speed']):
        return ('Enhancement', '✨')
    elif any(word in combined for word in ['merge', 'pull request', 'pr']):
        return ('Merge', '🔀')

    # Check file extensions if no keyword match
    if changed_files:
        has_test = any('test' in f.lower() for f in changed_files)
        has_docs = any(f.endswith(('.md', '.rst', '.txt')) for f in changed_files)

        if has_test:
            return ('Test', '🧪')
        elif has_docs:
            return ('Documentation', '📚')

    # Default to generic task
    return ('Task', '📝')


def create_commit_task(client, list_id, commit_info, repo_name, branch_name):
    """Create a ClickUp task for a commit."""

    # Detect commit type
    task_type, emoji = detect_commit_type(
        commit_info['subject'],
        commit_info['body'],
        commit_info['changed_files']
    )

    # Build task name with emoji
    task_name = f"{emoji} [Commit {commit_info['hash']}] {commit_info['subject']}"

    # Build task description with detailed commit info
    description = f"""# Commit Details

**Type:** {emoji} {task_type}
**Commit:** `{commit_info['full_hash']}`
**Author:** {commit_info['author_name']} <{commit_info['author_email']}>
**Date:** {commit_info['date']}
**Branch:** {branch_name}
**Repository:** {repo_name}

## Message

{commit_info['subject']}

{commit_info['body']}

## Files Changed ({commit_info['changed_files_count']})

"""

    # Add changed files
    for file in commit_info['changed_files']:
        if file:
            description += f"- `{file}`\n"

    # Add stats
    if commit_info['stats']:
        description += f"\n## Statistics\n\n```\n{commit_info['stats']}\n```"

    # Create the task with custom type
    task = client.create_task(
        list_id,
        name=task_name,
        description=description,
        custom_type=task_type,
        tags=[
            {'name': 'commit'},
            {'name': 'automated'},
            {'name': task_type.lower()},
            {'name': branch_name}
        ]
    )

    return task


def main():
    """Main entry point."""
    # Configuration
    LIST_ID = "901517412318"  # Development Tasks list
    REPO_NAME = os.environ.get('GITHUB_REPOSITORY', 'clickup_framework')
    BRANCH_NAME = os.environ.get('GITHUB_REF_NAME', 'unknown')
    COMMIT_COUNT = int(os.environ.get('COMMIT_COUNT', '5'))

    print("=" * 80)
    print(f"Posting Commits to ClickUp")
    print("=" * 80)
    print(f"Repository: {REPO_NAME}")
    print(f"Branch: {BRANCH_NAME}")
    print(f"Commits to post: {COMMIT_COUNT}")
    print()

    # Initialize client
    try:
        client = ClickUpClient()
    except Exception as e:
        print(f"✗ Error initializing ClickUp client: {e}", file=sys.stderr)
        print("Make sure CLICKUP_API_TOKEN environment variable is set.", file=sys.stderr)
        return 1

    # Get recent commits
    commit_hashes = get_recent_commits(COMMIT_COUNT)

    if not commit_hashes:
        print("No commits found.")
        return 0

    print(f"Found {len(commit_hashes)} commits")
    print()

    # Post each commit
    created_tasks = []
    for commit_hash in commit_hashes:
        print(f"Processing commit: {commit_hash[:8]}")

        # Get commit info
        commit_info = get_commit_info(commit_hash)

        if not commit_info:
            print(f"  ✗ Could not get info for commit {commit_hash[:8]}")
            continue

        print(f"  Subject: {commit_info['subject']}")
        print(f"  Author: {commit_info['author_name']}")
        print(f"  Files changed: {commit_info['changed_files_count']}")

        try:
            # Create task in ClickUp
            task = create_commit_task(
                client,
                LIST_ID,
                commit_info,
                REPO_NAME,
                BRANCH_NAME
            )
            created_tasks.append(task)
            print(f"  ✓ Task created: {task['id']}")
            print(f"    URL: {task.get('url', 'N/A')}")
        except Exception as e:
            print(f"  ✗ Error creating task: {e}")

        print()

    # Summary
    print("=" * 80)
    print("SUMMARY")
    print("=" * 80)
    print(f"Commits processed: {len(commit_hashes)}")
    print(f"Tasks created: {len(created_tasks)}")
    print()

    if created_tasks:
        print("Created tasks:")
        for task in created_tasks:
            print(f"  - {task['name']}")
            print(f"    ID: {task['id']}")
            print(f"    URL: {task.get('url', 'N/A')}")
        print()

    print("=" * 80)

    return 0


if __name__ == "__main__":
    sys.exit(main())
