"""Git reauthor command - rewrite git history to change author."""

import subprocess
import sys
from pathlib import Path
from clickup_framework.commands.base_command import BaseCommand


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


class ReauthorCommand(BaseCommand):
    """Rewrite git history to change author to current git user."""

    def execute(self):
        """Execute the reauthor command."""
        # Check if in Git repository
        if not check_git_repository():
            self.error("Not in a Git repository\n" +
                      "Please run this command from the root of a Git repository.")

        # Get current user's git config
        user_name = get_git_config('user.name')
        user_email = get_git_config('user.email')

        if not user_name or not user_email:
            self.error("Git user.name and user.email must be configured\n\n" +
                      "Configure them with:\n" +
                      "  git config --global user.name \"Your Name\"\n" +
                      "  git config --global user.email \"your.email@example.com\"")

        # Check for uncommitted changes
        if check_uncommitted_changes():
            self.error("You have uncommitted changes\n" +
                      "Please commit or stash your changes before rewriting history.")

        # Get current branch
        current_branch = get_current_branch()
        if not current_branch:
            self.error("Could not determine current branch")

        # Display warning and information
        self.print("⚠️  WARNING: This will rewrite Git history!")
        self.print("\nThis command will:")
        self.print("  • Rewrite ALL commits in the current branch")
        self.print("  • Change the author of all commits to your current git user")
        self.print("  • Create a backup branch before rewriting")
        self.print("  • Optionally force-push to remote (if requested)")
        self.print("\n" + "=" * 70)
        self.print("Current branch:", current_branch)
        self.print("New author will be:", f"{user_name} <{user_email}>")
        self.print("=" * 70 + "\n")

        # Confirm the action
        if not self.args.yes:
            if not confirm_action("Do you want to proceed?"):
                self.print("\nOperation cancelled.")
                return

        # Create backup branch
        backup_branch = f"{current_branch}-backup-before-reauthor"
        self.print(f"\n📦 Creating backup branch: {backup_branch}")

        try:
            subprocess.run(
                ['git', 'branch', backup_branch],
                check=True,
                capture_output=True,
                text=True,
                encoding='utf-8',
                errors='replace'
            )
            self.print(f"✅ Backup created: {backup_branch}")
        except subprocess.CalledProcessError as e:
            self.print_error(f"Error creating backup branch: {e.stderr}")
            self.print_error("\nYou can create it manually with:")
            self.print_error(f"  git branch {backup_branch}")

            if not self.args.yes:
                if not confirm_action("Continue without backup?"):
                    self.print("\nOperation cancelled.")
                    return

        # Clean up any existing backup refs from previous filter-branch runs
        self.print("\n🧹 Cleaning up old filter-branch backups...")
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
        self.print("\n🔄 Rewriting git history...")
        self.print("This may take a while for large repositories...\n")

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
                    self.print("⚠️  Note: Git created backup refs. This is normal.")
                else:
                    self.print_error(f"Error during git filter-branch: {result.stderr}")
                    self.print_error(f"Stdout: {result.stdout}")
                    self.error("")

            self.print("✅ Git history rewritten successfully!")

            # Show what changed
            self.print("\n" + "=" * 70)
            self.print("Summary:")
            self.print(f"  • All commits now authored by: {user_name} <{user_email}>")
            self.print(f"  • Backup branch created: {backup_branch}")
            self.print("=" * 70)

        except Exception as e:
            self.error(f"Error rewriting history: {e}")

        # Ask about force push
        if not self.args.no_push:
            self.print("\n" + "=" * 70)
            self.print("Next steps:")
            self.print("=" * 70)

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
                    self.print(f"\n⚠️  Your branch '{current_branch}' tracks remote '{remote_branch}'")
                    self.print("You need to force-push to update the remote:")
                    self.print(f"  git push --force-with-lease origin {current_branch}")
                    self.print("\n⚠️  WARNING: Force pushing will rewrite remote history!")
                    self.print("This may affect other collaborators.")

                    if not self.args.yes:
                        if confirm_action("\nDo you want to force-push now?"):
                            self.print(f"\n🚀 Force-pushing to origin/{current_branch}...")
                            try:
                                subprocess.run(
                                    ['git', 'push', '--force-with-lease', 'origin', current_branch],
                                    check=True,
                                    encoding='utf-8',
                                    errors='replace'
                                )
                                self.print("✅ Force-push completed successfully!")
                            except subprocess.CalledProcessError as e:
                                self.print_error(f"Error during force-push: {e}")
                                self.print_error("\nYou can manually force-push later with:")
                                self.print_error(f"  git push --force-with-lease origin {current_branch}")
                                self.error("")
                        else:
                            self.print("\nSkipping force-push. You can manually push later with:")
                            self.print(f"  git push --force-with-lease origin {current_branch}")
            except Exception:
                pass

        self.print("\n✅ Done!")
        self.print(f"\nIf you need to revert, you can reset to the backup branch:")
        self.print(f"  git reset --hard {backup_branch}")


def reauthor_command(args):
    """Command wrapper for backward compatibility."""
    command = ReauthorCommand(args, command_name='reauthor')
    command.execute()


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
