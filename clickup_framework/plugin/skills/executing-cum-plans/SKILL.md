---
name: executing-cum-plans
description: Use when you have a ClickUp task hierarchy created by writing-cum-plans and need to implement it task-by-task, tracking progress in ClickUp rather than a local plan file.
---

# Executing cum plans

Load a plan from ClickUp, review it critically, work its tasks in
dependency order, keep ClickUp updated as the single record of progress,
report when done. The mirror of superpowers' `executing-plans`, with
`cum d` in place of reading a plan file and ClickUp state in place of
checkboxes and a ledger.

**Announce at start:** "I'm using the executing-cum-plans skill to
implement plan `<parent_id>`."

**Isolation first:** work in an isolated workspace — use
`superpowers:using-git-worktrees` or the harness's worktree tool. Never
start implementation on main/master without the user's explicit consent.

## Procedure

### 1. Load and review

```
cum d <parent_id>
```

Read the parent description (goal, architecture, global constraints — the
spec it names is the binding authority) and every subtask. Review
critically: gaps, contradictions, an interface consumed by one task that
no earlier task produces. Raise concerns with the user **before** starting.
If none, create a local todo per subtask (`TaskCreate`) so this session
has a visible worklist — the todos are a convenience; ClickUp is the
record.

### 2. Find ready work

`cum d <parent_id>` shows each subtask's dependencies; a subtask whose
`--waiting-on` tasks are all complete is ready. Work ready tasks only. If
every remaining subtask is blocked, that is a plan defect (a dependency
cycle, or a dependency on a task that doesn't exist) — stop and ask,
don't work an out-of-order task to route around it.

### 3. Work a task

Read its description and checklist:

```
cum d <subtask_id>
cum chk list <subtask_id>
```

Mark it started. Status names are list-specific: `cum d` shows what this
list has. Use "in progress" only if it exists; many lists have only
"to do"/"complete", in which case leave the status alone and record the
start as a comment instead:

```
cum tss <subtask_id> "in progress"      # only if the list has it
cum ca <subtask_id> "Starting work."     # always fine
```

Then follow each checklist item exactly, in order. The moment an item is
done — the test written, the command run and its expected result seen,
the commit made — resolve it:

```
cum chk item-update <checklist_id> <item_id> --resolved true
```

Resolve items as you go, not in a batch at the end. The checklist state
is the progress record; a batch at the end is a record that lies during
the whole task.

### 4. Complete the task

```
cum tss <subtask_id> "complete"
```

This refuses if any checklist item is unresolved. That refusal is a
correctness signal — an item you forgot, or one you skipped — not an
obstacle. Go back and finish or resolve it. Do not pass `--force`.

Anything worth a human seeing that isn't a checklist item — a deviation
from the plan, a decision you made, a blocker you hit and how you got
past it — goes on the task as a comment:

```
cum ca <subtask_id> "<what happened and why>"
```

This is the ledger. It survives compaction and it's visible in ClickUp to
people who never see this session.

### 5. Repeat, then finish

Back to step 2 until no subtasks remain. Then complete the parent:

```
cum tss <parent_id> "complete"
```

and report the parent ID to the user as the record of what was built.
Hand off to `superpowers:finishing-a-development-branch` (if present) for
the merge/PR decision — nutcracker doesn't make that call.

## When to stop and ask

Stop immediately — don't guess, don't route around — when:

- a blocker appears (missing dependency, a test that fails repeatedly, an
  instruction you don't understand)
- the plan has a gap that prevents starting a task
- `cum d` reports every remaining subtask blocked
- a checklist item's expected result doesn't match what you observe

Record what you hit as a comment on the task before asking, so the
question and its context are in ClickUp, not only in this session.

## Never

- Never `--force` a status change past unresolved checklist items.
- Never delete a task or checklist. Destructive; never without an
  explicit ask.
- Never mark an item resolved you didn't actually do.
