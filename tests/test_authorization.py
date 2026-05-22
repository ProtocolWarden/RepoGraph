# SPDX-License-Identifier: AGPL-3.0-or-later
"""Authorization-view + RepoGraph anchor-host tests (P2.3 / P2.5 / P2.7)."""

from __future__ import annotations

from pathlib import Path

import pytest
import yaml

from repograph import (
    AmbiguousAnchorError,
    Registry,
    RepoGraph,
    RepoGraphConfigError,
    build_authorization_view,
)


# ---- fixture helpers ------------------------------------------------------


def _pub(root: Path, repos: list[str]) -> Path:
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


def _priv(
    root: Path,
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
def tmp_registry(tmp_path, monkeypatch):
    registry_file = tmp_path / "registry.yaml"
    monkeypatch.setenv("REPOGRAPH_REGISTRY", str(registry_file))
    return registry_file


# ---- clause-by-clause ----------------------------------------------------


def test_clause_1_anchor_owns_repo(tmp_registry, tmp_path):
    pm = tmp_path / "PM"
    _pub(pm, ["OperatorConsole"])
    Registry.load().add(pm)

    g = RepoGraph()
    ok, reason = g.can_anchor_host(pm, "OperatorConsole")
    assert ok, reason
    assert "owns" in reason


def test_clause_2_public_repo_universally_visible(tmp_registry, tmp_path):
    pm = tmp_path / "PM"
    privm = tmp_path / "PrivM"
    _pub(pm, ["PublicLib"])
    _priv(privm, ["privA"])
    Registry.load().add(pm)
    Registry.load().add(privm)

    ok, reason = RepoGraph().can_anchor_host(privm, "PublicLib")
    assert ok, reason
    assert "public manifest" in reason


def test_clause_3_explicit_also_hosts_grant(tmp_registry, tmp_path):
    foo = tmp_path / "PrivFoo"
    bar = tmp_path / "PrivBar"
    _priv(bar, ["shared-component"])
    _priv(
        foo,
        ["foo-internal"],
        also_hosts=[{"manifest": "PrivBar", "repos": ["shared-component"]}],
    )
    Registry.load().add(foo)
    Registry.load().add(bar)

    ok, reason = RepoGraph().can_anchor_host(foo, "shared-component")
    assert ok, reason
    assert "also_hosts" in reason


def test_blocked_cross_private_without_grant(tmp_registry, tmp_path):
    foo = tmp_path / "PrivFoo"
    bar = tmp_path / "PrivBar"
    _priv(bar, ["bar-only"])
    _priv(foo, ["foo-only"])
    Registry.load().add(foo)
    Registry.load().add(bar)

    ok, reason = RepoGraph().can_anchor_host(foo, "bar-only")
    assert not ok
    assert "PrivBar" in reason


def test_blocked_unknown_anchor(tmp_registry, tmp_path):
    pm = tmp_path / "PM"
    _pub(pm, ["X"])
    Registry.load().add(pm)

    ok, reason = RepoGraph().can_anchor_host(tmp_path / "Unregistered", "X")
    assert not ok
    assert "not registered" in reason


def test_blocked_unregistered_repo(tmp_registry, tmp_path):
    pm = tmp_path / "PM"
    _pub(pm, ["X"])
    Registry.load().add(pm)

    ok, reason = RepoGraph().can_anchor_host(pm, "MysteryRepo")
    assert not ok
    assert "not registered in any manifest" in reason


# ---- load-time validations -----------------------------------------------


def test_dual_claim_fatal(tmp_registry, tmp_path):
    pm = tmp_path / "PM"
    privm = tmp_path / "PrivM"
    _pub(pm, ["shared"])
    _priv(privm, ["shared"])
    Registry.load().add(pm)
    Registry.load().add(privm)

    with pytest.raises(RepoGraphConfigError, match="shared"):
        RepoGraph().can_anchor_host(pm, "shared")


def test_bad_also_hosts_ref_fatal(tmp_registry, tmp_path):
    foo = tmp_path / "PrivFoo"
    _priv(
        foo,
        ["foo"],
        also_hosts=[{"manifest": "Ghost", "repos": ["x"]}],
    )
    Registry.load().add(foo)

    with pytest.raises(RepoGraphConfigError, match="Ghost"):
        RepoGraph().can_anchor_host(foo, "foo")


def test_redundant_also_hosts_warns_but_passes(tmp_registry, tmp_path):
    pm = tmp_path / "PM"
    foo = tmp_path / "PrivFoo"
    _pub(pm, ["public-repo"])
    _priv(
        foo,
        ["foo"],
        also_hosts=[{"manifest": "PM", "repos": ["public-repo"]}],
    )
    Registry.load().add(pm)
    Registry.load().add(foo)

    view = build_authorization_view(Registry.load().list())
    assert any("redundant" in w for w in view.warnings)


# ---- find_anchor_for_path ------------------------------------------------


def test_find_anchor_unique_via_local_path(tmp_registry, tmp_path):
    pm_root = tmp_path / "PM"
    repo_local = tmp_path / "checkouts" / "MyRepo"
    repo_local.mkdir(parents=True)
    pm_root.mkdir()
    (pm_root / "platform_manifest.yaml").write_text(
        yaml.safe_dump(
            {
                "manifest_kind": "platform",
                "manifest_version": "1.0.0",
                "visibility_scope": "public",
                "repos": [{"name": "MyRepo", "local_path": str(repo_local)}],
            }
        ),
        encoding="utf-8",
    )
    Registry.load().add(pm_root)

    inferred = RepoGraph().find_anchor_for_path(repo_local)
    assert inferred == pm_root.resolve()


def test_find_anchor_basename_match(tmp_registry, tmp_path):
    pm = tmp_path / "PM"
    _pub(pm, ["WidgetRepo"])
    Registry.load().add(pm)

    fake_widget = tmp_path / "elsewhere" / "WidgetRepo"
    fake_widget.mkdir(parents=True)
    inferred = RepoGraph().find_anchor_for_path(fake_widget)
    assert inferred == pm.resolve()


def test_find_anchor_no_match(tmp_registry, tmp_path):
    pm = tmp_path / "PM"
    _pub(pm, ["X"])
    Registry.load().add(pm)

    elsewhere = tmp_path / "elsewhere" / "totally-other"
    elsewhere.mkdir(parents=True)
    assert RepoGraph().find_anchor_for_path(elsewhere) is None


def test_find_anchor_ambiguous_raises(tmp_registry, tmp_path):
    pm = tmp_path / "PM"
    privm = tmp_path / "PrivM"
    shared = tmp_path / "checkouts" / "Shared"
    shared.mkdir(parents=True)
    pm.mkdir()
    privm.mkdir()
    (pm / "platform_manifest.yaml").write_text(
        yaml.safe_dump(
            {
                "manifest_kind": "platform",
                "manifest_version": "1.0.0",
                "visibility_scope": "public",
                "repos": [{"name": "PubShared", "local_path": str(shared)}],
            }
        ),
        encoding="utf-8",
    )
    (privm / "private_manifest.yaml").write_text(
        yaml.safe_dump(
            {
                "manifest_kind": "private",
                "manifest_version": "1.0.0",
                "visibility_scope": "private",
                "repos": [{"name": "PrivShared", "local_path": str(shared)}],
            }
        ),
        encoding="utf-8",
    )
    Registry.load().add(pm)
    Registry.load().add(privm)

    with pytest.raises(AmbiguousAnchorError):
        RepoGraph().find_anchor_for_path(shared)


# ---- backward-compat: scope derivation -----------------------------------


def test_backward_compat_scope_derived_from_repos_visibility(tmp_registry, tmp_path):
    pm = tmp_path / "PM"
    pm.mkdir()
    # No top-level visibility_scope; all repos are public → derive public.
    (pm / "platform_manifest.yaml").write_text(
        yaml.safe_dump(
            {
                "manifest_kind": "platform",
                "manifest_version": "1.0.0",
                "repos": {
                    "alpha": {"canonical_name": "Alpha", "visibility": "public"},
                },
            }
        ),
        encoding="utf-8",
    )
    Registry.load().add(pm)
    ok, reason = RepoGraph().can_anchor_host(pm, "Alpha")
    assert ok, reason
