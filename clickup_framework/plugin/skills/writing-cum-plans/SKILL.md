---
name: writing-cum-plans
description: Use when you have a spec or requirements for a multi-step task and want the plan tracked as a ClickUp task hierarchy instead of local files, before touching code.
---

# Writing cum plans

Turn a spec into a ClickUp task hierarchy the way superpowers'
`writing-plans` turns one into a markdown file. Same rigor — DRY, YAGNI,
TDD, bite-sized steps, no placeholders — different persistence: the plan
is a parent task, its implementation tasks are subtasks, each task's steps
are a checklist, and ordering is a real dependency graph.

**Announce at start:** "I'm using the writing-cum-plans skill to create
the plan in ClickUp."

Nothing is written to a local plan file. The ClickUp hierarchy is the
plan, and its comment thread, checklist state, and task statuses are its
live record — which is why there's no ledger file: `cum d <parent_id>`
survives context loss and compaction because it isn't in session state.

## Procedure

### 1. Resolve the target list

Run `cum show`. If a current list is set, use it. If not, ask the user
which list the plan belongs in — never guess a list ID. Once known, set
it so later commands can use `current`:

```
cum set list <list_id>
```

### 2. Plan the file structure (no cum calls yet)

Exactly as in superpowers' `writing-plans`: before any tasks, map which
files will be created or modified and what each is responsible for. One
clear responsibility per file; files that change together live together;
follow the codebase's existing patterns. This decides the task
boundaries. Do this in your head or in scratch text — it goes into task
descriptions in step 4, not into ClickUp on its own.

### 3. Create the parent task

```
cum tc "<Feature Name>" --list current --description "<description>" -O json
```

The description is the plan header, as markdown (cum renders markdown in
descriptions):

```
**Goal:** <one sentence>

**Architecture:** <2-3 sentences>

**Tech Stack:** <key technologies>

**Spec:** <path or link to the spec this plan implements>

## Global Constraints
- <one line per project-wide requirement, exact values copied from the spec>
```

Use `-O json` so the created task's `id` is machine-readable — read it from
the JSON output file rather than parsing colored console text. Record it:
every later step needs `<parent_id>`.

### 4. Create one subtask per implementation task

Right-size tasks as `writing-plans` does: the smallest unit that carries
its own test cycle and is worth a reviewer's gate. Fold setup/scaffolding/
docs into the task whose deliverable needs them.

```
cum tc "Task N: <Component Name>" --parent <parent_id> --description "<description>" -O json
```

Task description = the Files and Interfaces blocks, as markdown:

```
**Files:**
- Create: `exact/path/to/file.py`
- Modify: `exact/path/to/existing.py:123-145`
- Test: `tests/exact/path/to/test.py`

**Interfaces:**
- Consumes: <what this task uses from earlier tasks — exact signatures>
- Produces: <what later tasks rely on — exact names, parameter and return types>
```

Record each subtask's `id` from the JSON output. Number tasks in the name
(`Task 1:`, `Task 2:`, ...) so `cum d <parent_id>` reads in order even
though execution order is governed by dependencies, not numbering.

### 5. Add each task's steps as a checklist

One checklist per subtask, one item per bite-sized step (2–5 minutes
each). Keep the TDD steps separate items — they are separate gates:

```
cum chk create <subtask_id> "Steps"
cum chk item-add <checklist_id> "Step 1: Write the failing test: <what it asserts>"
cum chk item-add <checklist_id> "Step 2: Run it and confirm it fails: <command> -> <expected failure>"
cum chk item-add <checklist_id> "Step 3: Implement the minimal code: <file, what changes>"
cum chk item-add <checklist_id> "Step 4: Run it and confirm it passes: <command>"
cum chk item-add <checklist_id> "Step 5: Commit: git add <files> && git commit -m '<message>'"
```

`<checklist_id>` is the UUID on the `Checklist ID:` line of `chk create`'s
console output. Read it from there — `chk create` does **not** refresh
`cum_output.json` even with `-O json` (verified live), so the JSON file
still holds the previous `tc` call's task and reading it would hand you a
task ID where a checklist ID belongs. Put the actual content in each item — the test's assertion, the exact command, the
file — not "write tests" or "implement it". A step an engineer with zero
context couldn't act on is a plan failure, same as in `writing-plans`.

Code that a step needs (a test body, a function) goes in the subtask's
description under a `## Code` heading, referenced from the item ("see
`## Code` › Step 1") — checklist items are one line, descriptions are
where the code lives.

### 6. Wire dependencies

For every task that must wait on another:

```
cum tad <task_id> --waiting-on <other_task_id>
```

This is `--waiting-on`, read as "`<task_id>` is waiting on
`<other_task_id>`". There is no `--depends-on`. Only add dependencies that
are real (Task 3 consumes Task 2's interface) — not positional ones (Task 3
comes after Task 2 in the list). Independent tasks get no dependency; that's
what lets them be worked in any order.

### 7. Self-review by reading it back

Do not trust what you just wrote. Read the hierarchy back:

```
cum d <parent_id>
```

and check it against the spec:

1. **Spec coverage:** every spec requirement maps to a subtask. Add any
   missing one.
2. **Placeholder scan:** no checklist item says "TBD", "implement later",
   "add error handling", "write tests", or "similar to Task N". Fix with
   `cum chk item-update <checklist_id> <item_id> --name "<new text>"`.
3. **Interface consistency:** a name defined in one task's Produces block
   matches how a later task's Consumes block uses it. Fix with
   `cum tu <task_id> --description "<corrected>"`.

### 8. Hand off

Report to the user:

> Plan created as ClickUp task `<parent_id>` (`<Feature Name>`, N tasks).
> Use `nutcracker:executing-cum-plans` with that ID to implement it.

## Partial failure

If a `cum tc` fails after the parent (or some subtasks) already exist,
stop and report the parent ID plus which subtasks were created and which
weren't. Do not delete anything — task deletion is destructive and never
done without an explicit ask. The user decides whether to retry the rest
or clean up.
