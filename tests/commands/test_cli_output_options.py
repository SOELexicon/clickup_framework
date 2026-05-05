"""Regression tests for shared CLI output options."""

import argparse
import json
from pathlib import Path
from types import SimpleNamespace
from uuid import uuid4

from clickup_framework.commands import discover_commands
from clickup_framework.commands.base_command import BaseCommand
from clickup_framework.commands.utils import add_common_args


class DummyCommand(BaseCommand):
    """Minimal command subclass for exercising BaseCommand output helpers."""

    def _get_context_manager(self):
        return SimpleNamespace(get_ansi_output=lambda: False)

    def _create_client(self):
        return None

    def execute(self):
        return None


def test_add_common_args_keeps_command_owned_short_flags():
    parser = argparse.ArgumentParser()
    parser.add_argument("-c", "--context", type=int, default=3)

    add_common_args(parser)

    args = parser.parse_args(
        ["-c", "8", "--show-comments", "2", "--output", "markdown"]
    )

    assert args.context == 8
    assert args.show_comments == 2
    assert args.output == "markdown"


def test_add_common_args_does_not_reuse_command_output_file_dest():
    parser = argparse.ArgumentParser()
    parser.add_argument("--output-file", dest="output_file")

    add_common_args(parser)

    args = parser.parse_args(["--output-file", "command-owned.txt"])

    assert args.output_file == "command-owned.txt"
    assert not hasattr(args, "common_output_file")


def test_discovered_commands_register_without_common_arg_collisions():
    parser = argparse.ArgumentParser()
    subparsers = parser.add_subparsers(dest="command")

    failures = []
    for module in discover_commands():
        try:
            module.register_command(subparsers)
        except Exception as exc:  # pragma: no cover - failure path reports details.
            failures.append((module.__name__, type(exc).__name__, str(exc)))

    assert failures == []


def _cache_output_path(suffix: str) -> Path:
    output_dir = Path(".cache") / "test_cli_output_options"
    output_dir.mkdir(parents=True, exist_ok=True)
    return output_dir / f"{uuid4().hex}{suffix}"


def test_handle_output_writes_json_to_common_output_file(capsys):
    output_file = _cache_output_path(".json")
    command = DummyCommand(
        argparse.Namespace(output="json", common_output_file=str(output_file))
    )

    try:
        command.handle_output({"id": "task-1", "name": "Example"}, console_output="done")

        assert json.loads(output_file.read_text(encoding="utf-8")) == {
            "id": "task-1",
            "name": "Example",
        }
        captured = capsys.readouterr()
        assert captured.out == "done\n"
        assert "Output written:" in captured.err
    finally:
        output_file.unlink(missing_ok=True)


def test_handle_output_writes_markdown_to_common_output_file(capsys):
    output_file = _cache_output_path(".md")
    command = DummyCommand(
        argparse.Namespace(output="markdown", common_output_file=str(output_file))
    )

    try:
        command.handle_output({"id": "task-1"})

        assert output_file.read_text(encoding="utf-8").startswith("```json")
        captured = capsys.readouterr()
        assert captured.out == ""
        assert "Output written:" in captured.err
    finally:
        output_file.unlink(missing_ok=True)
