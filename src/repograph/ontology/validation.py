# SPDX-License-Identifier: AGPL-3.0-or-later
# Copyright (C) 2026 ProtocolWarden
"""Ontology validation helpers."""

from __future__ import annotations

from typing import Any

from ..errors import RepoGraphConfigError
from ..projection.validation import parse_projection_behavior
from .enums import (
    DisclosureMode,
    EntityKind,
    OwnerKind,
    PlatformPlane,
    RepoVisibility,
)
from .models import RepoIdentity


def parse_visibility(repo_id: object, fields: dict[str, Any]) -> RepoVisibility:
    raw = fields.get("visibility")
    if raw is None:
        raise RepoGraphConfigError(
            f"repo '{repo_id}' missing required 'visibility' field "
            f"(allowed: {[v.value for v in RepoVisibility]})"
        )
    try:
        return RepoVisibility(raw)
    except ValueError as exc:
        raise RepoGraphConfigError(
            f"repo '{repo_id}' has unknown visibility={raw!r}; "
            f"allowed: {[v.value for v in RepoVisibility]}"
        ) from exc


def parse_disclosure_mode(
    repo_id: object,
    fields: dict[str, Any],
    *,
    visibility: RepoVisibility,
) -> DisclosureMode:
    raw = fields.get("disclosure_mode")
    if raw is None:
        if visibility is RepoVisibility.PUBLIC:
            return DisclosureMode.PUBLIC
        if visibility is RepoVisibility.LOCAL:
            return DisclosureMode.LOCAL_ONLY
        return DisclosureMode.PRIVATE
    try:
        return DisclosureMode(raw)
    except ValueError as exc:
        raise RepoGraphConfigError(
            f"repo '{repo_id}' has unknown disclosure_mode={raw!r}; "
            f"allowed: {[m.value for m in DisclosureMode]}"
        ) from exc


def parse_kind(repo_id: object, fields: dict[str, Any]) -> EntityKind:
    raw = fields.get("kind", EntityKind.REPOSITORY.value)
    try:
        return EntityKind(raw)
    except ValueError as exc:
        raise RepoGraphConfigError(
            f"repo '{repo_id}' has unknown kind={raw!r}; "
            f"allowed: {[k.value for k in EntityKind]}"
        ) from exc


def parse_plane(repo_id: object, fields: dict[str, Any]) -> PlatformPlane | None:
    raw = fields.get("plane")
    if raw is None:
        return None
    try:
        return PlatformPlane(raw)
    except ValueError as exc:
        raise RepoGraphConfigError(
            f"repo '{repo_id}' has unknown plane={raw!r}; "
            f"allowed: {[p.value for p in PlatformPlane]}"
        ) from exc


def parse_owner_kind(repo_id: object, fields: dict[str, Any]) -> OwnerKind | None:
    raw = fields.get("owner_kind")
    if raw is None:
        return None
    try:
        return OwnerKind(raw)
    except ValueError as exc:
        raise RepoGraphConfigError(
            f"repo '{repo_id}' has unknown owner_kind={raw!r}; "
            f"allowed: {[o.value for o in OwnerKind]}"
        ) from exc


def enforce_platform_public_only(nodes: list[RepoIdentity]) -> None:
    private = [n.repo_id for n in nodes if n.visibility is not RepoVisibility.PUBLIC]
    if private:
        raise RepoGraphConfigError(
            "PlatformManifest may only contain public nodes; "
            f"non-public node(s): {private}"
        )


def parse_entity_projection_behavior(
    repo_id: object,
    fields: dict[str, Any],
    *,
    visibility: RepoVisibility,
):
    return parse_projection_behavior(
        subject_kind="repo",
        subject_id=repo_id,
        raw=fields.get("projection_behavior"),
        visibility=visibility,
        default_from_visibility=True,
    )
