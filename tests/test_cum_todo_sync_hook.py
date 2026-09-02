"""
Tests for the cum-todo-sync skill's SessionStart hook.

The hook (clickup_framework/skill_assets/cum-todo-sync/hooks/session_start.py)
is a standalone script, not a package module -- it's shipped and run as a
plain Python file by `cum install-skill --hook`, not imported by
clickup_framework itself. Loaded here via importlib since its parent
directory (cum-todo-sync) isn't a valid Python identifier.
"""

import importlib.util
import json
import subprocess
import unittest
from pathlib import Path
from unittest.mock import patch

HOOK_PATH = (
    Path(__file__).resolve().parent.parent
    / "clickup_framework"
    / "skill_assets"
    / "cum-todo-sync"
    / "hooks"
    / "session_start.py"
)

_spec = importlib.util.spec_from_file_location("cum_todo_sync_session_start", HOOK_PATH)
hook = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(hook)


class TestIsDisabled(unittest.TestCase):
    def test_truthy_values_disable(self):
        for value in ["1", "true", "True", "TRUE", "yes", "Yes", "on", "t", "y"]:
            with self.subTest(value=value):
                self.assertTrue(hook.is_disabled({hook.DISABLE_ENV_VAR: value}))

    def test_falsy_or_unset_values_do_not_disable(self):
        for env in [
            {},
            {hook.DISABLE_ENV_VAR: "0"},
            {hook.DISABLE_ENV_VAR: "false"},
            {hook.DISABLE_ENV_VAR: ""},
        ]:
            with self.subTest(env=env):
                self.assertFalse(hook.is_disabled(env))

    def test_whitespace_and_case_are_tolerated(self):
        self.assertTrue(hook.is_disabled({hook.DISABLE_ENV_VAR: "  TRUE  "}))


class TestBuildSummary(unittest.TestCase):
    def test_empty_or_none_tasks_returns_none(self):
        self.assertIsNone(hook.build_summary(None))
        self.assertIsNone(hook.build_summary([]))

    def test_basic_summary_includes_id_name_status(self):
        tasks = [{"id": "86c9p2860", "name": "Fix bug", "status": {"status": "in progress"}}]
        summary = hook.build_summary(tasks)
        self.assertIn("86c9p2860", summary)
        self.assertIn("Fix bug", summary)
        self.assertIn("in progress", summary)
        self.assertIn("1 ClickUp task(s)", summary)

    def test_missing_status_falls_back_to_question_mark(self):
        summary = hook.build_summary([{"id": "1", "name": "No status"}])
        self.assertIn("(?)", summary)

    def test_truncates_at_limit_and_reports_remainder(self):
        tasks = [{"id": str(i), "name": f"Task {i}"} for i in range(20)]
        summary = hook.build_summary(tasks, limit=15)
        self.assertIn("...and 5 more.", summary)
        # Only the first 15 task IDs should actually be listed as bullet lines.
        self.assertEqual(summary.count("- ["), 15)

    def test_long_name_is_truncated(self):
        long_name = "x" * 200
        summary = hook.build_summary([{"id": "1", "name": long_name}])
        self.assertNotIn(long_name, summary)


