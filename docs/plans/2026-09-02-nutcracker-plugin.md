# Nutcracker Plugin Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build `nutcracker`, a Claude Code plugin (inside `clickup_framework/plugin/`) whose skills persist hierarchical task plans as ClickUp task hierarchies via the `cum` CLI instead of local plan files.

**Architecture:** A plugin directory with a manifest, one SessionStart hook that force-loads the routing skill (`using-cum-planning`) into every session, and two workflow skills (`writing-cum-plans`, `executing-cum-plans`) that map superpowers' plan concepts onto ClickUp primitives: parent task = plan, subtask = implementation task, checklist = bite-sized steps, `cum tad --waiting-on` = dependency, `cum tss` (checklist-gated) = completion, `cum ca` comments = progress ledger. A pytest suite validates the manifest, hook output, skill frontmatter, and — critically — that every `cum` command/flag documented in the skills actually exists in the installed CLI.

**Tech Stack:** Markdown skill files (Claude Code skill format, YAML frontmatter), bash (hook script, Git Bash on Windows), JSON (manifest + hooks config), pytest for structural/behavioral tests.

**Spec:** `docs/specs/2026-09-02-nutcracker-plugin-design.md`

## Global Constraints

- Plugin lives at `clickup_framework/plugin/`, is Claude-Code-only — no `.codex-plugin`/`.cursor-plugin`/`.devin-plugin`/`.hermes-plugin`/`.kimi-plugin`/`.opencode`/`.pi` directories.
- Plugin name is exactly `nutcracker`; version `0.1.0`; author name `ClickUp Skills Development Team` (matches `pyproject.toml`).
- Skill directory names are exactly `using-cum-planning`, `writing-cum-plans`, `executing-cum-plans`, and each `SKILL.md`'s frontmatter `name:` must equal its directory name.
- Every skill `description:` must start with `Use when` (Claude Code skill discovery convention, same as every other skill in this environment).
- Every `cum` command shown in a skill must be a real command with real flags. In particular: dependencies are `--waiting-on` / `--blocking` (NOT `--depends-on` / `--blocks`); checklist item resolution is `--resolved true` (a bool flag using `parse_bool_flag`, fixed in commit `e1d1531`); subtasks are `--parent <id>`; status names are list-specific and must be checked with `cum d` before use.
- The hook must always print valid JSON (`{}` at minimum) — it must never emit a non-JSON error that could corrupt session start for other hooks.
- No task deletion anywhere in these skills (destructive, never done without an explicit ask).
- Line length 100, `black`/`flake8` clean for the Python test file, matching the repo's pre-commit config.
- Python tests must pass on Windows via Git Bash (`bash` on PATH) for the hook subprocess test.

---

### Task 1: Plugin manifest and hooks config

**Files:**
- Create: `clickup_framework/plugin/.claude-plugin/plugin.json`
- Create: `clickup_framework/plugin/hooks/hooks.json`
- Test: `tests/test_nutcracker_plugin.py`

**Interfaces:**
- Consumes: nothing.
- Produces: `PLUGIN_ROOT` module-level constant in the test file (`Path(__file__).resolve().parent.parent / "clickup_framework" / "plugin"`) that every later task's tests reuse; `hooks.json` referencing `${CLAUDE_PLUGIN_ROOT}/hooks/session-start.sh`, the exact script path Task 2 must create.

- [ ] **Step 1: Write the failing tests**

Create `tests/test_nutcracker_plugin.py`:

