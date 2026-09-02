"""
Tests for `cum install-plugin` (clickup_framework/commands/plugin_install_command.py).

All tests use a tmp_path as --target-dir and never touch the real
~/.claude -- this is filesystem-mutating code, not something to exercise
against a real profile in a test run.
"""

import argparse
import json
import unittest
from pathlib import Path

from clickup_framework.commands import plugin_install_command as mod


def make_args(target_dir, enable=False, force=False, plugin_name="nutcracker"):
    return argparse.Namespace(
        plugin_name=plugin_name,
        enable=enable,
        force=force,
        target_dir=str(target_dir),
        colorize=False,
    )


class InstallPluginTestCase(unittest.TestCase):
    def setUp(self):
        import tempfile

        self._tmp = tempfile.TemporaryDirectory()
        self.target_dir = Path(self._tmp.name)

    def tearDown(self):
        self._tmp.cleanup()


class TestFreshInstall(InstallPluginTestCase):
    def test_installs_plugin_files_only_by_default(self):
        mod.install_plugin_command(make_args(self.target_dir))
        plugin_target = self.target_dir / "plugins" / "nutcracker"
        self.assertTrue((plugin_target / ".claude-plugin" / "plugin.json").exists())
        self.assertTrue((plugin_target / "hooks" / "hooks.json").exists())
        self.assertTrue(
            (plugin_target / "skills" / "using-cum-planning" / "SKILL.md").exists()
        )
        self.assertFalse((self.target_dir / "settings.json").exists())

    def test_enable_flag_also_wires_settings_json(self):
        mod.install_plugin_command(make_args(self.target_dir, enable=True))
        settings_path = self.target_dir / "settings.json"
        self.assertTrue(settings_path.exists())
        settings = json.loads(settings_path.read_text(encoding="utf-8"))
        self.assertEqual(settings["enabledPlugins"], {"nutcracker": True})

    def test_unknown_plugin_name_errors(self):
        with self.assertRaises(SystemExit):
            mod.install_plugin_command(make_args(self.target_dir, plugin_name="does-not-exist"))


class TestIdempotency(InstallPluginTestCase):
    def test_rerun_without_force_does_not_touch_existing_files(self):
        mod.install_plugin_command(make_args(self.target_dir, enable=True))
        plugin_target = self.target_dir / "plugins" / "nutcracker"
        manifest = plugin_target / ".claude-plugin" / "plugin.json"
        manifest_before = manifest.read_text(encoding="utf-8")

        # Tamper with the installed copy, then re-run without --force: must
        # be left alone (not silently overwritten).
        manifest.write_text("tampered", encoding="utf-8")
        mod.install_plugin_command(make_args(self.target_dir, enable=True))

        self.assertEqual(manifest.read_text(encoding="utf-8"), "tampered")
        self.assertNotEqual(manifest.read_text(encoding="utf-8"), manifest_before)

    def test_rerun_enable_stays_at_one_entry(self):
        mod.install_plugin_command(make_args(self.target_dir, enable=True))
        mod.install_plugin_command(make_args(self.target_dir, enable=True))
        settings = json.loads((self.target_dir / "settings.json").read_text(encoding="utf-8"))
        self.assertEqual(settings["enabledPlugins"], {"nutcracker": True})


class TestForceReinstall(InstallPluginTestCase):
    def test_force_reinstall_backs_up_previous_files(self):
        mod.install_plugin_command(make_args(self.target_dir, enable=True))
        mod.install_plugin_command(make_args(self.target_dir, enable=True, force=True))

        plugins_dir = self.target_dir / "plugins"
        # Only the real plugin directory may exist under plugins/ -- a backup
        # sibling there would risk being picked up as its own stale plugin.
        self.assertEqual([p.name for p in plugins_dir.iterdir()], ["nutcracker"])

        backup_dir = self.target_dir / "plugin-backups" / "nutcracker"
        self.assertTrue(backup_dir.exists())
        self.assertTrue((backup_dir / ".claude-plugin" / "plugin.json").exists())

    def test_force_reinstall_preserves_other_settings_keys(self):
        settings_path = self.target_dir / "settings.json"
        settings_path.parent.mkdir(parents=True, exist_ok=True)
        settings_path.write_text(
            json.dumps({"model": "sonnet", "enabledPlugins": {"other-plugin": True}}),
            encoding="utf-8",
        )

        mod.install_plugin_command(make_args(self.target_dir, enable=True))
        mod.install_plugin_command(make_args(self.target_dir, enable=True, force=True))

        settings = json.loads(settings_path.read_text(encoding="utf-8"))
        self.assertEqual(settings["model"], "sonnet")
        self.assertEqual(
            settings["enabledPlugins"], {"other-plugin": True, "nutcracker": True}
        )


class TestSettingsMerge(InstallPluginTestCase):
    def test_preserves_unrelated_top_level_keys(self):
        settings_path = self.target_dir / "settings.json"
        settings_path.parent.mkdir(parents=True, exist_ok=True)
        settings_path.write_text(
            json.dumps({"model": "sonnet", "env": {"FOO": "bar"}}), encoding="utf-8"
        )

        mod.install_plugin_command(make_args(self.target_dir, enable=True))

        settings = json.loads(settings_path.read_text(encoding="utf-8"))
        self.assertEqual(settings["model"], "sonnet")
        self.assertEqual(settings["env"], {"FOO": "bar"})
        self.assertEqual(settings["enabledPlugins"], {"nutcracker": True})

    def test_malformed_existing_settings_errors_clearly(self):
        settings_path = self.target_dir / "settings.json"
        settings_path.parent.mkdir(parents=True, exist_ok=True)
        settings_path.write_text("{not valid json", encoding="utf-8")

        with self.assertRaises(SystemExit):
            mod.install_plugin_command(make_args(self.target_dir, enable=True))


if __name__ == "__main__":
    unittest.main()
