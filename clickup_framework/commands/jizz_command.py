"""Jizz Command - Humorous auto-deploy workflow."""

import sys
import time
import subprocess
import re
import platform
from pathlib import Path
from typing import Optional, Tuple

from clickup_framework import get_context_manager
from clickup_framework.utils.colors import colorize, TextColor, TextStyle
from clickup_framework.utils.animations import ANSIAnimations

# Ensure UTF-8 encoding and enable VT100 mode for Windows
if platform.system() == 'Windows':
    try:
        # Try to reconfigure stdout/stderr to use UTF-8
        if hasattr(sys.stdout, 'reconfigure'):
            sys.stdout.reconfigure(encoding='utf-8')
        if hasattr(sys.stderr, 'reconfigure'):
            sys.stderr.reconfigure(encoding='utf-8')
        
        # VT100 mode is enabled by colors module on import
    except Exception:
        pass  # If reconfigure fails, continue anyway


def parse_version(version_str: str) -> Tuple[int, int, int]:
    """Parse a version string into components."""
    # Remove 'v' prefix if present
    version_str = version_str.lstrip('v')

    # Extract major.minor.patch
    match = re.match(r'^(\d+)\.(\d+)\.(\d+)', version_str)
    if not match:
        raise ValueError(f"Invalid version format: {version_str}")

    major, minor, patch = match.groups()
    return int(major), int(minor), int(patch)


def increment_version_by_point_one(version_str: str) -> str:
    """Increment version by 0.0.1 with proper rollover (e.g., 2.2.5 -> 2.2.6, 2.2.9 -> 2.3.0, 1.9.9 -> 2.0.0)."""
    major, minor, patch = parse_version(version_str)

    # Increment patch by 1
    patch += 1

    # If patch reaches 10, rollover to minor
    if patch >= 10:
        patch = 0
        minor += 1

    # If minor reaches 10, rollover to major
    if minor >= 10:
        minor = 0
        major += 1

    return f"{major}.{minor}.{patch}"


def get_latest_tag() -> Optional[str]:
    """Get the latest version tag from git."""
    result = subprocess.run(
        ['git', 'tag', '-l', '--sort=-v:refname'],
        capture_output=True,
        text=True
    )

    if result.returncode != 0 or not result.stdout.strip():
        return None

    # Get the first tag (most recent)
    tags = result.stdout.strip().split('\n')
    for tag in tags:
        # Match semantic versioning pattern
        if re.match(r'^v?\d+\.\d+\.\d+', tag):
            return tag.lstrip('v')

    return None


def run_command(cmd: list, description: str, use_color: bool = True) -> bool:
    """Run a command and return success status."""
    result = subprocess.run(cmd, capture_output=True, text=True)

    if result.returncode == 0:
        if result.stdout:
            print(result.stdout.strip())
        return True
    else:
        if use_color:
            print(ANSIAnimations.error_message(f"{description} failed!"))
        else:
            print(f"✗ {description} failed!")
        if result.stderr:
            print(result.stderr.strip(), file=sys.stderr)
        return False


def show_progress_bar(message: str, duration: float = 1.0, use_color: bool = True):
    """Display an animated progress bar."""
    if not use_color:
        print(f"⏳ {message}...")
        time.sleep(duration)
        return

    bar_length = 40
    colored_msg = ANSIAnimations.white_sheen_text(message, TextColor.BRIGHT_MAGENTA)

    for i in range(bar_length + 1):
        # Calculate percentage
        percent = int((i / bar_length) * 100)

        # Create bar with gradient effect
        filled = '█' * i
        empty = '░' * (bar_length - i)

        # Color the filled portion
        if percent < 33:
            color = TextColor.BRIGHT_CYAN
        elif percent < 66:
            color = TextColor.BRIGHT_MAGENTA
        else:
            color = TextColor.BRIGHT_YELLOW

        colored_filled = colorize(filled, color)
        bar = f"{colored_filled}{empty}"

        # Print progress bar
        print(f"\r{colored_msg} [{bar}] {percent}%", end='', flush=True)

        # Sleep to create animation
        time.sleep(duration / bar_length)

    print()  # New line after completion