```python
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
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `python -m pytest tests/test_nutcracker_plugin.py -v`
Expected: FAIL — `AssertionError: missing ...plugin.json` and `missing ...hooks.json`.

- [ ] **Step 3: Create the manifest**

Create `clickup_framework/plugin/.claude-plugin/plugin.json`:

```json
{
  "name": "nutcracker",
  "description": "Hierarchical task planning and execution backed by ClickUp via the cum CLI, instead of local plan files",
  "version": "0.1.0",
  "author": {
    "name": "ClickUp Skills Development Team"
  },
  "keywords": [
    "clickup",
    "cum",
    "planning",
    "task-hierarchy",
    "skills"
  ]
}
```

- [ ] **Step 4: Create the hooks config**

Create `clickup_framework/plugin/hooks/hooks.json`:

```json
{
  "hooks": {
    "SessionStart": [
      {
        "matcher": "startup|clear|compact",
        "hooks": [
          {
            "type": "command",
            "command": "\"${CLAUDE_PLUGIN_ROOT}/hooks/session-start.sh\"",
            "shell": "bash",
            "timeout": 15
          }
        ]
      }
    ]
  }
}
```

- [ ] **Step 5: Run tests to verify they pass**

Run: `python -m pytest tests/test_nutcracker_plugin.py -v`
Expected: PASS (4 tests).

- [ ] **Step 6: Commit**

```bash
git add clickup_framework/plugin/.claude-plugin/plugin.json clickup_framework/plugin/hooks/hooks.json tests/test_nutcracker_plugin.py
git commit -m "feat(nutcracker): add plugin manifest and SessionStart hook config"
```

---

### Task 2: SessionStart hook script

**Files:**
- Create: `clickup_framework/plugin/hooks/session-start.sh`
- Modify: `tests/test_nutcracker_plugin.py` (append a test class)

**Interfaces:**
- Consumes: `hooks.json` from Task 1 (the script path it points at). Reads `skills/using-cum-planning/SKILL.md` relative to the plugin root — Task 3 creates that file; until then the script must still emit valid JSON (its error-content fallback), which is exactly what the "missing skill" test asserts.
- Produces: a bash script printing `{"hookSpecificOutput": {"hookEventName": "SessionStart", "additionalContext": "<banner + skill content>"}}`.

- [ ] **Step 1: Write the failing tests**

Append to `tests/test_nutcracker_plugin.py` (before the `if __name__` block):

```python
def _run_hook(plugin_root: Path) -> dict:
    """Run the SessionStart hook script via bash and parse its JSON output."""
    script = plugin_root / "hooks" / "session-start.sh"
    result = subprocess.run(
        ["bash", str(script)],
        input="{}",
        capture_output=True,
        text=True,
        encoding="utf-8",
        timeout=30,
    )
    return json.loads(result.stdout)


class TestSessionStartHook(unittest.TestCase):
    def test_hook_script_exists(self):
        self.assertTrue((PLUGIN_ROOT / "hooks" / "session-start.sh").exists())

    def test_emits_hook_json_with_skill_content(self):
        output = _run_hook(PLUGIN_ROOT)
        hook_out = output["hookSpecificOutput"]
        self.assertEqual(hook_out["hookEventName"], "SessionStart")
        context = hook_out["additionalContext"]
        self.assertIn("nutcracker", context)
        # The routing skill's own name must be present -- that's the point of
        # force-loading it. If the skill file is missing, the fallback error
        # text lands here instead and this assertion catches it.
        self.assertIn("using-cum-planning", context)

    def test_degrades_to_valid_json_when_skill_missing(self):
        import tempfile

        with tempfile.TemporaryDirectory() as tmp:
            fake_root = Path(tmp)
            (fake_root / "hooks").mkdir()
            shutil.copy(PLUGIN_ROOT / "hooks" / "session-start.sh", fake_root / "hooks")
            # No skills/ directory at all -- the script must still print JSON.
            output = _run_hook(fake_root)
        self.assertIn("hookSpecificOutput", output)
        self.assertIn("Error reading", output["hookSpecificOutput"]["additionalContext"])
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `python -m pytest tests/test_nutcracker_plugin.py::TestSessionStartHook -v`
Expected: FAIL — `test_hook_script_exists` fails on the missing file; the other two fail because `bash` can't open the script.

- [ ] **Step 3: Write the hook script**

Create `clickup_framework/plugin/hooks/session-start.sh`:

