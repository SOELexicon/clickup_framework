---
name: cum-todo-sync
description: Use when the user asks to sync, pull, or import their ClickUp tasks into local todos, wants their `cum assigned`/`cum my-tasks` work mirrored as trackable Claude Code todos, or references keeping local todos in sync with ClickUp. Also applies at the start of ClickUp-driven work sessions when no local todos exist yet for tasks already assigned in ClickUp.
---

# cum -> local todo sync

## Quick install

`cum install-skill` copies this skill (and, with `--hook`, wires up the
SessionStart hook below) straight into `~/.claude/skills/cum-todo-sync/` and
`~/.claude/settings.json`. Run `cum install-skill --help` for options. The
sections below document what that command does and how to do it by hand if
`cum install-skill` isn't available in your version.

## Overview

One-directional sync: ClickUp tasks assigned to the user (via `cum`) become
Claude Code local todos (`TaskCreate`/`TaskList`/`TaskUpdate`). This is NOT a
feature of the `cum` CLI itself -- `cum` is a plain Python program and has no
way to call Claude Code's tools. The sync only happens because *you* (the
agent) run `cum`, read its output, and call `TaskCreate` yourself. There is no
code to write for this; it's a workflow you execute on request.

## When to run this

- User asks to sync/pull/import ClickUp tasks into todos ("sync my tasks",
  "pull my ClickUp tasks in", "add my assigned tasks as todos")
- Starting work that's driven by ClickUp tasks and `TaskList` is empty or
  missing tasks you know are assigned in ClickUp

Don't run this proactively on every session start unless the user has asked
for that (see the hook section below) -- default is on-request only.

## Procedure

1. **Pull assigned ClickUp tasks as structured data.**
   ```
   PowerShell tool — command: "cum assigned -O json"
   ```
   This writes `cum_output.json` (or the path from `--output-file` if you
   pass one) and also prints console output. Read the JSON file rather than
   parsing the colorized console text. If the user wants a specific list
   instead of "assigned to me", use `cum ls <list_id> -O json` or
   `cum flat <list_id> -O json` instead.

2. **Read the current local todo list** with `TaskList` before creating
   anything -- this is required by `TaskCreate`'s own dedup guidance, and
   doubly important here since re-running this sync should not create
   duplicate todos for tasks already mirrored.

3. **Dedup by ClickUp task ID embedded in the subject.** When you create a
   todo from a ClickUp task, prefix the subject with the task's short ID in
   brackets: `[86c9p2860] Fix pagination bug`. On a re-sync, skip any
   ClickUp task whose ID already appears as a `[id]` prefix in an existing
   `TaskList` subject. This makes dedup a plain string check against
   `TaskList`'s summary output -- no need to fetch full task details via
   `TaskGet` for every candidate.

4. **For each ClickUp task with no matching local todo**, call `TaskCreate`:
   - `subject`: `[<clickup_task_id>] <task name>`, trimmed to stay readable
     (task names can be long; keep the ClickUp ID prefix intact, truncate
     the name if needed)
   - `description`: short summary — priority, status, list name, and the
     full ClickUp task URL/ID for reference. Enough for `TaskGet` to be
     self-contained without going back to ClickUp.
   - `metadata`: `{"clickup_task_id": "<id>", "clickup_list_id": "<list_id>"}`
     — structured backup to the subject-prefix dedup, useful if anything
     ever needs to filter todos by ClickUp origin programmatically.

5. **Report what happened**: how many ClickUp tasks were found, how many
   were already mirrored (skipped), how many new todos were created. Don't
   silently create dozens of todos without summarizing — the user should be
   able to see the sync happened and roughly what landed.

## What this does NOT do (by design, unless asked)

