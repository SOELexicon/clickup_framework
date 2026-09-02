"""Install bundled Claude Code plugins (e.g. nutcracker) for cum.

Deliberately NOT a BaseCommand: BaseCommand.__init__ unconditionally
constructs a ClickUpClient, which hard-fails without ClickUp credentials
configured. Installing a plugin is a pure filesystem operation with no
ClickUp API involved, and is exactly the kind of thing someone might run
before they've set up credentials at all -- it shouldn't require them.

Mirrors clickup_framework/commands/skill_install_command.py: same
copy/backup/force semantics, same --target-dir override, same "files only
by default, opt in to wiring config" shape. A plugin's equivalent of the
skill installer's --hook is --enable, which flips it on in
enabledPlugins in settings.json -- a copied-but-unlisted plugin directory
is otherwise inert.
"""

import json
import shutil
import sys
from pathlib import Path

from clickup_framework.commands.utils import add_common_args
from clickup_framework.utils.animations import ANSIAnimations
from clickup_framework.utils.colors import TextColor, TextStyle, colorize

PLUGIN_SOURCE_ROOT = Path(__file__).resolve().parent.parent / "plugin"

# Bundled plugins available to install. Add an entry here when a new plugin
# ships in clickup_framework/plugin/.
AVAILABLE_PLUGINS = {
    "nutcracker": PLUGIN_SOURCE_ROOT,
}

COMMAND_METADATA = {
    "category": "🎨 Configuration",
    "commands": [
        {
            "name": "install-plugin",
            "args": "[plugin_name] [--enable] [--force]",
            "description": "Install a bundled Claude Code plugin (default: nutcracker)",
        },
    ],
}


def _err(message):
    print(f"Error: {message}", file=sys.stderr)
    sys.exit(1)


def _install_plugin_files(
    source_dir: Path, plugin_target: Path, target_root: Path, force: bool, use_color: bool
) -> bool:
    """Copy the bundled plugin directory into place. Returns True if files were (re)written."""
    if plugin_target.exists():
        if not force:
            print(f"Plugin files already present at {plugin_target} (use --force to reinstall).")
            return False
        # Back up OUTSIDE target_root/"plugins" for the same reason
        # skill_install_command keeps skill backups outside "skills/" --
        # avoid the backup being picked up as its own stale plugin install.
        backup_dir = target_root / "plugin-backups"
        backup_dir.mkdir(parents=True, exist_ok=True)
        backup = backup_dir / plugin_target.name
        if backup.exists():
            shutil.rmtree(backup)
        shutil.move(str(plugin_target), str(backup))
        print(f"Backed up existing install to {backup}")

    plugin_target.parent.mkdir(parents=True, exist_ok=True)
    shutil.copytree(source_dir, plugin_target)

    msg = f"Installed plugin files: {plugin_target}"
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
            "Fix or remove it, then retry with --enable."
        )


def _enable_plugin(plugin_name: str, target_root: Path, use_color: bool) -> None:
    settings_path = target_root / "settings.json"
    settings = _load_settings(settings_path)

    enabled_plugins = settings.setdefault("enabledPlugins", {})
    already_enabled = enabled_plugins.get(plugin_name) is True
    enabled_plugins[plugin_name] = True

    settings_path.parent.mkdir(parents=True, exist_ok=True)
    settings_path.write_text(json.dumps(settings, indent=2) + "\n", encoding="utf-8")

    if already_enabled:
        print(f"\n{plugin_name} was already enabled in {settings_path}.")
        return

    msg = f"Enabled {plugin_name!r} in {settings_path}"
    print(f"\n{ANSIAnimations.success_message(msg) if use_color else '[OK] ' + msg}")
    print(
        "Start a new session (or run /hooks once) to pick up the config change "
        "if this settings file wasn't already being watched."
    )


def install_plugin_command(args):
    """Command function for `cum install-plugin`."""
    use_color = bool(getattr(args, "colorize", None))

    plugin_name = args.plugin_name
    source_dir = AVAILABLE_PLUGINS.get(plugin_name)
    if source_dir is None:
        _err(
            f"Unknown bundled plugin: {plugin_name!r}. Available: "
            f"{', '.join(sorted(AVAILABLE_PLUGINS))}"
        )
    if not source_dir.is_dir():
        _err(
            f"Bundled plugin assets missing at {source_dir} -- this looks like a "
            "broken clickup_framework install (plugin/ should ship with the package)."
        )

    target_root = Path(args.target_dir).expanduser() if args.target_dir else Path.home() / ".claude"
    plugin_target = target_root / "plugins" / plugin_name

    header = (
        colorize(f"Installing {plugin_name}", TextColor.BRIGHT_CYAN, TextStyle.BOLD)
        if use_color
        else f"Installing {plugin_name}"
    )
    print(f"\n{header}")
    print(f"Target: {plugin_target}")

    _install_plugin_files(source_dir, plugin_target, target_root, args.force, use_color)

    if args.enable:
        _enable_plugin(plugin_name, target_root, use_color)
    else:
        print(
            "\nPlugin installed without being enabled. Re-run with --enable to "
            "also wire it into settings.json, or set enabledPlugins manually "
            f'(\"{plugin_name}\": true).'
        )


def register_command(subparsers):
    """Register the install-plugin command."""
    parser = subparsers.add_parser(
        "install-plugin",
        aliases=["plugin-install"],
        help="Install a bundled Claude Code plugin into ~/.claude/plugins",
        description=(
            "Copy a plugin bundled with clickup_framework (e.g. nutcracker) into "
            "the current user's Claude profile directory, and optionally enable it "
            "in settings.json."
        ),
        epilog="""Tips:
  • Plugin files only: cum install-plugin
  • Plugin + enable: cum install-plugin --enable
  • Reinstall/overwrite: cum install-plugin --enable --force
  • Install into a project instead of the user profile: cum install-plugin --target-dir ./.claude""",
    )
    parser.add_argument(
        "plugin_name",
        nargs="?",
        default="nutcracker",
        help="Bundled plugin to install (default: nutcracker)",
    )
    parser.add_argument(
        "--enable",
        action="store_true",
        help="Also enable the plugin in settings.json (enabledPlugins)",
    )
    parser.add_argument(
        "--force",
        action="store_true",
        help="Overwrite an existing install",
    )
    parser.add_argument(
        "--target-dir",
        help="Claude directory to install into (default: ~/.claude, the current user's profile)",
    )
    add_common_args(parser)
    parser.set_defaults(func=install_plugin_command)
