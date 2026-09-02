"""
Tests for the nutcracker plugin (clickup_framework/plugin/).

Structural tests for the manifest, hooks config, and skill frontmatter,
a behavioral test for the SessionStart hook script, and a correctness
test that every `cum` command documented in the skills actually exists in
the installed CLI (the "ensure correct usage" guarantee, enforced
mechanically rather than by review).
"""

import json
import re
import shutil
import subprocess
import unittest
from pathlib import Path

PLUGIN_ROOT = Path(__file__).resolve().parent.parent / "clickup_framework" / "plugin"
SKILL_NAMES = ["using-cum-planning", "writing-cum-plans", "executing-cum-plans"]


class TestPluginManifest(unittest.TestCase):
    def setUp(self):
        self.manifest_path = PLUGIN_ROOT / ".claude-plugin" / "plugin.json"

    def test_manifest_exists_and_is_valid_json(self):
        self.assertTrue(self.manifest_path.exists(), f"missing {self.manifest_path}")
        json.loads(self.manifest_path.read_text(encoding="utf-8"))

    def test_manifest_required_fields(self):
        manifest = json.loads(self.manifest_path.read_text(encoding="utf-8"))
        self.assertEqual(manifest["name"], "nutcracker")
        self.assertEqual(manifest["version"], "0.1.0")
        self.assertTrue(manifest["description"])
        self.assertEqual(manifest["author"]["name"], "ClickUp Skills Development Team")


class TestHooksConfig(unittest.TestCase):
    def setUp(self):
        self.hooks_path = PLUGIN_ROOT / "hooks" / "hooks.json"

    def test_hooks_json_is_valid(self):
        self.assertTrue(self.hooks_path.exists(), f"missing {self.hooks_path}")
        json.loads(self.hooks_path.read_text(encoding="utf-8"))

    def test_registers_session_start_hook_pointing_at_script(self):
        hooks = json.loads(self.hooks_path.read_text(encoding="utf-8"))
        session_start = hooks["hooks"]["SessionStart"]
        self.assertEqual(len(session_start), 1)
        entry = session_start[0]
        self.assertEqual(entry["matcher"], "startup|clear|compact")
        command_hooks = [h for h in entry["hooks"] if h.get("type") == "command"]
        self.assertEqual(len(command_hooks), 1)
        self.assertIn("${CLAUDE_PLUGIN_ROOT}/hooks/session-start.sh", command_hooks[0]["command"])
        self.assertEqual(command_hooks[0].get("shell"), "bash")


def _run_hook(plugin_root: Path) -> dict:
    """Run the SessionStart hook script via bash and parse its JSON output."""
    script = plugin_root / "hooks" / "session-start.sh"
    # Resolve bash through PATH explicitly. A bare "bash" goes through Windows
    # CreateProcess, which searches System32 BEFORE PATH -- and System32 holds
    # WSL's bash.exe launcher, which (with no distro) prints a UTF-16
    # "Catastrophic failure ... E_UNEXPECTED" to stdout instead of running the
    # script. shutil.which only searches PATH, so it finds Git Bash instead.
    bash = shutil.which("bash") or "bash"
    result = subprocess.run(
        [bash, str(script)],
        input="{}",
        capture_output=True,
        text=True,
        encoding="utf-8",
        timeout=30,
    )
    return json.loads(result.stdout)


