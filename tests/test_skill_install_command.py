"""
Tests for `cum install-skill` (clickup_framework/commands/skill_install_command.py).

All tests use a tmp_path as --target-dir and never touch the real
~/.claude -- this is filesystem-mutating code, not something to exercise
against a real profile in a test run.
"""

import argparse
import json
import unittest
from pathlib import Path
from unittest.mock import patch

from clickup_framework.commands import skill_install_command as mod


def make_args(target_dir, hook=False, force=False, skill_name="cum-todo-sync"):
    return argparse.Namespace(
        skill_name=skill_name,
        hook=hook,
        force=force,
        target_dir=str(target_dir),
        colorize=False,
    )


class InstallSkillTestCase(unittest.TestCase):
    def setUp(self):
        import tempfile

        self._tmp = tempfile.TemporaryDirectory()
        self.target_dir = Path(self._tmp.name)

    def tearDown(self):
        self._tmp.cleanup()


class TestFreshInstall(InstallSkillTestCase):
    def test_installs_skill_files_only_by_default(self):
        mod.install_skill_command(make_args(self.target_dir))
        skill_target = self.target_dir / "skills" / "cum-todo-sync"
        self.assertTrue((skill_target / "SKILL.md").exists())
        self.assertTrue((skill_target / "hooks" / "session_start.py").exists())
        self.assertFalse((self.target_dir / "settings.json").exists())

    def test_hook_flag_also_wires_settings_json(self):
        mod.install_skill_command(make_args(self.target_dir, hook=True))
        settings_path = self.target_dir / "settings.json"
        self.assertTrue(settings_path.exists())
        settings = json.loads(settings_path.read_text(encoding="utf-8"))
        session_start = settings["hooks"]["SessionStart"]
        self.assertEqual(len(session_start), 1)
        command = session_start[0]["hooks"][0]["command"]
        self.assertIn("session_start.py", command)
        self.assertIn(str(self.target_dir), command)

    def test_unknown_skill_name_errors(self):
        with self.assertRaises(SystemExit):
            mod.install_skill_command(make_args(self.target_dir, skill_name="does-not-exist"))


class TestIdempotency(InstallSkillTestCase):
    def test_rerun_without_force_does_not_touch_existing_files(self):
        mod.install_skill_command(make_args(self.target_dir, hook=True))
        skill_target = self.target_dir / "skills" / "cum-todo-sync"
        skill_md_before = (skill_target / "SKILL.md").read_text(encoding="utf-8")

        # Tamper with the installed copy, then re-run without --force: must
        # be left alone (not silently overwritten).
        (skill_target / "SKILL.md").write_text("tampered", encoding="utf-8")
        mod.install_skill_command(make_args(self.target_dir, hook=True))

        self.assertEqual((skill_target / "SKILL.md").read_text(encoding="utf-8"), "tampered")
        self.assertNotEqual(
            (skill_target / "SKILL.md").read_text(encoding="utf-8"), skill_md_before
        )

    def test_rerun_without_force_does_not_duplicate_hook_entry(self):
        mod.install_skill_command(make_args(self.target_dir, hook=True))
        mod.install_skill_command(make_args(self.target_dir, hook=True))
        settings = json.loads((self.target_dir / "settings.json").read_text(encoding="utf-8"))
        self.assertEqual(len(settings["hooks"]["SessionStart"]), 1)


