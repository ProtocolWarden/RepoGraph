# SPDX-License-Identifier: AGPL-3.0-or-later
"""Registry CLI + persistence tests."""

from __future__ import annotations

from pathlib import Path

import pytest
import yaml
from typer.testing import CliRunner

from repograph import RepoGraphConfigError
from repograph.cli import app
from repograph.registry import Registry, default_registry_path


runner = CliRunner()


def _write_public_manifest(root: Path, name: str, repos: list[str]) -> Path:
    root.mkdir(parents=True, exist_ok=True)
    doc = {
        "manifest_kind": "platform",
        "manifest_version": "1.0.0",
        "visibility_scope": "public",
        "repos": [{"name": r} for r in repos],
    }
    p = root / "platform_manifest.yaml"
    p.write_text(yaml.safe_dump(doc), encoding="utf-8")
    return p


def _write_private_manifest(
    root: Path,
    name: str,
    repos: list[str],
    also_hosts: list[dict] | None = None,
) -> Path:
    root.mkdir(parents=True, exist_ok=True)
    doc = {
        "manifest_kind": "private",
        "manifest_version": "1.0.0",
        "visibility_scope": "private",
        "repos": [{"name": r} for r in repos],
    }
    if also_hosts:
        doc["also_hosts"] = also_hosts
    p = root / "private_manifest.yaml"
    p.write_text(yaml.safe_dump(doc), encoding="utf-8")
    return p


@pytest.fixture
def registry_env(tmp_path, monkeypatch):
    registry_file = tmp_path / "registry.yaml"
    monkeypatch.setenv("REPOGRAPH_REGISTRY", str(registry_file))
    return registry_file


def test_default_registry_path_honors_override(registry_env):
    assert default_registry_path() == registry_env.resolve()


def test_registry_add_list_remove_roundtrip(registry_env, tmp_path):
    pm = tmp_path / "PM"
    _write_public_manifest(pm, "PM", ["repoA"])
    result = runner.invoke(app, ["manifest", "add", str(pm)])
    assert result.exit_code == 0, result.output

    listing = runner.invoke(app, ["manifest", "list"])
    assert listing.exit_code == 0
    assert str(pm.resolve()) in listing.output

    rm = runner.invoke(app, ["manifest", "remove", str(pm)])
    assert rm.exit_code == 0

    listing2 = runner.invoke(app, ["manifest", "list"])
    assert "(empty)" in listing2.output


def test_registry_validate_ok(registry_env, tmp_path):
    pm = tmp_path / "PM"
    privm = tmp_path / "PrivM"
    _write_public_manifest(pm, "PM", ["pubA"])
    _write_private_manifest(privm, "PrivM", ["privA"])
    Registry.load().add(pm)
    Registry.load().add(privm)

    result = runner.invoke(app, ["manifest", "validate"])
    assert result.exit_code == 0, result.output
    assert "ok:" in result.output


def test_registry_validate_dual_claim_fatal(registry_env, tmp_path):
    pm = tmp_path / "PM"
    privm = tmp_path / "PrivM"
    _write_public_manifest(pm, "PM", ["shared"])
    _write_private_manifest(privm, "PrivM", ["shared"])
    Registry.load().add(pm)
    Registry.load().add(privm)

    result = runner.invoke(app, ["manifest", "validate"])
    assert result.exit_code == 1
    assert "shared" in (result.stderr or result.output) or "shared" in result.output


def test_registry_show(registry_env, tmp_path):
    pm = tmp_path / "PM"
    _write_public_manifest(pm, "PM", ["a", "b"])
    Registry.load().add(pm)
    result = runner.invoke(app, ["manifest", "show", str(pm)])
    assert result.exit_code == 0
    assert "visibility_scope: public" in result.output
    assert "- a" in result.output and "- b" in result.output


def test_registry_remove_nonexistent_errors(registry_env, tmp_path):
    pm = tmp_path / "PM"
    pm.mkdir()
    result = runner.invoke(app, ["manifest", "remove", str(pm)])
    assert result.exit_code == 1


def test_registry_add_missing_path_errors(registry_env, tmp_path):
    result = runner.invoke(app, ["manifest", "add", str(tmp_path / "ghost")])
    assert result.exit_code == 1
