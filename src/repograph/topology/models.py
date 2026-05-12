# SPDX-License-Identifier: AGPL-3.0-or-later
# Copyright (C) 2026 ProtocolWarden
"""Graph models and queries."""

from __future__ import annotations

from dataclasses import dataclass, field

from ..ontology.enums import DisclosureMode, RepoVisibility, Source
from ..ontology.models import MetadataValue, RepoIdentity
from ..projection.models import ProjectionBehavior
from .edges import EdgeKind, RepoEdgeType
from .validation import validate_graph_topology


@dataclass(frozen=True)
class RepoEdge:
    src: str
    dst: str
    type: RepoEdgeType
    source: Source = Source.PLATFORM


@dataclass(frozen=True)
class GraphEdge:
    relationship_id: str
    source_id: str
    target_id: str
    kind: EdgeKind
    visibility: RepoVisibility = RepoVisibility.PUBLIC
    disclosure_mode: DisclosureMode = DisclosureMode.PUBLIC
    description: str | None = None
    projection_behavior: ProjectionBehavior = ProjectionBehavior.PUBLIC_SAFE
    policy_ref: str | None = None
    redaction_label: str | None = None
    metadata: tuple[tuple[str, MetadataValue], ...] = ()
    source: Source = Source.PLATFORM


OntologyRelationship = GraphEdge


@dataclass
class RepoGraph:
    nodes: dict[str, RepoIdentity] = field(default_factory=dict)
    edges: tuple[RepoEdge, ...] = ()
    relationships: tuple[GraphEdge, ...] = ()
    _name_index: dict[str, str] = field(default_factory=dict, repr=False)

    @classmethod
    def build(
        cls,
        nodes: list[RepoIdentity],
        edges: list[RepoEdge],
        relationships: list[GraphEdge] | None = None,
    ) -> "RepoGraph":
        graph = cls(
            nodes={node.repo_id: node for node in nodes},
            edges=tuple(edges),
            relationships=tuple(relationships or []),
            _name_index={},
        )
        validate_graph_topology(graph, nodes)
        return graph

    def list_nodes(self) -> list[RepoIdentity]:
        return sorted(self.nodes.values(), key=lambda n: n.canonical_name)

    def resolve(self, name: str) -> RepoIdentity | None:
        repo_id = self._name_index.get(name.lower())
        if repo_id is None:
            return None
        return self.nodes[repo_id]

    def upstream(self, repo_id: str) -> list[RepoIdentity]:
        if repo_id not in self.nodes:
            raise KeyError(repo_id)
        targets = {e.dst for e in self.edges if e.src == repo_id}
        return [self.nodes[t] for t in sorted(targets)]

    def downstream(self, repo_id: str) -> list[RepoIdentity]:
        if repo_id not in self.nodes:
            raise KeyError(repo_id)
        sources = {e.src for e in self.edges if e.dst == repo_id}
        return [self.nodes[s] for s in sorted(sources)]

    def affected_by_contract_change(self, repo_id: str) -> list[RepoIdentity]:
        if repo_id not in self.nodes:
            raise KeyError(repo_id)
        consumers = {
            e.src
            for e in self.edges
            if e.dst == repo_id and e.type == RepoEdgeType.DEPENDS_ON_CONTRACTS_FROM
        }
        return [self.nodes[c] for c in sorted(consumers)]

    def who_consumes_assets_of(self, repo_id: str) -> list[RepoIdentity]:
        if repo_id not in self.nodes:
            raise KeyError(repo_id)
        consumers = {
            e.src
            for e in self.edges
            if e.dst == repo_id and e.type == RepoEdgeType.BUNDLES_ASSETS_FROM
        }
        return [self.nodes[c] for c in sorted(consumers)]

    def who_dispatches_to(self, repo_id: str) -> list[RepoIdentity]:
        if repo_id not in self.nodes:
            raise KeyError(repo_id)
        dispatchers = {
            e.src
            for e in self.edges
            if e.dst == repo_id and e.type == RepoEdgeType.DISPATCHES_TO
        }
        return [self.nodes[d] for d in sorted(dispatchers)]

    def list_relationships(self) -> list[GraphEdge]:
        return sorted(self.relationships, key=lambda r: r.relationship_id)

    def relationships_by_kind(self, kind: EdgeKind) -> list[GraphEdge]:
        return [r for r in self.list_relationships() if r.kind is kind]

    def relationships_from(
        self,
        source_id: str,
        *,
        visibility: RepoVisibility | None = None,
        projection_behavior: ProjectionBehavior | None = None,
    ) -> list[GraphEdge]:
        return [
            r
            for r in self.list_relationships()
            if r.source_id == source_id
            and (visibility is None or r.visibility is visibility)
            and (
                projection_behavior is None
                or r.projection_behavior is projection_behavior
            )
        ]

    def relationships_to(
        self,
        target_id: str,
        *,
        visibility: RepoVisibility | None = None,
        projection_behavior: ProjectionBehavior | None = None,
    ) -> list[GraphEdge]:
        return [
            r
            for r in self.list_relationships()
            if r.target_id == target_id
            and (visibility is None or r.visibility is visibility)
            and (
                projection_behavior is None
                or r.projection_behavior is projection_behavior
            )
        ]
