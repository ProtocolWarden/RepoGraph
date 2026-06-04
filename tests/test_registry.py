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


# ---- manifest YAML discovery helpers --------------------------------------


def test_discover_manifest_yaml_finds_by_glob_priority(tmp_path):
    from repograph.registry import discover_manifest_yaml

    root = tmp_path / "M"
    root.mkdir()
    # Both a top-level and a nested candidate exist; glob order prefers the
    # top-level platform_manifest.yaml.
    (root / "platform_manifest.yaml").write_text("repos: []\n", encoding="utf-8")
    nested = root / "manifests"
    nested.mkdir()
    (nested / "other.yaml").write_text("repos: []\n", encoding="utf-8")

    hit = discover_manifest_yaml(root)
    assert hit == root / "platform_manifest.yaml"


def test_discover_manifest_yaml_returns_none_when_absent(tmp_path):
    from repograph.registry import discover_manifest_yaml

    root = tmp_path / "empty"
    root.mkdir()
    assert discover_manifest_yaml(root) is None


def test_discover_all_manifest_yamls_collects_and_dedupes(tmp_path):
    from repograph.registry import discover_all_manifest_yamls

    root = tmp_path / "M"
    nested = root / "manifests"
    nested.mkdir(parents=True)
    (root / "private_manifest.yaml").write_text("repos: []\n", encoding="utf-8")
    (nested / "a.yaml").write_text("repos: []\n", encoding="utf-8")
    (nested / "b.yaml").write_text("repos: []\n", encoding="utf-8")

    found = discover_all_manifest_yamls(root)
    # All three discovered, resolved, no duplicates.
    assert len(found) == len(set(found)) == 3
    names = {p.name for p in found}
    assert names == {"private_manifest.yaml", "a.yaml", "b.yaml"}


def test_iter_yaml_documents_skips_non_mappings(tmp_path):
    from repograph.registry import iter_yaml_documents

    mapping = tmp_path / "ok.yaml"
    mapping.write_text("repos: []\n", encoding="utf-8")
    sequence = tmp_path / "list.yaml"
    sequence.write_text("- a\n- b\n", encoding="utf-8")

    docs = iter_yaml_documents([mapping, sequence])
    assert len(docs) == 1
    path, raw = docs[0]
    assert path == mapping
    assert raw == {"repos": []}


def test_iter_yaml_documents_raises_on_bad_yaml(tmp_path):
    from repograph.registry import iter_yaml_documents

    bad = tmp_path / "bad.yaml"
    bad.write_text("key: : :\n  - broken\n", encoding="utf-8")
    with pytest.raises(RepoGraphConfigError, match="parse error"):
        iter_yaml_documents([bad])


# ----------------------------------------------------------------------
# resolve_private_manifest — the shared private-manifest *role* resolver
# ----------------------------------------------------------------------


def test_resolve_private_manifest_env_override(tmp_path, monkeypatch):
    from repograph.registry import resolve_private_manifest

    privm = tmp_path / "AnyName"
    privm.mkdir()
    monkeypatch.setenv("PRIVATE_MANIFEST_DIR", str(privm))
    assert resolve_private_manifest() == privm.resolve()


def test_resolve_private_manifest_env_bogus_returns_none(tmp_path, monkeypatch):
    from repograph.registry import resolve_private_manifest

    monkeypatch.setenv("PRIVATE_MANIFEST_DIR", str(tmp_path / "missing"))
    assert resolve_private_manifest() is None


def test_resolve_private_manifest_via_registry(registry_env, tmp_path, monkeypatch):
    from repograph.registry import resolve_private_manifest

    monkeypatch.delenv("PRIVATE_MANIFEST_DIR", raising=False)
    pm = tmp_path / "PublicSide"
    _write_public_manifest(pm, "PM", ["pubA"])
    # The private repo's NAME is arbitrary — resolution matches the manifest
    # type filename (private_manifest*), never a repo-instance name.
    privm = tmp_path / "ArbitraryPrivateRepoName"
    _write_private_manifest(privm, "PrivM", ["privA"])
    reg = Registry.load()
    reg.add(pm)
    reg.add(privm)
    reg.save()

    assert resolve_private_manifest() == privm.resolve()


def test_resolve_private_manifest_none_when_no_private(registry_env, tmp_path, monkeypatch):
    from repograph.registry import resolve_private_manifest

    monkeypatch.delenv("PRIVATE_MANIFEST_DIR", raising=False)
    pm = tmp_path / "PublicOnly"
    _write_public_manifest(pm, "PM", ["pubA"])
    reg = Registry.load()
    reg.add(pm)
    reg.save()

    assert resolve_private_manifest() is None


def test_resolve_private_manifest_none_when_registry_missing(registry_env, monkeypatch):
    from repograph.registry import resolve_private_manifest

    monkeypatch.delenv("PRIVATE_MANIFEST_DIR", raising=False)
    # registry_env points at a nonexistent file → empty registry, no private root.
    assert resolve_private_manifest() is None