```bash
#!/usr/bin/env bash
# SessionStart hook for the nutcracker plugin.
#
# Force-loads the using-cum-planning routing skill into every session's
# context, the same way superpowers force-loads using-superpowers. Adapted
# from superpowers' hooks/session-start (Claude Code output shape only --
# nutcracker doesn't ship the Cursor/Copilot branches superpowers carries).

set -euo pipefail

# Resolve the plugin root from this script's own location rather than
# trusting CLAUDE_PLUGIN_ROOT -- works the same whether invoked by the hook
# runner or by hand in a test.
SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
PLUGIN_ROOT="$(cd "${SCRIPT_DIR}/.." && pwd)"

# A missing/unreadable skill file must NOT break session start: fall back to
# an error string that still gets wrapped in valid JSON below.
skill_content=$(cat "${PLUGIN_ROOT}/skills/using-cum-planning/SKILL.md" 2>&1 || echo "Error reading using-cum-planning skill")

# Escape for embedding in a JSON string. Each ${s//old/new} is one pass.
escape_for_json() {
    local s="$1"
    s="${s//\\/\\\\}"
    s="${s//\"/\\\"}"
    s="${s//$'\n'/\\n}"
    s="${s//$'\r'/\\r}"
    s="${s//$'\t'/\\t}"
    printf '%s' "$s"
}

escaped=$(escape_for_json "$skill_content")
context="<IMPORTANT>\nYou have nutcracker: hierarchical task planning backed by ClickUp via the cum CLI.\n\n**Below is the full content of your 'nutcracker:using-cum-planning' skill. For all other nutcracker skills, use the Skill tool:**\n\n${escaped}\n</IMPORTANT>"

# printf with %s keeps any '%' in the content literal (it's an argument, not
# part of the format string). Avoids a heredoc, which hangs on bash 5.3+.
printf '{\n  "hookSpecificOutput": {\n    "hookEventName": "SessionStart",\n    "additionalContext": "%s"\n  }\n}\n' "$context"

exit 0
```

- [ ] **Step 4: Make the script executable and pipe-test it by hand**

Run: `chmod +x clickup_framework/plugin/hooks/session-start.sh && echo '{}' | bash clickup_framework/plugin/hooks/session-start.sh`
Expected: a JSON object whose `additionalContext` contains `Error reading using-cum-planning skill` (the skill doesn't exist yet — that's correct for now).

- [ ] **Step 5: Run tests to verify the expected state**

Run: `python -m pytest tests/test_nutcracker_plugin.py::TestSessionStartHook -v`
Expected: `test_hook_script_exists` PASS, `test_degrades_to_valid_json_when_skill_missing` PASS, `test_emits_hook_json_with_skill_content` FAIL (asserts `using-cum-planning` in the content, which is only true once Task 3 creates the skill — leave it red; Task 3 turns it green).

- [ ] **Step 6: Commit**

```bash
git add clickup_framework/plugin/hooks/session-start.sh tests/test_nutcracker_plugin.py
git commit -m "feat(nutcracker): add SessionStart hook script that force-loads using-cum-planning"
```

---

### Task 3: `using-cum-planning` routing skill

**Files:**
- Create: `clickup_framework/plugin/skills/using-cum-planning/SKILL.md`
- Modify: `tests/test_nutcracker_plugin.py` (append a frontmatter test class and the cum-correctness test)

**Interfaces:**
- Consumes: Task 2's hook (which reads this exact file path).
- Produces: the routing skill every session sees. Its correct-usage table is the canonical list that the `TestCumCommandsAreReal` test parses — Tasks 4 and 5 must use only commands/flags that appear in this table (or add to it), so the test keeps the whole plugin honest.

- [ ] **Step 1: Write the failing tests**

Append to `tests/test_nutcracker_plugin.py` (before the `if __name__` block):