class TestFetchAssignedTasks(unittest.TestCase):
    def test_returns_none_and_skips_subprocess_when_cum_missing(self):
        with patch.object(hook.shutil, "which", return_value=None):
            with patch.object(hook.subprocess, "run") as mock_run:
                result = hook.fetch_assigned_tasks()
        self.assertIsNone(result)
        mock_run.assert_not_called()

    def test_returns_none_on_nonzero_exit(self):
        with patch.object(hook.shutil, "which", return_value="/usr/bin/cum"):
            with patch.object(
                hook.subprocess, "run", return_value=subprocess.CompletedProcess([], 1)
            ):
                result = hook.fetch_assigned_tasks()
        self.assertIsNone(result)

    def test_returns_none_on_timeout(self):
        with patch.object(hook.shutil, "which", return_value="/usr/bin/cum"):
            with patch.object(
                hook.subprocess, "run", side_effect=subprocess.TimeoutExpired(cmd="cum", timeout=30)
            ):
                result = hook.fetch_assigned_tasks()
        self.assertIsNone(result)

    def test_returns_none_on_malformed_json_output(self):
        def fake_run(cmd, **kwargs):
            out_path = cmd[cmd.index("--output-file") + 1]
            Path(out_path).write_text("not valid json{{{", encoding="utf-8")
            return subprocess.CompletedProcess(cmd, 0)

        with patch.object(hook.shutil, "which", return_value="/usr/bin/cum"):
            with patch.object(hook.subprocess, "run", side_effect=fake_run):
                result = hook.fetch_assigned_tasks()
        self.assertIsNone(result)

    def test_returns_none_when_output_is_not_a_list(self):
        def fake_run(cmd, **kwargs):
            out_path = cmd[cmd.index("--output-file") + 1]
            Path(out_path).write_text(json.dumps({"not": "a list"}), encoding="utf-8")
            return subprocess.CompletedProcess(cmd, 0)

        with patch.object(hook.shutil, "which", return_value="/usr/bin/cum"):
            with patch.object(hook.subprocess, "run", side_effect=fake_run):
                result = hook.fetch_assigned_tasks()
        self.assertIsNone(result)

    def test_happy_path_returns_parsed_task_list(self):
        fake_tasks = [{"id": "1", "name": "Task one", "status": {"status": "open"}}]

        def fake_run(cmd, **kwargs):
            out_path = cmd[cmd.index("--output-file") + 1]
            Path(out_path).write_text(json.dumps(fake_tasks), encoding="utf-8")
            return subprocess.CompletedProcess(cmd, 0)

        with patch.object(hook.shutil, "which", return_value="/usr/bin/cum"):
            with patch.object(hook.subprocess, "run", side_effect=fake_run):
                result = hook.fetch_assigned_tasks()
        self.assertEqual(result, fake_tasks)

    def test_temp_file_is_cleaned_up_even_on_failure(self):
        captured_path = {}

        def fake_run(cmd, **kwargs):
            captured_path["path"] = cmd[cmd.index("--output-file") + 1]
            return subprocess.CompletedProcess(cmd, 1)

        with patch.object(hook.shutil, "which", return_value="/usr/bin/cum"):
            with patch.object(hook.subprocess, "run", side_effect=fake_run):
                hook.fetch_assigned_tasks()
        self.assertFalse(Path(captured_path["path"]).exists())


class TestBuildOutput(unittest.TestCase):
    def test_disabled_short_circuits_before_touching_cum(self):
        with patch.object(hook, "fetch_assigned_tasks") as mock_fetch:
            output = hook.build_output({hook.DISABLE_ENV_VAR: "1"})
        self.assertEqual(output, "{}")
        mock_fetch.assert_not_called()

    def test_enabled_calls_fetch_and_builds_hook_json(self):
        fake_tasks = [{"id": "1", "name": "Task one", "status": {"status": "open"}}]
        with patch.object(hook, "fetch_assigned_tasks", return_value=fake_tasks):
            output = hook.build_output({})
        parsed = json.loads(output)
        self.assertEqual(parsed["hookSpecificOutput"]["hookEventName"], "SessionStart")
        self.assertIn("Task one", parsed["hookSpecificOutput"]["additionalContext"])

    def test_no_tasks_produces_empty_object(self):
        with patch.object(hook, "fetch_assigned_tasks", return_value=None):
            output = hook.build_output({})
        self.assertEqual(output, "{}")

    def test_output_is_always_valid_json(self):
        for tasks in (None, [], [{"id": "1", "name": "x"}]):
            with patch.object(hook, "fetch_assigned_tasks", return_value=tasks):
                output = hook.build_output({})
            json.loads(output)  # raises if not valid JSON


if __name__ == "__main__":
    unittest.main()
