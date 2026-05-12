from __future__ import annotations

import pytest

from repograph import DisclosureMode, PlatformPlane, RepoGraphConfigError, RepoIdentity, RepoKind, RepoVisibility


def test_alias_only_requires_public_alias() -> None:
    with pytest.raises(RepoGraphConfigError):
        RepoIdentity(
            repo_id="private_docs",
            canonical_name="PrivateDocs",
            visibility=RepoVisibility.PRIVATE,
            disclosure_mode=DisclosureMode.ALIAS_ONLY,
        )


def test_warehouse_cannot_classify_as_control_plane() -> None:
    with pytest.raises(RepoGraphConfigError):
        RepoIdentity(
            repo_id="Warehouse",
            canonical_name="Warehouse",
            visibility=RepoVisibility.PUBLIC,
            disclosure_mode=DisclosureMode.PUBLIC,
            plane=PlatformPlane.CONTROL,
            repo_kind=RepoKind.CONTEXT_PACKAGING_UTILITY,
        )


def test_invalid_visibility_value_fails() -> None:
    with pytest.raises(ValueError):
        RepoVisibility("bogus")