```python
def _read_frontmatter(skill_md: Path) -> dict:
    """Parse the YAML-ish frontmatter block (name/description only) of a SKILL.md."""
    text = skill_md.read_text(encoding="utf-8")
    match = re.match(r"^---\n(.*?)\n---\n", text, re.DOTALL)
    assert match, f"no frontmatter block in {skill_md}"
    fields = {}
    for line in match.group(1).splitlines():
        if ":" in line:
            key, _, value = line.partition(":")
            fields[key.strip()] = value.strip()
    return fields


class TestSkillFrontmatter(unittest.TestCase):
    def test_every_skill_has_valid_frontmatter(self):
        for name in SKILL_NAMES:
            with self.subTest(skill=name):
                skill_md = PLUGIN_ROOT / "skills" / name / "SKILL.md"
                self.assertTrue(skill_md.exists(), f"missing {skill_md}")
                fm = _read_frontmatter(skill_md)
                self.assertEqual(fm["name"], name)
                self.assertTrue(
                    fm["description"].startswith("Use when"),
                    f"{name} description must start with 'Use when': {fm['description']!r}",
                )


# Each row: (cum subcommand argv, [flags that must appear in its --help]).
# This is the mechanical form of the "ensure correct usage" requirement: if a
# skill documents a command or flag that the installed cum doesn't have, this
# test fails rather than the skill silently teaching a wrong command.
CUM_COMMANDS_DOCUMENTED = [
    (["tc"], ["--list", "--parent", "--description"]),
    (["chk", "create"], []),
    (["chk", "item-add"], ["--task"]),
    (["chk", "item-update"], ["--resolved", "--task"]),
    (["tad"], ["--waiting-on", "--blocking"]),
    (["tss"], ["--force"]),
    (["ca"], []),
    (["d"], []),
    (["show"], []),
]

CUM_FLAGS_THAT_MUST_NOT_EXIST = [
    (["tad"], ["--depends-on", "--blocks"]),
]


@unittest.skipIf(shutil.which("cum") is None, "cum not on PATH")
class TestCumCommandsAreReal(unittest.TestCase):
    def _help(self, argv):
        result = subprocess.run(
            ["cum", *argv, "--help"],
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="replace",
            timeout=30,
        )
        self.assertEqual(result.returncode, 0, f"cum {' '.join(argv)} --help failed:\n{result.stderr}")
        return result.stdout

    def test_documented_commands_and_flags_exist(self):
        for argv, flags in CUM_COMMANDS_DOCUMENTED:
            with self.subTest(command=" ".join(argv)):
                help_text = self._help(argv)
                for flag in flags:
                    self.assertIn(flag, help_text, f"cum {' '.join(argv)} lacks {flag}")

    def test_known_wrong_flags_do_not_exist(self):
        for argv, flags in CUM_FLAGS_THAT_MUST_NOT_EXIST:
            with self.subTest(command=" ".join(argv)):
                help_text = self._help(argv)
                for flag in flags:
                    self.assertNotIn(flag, help_text, f"cum {' '.join(argv)} unexpectedly has {flag}")
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `python -m pytest tests/test_nutcracker_plugin.py::TestSkillFrontmatter -v`
Expected: FAIL — `missing .../using-cum-planning/SKILL.md` (and the other two skills, also not yet created).

Run: `python -m pytest tests/test_nutcracker_plugin.py::TestCumCommandsAreReal -v`
Expected: PASS already — these test the installed `cum`, not the plugin, and are here to pin the truth the skill is written against. If any fail here, `cum` has changed and the skill text below must be corrected before writing it.

- [ ] **Step 3: Write the skill**

Create `clickup_framework/plugin/skills/using-cum-planning/SKILL.md`:

````markdown
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
````

- [ ] **Step 4: Run the tests**

Run: `python -m pytest tests/test_nutcracker_plugin.py -v`
Expected: `TestSessionStartHook::test_emits_hook_json_with_skill_content` now PASS (the hook picks up the real skill); `TestSkillFrontmatter` still FAIL for `writing-cum-plans` and `executing-cum-plans` (Tasks 4–5); everything else PASS.

- [ ] **Step 5: Commit**

```bash
git add clickup_framework/plugin/skills/using-cum-planning/SKILL.md tests/test_nutcracker_plugin.py
git commit -m "feat(nutcracker): add using-cum-planning routing skill with verified cum reference"
```

---

### Task 4: `writing-cum-plans` skill

**Files:**
- Create: `clickup_framework/plugin/skills/writing-cum-plans/SKILL.md`

**Interfaces:**
- Consumes: only commands listed in Task 3's verified reference table.
- Produces: a skill whose output contract is a **parent task ID** reported to the user, which `executing-cum-plans` (Task 5) takes as its input.

- [ ] **Step 1: Confirm the failing test**

Run: `python -m pytest tests/test_nutcracker_plugin.py::TestSkillFrontmatter -v`
Expected: FAIL on `skill=writing-cum-plans` — `missing .../writing-cum-plans/SKILL.md`.

- [ ] **Step 2: Write the skill**

Create `clickup_framework/plugin/skills/writing-cum-plans/SKILL.md`:

````markdown
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
cum chk create <subtask_id> "Steps" -O json
cum chk item-add <checklist_id> "Step 1: Write the failing test: <what it asserts>"
cum chk item-add <checklist_id> "Step 2: Run it and confirm it fails: <command> -> <expected failure>"
cum chk item-add <checklist_id> "Step 3: Implement the minimal code: <file, what changes>"
cum chk item-add <checklist_id> "Step 4: Run it and confirm it passes: <command>"
cum chk item-add <checklist_id> "Step 5: Commit: git add <files> && git commit -m '<message>'"
```