- **No reverse sync.** Completing a local todo does NOT mark the ClickUp
  task complete. If the user wants that too, it's a separate, explicit ask
  (`cum tss <task_id> "complete"`) — don't do it automatically as a side
  effect of `TaskUpdate`, since a local todo being "done" (e.g. "I've
  reviewed this") doesn't necessarily mean the ClickUp task itself is done.
- **The installed hook (below) does not itself create todos.** It only
  surfaces a summary as context. Actually syncing (steps 2-5) still only
  happens when the user asks for it in that session.

## SessionStart hook (self-installing)

This skill ships a ready-to-use hook script at
`hooks/session_start.py` (relative to this skill's own directory) -- nothing
to author, only to wire up. `cum install-skill --hook` does this for you; the
rest of this section is what it does under the hood, for when you need to do
it by hand (a manual install, a different machine, or `cum install-skill`
isn't available in the version you're running).

The hook checks `shutil.which("cum")` before doing anything else (an
explicit dependency check, not exception fallout) and runs `cum assigned -O
json --output-file <tmp>` (stdout/stderr discarded, not
`capture_output=True`/`text=True`, to dodge a Windows console-codepage
`UnicodeDecodeError` on cum's colorized output), reads the resulting tasks,
and prints `{"hookSpecificOutput": {"hookEventName": "SessionStart",
"additionalContext": "<summary>"}}` -- a short list of assigned tasks plus a
one-line pointer back to this skill. It degrades to `{}` silently on any
failure (cum missing, no credentials, no assigned tasks, timeout, malformed
output) -- never breaks session start. `cum install-skill --hook` warns (but
still installs) if `cum` isn't on PATH at install time, since a silently
inert hook is confusing otherwise.

**Turning it off:** set `CUM_TODO_SYNC_DISABLED=1` (also accepts
`true`/`yes`/`on`, case-insensitive) in the environment to make the hook
print `{}` immediately without ever touching `cum` -- useful for turning the
feature off temporarily without editing `settings.json`. The hook's own
logic (`is_disabled`, `fetch_assigned_tasks`, `build_summary`, `build_output`
in `hooks/session_start.py`) is unit-tested in
`tests/test_cum_todo_sync_hook.py` in the clickup_framework repo, covering
the disabled path, cum-missing, non-zero exit, timeout, malformed/non-list
JSON output, and the happy path.

**Check before assuming it's live.** Read `~/.claude/settings.json` (global)
or `.claude/settings.json`/`.claude/settings.local.json` (project, if
installed there instead) for a `hooks.SessionStart` entry whose command
references `session_start.py` under this skill's directory. Do not assume
it's installed just because this skill exists in `.claude/skills/` -- the
skill directory can be present (synced, copied, or added to a fresh project)
without the hook ever having been wired into settings.

**If it's not installed, install it yourself** using the `update-config`
skill's "Constructing a Hook" procedure (dedup check, pipe-test, `jq -e`
validate, since-it's-SessionStart skip the in-turn firing proof). The entry
to merge, with the command path adjusted for wherever this skill directory
actually lives (an absolute path is safest for a user-level install, since
it must resolve regardless of the current working directory):

```json
{
  "hooks": {
    "SessionStart": [
      {
        "hooks": [
          {
            "type": "command",
            "command": "python <absolute-path-to>/cum-todo-sync/hooks/session_start.py",
            "timeout": 35,
            "statusMessage": "Checking ClickUp assigned tasks (cum-todo-sync)..."
          }
        ]
      }
    ]
  }
}
```

Pipe-test first: `echo '{}' | python <path-to>/session_start.py` should print
valid JSON (or `{}`) with no stderr noise. `cum` must be on PATH and
authenticated for real results; a `{}` output when `cum` genuinely works
means something else is wrong (rerun without piping to `python` to see cum's
own error).

Once installed, the summary appears in context automatically every session
without prompting the user -- but it still never calls `TaskCreate` itself;
hooks are shell commands, they cannot call Claude Code tools. Run the full
Procedure above only when the user actually asks for the sync.

To disable: remove the `hooks.SessionStart` entry (leave
`worktree.bgIsolation`, if present, alone -- unrelated). To verify it's live
without waiting for a new session: `/hooks` in the CLI.
