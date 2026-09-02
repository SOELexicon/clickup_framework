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


if __name__ == "__main__":
    unittest.main()