`<checklist_id>` is the real ID from the `chk create` JSON output. Put the
actual content in each item — the test's assertion, the exact command, the
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
````

- [ ] **Step 3: Verify every command in the skill is in the pinned reference**

Every `cum` invocation in the file above uses only `tc`, `chk create`, `chk item-add`, `chk item-update`, `tad`, `tu`, `d`, `show`, `set`. `tu` and `set` aren't in Task 3's `CUM_COMMANDS_DOCUMENTED` list yet — add them so the test pins them too. Edit `tests/test_nutcracker_plugin.py`, in `CUM_COMMANDS_DOCUMENTED`, add:

```python
    (["tu"], ["--description", "--name"]),
    (["set"], []),
```

- [ ] **Step 4: Run the tests**

Run: `python -m pytest tests/test_nutcracker_plugin.py -v`
Expected: `TestSkillFrontmatter` now FAIL only on `executing-cum-plans`; `TestCumCommandsAreReal` PASS including the two new rows; everything else PASS.

- [ ] **Step 5: Commit**

```bash
git add clickup_framework/plugin/skills/writing-cum-plans/SKILL.md tests/test_nutcracker_plugin.py
git commit -m "feat(nutcracker): add writing-cum-plans skill"
```

---

### Task 5: `executing-cum-plans` skill

**Files:**
- Create: `clickup_framework/plugin/skills/executing-cum-plans/SKILL.md`

**Interfaces:**
- Consumes: a parent task ID produced by `writing-cum-plans` (Task 4); only commands from Task 3's reference table.
- Produces: the completed hierarchy (all subtasks and the parent at "complete").

- [ ] **Step 1: Confirm the failing test**

Run: `python -m pytest tests/test_nutcracker_plugin.py::TestSkillFrontmatter -v`
Expected: FAIL on `skill=executing-cum-plans` only.

- [ ] **Step 2: Write the skill**

Create `clickup_framework/plugin/skills/executing-cum-plans/SKILL.md`:

````markdown
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
````

- [ ] **Step 3: Verify every command is pinned**

`chk list` is used above and isn't in `CUM_COMMANDS_DOCUMENTED`. Edit `tests/test_nutcracker_plugin.py`, in `CUM_COMMANDS_DOCUMENTED`, add:

