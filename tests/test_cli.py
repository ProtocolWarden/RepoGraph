# SPDX-License-Identifier: AGPL-3.0-or-later
# Copyright (C) 2026 ProtocolWarden
"""CLI tests for the ``repograph manifest`` subcommands.

Drives the typer app through ``CliRunner`` so the entrypoint functions
``manifest_add`` / ``manifest_remove`` / ``manifest_list`` / ``manifest_validate``
/ ``manifest_show`` carry real exit-code and output coverage.
"""

from __future__ import annotations

from pathlib import Path

import pytest
import yaml
from typer.testing import CliRunner

from repograph.cli import app

runner = CliRunner()


@pytest.fixture
def registry_env(tmp_path, monkeypatch):
    registry_file = tmp_path / "registry.yaml"
    monkeypatch.setenv("REPOGRAPH_REGISTRY", str(registry_file))
    return registry_file


def _pub_manifest(root: Path, repos: list[str]) -> Path:
    root.mkdir(parents=True, exist_ok=True)
    p = root / "platform_manifest.yaml"
    p.write_text(
        yaml.safe_dump(
            {
                "manifest_kind": "platform",
                "manifest_version": "1.0.0",
                "visibility_scope": "public",
                "repos": [{"name": r} for r in repos],
            }
        ),
        encoding="utf-8",
    )
    return p


def test_add_then_list_then_remove(registry_env, tmp_path):
    pm = tmp_path / "PM"
    _pub_manifest(pm, ["Lib"])

    res = runner.invoke(app, ["manifest", "add", str(pm)])
    assert res.exit_code == 0, res.output
    assert "added" in res.output

    # Adding again is idempotent (not an error).
    res = runner.invoke(app, ["manifest", "add", str(pm)])
    assert res.exit_code == 0
    assert "already registered" in res.output

    res = runner.invoke(app, ["manifest", "list"])
    assert res.exit_code == 0
    assert str(pm.resolve()) in res.output

    res = runner.invoke(app, ["manifest", "remove", str(pm)])
    assert res.exit_code == 0
    assert "removed" in res.output


def test_add_nonexistent_path_errors(registry_env, tmp_path):
    res = runner.invoke(app, ["manifest", "add", str(tmp_path / "ghost")])
    assert res.exit_code == 1
    assert "does not exist" in res.output


def test_remove_unregistered_errors(registry_env, tmp_path):
    res = runner.invoke(app, ["manifest", "remove", str(tmp_path / "ghost")])
    assert res.exit_code == 1
    assert "not registered" in res.output


def test_list_empty_registry(registry_env):
    res = runner.invoke(app, ["manifest", "list"])
    assert res.exit_code == 0
    assert "empty" in res.output


def test_validate_ok(registry_env, tmp_path):
    pm = tmp_path / "PM"
    _pub_manifest(pm, ["Lib"])
    runner.invoke(app, ["manifest", "add", str(pm)])

    res = runner.invoke(app, ["manifest", "validate"])
    assert res.exit_code == 0
    assert "ok" in res.output


def test_show_summary(registry_env, tmp_path):
    pm = tmp_path / "PM"
    _pub_manifest(pm, ["Lib", "App"])
    runner.invoke(app, ["manifest", "add", str(pm)])

    res = runner.invoke(app, ["manifest", "show", str(pm)])
    assert res.exit_code == 0
    assert "visibility_scope: public" in res.output
    assert "Lib" in res.output and "App" in res.output


def test_show_unregistered_errors(registry_env, tmp_path):
    res = runner.invoke(app, ["manifest", "show", str(tmp_path / "ghost")])
    assert res.exit_code == 1
    assert "not registered" in res.output
