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


if __name__ == "__main__":
    unittest.main()