```python
    (["chk", "list"], []),
```

- [ ] **Step 4: Run the full suite**

Run: `python -m pytest tests/test_nutcracker_plugin.py -v`
Expected: all PASS (`TestSkillFrontmatter` now green for all three skills).

- [ ] **Step 5: Lint the test file**

Run: `python -m black --line-length=100 tests/test_nutcracker_plugin.py && python -m flake8 --max-line-length=100 --extend-ignore=E203,W503 tests/test_nutcracker_plugin.py`
Expected: black reports the file formatted (or unchanged); flake8 prints nothing.

If black reformats anything, re-run the suite to confirm it's still green before committing.

- [ ] **Step 6: Commit**

```bash
git add clickup_framework/plugin/skills/executing-cum-plans/SKILL.md tests/test_nutcracker_plugin.py
git commit -m "feat(nutcracker): add executing-cum-plans skill"
```

---

### Task 6: Install docs and README pointer

**Files:**
- Create: `clickup_framework/plugin/README.md`
- Modify: `README.md` (insert a `## Plugins` section before the existing `## License` heading at line ~1241)

**Interfaces:**
- Consumes: the finished plugin from Tasks 1–5.
- Produces: documented manual install steps (the spec's install requirement — `cum install-skill` does not install plugins, so this is documentation, not code).

- [ ] **Step 1: Write the plugin README**

Create `clickup_framework/plugin/README.md`:

````markdown
# nutcracker

Hierarchical task planning and execution for Claude Code, backed by
ClickUp via the `cum` CLI instead of local plan files.

Modeled on the `superpowers` plugin's `writing-plans` / `executing-plans`
pair. Where those write a markdown plan and tick checkboxes, nutcracker
creates a ClickUp task hierarchy — a parent task per plan, a subtask per
implementation task, a checklist per task's steps, real dependencies
(`cum tad --waiting-on`) — and tracks progress there. `cum d <parent_id>`
is the plan, and it survives context loss and compaction because it isn't
in session state.

## Skills

- `using-cum-planning` — force-loaded into every session by the
  SessionStart hook; routes you to the other two and carries a verified
  `cum` command reference.
- `writing-cum-plans` — spec → ClickUp hierarchy.
- `executing-cum-plans` — ClickUp hierarchy → working, committed code.

## Requirements

- `cum` on PATH and authenticated (`pip install -e .` from the
  clickup_framework repo root, then set `CLICKUP_API_TOKEN` or run
  `cum set token <token>`).
- Claude Code.

## Install

This is a plugin, not a standalone skill, so `cum install-skill` doesn't
install it. Copy the plugin directory into your Claude plugins directory:

```bash
cp -r clickup_framework/plugin ~/.claude/plugins/nutcracker
```

then enable it in `~/.claude/settings.json`:

```json
{
  "enabledPlugins": {
    "nutcracker": true
  }
}
```

Start a new session (or run `/hooks` once) so the SessionStart hook is
picked up. You'll see a `You have nutcracker` banner in context.

## Verify

From the clickup_framework repo root:

```bash
python -m pytest tests/test_nutcracker_plugin.py -v
```

This checks the manifest, the hook's JSON output, each skill's
frontmatter, and — the important one — that every `cum` command the
skills document actually exists in your installed `cum`.

## Turning it off

Disable in `settings.json` (`"nutcracker": false`) or remove the
directory. The hook only surfaces a routing skill; it never calls `cum`
or touches ClickUp on its own.
````

- [ ] **Step 2: Add the README pointer**

Edit the root `README.md`: immediately before the line `## License`, insert:

```markdown
## Plugins

- **nutcracker** (`clickup_framework/plugin/`) — hierarchical task planning
  and execution for Claude Code, backed by ClickUp via `cum` instead of local
  plan files. See `clickup_framework/plugin/README.md` for install steps.

```

- [ ] **Step 3: Verify the README edit didn't break anything**

Run: `grep -n "^## Plugins" README.md && grep -n "^## License" README.md`
Expected: both headings print, `## Plugins` on a lower line number than `## License`.

- [ ] **Step 4: Commit**

```bash
git add clickup_framework/plugin/README.md README.md
git commit -m "docs(nutcracker): add plugin README with install steps and root README pointer"
```

---

### Task 7: End-to-end verification against a real ClickUp list

**Files:**
- None created. This task verifies the finished plugin behaves as the spec's mapping table says, by running its own skills' commands against a throwaway ClickUp hierarchy.

**Interfaces:**
- Consumes: everything from Tasks 1–6 and an authenticated `cum`.
- Produces: confidence, and a cleaned-up workspace.

- [ ] **Step 1: Pipe-test the hook from its final location**

Run: `echo '{}' | bash clickup_framework/plugin/hooks/session-start.sh | python -c "import json,sys; d=json.load(sys.stdin); c=d['hookSpecificOutput']['additionalContext']; assert 'using-cum-planning' in c and '--waiting-on' in c; print('hook OK')"`
Expected: `hook OK`.

- [ ] **Step 2: Create a throwaway plan hierarchy exactly as `writing-cum-plans` prescribes**

Run, capturing the IDs printed by each `-O json` call from `cum_output.json`:

```bash
cum tc "nutcracker e2e smoke plan" --list current --description "**Goal:** verify nutcracker mapping. **Spec:** docs/specs/2026-09-02-nutcracker-plugin-design.md" -O json
# note parent id -> PARENT
cum tc "Task 1: first" --parent PARENT --description "**Files:** none. **Produces:** nothing." -O json
# note -> T1
cum tc "Task 2: second" --parent PARENT --description "**Files:** none. **Consumes:** Task 1." -O json
# note -> T2
cum chk create T1 "Steps" -O json
# note checklist id -> C1
cum chk item-add C1 "Step 1: do the thing"
cum chk item-add C1 "Step 2: commit"
cum tad T2 --waiting-on T1
```

Expected: every command succeeds; `cum tad` reports the dependency added.

- [ ] **Step 3: Read it back and confirm the mapping**

Run: `cum d PARENT`
Expected: description shows the Goal/Spec markdown; both subtasks listed; `Task 2: second` shows it is waiting on `Task 1: first`.

- [ ] **Step 4: Exercise the completion gate exactly as `executing-cum-plans` prescribes**

Run: `cum tss T1 "complete"`
Expected: **refused** — the checklist has two unresolved items. This is the gate the design relies on; confirm it actually fires.

Run: `cum chk list T1` to get the two item IDs, then resolve both:

```bash
cum chk item-update C1 <item1_id> --resolved true
cum chk item-update C1 <item2_id> --resolved true
cum tss T1 "complete"
```

Expected: both resolves succeed; `tss` now succeeds. Confirm with `cum d T1` that status is complete and the checklist shows 2/2 resolved.

- [ ] **Step 5: Confirm the dependency unblocked Task 2**

Run: `cum d PARENT`
Expected: `Task 1` complete; `Task 2` no longer blocked.

- [ ] **Step 6: Clean up the throwaway hierarchy**

This is the one place deletion is correct — these are test artifacts this task created, never real plan data. Delete the subtasks then the parent:

```bash
cum td T2 --force
cum td T1 --force
cum td PARENT --force
```

Run: `cum d PARENT`
Expected: not found.

- [ ] **Step 7: Full test suite, one last time**

Run: `python -m pytest tests/test_nutcracker_plugin.py tests/test_help_command.py -v`
Expected: all PASS.

- [ ] **Step 8: Commit (nothing to add — confirm the tree is clean)**

Run: `git status --short`
Expected: empty. No commit needed; this task produced no files. If `cum_output.json` was left behind by the `-O json` calls, delete it (`rm -f cum_output.json`) — it's a scratch artifact, not part of the plugin.
