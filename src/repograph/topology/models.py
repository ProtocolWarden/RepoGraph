# SPDX-License-Identifier: AGPL-3.0-or-later
# Copyright (C) 2026 ProtocolWarden
"""Graph models and queries."""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import TYPE_CHECKING

from ..ontology.enums import DisclosureMode, RepoVisibility, Source
from ..ontology.models import MetadataValue, RepoIdentity
from ..projection.models import ProjectionBehavior
from .edges import EdgeKind, RepoEdgeType
from .validation import validate_graph_topology

if TYPE_CHECKING:  # pragma: no cover
    from ..authorization import AuthorizationView
    from ..registry import Registry


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


def _is_within(child: Path, parent: Path) -> bool:
    try:
        child.relative_to(parent)
        return True
    except ValueError:
        return False


@dataclass
class RepoGraph:
    nodes: dict[str, RepoIdentity] = field(default_factory=dict)
    edges: tuple[RepoEdge, ...] = ()
    relationships: tuple[GraphEdge, ...] = ()
    _name_index: dict[str, str] = field(default_factory=dict, repr=False)
    _authorization: "AuthorizationView | None" = field(default=None, repr=False)
    _registry: "Registry | None" = field(default=None, repr=False)

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

    # ------------------------------------------------------------------
    # Manifest-registry self-initialization (P2)
    # ------------------------------------------------------------------

    def _ensure_authorization(self) -> "AuthorizationView":
        """Lazily load the authorization view from the per-machine registry.

        Idempotent. Validations run on first load and may raise
        ``RepoGraphConfigError``.
        """
        if self._authorization is not None:
            return self._authorization
        from ..authorization import build_authorization_view
        from ..registry import Registry

        registry = self._registry or Registry.load()
        view = build_authorization_view(registry.list())
        # Stash on the instance for reuse. Using object.__setattr__ to be
        # robust across dataclass mutability changes.
        object.__setattr__(self, "_authorization", view)
        object.__setattr__(self, "_registry", registry)
        return view

    def authorization(self) -> "AuthorizationView":
        """Public accessor for the registry-backed authorization view."""
        return self._ensure_authorization()

    def can_anchor_host(self, anchor_path: Path, repo_name: str) -> tuple[bool, str]:
        """Check whether a session anchored at ``anchor_path`` may host
        cognition about ``repo_name``. See ADR 0002 P0.4."""
        return self._ensure_authorization().can_anchor_host(
            Path(anchor_path), repo_name
        )

    def find_anchor_for_path(self, cwd: Path) -> Path | None:
        """Infer which manifest claims ``cwd``.

        Walks every registered manifest's ``repos[*].local_path`` and, as a
        fallback, matches the cwd's nearest ancestor whose basename matches a
        registered manifest's owned repo name. Returns the manifest repo root
        on unique match, ``None`` on no match, raises ``AmbiguousAnchorError``
        on multiple distinct matches.
        """
        from ..errors import AmbiguousAnchorError

        view = self._ensure_authorization()
        cwd = Path(cwd).expanduser().resolve()

        matches: set[Path] = set()

        # Strategy A: any manifest's repo declares a local_path that contains cwd.
        for record in view.manifests.values():
            for repo_name, local in record.repo_local_paths.items():
                try:
                    resolved_local = Path(local).expanduser().resolve()
                except (OSError, RuntimeError):
                    continue
                if cwd == resolved_local or _is_within(cwd, resolved_local):
                    matches.add(record.root)

        # Strategy B: basename heuristic — walk cwd ancestors and match by
        # repo-name (canonical_name). Useful when no local_path is declared.
        if not matches:
            for ancestor in [cwd, *cwd.parents]:
                name = ancestor.name
                if not name:
                    continue
                hit_roots: set[Path] = set()
                for record in view.manifests.values():
                    if name in record.repos or name == record.name:
                        hit_roots.add(record.root)
                if hit_roots:
                    matches = hit_roots
                    break

        if not matches:
            return None
        if len(matches) > 1:
            raise AmbiguousAnchorError(
                f"path {cwd} is claimed by multiple manifests: "
                f"{sorted(str(m) for m in matches)}"
            )
        return next(iter(matches))

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
