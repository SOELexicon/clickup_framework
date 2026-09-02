#!/usr/bin/env python3
"""SessionStart hook for the cum-todo-sync skill.

Surfaces the user's ClickUp-assigned tasks (via `cum assigned`) as context at
session start, so Claude can offer to mirror them into local todos through
the cum-todo-sync skill without the user having to ask first. Does NOT create
any TaskCreate todos itself -- hooks are shell commands, they cannot call
Claude Code's tools. This only prints text; the actual sync (dedup + create)
is performed by the agent per the skill's procedure, on request.

Set CUM_TODO_SYNC_DISABLED=1 (or true/yes/on) to turn this hook off without
removing it from settings.json -- it will print "{}" immediately and never
touch `cum` at all.
"""
import json
import os
import shutil
import subprocess
import tempfile

DISABLE_ENV_VAR = "CUM_TODO_SYNC_DISABLED"
_TRUE_STRINGS = {"1", "true", "t", "yes", "y", "on"}
SUMMARY_TASK_LIMIT = 15
SUBPROCESS_TIMEOUT_SECONDS = 30


def is_disabled(env=None) -> bool:
    """Whether CUM_TODO_SYNC_DISABLED is set to a truthy value."""
    env = os.environ if env is None else env
    return env.get(DISABLE_ENV_VAR, "").strip().lower() in _TRUE_STRINGS


def fetch_assigned_tasks(timeout=SUBPROCESS_TIMEOUT_SECONDS):
    """Run `cum assigned -O json` and return the parsed task list, or None on
    any failure (cum not on PATH, non-zero exit, timeout, missing/malformed
    output, or a response that isn't a JSON list). Never raises."""
    if shutil.which("cum") is None:
        # Explicit dependency check rather than letting subprocess.run raise
        # FileNotFoundError -- avoids spawning a process we already know will
        # fail, and makes the "cum isn't installed/on PATH" case an intended
        # branch instead of exception fallout.
        return None

    fd, out_path = tempfile.mkstemp(suffix=".json")
    os.close(fd)
    try:
        # Discard stdout/stderr rather than capturing as text: cum's colorized
        # console output isn't needed (only out_path is), and capturing it as
        # text on Windows decodes with the console codepage, which can raise
        # UnicodeDecodeError on the ANSI/emoji bytes cum prints.
        result = subprocess.run(
            ["cum", "assigned", "-O", "json", "--output-file", out_path],
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
            timeout=timeout,
        )
        if result.returncode != 0 or not os.path.exists(out_path):
            return None
        with open(out_path, encoding="utf-8") as f:
            tasks = json.load(f)
    except Exception:
        # subprocess.TimeoutExpired, PermissionError, json.JSONDecodeError,
        # and anything else from a misbehaving `cum` all land here -- this
        # hook must never break session start no matter what `cum` does.
        return None
    finally:
        try:
            os.unlink(out_path)
        except OSError:
            pass

    return tasks if isinstance(tasks, list) else None


def build_summary(tasks, limit=SUMMARY_TASK_LIMIT):
    """Render the assigned-tasks context string, or None if there's nothing
    worth surfacing (no tasks, or tasks is falsy/None)."""
    if not tasks:
        return None

    lines = [f"You have {len(tasks)} ClickUp task(s) assigned (via `cum assigned`)."]
    for t in tasks[:limit]:
        status = (t.get("status") or {}).get("status", "?")
        name = (t.get("name") or "")[:80]
        lines.append(f"- [{t.get('id')}] {name} ({status})")
    if len(tasks) > limit:
        lines.append(f"...and {len(tasks) - limit} more.")
    lines.append(
        "If the user asks to sync these into local todos, use the cum-todo-sync "
        "skill (dedup by [clickup_task_id] prefix already present in TaskList) "
        "rather than creating all of them automatically."
    )
    return "\n".join(lines)


def build_output(env=None):
    """Return the full JSON string this hook should print."""
    if is_disabled(env):
        return "{}"

    tasks = fetch_assigned_tasks()
    summary = build_summary(tasks)
    if summary is None:
        return "{}"

    return json.dumps(
        {
            "hookSpecificOutput": {
                "hookEventName": "SessionStart",
                "additionalContext": summary,
            }
        }
    )


def main():
    print(build_output())


if __name__ == "__main__":
    main()
