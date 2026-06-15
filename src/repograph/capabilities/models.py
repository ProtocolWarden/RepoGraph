# SPDX-License-Identifier: AGPL-3.0-or-later
# Copyright (C) 2026 ProtocolWarden
"""Capability registry models.

Authoring is ergonomic flat fields (see ``compiler``); the canonical truth is
this node + typed-edge graph.
"""

from __future__ import annotations

from dataclasses import dataclass, field

from ..errors import RepoGraphConfigError
from ..ontology.enums import DisclosureMode, EntityKind, RepoVisibility
from ..ontology.models import MetadataValue
from ..schema.kinds import SchemaKind
from ..schema.versions import schema_version_for
from .enums import (
    LANE_REQUIRING_RISKS,
    CapabilityCategory,
    CapabilityEdgeKind,
    CapabilityInvocationKind,
    CapabilityRisk,
    TargetScopeKind,
)
from .validation import validate_capability_registry


@dataclass(frozen=True)
class CapabilityInput:
    name: str
    type: str
    required: bool = False


@dataclass(frozen=True)
class CapabilityInvocation:
    kind: CapabilityInvocationKind
    ref: str

    def __post_init__(self) -> None:
        if not self.ref or not self.ref.strip():
            raise RepoGraphConfigError("capability invocation requires a non-empty ref")


@dataclass(frozen=True)
class TargetScope:
    kind: TargetScopeKind
    repo_id: str | None = None
    selector: tuple[tuple[str, MetadataValue], ...] = ()

    def __post_init__(self) -> None:
        if self.kind is TargetScopeKind.REPO:
            if not self.repo_id:
                raise RepoGraphConfigError("target_scope kind='repo' requires repo_id")
            if self.selector:
                raise RepoGraphConfigError("target_scope kind='repo' must not set a selector")
        elif self.kind is TargetScopeKind.REPO_SET:
            if not self.selector:
                raise RepoGraphConfigError("target_scope kind='repo_set' requires a selector")
            if self.repo_id:
                raise RepoGraphConfigError("target_scope kind='repo_set' must not set repo_id")
        else:  # FLEET
            if self.repo_id or self.selector:
                raise RepoGraphConfigError(
                    "target_scope kind='fleet' must not set repo_id or selector"
                )


@dataclass(frozen=True)
class CapabilityEdge:
    source_id: str  # capability action_id
    target_id: str  # repo_id (repo-targeting kinds) or artifact id (produces)
    kind: CapabilityEdgeKind


@dataclass(frozen=True)
class CapabilityNode:
    action_id: str
    name: str
    category: CapabilityCategory
    risk: CapabilityRisk
    invocation: CapabilityInvocation
    target_scope: TargetScope
    inputs: tuple[CapabilityInput, ...] = ()
    preferred_lane: str | None = None
    description: str | None = None
    visibility: RepoVisibility = RepoVisibility.PUBLIC
    disclosure_mode: DisclosureMode = DisclosureMode.PUBLIC
    kind: EntityKind = EntityKind.CAPABILITY
    metadata: tuple[tuple[str, MetadataValue], ...] = ()

    def __post_init__(self) -> None:
        if not self.action_id or not self.action_id.strip():
            raise RepoGraphConfigError("capability requires a non-empty action_id")
        if self.risk in LANE_REQUIRING_RISKS and not self.preferred_lane:
            raise RepoGraphConfigError(
                f"capability '{self.action_id}' risk={self.risk.value!r} requires an "
                "explicit routing.preferred_lane"
            )
        if (
            self.visibility is RepoVisibility.LOCAL
            and self.disclosure_mode is DisclosureMode.PUBLIC
        ):
            raise RepoGraphConfigError(
                f"capability '{self.action_id}' cannot be local visibility with public disclosure"
            )

    @property
    def is_public(self) -> bool:
        return (
            self.visibility is RepoVisibility.PUBLIC
            and self.disclosure_mode is DisclosureMode.PUBLIC
        )


@dataclass
class CapabilityRegistry:
    nodes: dict[str, CapabilityNode] = field(default_factory=dict)
    edges: tuple[CapabilityEdge, ...] = ()

    @classmethod
    def build(
        cls,
        nodes: list[CapabilityNode],
        edges: list[CapabilityEdge],
        *,
        known_repo_ids: set[str] | None = None,
    ) -> "CapabilityRegistry":
        registry = cls(
            nodes={node.action_id: node for node in nodes},
            edges=tuple(edges),
        )
        validate_capability_registry(registry, nodes, known_repo_ids=known_repo_ids)
        return registry

    def list_capabilities(self) -> list[CapabilityNode]:
        return sorted(self.nodes.values(), key=lambda n: n.action_id)

    def capability(self, action_id: str) -> CapabilityNode | None:
        return self.nodes.get(action_id)

    def edges_for(self, action_id: str) -> list[CapabilityEdge]:
        return [e for e in self.edges if e.source_id == action_id]

    def targets_by_kind(self, action_id: str, kind: CapabilityEdgeKind) -> list[str]:
        return [
            e.target_id
            for e in self.edges
            if e.source_id == action_id and e.kind is kind
        ]

    def owner_of(self, action_id: str) -> str | None:
        owners = self.targets_by_kind(action_id, CapabilityEdgeKind.OWNS)
        return owners[0] if owners else None

    def to_payload(self) -> dict:
        """Canonical, deterministic projection for boundary hashing."""
        return {
            "schema_kind": SchemaKind.CAPABILITIES.value,
            "schema_version": schema_version_for(SchemaKind.CAPABILITIES).version,
            "capabilities": [
                {
                    "action_id": n.action_id,
                    "name": n.name,
                    "category": n.category.value,
                    "risk": n.risk.value,
                    "visibility": n.visibility.value,
                    "disclosure_mode": n.disclosure_mode.value,
                    "preferred_lane": n.preferred_lane,
                    "description": n.description,
                    "invocation": {
                        "kind": n.invocation.kind.value,
                        "ref": n.invocation.ref,
                    },
                    "target_scope": {
                        "kind": n.target_scope.kind.value,
                        "repo_id": n.target_scope.repo_id,
                        "selector": [list(pair) for pair in n.target_scope.selector],
                    },
                    "inputs": [
                        {"name": i.name, "type": i.type, "required": i.required}
                        for i in n.inputs
                    ],
                    "metadata": [list(pair) for pair in n.metadata],
                }
                for n in self.list_capabilities()
            ],
            "edges": sorted(
                [e.source_id, e.kind.value, e.target_id] for e in self.edges
            ),
        }