class TestSessionStartHook(unittest.TestCase):
    def test_hook_script_exists(self):
        self.assertTrue((PLUGIN_ROOT / "hooks" / "session-start.sh").exists())

    def test_emits_hook_json_with_skill_content(self):
        output = _run_hook(PLUGIN_ROOT)
        hook_out = output["hookSpecificOutput"]
        self.assertEqual(hook_out["hookEventName"], "SessionStart")
        context = hook_out["additionalContext"]
        self.assertIn("nutcracker", context)
        # Must be the REAL skill content, not the fallback. The fallback error
        # string itself contains "using-cum-planning", so asserting on the
        # name alone can't tell the two apart -- assert on a marker that only
        # the actual skill body has (its verified command table), and that no
        # error text leaked in.
        self.assertNotIn("Error reading", context)
        self.assertIn("--waiting-on", context)

    def test_degrades_to_valid_json_when_skill_missing(self):
        import tempfile

        with tempfile.TemporaryDirectory() as tmp:
            fake_root = Path(tmp)
            (fake_root / "hooks").mkdir()
            shutil.copy(PLUGIN_ROOT / "hooks" / "session-start.sh", fake_root / "hooks")
            # No skills/ directory at all -- the script must still print JSON.
            output = _run_hook(fake_root)
        self.assertIn("hookSpecificOutput", output)
        self.assertIn("Error reading", output["hookSpecificOutput"]["additionalContext"])


def _read_frontmatter(skill_md: Path) -> dict:
    """Parse the YAML-ish frontmatter block (name/description only) of a SKILL.md."""
    text = skill_md.read_text(encoding="utf-8")
    match = re.match(r"^---\n(.*?)\n---\n", text, re.DOTALL)
    assert match, f"no frontmatter block in {skill_md}"
    fields = {}
    for line in match.group(1).splitlines():
        if ":" in line:
            key, _, value = line.partition(":")
            fields[key.strip()] = value.strip()
    return fields


class TestSkillFrontmatter(unittest.TestCase):
    def test_every_skill_has_valid_frontmatter(self):
        for name in SKILL_NAMES:
            with self.subTest(skill=name):
                skill_md = PLUGIN_ROOT / "skills" / name / "SKILL.md"
                self.assertTrue(skill_md.exists(), f"missing {skill_md}")
                fm = _read_frontmatter(skill_md)
                self.assertEqual(fm["name"], name)
                self.assertTrue(
                    fm["description"].startswith("Use when"),
                    f"{name} description must start with 'Use when': {fm['description']!r}",
                )


# Each row: (cum subcommand argv, [flags that must appear in its --help]).
# This is the mechanical form of the "ensure correct usage" requirement: if a
# skill documents a command or flag that the installed cum doesn't have, this
# test fails rather than the skill silently teaching a wrong command.
CUM_COMMANDS_DOCUMENTED = [
    (["tc"], ["--list", "--parent", "--description"]),
    (["chk", "create"], []),
    (["chk", "item-add"], ["--task"]),
    (["chk", "item-update"], ["--resolved", "--task"]),
    (["tad"], ["--waiting-on", "--blocking"]),
    (["tss"], ["--force"]),
    (["ca"], []),
    (["d"], []),
    (["show"], []),
    (["tu"], ["--description", "--name"]),
    (["set"], []),
    (["chk", "list"], []),
]

CUM_FLAGS_THAT_MUST_NOT_EXIST = [
    (["tad"], ["--depends-on", "--blocks"]),
]


@unittest.skipIf(shutil.which("cum") is None, "cum not on PATH")
class TestCumCommandsAreReal(unittest.TestCase):
    def _help(self, argv):
        result = subprocess.run(
            ["cum", *argv, "--help"],
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="replace",
            timeout=30,
        )
        self.assertEqual(
            result.returncode, 0, f"cum {' '.join(argv)} --help failed:\n{result.stderr}"
        )
        return result.stdout

    def test_documented_commands_and_flags_exist(self):
        for argv, flags in CUM_COMMANDS_DOCUMENTED:
            with self.subTest(command=" ".join(argv)):
                help_text = self._help(argv)
                for flag in flags:
                    self.assertIn(flag, help_text, f"cum {' '.join(argv)} lacks {flag}")

    def test_known_wrong_flags_do_not_exist(self):
        for argv, flags in CUM_FLAGS_THAT_MUST_NOT_EXIST:
            with self.subTest(command=" ".join(argv)):
                help_text = self._help(argv)
                for flag in flags:
                    self.assertNotIn(
                        flag, help_text, f"cum {' '.join(argv)} unexpectedly has {flag}"
                    )


if __name__ == "__main__":
    unittest.main()