def jizz_command(args):
    """
    Execute the jizz workflow: stash → pull → tag → push → update.

    This command performs a humorous auto-deploy workflow with animated output.
    """
    context = get_context_manager()
    use_color = context.get_ansi_output()
    dry_run = args.dry_run

    # Check if in Git repository
    git_dir = Path('.git')
    if not git_dir.exists():
        if use_color:
            print(ANSIAnimations.error_message("Not in a Git repository! No cum zone detected."))
        else:
            print("✗ Error: Not in a Git repository", file=sys.stderr)
        sys.exit(1)

    # Display intro
    print()
    if use_color:
        # Animated rainbow header
        ANSIAnimations.display_animated_rainbow("💦 CUM JIZZ WORKFLOW 💦", duration=1.5, speed=3.0)
        print()

        # Dry run warning
        if dry_run:
            dry_run_msg = colorize("🧪 DRY RUN MODE - No actual changes will be made",
                                  TextColor.BRIGHT_YELLOW, TextStyle.BOLD)
            print(dry_run_msg)
            print()

        # Fun intro message with white sheen
        intro_lines = [
            ANSIAnimations.white_sheen_text("🍆 Preparing to release...", TextColor.BRIGHT_MAGENTA),
            ANSIAnimations.white_sheen_text("💦 Auto-deploy workflow initiated", TextColor.BRIGHT_CYAN),
            ANSIAnimations.white_sheen_text("🎯 Target: Maximum velocity deployment", TextColor.BRIGHT_YELLOW)
        ]

        box = ANSIAnimations.animated_box(
            ANSIAnimations.white_sheen_text("DEPLOYMENT SEQUENCE", TextColor.BRIGHT_MAGENTA),
            intro_lines,
            TextColor.BRIGHT_MAGENTA
        )
        print(box)
        print()
    else:
        print("=== CUM JIZZ WORKFLOW ===")
        if dry_run:
            print("🧪 DRY RUN MODE - No actual changes will be made")
        print("Preparing to release...")
        print()

    steps_completed = 0
    total_steps = 5

    # Step 1: Stash
    steps_completed += 1
    if use_color:
        step_msg = ANSIAnimations.white_sheen_text(f"[{steps_completed}/{total_steps}]", TextColor.BRIGHT_CYAN)
        step_text = ANSIAnimations.white_sheen_text("🍆 Building pressure (stashing changes)...", TextColor.BRIGHT_MAGENTA)
        print(f"{step_msg} {step_text}")
    else:
        print(f"[{steps_completed}/{total_steps}] Stashing changes...")

    show_progress_bar("Storing the goods", 0.8, use_color)

    if dry_run:
        if use_color:
            print(colorize("  [DRY RUN] Would execute: git stash", TextColor.BRIGHT_BLUE))
        else:
            print("  [DRY RUN] Would execute: git stash")
    else:
        result = subprocess.run(['git', 'stash'], capture_output=True, text=True)
        if result.returncode == 0:
            if use_color:
                print(ANSIAnimations.success_message("Stash complete! All tucked away safely."))
            else:
                print("✓ Stash complete!")
        else:
            # Stash might fail if there's nothing to stash - that's okay
            if "No local changes" in result.stdout or not result.stderr:
                if use_color:
                    print(colorize("  ℹ️  Nothing to stash (already clean)", TextColor.BRIGHT_BLUE))
                else:
                    print("  ℹ️  Nothing to stash")
            else:
                print(result.stderr.strip(), file=sys.stderr)

    print()

    # Step 2: Pull
    steps_completed += 1
    if use_color:
        step_msg = ANSIAnimations.white_sheen_text(f"[{steps_completed}/{total_steps}]", TextColor.BRIGHT_CYAN)
        step_text = ANSIAnimations.white_sheen_text("💪 Getting fresh (pulling latest)...", TextColor.BRIGHT_MAGENTA)
        print(f"{step_msg} {step_text}")
    else:
        print(f"[{steps_completed}/{total_steps}] Pulling latest...")

    show_progress_bar("Extracting the latest release", 1.0, use_color)

    if dry_run:
        if use_color:
            print(colorize("  [DRY RUN] Would execute: git pull --rebase", TextColor.BRIGHT_BLUE))
        else:
            print("  [DRY RUN] Would execute: git pull --rebase")
    else:
        if not run_command(['git', 'pull', '--rebase'], "Pull", use_color):
            sys.exit(1)

        if use_color:
            print(ANSIAnimations.success_message("Pull complete! Fresh and ready."))
        else:
            print("✓ Pull complete!")

    print()

    # Step 3: Update tag (increment version)
    steps_completed += 1
    if use_color:
        step_msg = ANSIAnimations.white_sheen_text(f"[{steps_completed}/{total_steps}]", TextColor.BRIGHT_CYAN)
        step_text = ANSIAnimations.white_sheen_text("📈 Pumping up the version...", TextColor.BRIGHT_MAGENTA)
        print(f"{step_msg} {step_text}")
    else:
        print(f"[{steps_completed}/{total_steps}] Updating version tag...")

    # Get current version
    current_version = get_latest_tag()
    if not current_version:
        if use_color:
            print(ANSIAnimations.error_message("No existing version tag found! Need a base to pump from."))
        else:
            print("✗ Error: No existing version tag found!", file=sys.stderr)
        sys.exit(1)

    # Increment version
    try:
        new_version = increment_version_by_point_one(current_version)
    except ValueError as e:
        if use_color:
            print(ANSIAnimations.error_message(f"Version parse error: {e}"))
        else:
            print(f"✗ Error: {e}", file=sys.stderr)
        sys.exit(1)

    if use_color:
        old_v = colorize(f"v{current_version}", TextColor.BRIGHT_RED, TextStyle.DIM)
        arrow = colorize("➜", TextColor.BRIGHT_YELLOW, TextStyle.BOLD)
        new_v = colorize(f"v{new_version}", TextColor.BRIGHT_GREEN, TextStyle.BOLD)
        print(f"  💦 Version trajectory: {old_v} {arrow} {new_v}")
    else:
        print(f"  Version: v{current_version} → v{new_version}")

    show_progress_bar("Inflating version number", 0.8, use_color)

    # Create the tag
    tag_name = f"v{new_version}"

    if dry_run:
        if use_color:
            print(colorize(f"  [DRY RUN] Would execute: git tag -a {tag_name} -m 'Release {new_version} 💦'",
                          TextColor.BRIGHT_BLUE))
        else:
            print(f"  [DRY RUN] Would execute: git tag -a {tag_name} -m 'Release {new_version} 💦'")
    else:
        result = subprocess.run(
            ['git', 'tag', '-a', tag_name, '-m', f'Release {new_version} 💦'],
            capture_output=True,
            text=True
        )

        if result.returncode != 0:
            if use_color:
                print(ANSIAnimations.error_message(f"Failed to create tag: {result.stderr}"))
            else:
                print(f"✗ Error creating tag: {result.stderr}", file=sys.stderr)
            sys.exit(1)

        if use_color:
            print(ANSIAnimations.success_message(f"Tag {tag_name} created! Ready to blow."))
        else:
            print(f"✓ Tag {tag_name} created!")

    print()

    # Step 4: Push tag
    steps_completed += 1
    if use_color:
        step_msg = ANSIAnimations.white_sheen_text(f"[{steps_completed}/{total_steps}]", TextColor.BRIGHT_CYAN)
        step_text = ANSIAnimations.white_sheen_text(f"🚀 Releasing the payload (pushing {tag_name})...", TextColor.BRIGHT_MAGENTA)
        print(f"{step_msg} {step_text}")
    else:
        print(f"[{steps_completed}/{total_steps}] Pushing {tag_name}...")

    show_progress_bar("Ejecting to origin", 1.2, use_color)

    if dry_run:
        if use_color:
            print(colorize(f"  [DRY RUN] Would execute: git push origin {tag_name}",
                          TextColor.BRIGHT_BLUE))
        else:
            print(f"  [DRY RUN] Would execute: git push origin {tag_name}")
    else:
        if not run_command(['git', 'push', 'origin', tag_name], f"Push {tag_name}", use_color):
            sys.exit(1)

        if use_color:
            print(ANSIAnimations.success_message(f"Tag {tag_name} pushed! Money shot delivered! 💦"))
        else:
            print(f"✓ Tag {tag_name} pushed!")

    print()

    # Step 5: Update cum
    steps_completed += 1
    if use_color:
        step_msg = ANSIAnimations.white_sheen_text(f"[{steps_completed}/{total_steps}]", TextColor.BRIGHT_CYAN)
        step_text = ANSIAnimations.white_sheen_text("🔄 Refreshing the tool (cum update cum)...", TextColor.BRIGHT_MAGENTA)
        print(f"{step_msg} {step_text}")
    else:
        print(f"[{steps_completed}/{total_steps}] Updating cum tool...")

    show_progress_bar("Reloading for round two", 1.5, use_color)

    if dry_run:
        if use_color:
            print(colorize("  [DRY RUN] Would execute: cum update cum", TextColor.BRIGHT_BLUE))
        else:
            print("  [DRY RUN] Would execute: cum update cum")
    else:
        # Run cum update cum without capturing output so progress bars are shown
        print()
        result = subprocess.run(['cum', 'update', 'cum'])

        if result.returncode == 0:
            print()
            if use_color:
                print(ANSIAnimations.success_message("Cum tool updated! Back at full capacity."))
            else:
                print("✓ Cum tool updated!")
        else:
            print()
            if use_color:
                print(ANSIAnimations.warning_message("Cum update had issues (might be okay)"))
            else:
                print("⚠ Cum update had issues")

    print()

    # Final success message
    if use_color:
        # Epic finale
        print()
        finale_lines = [
            f"✨ Released version: {colorize(tag_name, TextColor.BRIGHT_GREEN, TextStyle.BOLD)}",
            f"🎯 Deployment: {colorize('SUCCESSFUL', TextColor.BRIGHT_GREEN, TextStyle.BOLD)}",
            f"💦 Status: {colorize('Fully emptied and satisfied', TextColor.BRIGHT_MAGENTA)}",
            "",
            colorize("Ready for the next release cycle! 🍆", TextColor.BRIGHT_YELLOW)
        ]

        for line in finale_lines:
            print(line)

        print()

        # Animated rainbow celebration
        ANSIAnimations.display_animated_rainbow(
            "🎉 JIZZ WORKFLOW COMPLETE! CLEANUP IN AISLE EVERYWHERE! 🎉",
            duration=2.0,
            speed=3.0
        )
        print()
    else:
        print("=" * 50)
        print(f"✓ JIZZ WORKFLOW COMPLETE!")
        print(f"  Released: {tag_name}")
        print(f"  Status: SUCCESS")
        print("=" * 50)

    sys.exit(0)