class TestForceReinstallRegressions(InstallSkillTestCase):
    """Regression tests for two bugs found testing this against a real profile:
    --force duplicated the hook entry instead of replacing it, and the skill
    files backup directory was created as a *sibling* inside skills/, where
    it got picked up as its own (stale) auto-discovered skill."""

    def test_force_reinstall_does_not_duplicate_hook_entry(self):
        mod.install_skill_command(make_args(self.target_dir, hook=True))
        mod.install_skill_command(make_args(self.target_dir, hook=True, force=True))

        settings = json.loads((self.target_dir / "settings.json").read_text(encoding="utf-8"))
        session_start = settings["hooks"]["SessionStart"]
        matching = [
            h
            for entry in session_start
            for h in entry["hooks"]
            if "session_start.py" in h.get("command", "")
        ]
        self.assertEqual(
            len(matching), 1, f"expected exactly one cum-todo-sync hook entry, got: {matching}"
        )

    def test_force_reinstall_preserves_other_hook_entries(self):
        settings_path = self.target_dir / "settings.json"
        settings_path.parent.mkdir(parents=True, exist_ok=True)
        settings_path.write_text(
            json.dumps(
                {
                    "permissions": {"allow": ["Bash(git *)"]},
                    "hooks": {
                        "SessionStart": [
                            {"hooks": [{"type": "command", "command": "echo unrelated"}]}
                        ]
                    },
                }
            ),
            encoding="utf-8",
        )

        mod.install_skill_command(make_args(self.target_dir, hook=True))
        mod.install_skill_command(make_args(self.target_dir, hook=True, force=True))

        settings = json.loads(settings_path.read_text(encoding="utf-8"))
        self.assertEqual(settings["permissions"]["allow"], ["Bash(git *)"])
        commands = [
            h.get("command") for entry in settings["hooks"]["SessionStart"] for h in entry["hooks"]
        ]
        self.assertIn("echo unrelated", commands)
        self.assertEqual(sum("session_start.py" in c for c in commands), 1)

    def test_force_reinstall_backup_is_not_under_skills_dir(self):
        mod.install_skill_command(make_args(self.target_dir, hook=True))
        mod.install_skill_command(make_args(self.target_dir, hook=True, force=True))

        skills_dir = self.target_dir / "skills"
        # Only the real skill directory may exist under skills/ -- a backup
        # sibling there would itself be auto-discovered as a skill.
        self.assertEqual([p.name for p in skills_dir.iterdir()], ["cum-todo-sync"])

        backup_dir = self.target_dir / "skill-backups" / "cum-todo-sync"
        self.assertTrue(backup_dir.exists())
        self.assertTrue((backup_dir / "SKILL.md").exists())

    def test_repeated_force_reinstalls_stay_at_one_hook_entry(self):
        mod.install_skill_command(make_args(self.target_dir, hook=True))
        for _ in range(3):
            mod.install_skill_command(make_args(self.target_dir, hook=True, force=True))

        settings = json.loads((self.target_dir / "settings.json").read_text(encoding="utf-8"))
        matching = [
            h
            for entry in settings["hooks"]["SessionStart"]
            for h in entry["hooks"]
            if "session_start.py" in h.get("command", "")
        ]
        self.assertEqual(len(matching), 1)


class TestSettingsMerge(InstallSkillTestCase):
    def test_preserves_unrelated_top_level_keys(self):
        settings_path = self.target_dir / "settings.json"
        settings_path.parent.mkdir(parents=True, exist_ok=True)
        settings_path.write_text(
            json.dumps({"model": "sonnet", "env": {"FOO": "bar"}}), encoding="utf-8"
        )

        mod.install_skill_command(make_args(self.target_dir, hook=True))

        settings = json.loads(settings_path.read_text(encoding="utf-8"))
        self.assertEqual(settings["model"], "sonnet")
        self.assertEqual(settings["env"], {"FOO": "bar"})
        self.assertIn("SessionStart", settings["hooks"])

    def test_malformed_existing_settings_errors_clearly(self):
        settings_path = self.target_dir / "settings.json"
        settings_path.parent.mkdir(parents=True, exist_ok=True)
        settings_path.write_text("{not valid json", encoding="utf-8")

        with self.assertRaises(SystemExit):
            mod.install_skill_command(make_args(self.target_dir, hook=True))


class TestDependencyCheck(InstallSkillTestCase):
    def test_warns_when_cum_not_on_path(self):
        with patch.object(mod.shutil, "which", return_value=None):
            with patch("builtins.print") as mock_print:
                mod.install_skill_command(make_args(self.target_dir, hook=True))
        printed = " ".join(str(c.args[0]) for c in mock_print.call_args_list if c.args)
        self.assertIn("not found on PATH", printed)

    def test_no_warning_when_cum_is_on_path(self):
        with patch.object(mod.shutil, "which", return_value="/usr/bin/cum"):
            with patch("builtins.print") as mock_print:
                mod.install_skill_command(make_args(self.target_dir, hook=True))
        printed = " ".join(str(c.args[0]) for c in mock_print.call_args_list if c.args)
        self.assertNotIn("not found on PATH", printed)


if __name__ == "__main__":
    unittest.main()
