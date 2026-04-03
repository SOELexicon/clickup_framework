# Repository Guidelines

## Project Structure & Module Organization
`clickup_framework/` is the main package. Put CLI behavior in `clickup_framework/commands/`, API wrappers in `clickup_framework/resources/` and `clickup_framework/apis/`, display logic in `clickup_framework/components/` and `clickup_framework/formatters/`, and shared helpers in `clickup_framework/utils/` or `clickup_framework/git/`. Tests live in `tests/` and generally mirror the package area they cover, for example `tests/components/` and `tests/commands/`. Documentation belongs in `docs/`; automation and maintenance scripts belong in `scripts/`. Generated artifacts under `screenshots/`, `output/`, and `benchmark_output/` should only change when intentionally regenerating them.

## Build, Test, and Development Commands
Use `pip install -e .` to install the package locally and expose `clickup`, `cum`, and `cum-mcp`. Run `python -m clickup_framework --help` or `cum --help` to verify the CLI entry point. Use `./scripts/setup_hooks.sh` to configure `.githooks/` and install development tooling. Run `pre-commit run --all-files` before opening a PR; it applies file checks, Black, Flake8, isort, and the custom tree/help validations. Fast CI-aligned checks are `python -m pytest tests/test_help_command.py -v --tb=short` and `python tests/run_tests.py --coverage-only`. The broader regression suite is `python tests/run_tests.py --verbose --coverage`.

## Coding Style & Naming Conventions
Follow PEP 8 with 4-space indentation, type hints on public functions, and Google-style docstrings. Keep lines near 100 characters; the hooks enforce Black, Flake8, and isort with that target. Use `snake_case` for functions and modules, `PascalCase` for classes, and `UPPER_SNAKE_CASE` for constants. New CLI modules should follow the existing pattern: implement `<name>_command(args)` and `register_command(subparsers)`.

## Testing Guidelines
Prefer `pytest` for new tests even though `tests/run_tests.py` still drives the full suite and coverage reporting. Name files `test_*.py`; for ordered integration-style cases, this repo uses method names like `test_01_create_task`. When changing CLI help, hierarchy rendering, or tree formatting, add or update focused tests because those paths are guarded by commit hooks and CI.

## Commit & Pull Request Guidelines
Recent history uses short imperative summaries and frequent Conventional Commit prefixes. Prefer `feat:`, `fix:`, `docs:`, or `test:` followed by a concise subject. PRs should explain user-visible behavior, list the commands/tests you ran, link the relevant issue or ClickUp task, and include screenshots or sample output for display, HTML export, or diagram changes.

## Security & Configuration Tips
Keep `CLICKUP_API_TOKEN` and other local settings in your environment or untracked `.env` files. Do not commit secrets, personal workspace IDs, or temporary debug output.