def register_command(subparsers):
    """Register the jizz command."""
    parser = subparsers.add_parser(
        'jizz',
        help='💦 Humorous auto-deploy workflow (stash → pull → tag → push → update)',
        description='''Execute the jizz workflow: automatic deployment with style.

This command performs the following steps:
  1. 💦 Stash any uncommitted changes
  2. 💪 Pull latest changes with rebase
  3. 📈 Increment version tag by 0.0.1 (e.g., 2.2.9 → 2.3.0)
  4. 🚀 Push the new version tag to origin
  5. 🔄 Update the cum tool itself

All with humorous output, animations, and progress bars!
        ''',
        epilog='''Examples:
  cum jizz                # Execute the full workflow
  cum jizz --dry-run      # Show what would be done without making changes
  cum jizz --no-ansi      # Run without fancy animations
  cum jizz --dry-run --no-ansi  # Dry run without animations

Note: This is a humorous command for a humorous CLI tool.
      It performs real git operations, so use responsibly!
        '''
    )

    # Optional flags
    parser.add_argument(
        '--no-ansi',
        action='store_true',
        help='Disable ANSI colors and animations'
    )

    parser.add_argument(
        '-dry', '--dry-run',
        action='store_true',
        help='Show what would be done without making any changes'
    )

    parser.set_defaults(func=jizz_command)
