# SPDX-License-Identifier: AGPL-3.0-or-later
# Copyright (C) 2026 ProtocolWarden
"""Projection validation helpers."""

from __future__ import annotations

from typing import Any

from ..errors import RepoGraphConfigError
from ..ontology.enums import RepoVisibility
from .models import ProjectionBehavior
from .rules import PUBLIC_RELATIONSHIP_BEHAVIORS, default_projection_behavior_for_visibility


def parse_projection_behavior(
    *,
    subject_kind: str,
    subject_id: object,
    raw: Any,
    visibility: RepoVisibility,
    default_from_visibility: bool,
) -> ProjectionBehavior:
    if raw is None:
        if default_from_visibility:
            return default_projection_behavior_for_visibility(visibility)
        raise RepoGraphConfigError(
            f"{subject_kind} '{subject_id}' missing required 'projection_behavior' field "
            f"(allowed: {[b.value for b in ProjectionBehavior]})"
        )
    try:
        return ProjectionBehavior(raw)
    except ValueError as exc:
        raise RepoGraphConfigError(
            f"{subject_kind} '{subject_id}' has unknown projection_behavior={raw!r}; "
            f"allowed: {[b.value for b in ProjectionBehavior]}"
        ) from exc


def can_project_node(node) -> bool:
    return (
        node.visibility is RepoVisibility.PUBLIC
        and node.projection_behavior is ProjectionBehavior.PUBLIC_SAFE
    )


def can_project_relationship(relationship, public_node_ids: set[str]) -> bool:
    return (
        relationship.source_id in public_node_ids
        and relationship.target_id in public_node_ids
        and relationship.visibility is RepoVisibility.PUBLIC
        and relationship.projection_behavior in PUBLIC_RELATIONSHIP_BEHAVIORS
    )
