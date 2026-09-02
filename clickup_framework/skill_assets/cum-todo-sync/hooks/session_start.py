#!/usr/bin/env python3
"""SessionStart hook for the cum-todo-sync skill.

Surfaces the user's ClickUp-assigned tasks (via `cum assigned`) as context at
session start, so Claude can offer to mirror them into local todos through
the cum-todo-sync skill without the user having to ask first. Does NOT create
any TaskCreate todos itself -- hooks are shell commands, they cannot call
Claude Code's tools. This only prints text; the actual sync (dedup + create)
is performed by the agent per the skill's procedure, on request.
"""
import json
import os
import subprocess
import sys
import tempfile


def main():
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
            timeout=30,
        )
        if result.returncode != 0 or not os.path.exists(out_path):
            print("{}")
            return
        with open(out_path, encoding="utf-8") as f:
            tasks = json.load(f)
    except Exception:
        print("{}")
        return
    finally:
        try:
            os.unlink(out_path)
        except OSError:
            pass

    if not isinstance(tasks, list) or not tasks:
        print("{}")
        return

    lines = [f"You have {len(tasks)} ClickUp task(s) assigned (via `cum assigned`)."]
    for t in tasks[:15]:
        status = (t.get("status") or {}).get("status", "?")
        name = (t.get("name") or "")[:80]
        lines.append(f"- [{t.get('id')}] {name} ({status})")
    if len(tasks) > 15:
        lines.append(f"...and {len(tasks) - 15} more.")
    lines.append(
        "If the user asks to sync these into local todos, use the cum-todo-sync "
        "skill (dedup by [clickup_task_id] prefix already present in TaskList) "
        "rather than creating all of them automatically."
    )

    output = {
        "hookSpecificOutput": {
            "hookEventName": "SessionStart",
            "additionalContext": "\n".join(lines),
        }
    }
    print(json.dumps(output))


if __name__ == "__main__":
    main()
