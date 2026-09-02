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

```bash
cum install-plugin --enable
```

Copies this directory into `~/.claude/plugins/nutcracker` and sets
`enabledPlugins.nutcracker` to `true` in `~/.claude/settings.json`. Run
`cum install-plugin` without `--enable` to copy the files only and wire
`enabledPlugins` yourself; add `--force` to reinstall over an existing
copy (the previous install is backed up to `~/.claude/plugin-backups/`);
`--target-dir` installs into a project's `.claude/` instead of the user
profile.

Equivalent manual steps, if you'd rather not use the CLI:

```bash
cp -r clickup_framework/plugin ~/.claude/plugins/nutcracker
```

```json
{
  "enabledPlugins": {
    "nutcracker": true
  }
}
```

Either way, start a new session (or run `/hooks` once) so the
SessionStart hook is picked up. You'll see a `You have nutcracker`
banner in context.

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
