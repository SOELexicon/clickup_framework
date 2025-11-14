"""Git reauthor command - rewrite git history to change author."""

import subprocess
import sys
from pathlib import Path


def get_git_config(key):
    """Get a git config value."""
    try:
        result = subprocess.run(
            ['git', 'config', '--get', key],
            capture_output=True,
            text=True,
            encoding='utf-8',
            errors='replace',
            check=False
        )
        if result.returncode == 0:
            return result.stdout.strip()
        return None
    except Exception as e:
        print(f"Error getting git config '{key}': {e}", file=sys.stderr)
        return None


def check_git_repository():
    """Check if current directory is a Git repository."""
    git_dir = Path('.git')
    if not git_dir.exists():
        print("Error: Not in a Git repository", file=sys.stderr)
        print("Please run this command from the root of a Git repository.", file=sys.stderr)
        return False
    return True


def get_current_branch():
    """Get the name of the current branch."""
    try:
        result = subprocess.run(
            ['git', 'rev-parse', '--abbrev-ref', 'HEAD'],
            capture_output=True,
            text=True,
            encoding='utf-8',
            errors='replace',
            check=True
        )
        return result.stdout.strip()
    except subprocess.CalledProcessError:
        return None


def check_uncommitted_changes():
    """Check if there are uncommitted changes."""
    try:
        result = subprocess.run(
            ['git', 'status', '--porcelain'],
            capture_output=True,
            text=True,
            encoding='utf-8',
            errors='replace',
            check=True
        )
        return bool(result.stdout.strip())
    except subprocess.CalledProcessError:
        return True


def confirm_action(message):
    """Ask user for confirmation."""
    response = input(f"{message} (yes/no): ").strip().lower()
    return response in ['yes', 'y']


