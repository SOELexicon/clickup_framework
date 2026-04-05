# Lessons Learned

Real implementation notes that should change how work is done in this repository.

## How To Use This File

- Add a new entry when a bug, API quirk, or workflow failure revealed a reusable pattern.
- Include the failing command, root cause, fix, and the action future work should take.
- Link the related task, command, or file path where the lesson was applied.

## 2025-11-09: Docs API Page Content Requires Per-Page Fetches

- Problem: `get_doc_pages()` returned page metadata, but exported markdown files were empty.
- Root cause: the batch endpoint lists pages only; it does not include full page content.
- Fix: fetch each page again with `get_page(workspace_id, doc_id, page_id)` before export.
- Apply this rule when working with similar ClickUp APIs: list endpoints often return lighter metadata than individual GET endpoints.
- Related files: `clickup_framework/resources/docs.py`, `clickup_framework/commands/doc_commands.py`

## 2025-11-20: Command Discovery Should Not Depend On External Shell Tools

- Problem: command workflows failed because some paths assumed `cum`, `grep`, or shell-specific behavior existed on `PATH`.
- Root cause: command discovery and search paths mixed CLI parsing with external process dependencies.
- Fix: prefer parser-tree introspection and Python fallbacks over shelling out to external commands.
- Apply this rule to any new CLI feature: if the framework already knows its commands internally, do not rediscover them through `subprocess`.
- Related files: `clickup_framework/commands/command_sync.py`, `clickup_framework/commands/search_command.py`

## 2025-11-20: CLI Registration Must Be Verified, Not Assumed

- Problem: commands existed in help or source, but failed at runtime with missing handler errors.
- Root cause: parser registration and `set_defaults(func=...)` drifted out of sync with implementation.
- Fix: add command-level tests that call the registered entrypoint and validate `--help` plus one execution path.
- Apply this rule to new commands and migrations: parser wiring is part of the feature, not follow-up cleanup.
- Related files: `clickup_framework/cli.py`, `tests/test_help_command.py`

## 2025-11-20: Token Errors Need Workspace Context, Not Just Auth Wording

- Problem: task updates failed with `401` or list-access errors even though the token itself was valid.
- Root cause: the active token and workspace/list context did not match the target task's accessible team.
- Fix: troubleshoot with `cum show`, verify the task's actual location, and improve errors so they mention context and access scope.
- Apply this rule before mutating tasks across spaces or workspaces: validate context first, then assume permission failure only if the target is confirmed.
- Related files: `clickup_framework/context.py`, `clickup_framework/client.py`

## 2025-11-20: PowerShell Argument Quoting Can Change CLI Behavior

- Problem: task creation examples that looked correct still failed because argument parsing differed in PowerShell.
- Root cause: shell quoting rules changed how positional task names were passed into argparse.
- Fix: document PowerShell-safe examples and prefer explicit, low-ambiguity argument shapes in help text.
- Apply this rule whenever examples use names or descriptions with spaces: test them in PowerShell, not just bash.
- Related files: `README.md`, `docs/cli/INDEX.md`, `clickup_framework/cli.py`

## 2026-04-05: Command Catalog Links Must Use Canonical Task IDs

- Problem: issue-reporting links could drift or attach to the wrong work item when command matching relied on names alone.
- Root cause: name lookup was weaker than the curated CLI command catalog managed by `command-sync`.
- Fix: store framework list IDs and CLI command task IDs in constants, then link report tasks by canonical command task ID first.
- Apply this rule to new command-related work: use the CLI Commands catalog as the source of truth and fall back to name lookup only when mapping is missing.
- Related files: `clickup_framework/clickup_constants.py`, `clickup_framework/commands/base_command.py`, `clickup_framework/commands/command_sync.py`
