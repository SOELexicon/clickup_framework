"""Tests for Mermaid Live Editor integration in the map command."""

from pathlib import Path
from types import SimpleNamespace

import pytest

from clickup_framework.commands.map_command import _map_command_impl


def _make_args(**overrides):
    args = {
        "install": False,
        "list_themes": False,
        "python": True,
        "csharp": False,
        "all_langs": False,
        "ignore_gitignore": False,
        "mer": "flowchart",
        "output": None,
        "format": None,
        "html": False,
        "trace": False,
        "theme": "dark",
        "live_editor": False,
        "open_live_editor": False,
    }
    args.update(overrides)
    return SimpleNamespace(**args)


def _write_fake_mermaid_diagram(_stats, output_file, theme="dark"):
    Path(output_file).parent.mkdir(parents=True, exist_ok=True)
    Path(output_file).write_text(
        "# Diagram\n\n```mermaid\ngraph TD\n    A --> B\n```\n",
        encoding="utf-8",
    )


def test_map_live_editor_requires_mermaid(monkeypatch, capsys):
    """Live editor flags should require Mermaid diagram generation."""
    args = _make_args(mer=None, live_editor=True)

    with pytest.raises(SystemExit) as excinfo:
        _map_command_impl(args, use_color=False)

    assert excinfo.value.code == 1
    captured = capsys.readouterr()
    assert "--live-editor and --open require --mer" in captured.err


def test_map_live_editor_prints_share_url(monkeypatch, tmp_path, capsys):
    """Map command should print a Mermaid Live Editor URL after diagram generation."""
    monkeypatch.chdir(tmp_path)
    args = _make_args(live_editor=True)

    monkeypatch.setattr("clickup_framework.commands.map_command.get_ctags_executable", lambda: "ctags")
    monkeypatch.setattr("clickup_framework.commands.map_command.generate_ctags", lambda *a, **k: "{}")
    monkeypatch.setattr(
        "clickup_framework.commands.map_command.parse_tags_file",
        lambda *a, **k: {
            "total_symbols": 2,
            "files_analyzed": 1,
            "by_language": {"Python": {"function": 2}},
        },
    )
    monkeypatch.setattr(
        "clickup_framework.commands.map_command.generate_mermaid_flowchart",
        _write_fake_mermaid_diagram,
    )

    _map_command_impl(args, use_color=False)

    captured = capsys.readouterr()
    assert "Mermaid Live Editor: https://mermaid.live/edit#pako:" in captured.out
    assert "Mermaid Live Editor)" in captured.out


def test_map_open_flag_opens_browser(monkeypatch, tmp_path):
    """Open flag should launch the generated Mermaid Live Editor URL."""
    monkeypatch.chdir(tmp_path)
    args = _make_args(live_editor=True, open_live_editor=True)
    opened = {}

    monkeypatch.setattr("clickup_framework.commands.map_command.get_ctags_executable", lambda: "ctags")
    monkeypatch.setattr("clickup_framework.commands.map_command.generate_ctags", lambda *a, **k: "{}")
    monkeypatch.setattr(
        "clickup_framework.commands.map_command.parse_tags_file",
        lambda *a, **k: {
            "total_symbols": 2,
            "files_analyzed": 1,
            "by_language": {"Python": {"function": 2}},
        },
    )
    monkeypatch.setattr(
        "clickup_framework.commands.map_command.generate_mermaid_flowchart",
        _write_fake_mermaid_diagram,
    )
    monkeypatch.setattr(
        "clickup_framework.commands.map_command.webbrowser.open",
        lambda url: opened.setdefault("url", url) or True,
    )

    _map_command_impl(args, use_color=False)

    assert opened["url"].startswith("https://mermaid.live/edit#pako:")