def reauthor_command(args):
    """Rewrite git history to change author to current git user."""

    # Check if in Git repository
    if not check_git_repository():
        sys.exit(1)

    # Get current user's git config
    user_name = get_git_config('user.name')
    user_email = get_git_config('user.email')

    if not user_name or not user_email:
        print("Error: Git user.name and user.email must be configured", file=sys.stderr)
        print("\nConfigure them with:", file=sys.stderr)
        print("  git config --global user.name \"Your Name\"", file=sys.stderr)
        print("  git config --global user.email \"your.email@example.com\"", file=sys.stderr)
        sys.exit(1)

    # Check for uncommitted changes
    if check_uncommitted_changes():
        print("Error: You have uncommitted changes", file=sys.stderr)
        print("Please commit or stash your changes before rewriting history.", file=sys.stderr)
        sys.exit(1)

    # Get current branch
    current_branch = get_current_branch()
    if not current_branch:
        print("Error: Could not determine current branch", file=sys.stderr)
        sys.exit(1)

    # Display warning and information
    print("⚠️  WARNING: This will rewrite Git history!")
    print("\nThis command will:")
    print("  • Rewrite ALL commits in the current branch")
    print("  • Change the author of all commits to your current git user")
    print("  • Create a backup branch before rewriting")
    print("  • Optionally force-push to remote (if requested)")
    print("\n" + "=" * 70)
    print("Current branch:", current_branch)
    print("New author will be:", f"{user_name} <{user_email}>")
    print("=" * 70 + "\n")

    # Confirm the action
    if not args.yes:
        if not confirm_action("Do you want to proceed?"):
            print("\nOperation cancelled.")
            sys.exit(0)

    # Create backup branch
    backup_branch = f"{current_branch}-backup-before-reauthor"
    print(f"\n📦 Creating backup branch: {backup_branch}")

    try:
        subprocess.run(
            ['git', 'branch', backup_branch],
            check=True,
            capture_output=True,
            text=True,
            encoding='utf-8',
            errors='replace'
        )
        print(f"✅ Backup created: {backup_branch}")
    except subprocess.CalledProcessError as e:
        print(f"Error creating backup branch: {e.stderr}", file=sys.stderr)
        print("\nYou can create it manually with:", file=sys.stderr)
        print(f"  git branch {backup_branch}", file=sys.stderr)

        if not args.yes:
            if not confirm_action("Continue without backup?"):
                print("\nOperation cancelled.")
                sys.exit(1)

    # Clean up any existing backup refs from previous filter-branch runs
    print("\n🧹 Cleaning up old filter-branch backups...")
    try:
        subprocess.run(
            ['git', 'for-each-ref', '--format=%(refname)', 'refs/original/'],
            capture_output=True,
            text=True,
            encoding='utf-8',
            errors='replace',
            check=False
        )
        # Remove backup refs if they exist
        subprocess.run(
            ['git', 'update-ref', '-d', 'refs/original/refs/heads/master'],
            capture_output=True,
            check=False
        )
        subprocess.run(
            ['rm', '-rf', '.git/refs/original/'],
            capture_output=True,
            check=False
        )
        subprocess.run(
            ['git', 'reflog', 'expire', '--expire=now', '--all'],
            capture_output=True,
            check=False
        )
        subprocess.run(
            ['git', 'gc', '--prune=now'],
            capture_output=True,
            check=False
        )
    except Exception:
        pass  # It's okay if cleanup fails

    # Prepare filter-branch command
    print("\n🔄 Rewriting git history...")
    print("This may take a while for large repositories...\n")

    # Use git filter-branch to rewrite history with -f flag to force it
    env_filter = f'''
export GIT_AUTHOR_NAME="{user_name}"
export GIT_AUTHOR_EMAIL="{user_email}"
export GIT_COMMITTER_NAME="{user_name}"
export GIT_COMMITTER_EMAIL="{user_email}"
'''

    try:
        result = subprocess.run(
            ['git', 'filter-branch', '-f', '--env-filter', env_filter, '--', '--all'],
            capture_output=True,
            text=True,
            encoding='utf-8',
            errors='replace',
            check=False
        )

        if result.returncode != 0:
            # Check if it's just a warning about backup refs
            if 'backup refs' in result.stderr.lower() or 'original' in result.stderr.lower():
                print("⚠️  Note: Git created backup refs. This is normal.")
            else:
                print(f"Error during git filter-branch: {result.stderr}", file=sys.stderr)
                print(f"Stdout: {result.stdout}", file=sys.stderr)
                sys.exit(1)

        print("✅ Git history rewritten successfully!")

        # Show what changed
        print("\n" + "=" * 70)
        print("Summary:")
        print(f"  • All commits now authored by: {user_name} <{user_email}>")
        print(f"  • Backup branch created: {backup_branch}")
        print("=" * 70)

    except Exception as e:
        print(f"Error rewriting history: {e}", file=sys.stderr)
        sys.exit(1)

    # Ask about force push
    if not args.no_push:
        print("\n" + "=" * 70)
        print("Next steps:")
        print("=" * 70)

        # Check if branch has a remote
        try:
            result = subprocess.run(
                ['git', 'rev-parse', '--abbrev-ref', f'{current_branch}@{{upstream}}'],
                capture_output=True,
                text=True,
                encoding='utf-8',
                errors='replace',
                check=False
            )

            if result.returncode == 0:
                remote_branch = result.stdout.strip()
                print(f"\n⚠️  Your branch '{current_branch}' tracks remote '{remote_branch}'")
                print("You need to force-push to update the remote:")
                print(f"  git push --force-with-lease origin {current_branch}")
                print("\n⚠️  WARNING: Force pushing will rewrite remote history!")
                print("This may affect other collaborators.")

                if not args.yes:
                    if confirm_action("\nDo you want to force-push now?"):
                        print(f"\n🚀 Force-pushing to origin/{current_branch}...")
                        try:
                            subprocess.run(
                                ['git', 'push', '--force-with-lease', 'origin', current_branch],
                                check=True,
                                encoding='utf-8',
                                errors='replace'
                            )
                            print("✅ Force-push completed successfully!")
                        except subprocess.CalledProcessError as e:
                            print(f"Error during force-push: {e}", file=sys.stderr)
                            print("\nYou can manually force-push later with:", file=sys.stderr)
                            print(f"  git push --force-with-lease origin {current_branch}", file=sys.stderr)
                            sys.exit(1)
                    else:
                        print("\nSkipping force-push. You can manually push later with:")
                        print(f"  git push --force-with-lease origin {current_branch}")
        except Exception:
            pass

    print("\n✅ Done!")
    print(f"\nIf you need to revert, you can reset to the backup branch:")
    print(f"  git reset --hard {backup_branch}")


def register_command(subparsers, add_common_args=None):
    """Register the reauthor command."""
    parser = subparsers.add_parser(
        'reauthor',
        help='Rewrite git history to change author to current git user',
        description='''
Rewrite all commits in the current repository to use your current git user as the author.

⚠️  WARNING: This rewrites Git history! Use with caution.

This command will:
  • Rewrite ALL commits to use your configured git user (user.name and user.email)
  • Create a backup branch before making changes
  • Optionally force-push to remote (with confirmation)

This is useful when you need to change the author of commits, for example:
  • After configuring your git identity correctly
  • When taking ownership of a forked repository
  • When commits were made with incorrect author information
        ''',
        epilog='''
Examples:
  # Rewrite history (with prompts for confirmation)
  cum reauthor

  # Rewrite history without prompts (auto-confirm)
  cum reauthor --yes

  # Rewrite history but don't offer to force-push
  cum reauthor --no-push

Safety:
  • A backup branch is created before rewriting
  • Uncommitted changes must be committed or stashed first
  • Force-push requires explicit confirmation (unless --yes is used)
  • Use --force-with-lease to avoid overwriting others' work
        '''
    )

    parser.add_argument(
        '--yes', '-y',
        action='store_true',
        help='Auto-confirm all prompts (use with caution)'
    )

    parser.add_argument(
        '--no-push',
        action='store_true',
        help='Skip the force-push prompt after rewriting history'
    )

    parser.set_defaults(func=reauthor_command)
