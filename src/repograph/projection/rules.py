# SPDX-License-Identifier: AGPL-3.0-or-later
# Copyright (C) 2026 ProtocolWarden
"""Projection rules and public graph generation."""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

from ..ontology.enums import DisclosureMode, RepoVisibility
from ..ontology.models import RepoIdentity
from .boundary import build_boundary_artifact
from .models import ProjectionBehavior, PublicGraphProjection
from .redaction import public_name

if TYPE_CHECKING:
    from ..topology.models import GraphEdge, RepoGraph


PUBLIC_RELATIONSHIP_BEHAVIORS: frozenset[ProjectionBehavior] = frozenset({
    ProjectionBehavior.PUBLIC_SAFE,
    ProjectionBehavior.REDACTED_PUBLIC_STUB,
})


def default_projection_behavior_for_visibility(
    visibility: RepoVisibility,
) -> ProjectionBehavior:
    if visibility is RepoVisibility.PUBLIC:
        return ProjectionBehavior.PUBLIC_SAFE
    if visibility is RepoVisibility.LOCAL:
        return ProjectionBehavior.LOCAL_ONLY
    return ProjectionBehavior.DROP_FROM_PUBLIC


def _projectable_node(node: RepoIdentity) -> bool:
    if node.visibility is RepoVisibility.PUBLIC and node.disclosure_mode is DisclosureMode.PUBLIC:
        return True
    return node.disclosure_mode is DisclosureMode.ALIAS_ONLY and bool(node.public_alias)


def _project_node(node: RepoIdentity) -> RepoIdentity:
    if node.disclosure_mode is DisclosureMode.ALIAS_ONLY and node.public_alias:
        return RepoIdentity(
            repo_id=node.repo_id,
            canonical_name=node.public_alias,
            visibility=RepoVisibility.PUBLIC,
            disclosure_mode=DisclosureMode.PUBLIC,
            plane=node.plane,
            repo_kind=node.repo_kind,
            public_alias=node.public_alias,
            aliases=(),
            description=node.description,
            legacy_names=(),
            github_url=node.github_url if node.visibility is RepoVisibility.PUBLIC else None,
            runtime_role=node.runtime_role,
            kind=node.kind,
            owner=node.owner,
            scope=node.scope,
            metadata=tuple(
                item for item in node.metadata
                if not str(item[0]).startswith(("local_", "secret_", "private_"))
            ),
            projection_policy=node.projection_policy,
            projection_behavior=ProjectionBehavior.PUBLIC_SAFE,
            redaction_label=node.redaction_label or "alias_only",
            source=node.source,
            owner_kind=node.owner_kind,
        )
    return RepoIdentity(
        repo_id=node.repo_id,
        canonical_name=public_name(
            canonical_name=node.canonical_name,
            public_alias=node.public_alias,
        ),
        visibility=RepoVisibility.PUBLIC,
        disclosure_mode=DisclosureMode.PUBLIC,
        plane=node.plane,
        repo_kind=node.repo_kind,
        public_alias=node.public_alias,
        aliases=(),
        description=node.description,
        legacy_names=node.legacy_names,
        github_url=node.github_url,
        runtime_role=node.runtime_role,
        kind=node.kind,
        owner=node.owner,
        scope=node.scope,
        metadata=tuple(
            item for item in node.metadata
            if not str(item[0]).startswith(("local_", "secret_", "private_"))
        ),
        projection_policy=node.projection_policy,
        projection_behavior=ProjectionBehavior.PUBLIC_SAFE,
        redaction_label=node.redaction_label,
        source=node.source,
        owner_kind=node.owner_kind,
    )


def build_public_projection(
    graph: RepoGraph,
    *,
    source_graph_id: str,
    source_ref_or_commit: str | None = None,
    manifest_version: str = "1.0.0",
) -> PublicGraphProjection:
    from ..topology.models import RepoGraph

    public_nodes = {
        repo_id: _project_node(node)
        for repo_id, node in graph.nodes.items()
        if _projectable_node(node)
    }
    public_node_ids = set(public_nodes)

    relationships: list[GraphEdge] = []
    redactions: list[str] = []
    for relationship in graph.list_relationships():
        if (
            relationship.source_id in public_node_ids
            and relationship.target_id in public_node_ids
            and relationship.visibility is RepoVisibility.PUBLIC
            and relationship.projection_behavior in PUBLIC_RELATIONSHIP_BEHAVIORS
        ):
            relationships.append(relationship)
        else:
            redactions.append(f"edge:{relationship.relationship_id}")

    for repo_id in graph.nodes:
        if repo_id not in public_node_ids:
            redactions.append(f"repo:{repo_id}")

    projected = RepoGraph.build(
        nodes=list(public_nodes.values()),
        edges=[
            edge for edge in graph.edges
            if edge.src in public_node_ids and edge.dst in public_node_ids
        ],
        relationships=relationships,
    )
    manifest = to_public_manifest_dict(projected, manifest_version=manifest_version)
    boundary = build_boundary_artifact(
        graph,
        source_graph_id=source_graph_id,
        source_ref_or_commit=source_ref_or_commit,
    )
    return PublicGraphProjection(
        graph=projected,
        manifest=manifest,
        redaction_report=tuple(sorted(set(redactions))),
        boundary_artifact=boundary,
    )


def to_public_manifest_dict(
    graph: RepoGraph,
    *,
    manifest_version: str = "1.0.0",
) -> dict[str, Any]:
    from .validation import can_project_node, can_project_relationship

    public_nodes = {
        repo_id: node
        for repo_id, node in graph.nodes.items()
        if can_project_node(node)
    }
    public_node_ids = set(public_nodes)

    repos: dict[str, dict[str, Any]] = {}
    for repo_id, node in sorted(public_nodes.items()):
        fields: dict[str, Any] = {
            "canonical_name": public_name(
                canonical_name=node.canonical_name,
                public_alias=node.public_alias,
            ),
            "visibility": RepoVisibility.PUBLIC.value,
            "projection_behavior": ProjectionBehavior.PUBLIC_SAFE.value,
        }
        if node.kind.value != "Repository":
            fields["kind"] = node.kind.value
        if node.legacy_names:
            fields["legacy_names"] = list(node.legacy_names)
        if node.github_url:
            fields["github_url"] = node.github_url
        if node.runtime_role:
            fields["runtime_role"] = node.runtime_role
        if node.owner:
            fields["owner"] = node.owner
        if node.scope:
            fields["scope"] = node.scope
        if node.metadata:
            fields["metadata"] = dict(node.metadata)
        if node.public_alias:
            fields["public_alias"] = node.public_alias
        repos[repo_id] = fields

    edges = [
        {"from": edge.src, "to": edge.dst, "type": edge.type.value}
        for edge in graph.edges
        if edge.src in public_node_ids and edge.dst in public_node_ids
    ]

    relationships = [
        {
            "id": relationship.relationship_id,
            "source": relationship.source_id,
            "target": relationship.target_id,
            "kind": relationship.kind.value,
            "visibility": RepoVisibility.PUBLIC.value,
            "projection_behavior": relationship.projection_behavior.value,
            **({"policy_ref": relationship.policy_ref} if relationship.policy_ref else {}),
            **({"redaction_label": relationship.redaction_label} if relationship.redaction_label else {}),
            **({"metadata": dict(relationship.metadata)} if relationship.metadata else {}),
        }
        for relationship in graph.list_relationships()
        if can_project_relationship(relationship, public_node_ids)
    ]

    return {
        "manifest_kind": "platform",
        "manifest_version": manifest_version,
        "repos": repos,
        "edges": edges,
        "relationships": relationships,
    }
