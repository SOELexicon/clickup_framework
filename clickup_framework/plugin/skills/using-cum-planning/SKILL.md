---
name: using-cum-planning
description: Use when starting any conversation involving multi-step task planning or execution that should be tracked in ClickUp rather than local files, before choosing an implementation approach.
---

# Using cum planning (nutcracker)

Plans live in ClickUp, not in local markdown files. Two skills do the
work; this one just routes you to them.

- **`nutcracker:writing-cum-plans`** — you have a spec or requirements for
  a multi-step task and haven't touched code yet. Turns it into a ClickUp
  task hierarchy: one parent task per plan, one subtask per implementation
  task, a checklist per task's bite-sized steps, real dependencies
  between tasks.
- **`nutcracker:executing-cum-plans`** — you have a parent task ID from
  `writing-cum-plans` and need to implement it task-by-task, updating
  ClickUp as you go.

Invoke the relevant one with the `Skill` tool before planning or
implementing. If a plan already exists in ClickUp for the work at hand,
go straight to `executing-cum-plans` with its parent task ID.

## What this does NOT replace

- **Baseline `cum` usage** — the `cum-cli` skill (a separate personal
  skill, not bundled here) covers viewing, status, comments, context
  shortcuts. Load it if you need more than the table below.
- **Worktree isolation** — nutcracker doesn't manage git worktrees. Use
  `superpowers:using-git-worktrees` (if that plugin is present) or the
  harness's own worktree tool, exactly as you would for any other work.
- **Skill discipline in general** — that's `superpowers:using-superpowers`'
  job. Both plugins can be installed at once; they don't overlap.

## Verified command reference

Every command here was checked against the installed `cum --help` (and is
pinned by `tests/test_nutcracker_plugin.py::TestCumCommandsAreReal` in the
clickup_framework repo). Use these forms exactly.

| Task | Command | Note |
|---|---|---|
| Create parent task | `cum tc "<name>" --list <list_id> --description "<text>"` | `--list` is optional when `--parent` is given |
| Create subtask | `cum tc "<name>" --parent <parent_id> --description "<text>"` | |
| Create checklist | `cum chk create <task_id> "<name>"` | |
| Add checklist item | `cum chk item-add <checklist_id> "<name>"` | pass `--task <task_id>` only if `checklist_id` is a positional index (1, 2, ...) rather than the real ID |
| Resolve checklist item | `cum chk item-update <checklist_id> <item_id> --resolved true` | boolean flag: `true`/`false`/`1`/`0`/`yes`/`no` all parse correctly; anything else is rejected, not silently coerced |
| Task waits on another | `cum tad <task_id> --waiting-on <other_id>` | **not** `--depends-on` — doesn't exist |
| Task blocks another | `cum tad <task_id> --blocking <other_id>` | **not** `--blocks` — doesn't exist |
| Set status | `cum tss <task_id> "<status>"` | status names are **list-specific**; check `cum d <task_id>` first, never assume "in progress" exists. Refuses to complete a task with unresolved checklist items unless `--force` — don't pass `--force` routinely, that check is the point |
| Comment | `cum ca <task_id> "<text>"` | |
| Read a plan | `cum d <parent_id>` | shows description, subtasks, dependencies |
| Current context | `cum show` | which list/task/space is "current" |
