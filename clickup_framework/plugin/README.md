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
