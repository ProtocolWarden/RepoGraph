# SPDX-License-Identifier: AGPL-3.0-or-later
# Copyright (C) 2026 ProtocolWarden
"""Graph topology validation."""

from __future__ import annotations

from typing import Any

from ..errors import RepoGraphConfigError
from ..ontology.enums import RepoVisibility
from ..projection.validation import parse_projection_behavior
from .edges import EdgeKind, RepoEdgeType


def parse_repo_edge_type(idx: int, edge_type_raw: Any) -> RepoEdgeType:
    try:
        return RepoEdgeType(edge_type_raw)
    except ValueError as exc:
        raise RepoGraphConfigError(
            f"edge #{idx} has unknown type '{edge_type_raw}'; "
            f"allowed: {[t.value for t in RepoEdgeType]}"
        ) from exc


def parse_relationship_kind(idx: int, kind_raw: Any) -> EdgeKind:
    try:
        return EdgeKind(kind_raw)
    except ValueError as exc:
        raise RepoGraphConfigError(
            f"relationship #{idx} has unknown kind '{kind_raw}'; "
            f"allowed: {[k.value for k in EdgeKind]}"
        ) from exc


def parse_relationship_projection_behavior(
    idx: int,
    *,
    raw: Any,
    visibility: RepoVisibility,
):
    return parse_projection_behavior(
        subject_kind="relationship",
        subject_id=f"#{idx}",
        raw=raw,
        visibility=visibility,
        default_from_visibility=False,
    )


def validate_graph_topology(graph, nodes: list[Any]) -> None:
    from ..projection.rules import PUBLIC_RELATIONSHIP_BEHAVIORS

    node_map: dict[str, Any] = {}
    name_index: dict[str, str] = {}
    for node in nodes:
        if node.repo_id in node_map:
            raise RepoGraphConfigError(f"duplicate repo_id: {node.repo_id}")
        node_map[node.repo_id] = node
        aliases = [node.canonical_name, *node.all_aliases]
        if node.public_alias:
            aliases.append(node.public_alias)
        for alias in aliases:
            key = alias.lower()
            if key in name_index and name_index[key] != node.repo_id:
                raise RepoGraphConfigError(
                    f"name '{alias}' maps to both '{name_index[key]}' and '{node.repo_id}'"
                )
            name_index[key] = node.repo_id

    for edge in graph.edges:
        if edge.src not in node_map:
            raise RepoGraphConfigError(
                f"edge {edge.type.value} references unknown src '{edge.src}'"
            )
        if edge.dst not in node_map:
            raise RepoGraphConfigError(
                f"edge {edge.type.value} references unknown dst '{edge.dst}'"
            )

    rel_map: dict[str, Any] = {}
    for relationship in graph.relationships:
        if relationship.relationship_id in rel_map:
            raise RepoGraphConfigError(
                f"duplicate relationship id: {relationship.relationship_id}"
            )
        if relationship.source_id not in node_map:
            raise RepoGraphConfigError(
                f"relationship {relationship.relationship_id} references unknown source "
                f"'{relationship.source_id}'"
            )
        if relationship.target_id not in node_map:
            raise RepoGraphConfigError(
                f"relationship {relationship.relationship_id} references unknown target "
                f"'{relationship.target_id}'"
            )
        rel_map[relationship.relationship_id] = relationship
        if (
            relationship.visibility is RepoVisibility.PUBLIC
            and relationship.projection_behavior not in PUBLIC_RELATIONSHIP_BEHAVIORS
        ):
            raise RepoGraphConfigError(
                f"relationship {relationship.relationship_id} has public visibility "
                f"but unsafe projection_behavior={relationship.projection_behavior.value!r}"
            )
    graph._name_index = name_index
