# SPDX-License-Identifier: AGPL-3.0-or-later
# Copyright (C) 2026 ProtocolWarden
"""Direct unit tests for the authorization module's data structures.

Imports ``repograph.authorization`` by module path (not via the package
re-export) so the dataclasses ``AlsoHostsEntry``, ``ManifestRecord`` and
``AuthorizationView`` carry explicit, name-level coverage of their behaviour
(derived properties, lookup methods) rather than only being touched through
the integration tests in ``test_authorization.py``.
"""

from __future__ import annotations

from pathlib import Path

from repograph.authorization import (
    AlsoHostsEntry,
    AuthorizationView,
    ManifestRecord,
)


def _record(name: str, root: Path, **kw) -> ManifestRecord:
    return ManifestRecord(
        name=name,
        root=root,
        yaml_paths=(root / "manifest.yaml",),
        visibility_scope=kw.get("visibility_scope", "public"),
        repos=kw.get("repos", ()),
        also_hosts=kw.get("also_hosts", ()),
        repo_aliases=kw.get("repo_aliases", {}),
    )


def test_also_hosts_entry_is_immutable_value():
    a = AlsoHostsEntry(manifest="PrivBar", repos=("shared",))
    b = AlsoHostsEntry(manifest="PrivBar", repos=("shared",))
    assert a == b
    assert a.manifest == "PrivBar"
    assert a.repos == ("shared",)


def test_also_hosts_flattened_unions_across_entries():
    rec = _record(
        "PrivFoo",
        Path("/tmp/PrivFoo"),
        visibility_scope="private",
        also_hosts=(
            AlsoHostsEntry(manifest="A", repos=("x", "y")),
            AlsoHostsEntry(manifest="B", repos=("y", "z")),
        ),
    )
    assert rec.also_hosts_flattened == frozenset({"x", "y", "z"})


def test_also_hosts_flattened_empty_when_no_grants():
    rec = _record("Pub", Path("/tmp/Pub"))
    assert rec.also_hosts_flattened == frozenset()


def test_manifest_record_default_collections_are_independent():
    r1 = _record("A", Path("/tmp/A"))
    r2 = _record("B", Path("/tmp/B"))
    r1.repo_local_paths["k"] = Path("/tmp/k")
    assert r2.repo_local_paths == {}


def test_view_get_by_root_canonicalizes():
    root = Path("/tmp/PM").resolve()
    rec = _record("PM", root, repos=("Lib",))
    view = AuthorizationView(
        manifests={root: rec},
        repo_owner={"Lib": root},
    )
    # A non-canonical (relative-ish, trailing) form resolves to the same key.
    assert view.get_by_root(Path("/tmp/PM/")) is rec
    assert view.get_by_root(Path("/tmp/nope")) is None


def test_view_get_by_name_is_case_insensitive():
    root = Path("/tmp/PM").resolve()
    rec = _record("PlatformManifest", root)
    view = AuthorizationView(manifests={root: rec}, repo_owner={})
    assert view.get_by_name("platformmanifest") is rec
    assert view.get_by_name("PLATFORMMANIFEST") is rec
    assert view.get_by_name("missing") is None
