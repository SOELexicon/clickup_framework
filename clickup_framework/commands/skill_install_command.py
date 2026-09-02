"""Install bundled Claude Code skills (and their optional hooks) for cum.

Deliberately NOT a BaseCommand: BaseCommand.__init__ unconditionally
constructs a ClickUpClient, which hard-fails without ClickUp credentials
configured. Installing a skill is a pure filesystem operation with no
ClickUp API involved, and is exactly the kind of thing someone might run
before they've set up credentials at all -- it shouldn't require them.
"""

import json
import shutil
import sys
from pathlib import Path

from clickup_framework.commands.utils import add_common_args
from clickup_framework.utils.animations import ANSIAnimations
from clickup_framework.utils.colors import TextColor, TextStyle, colorize

SKILL_ASSETS_DIR = Path(__file__).resolve().parent.parent / "skill_assets"

# Bundled skills available to install. Add an entry here when a new skill
# ships in clickup_framework/skill_assets/.
AVAILABLE_SKILLS = {
    "cum-todo-sync": SKILL_ASSETS_DIR / "cum-todo-sync",
}

COMMAND_METADATA = {
    "category": "🎨 Configuration",
    "commands": [
        {
            "name": "install-skill",
            "args": "[skill_name] [--hook] [--force]",
            "description": "Install a bundled Claude Code skill (default: cum-todo-sync)",
        },
    ],
}


def _err(message):
    print(f"Error: {message}", file=sys.stderr)
    sys.exit(1)


def _check_cum_dependency() -> None:
    """Warn (don't block) if `cum` isn't resolvable on PATH.

    The hook depends on `cum` being callable; installing it anyway is fine
    (someone might install cum right after, or the PATH is fixed later), but
    silently leaving the hook non-functional with no explanation is not --
    install time is exactly when the user is paying attention.
    """
    if shutil.which("cum") is None:
        print(
            "Warning: 'cum' was not found on PATH. The hook will install fine "
            "but will do nothing (prints '{}') until 'cum' is installed and "
            "resolvable -- see 'pip install -e .' / the project README."
        )


def _install_skill_files(
    source_dir: Path, skill_target: Path, force: bool, use_color: bool
) -> bool:
    """Copy the bundled skill directory into place. Returns True if files were (re)written."""
    if skill_target.exists():
        if not force:
            print(f"Skill files already present at {skill_target} (use --force to reinstall).")
            return False
        backup = skill_target.with_name(skill_target.name + ".bak")
        if backup.exists():
            shutil.rmtree(backup)
        shutil.move(str(skill_target), str(backup))
        print(f"Backed up existing install to {backup}")

    skill_target.parent.mkdir(parents=True, exist_ok=True)
    shutil.copytree(source_dir, skill_target)

    msg = f"Installed skill files: {skill_target}"
    print(f"\n{ANSIAnimations.success_message(msg) if use_color else '[OK] ' + msg}")
    return True


def _load_settings(settings_path: Path) -> dict:
    if not settings_path.exists():
        return {}
    try:
        return json.loads(settings_path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as e:
        _err(
            f"Could not parse existing {settings_path}: {e}. "
            "Fix or remove it, then retry with --hook."
        )


def _install_hook(skill_target: Path, target_root: Path, force: bool, use_color: bool) -> None:
    hook_script = skill_target / "hooks" / "session_start.py"
    if not hook_script.exists():
        _err(
            f"Hook script not found at {hook_script} -- skill files may not "
            "have installed correctly. Re-run without --hook first to check."
        )

    settings_path = target_root / "settings.json"
    settings = _load_settings(settings_path)

    hooks = settings.setdefault("hooks", {})
    session_start = hooks.setdefault("SessionStart", [])

    command = f'python "{hook_script}"'
    already_present = any(
        h.get("type") == "command" and h.get("command") == command
        for entry in session_start
        for h in entry.get("hooks", [])
    )

    if already_present and not force:
        print("SessionStart hook already wired up (use --force to add a duplicate entry).")
        return

    session_start.append(
        {
            "hooks": [
                {
                    "type": "command",
                    "command": command,
                    "timeout": 35,
                    "statusMessage": "Checking ClickUp assigned tasks (cum-todo-sync)...",
                }
            ]
        }
    )

    settings_path.parent.mkdir(parents=True, exist_ok=True)
    settings_path.write_text(json.dumps(settings, indent=2) + "\n", encoding="utf-8")

    msg = f"Wired SessionStart hook into {settings_path}"
    print(f"\n{ANSIAnimations.success_message(msg) if use_color else '[OK] ' + msg}")
    print(
        "Open /hooks once (or start a new session) to pick up the config change "
        "if this settings file wasn't already being watched."
    )


def install_skill_command(args):
    """Command function for `cum install-skill`."""
    use_color = bool(getattr(args, "colorize", None))

    skill_name = args.skill_name
    source_dir = AVAILABLE_SKILLS.get(skill_name)
    if source_dir is None:
        _err(
            f"Unknown bundled skill: {skill_name!r}. Available: "
            f"{', '.join(sorted(AVAILABLE_SKILLS))}"
        )
    if not source_dir.is_dir():
        _err(
            f"Bundled skill assets missing at {source_dir} -- this looks like a "
            "broken clickup_framework install (skill_assets/ should ship with the package)."
        )

    target_root = Path(args.target_dir).expanduser() if args.target_dir else Path.home() / ".claude"
    skill_target = target_root / "skills" / skill_name

    header = (
        colorize(f"Installing {skill_name}", TextColor.BRIGHT_CYAN, TextStyle.BOLD)
        if use_color
        else f"Installing {skill_name}"
    )
    print(f"\n{header}")
    print(f"Target: {skill_target}")

    _install_skill_files(source_dir, skill_target, args.force, use_color)

    if args.hook:
        _check_cum_dependency()
        _install_hook(skill_target, target_root, args.force, use_color)
        print(
            "\nSet CUM_TODO_SYNC_DISABLED=1 in your environment to turn the hook off "
            "again later without removing it from settings.json."
        )
    else:
        print(
            "\nSkill installed without the SessionStart hook. Re-run with --hook "
            "to also wire it up, or see the skill's own doc for a manual install."
        )


def register_command(subparsers):
    """Register the install-skill command."""
    parser = subparsers.add_parser(
        "install-skill",
        aliases=["skill-install"],
        help="Install a bundled Claude Code skill into ~/.claude",
        description=(
            "Copy a skill bundled with clickup_framework (e.g. cum-todo-sync) into "
            "the current user's Claude profile directory, and optionally wire up "
            "its SessionStart hook."
        ),
        epilog="""Tips:
  • Skill files only: cum install-skill
  • Skill + hook: cum install-skill --hook
  • Reinstall/overwrite: cum install-skill --hook --force
  • Install into a project instead of the user profile: cum install-skill --target-dir ./.claude""",
    )
    parser.add_argument(
        "skill_name",
        nargs="?",
        default="cum-todo-sync",
        help="Bundled skill to install (default: cum-todo-sync)",
    )
    parser.add_argument(
        "--hook",
        action="store_true",
        help="Also wire the skill's SessionStart hook into settings.json",
    )
    parser.add_argument(
        "--force",
        action="store_true",
        help="Overwrite an existing install / add a duplicate hook entry",
    )
    parser.add_argument(
        "--target-dir",
        help="Claude directory to install into (default: ~/.claude, the current user's profile)",
    )
    add_common_args(parser)
    parser.set_defaults(func=install_skill_command)
