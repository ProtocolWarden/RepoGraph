# SPDX-License-Identifier: AGPL-3.0-or-later
# Copyright (C) 2026 ProtocolWarden
"""Compatibility helpers for RepoGraph schema evolution."""

from __future__ import annotations

from ..errors import RepoGraphConfigError
from .kinds import SchemaKind
from .versions import SchemaVersion, schema_version_for


def is_supported_schema_version(kind: SchemaKind, version: str) -> bool:
    return version == schema_version_for(kind).version


def ensure_supported_schema_version(kind: SchemaKind, version: str) -> None:
    current = schema_version_for(kind)
    if version == current.version:
        return
    raise RepoGraphConfigError(
        f"unsupported {kind.value} schema_version={version!r}; "
        f"expected {current.version!r}"
    )


def classify_schema_change(before: SchemaVersion, after: SchemaVersion) -> str:
    if before.schema_kind is not after.schema_kind:
        raise RepoGraphConfigError(
            f"cannot compare different schema kinds: {before.schema_kind.value} vs {after.schema_kind.value}"
        )
    if before.version == after.version:
        return "no_change"
    if before.version.split(".")[0] != after.version.split(".")[0]:
        return "breaking"
    if before.version < after.version:
        return "breaking_change_requires_review"
    return "unsupported_downgrade"
