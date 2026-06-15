# SPDX-License-Identifier: AGPL-3.0-or-later
# Copyright (C) 2026 ProtocolWarden
"""Compile ergonomic authoring fields into the canonical capability graph.

Authors write flat fields (owner_repo_id / target_scope / executes_on /
requires / validated_by / produces); this module expands them into a
``CapabilityNode`` plus typed ``CapabilityEdge`` list. The compiled graph is the
truth — the flat fields are sugar.
"""

from __future__ import annotations

from typing import Any

from ..errors import RepoGraphConfigError
from ..ontology.enums import DisclosureMode, RepoVisibility
from ..schema.kinds import SchemaKind
from ..schema.validation import validate_schema_document
from .enums import CapabilityEdgeKind, TargetScopeKind
from .models import (
    CapabilityEdge,
    CapabilityInput,
    CapabilityInvocation,
    CapabilityNode,
    CapabilityRegistry,
    TargetScope,
)
from .validation import (
    parse_capability_category,
    parse_capability_invocation_kind,
    parse_capability_risk,
    parse_target_scope_kind,
)


def _compile_target_scope(idx: int, raw: dict[str, Any]) -> TargetScope:
    kind = parse_target_scope_kind(idx, raw.get("kind"))
    selector_raw = raw.get("selector") or {}
    if not isinstance(selector_raw, dict):
        raise RepoGraphConfigError(
            f"capability #{idx} target_scope.selector must be a mapping"
        )
    selector = tuple(sorted((str(k), v) for k, v in selector_raw.items()))
    return TargetScope(kind=kind, repo_id=raw.get("repo_id"), selector=selector)


def _compile_optional_enum(idx: int, raw: Any, enum_cls: Any, default: Any, field_name: str) -> Any:
    if raw is None:
        return default
    try:
        return enum_cls(raw)
    except ValueError as exc:
        raise RepoGraphConfigError(
            f"capability #{idx} has unknown {field_name} '{raw}'"
        ) from exc


def compile_capability(
    idx: int, raw: dict[str, Any]
) -> tuple[CapabilityNode, list[CapabilityEdge]]:
    action_id = raw.get("action_id")
    if not action_id:
        raise RepoGraphConfigError(f"capability #{idx} requires action_id")

    invocation_raw = raw.get("invocation") or {}
    invocation = CapabilityInvocation(
        kind=parse_capability_invocation_kind(idx, invocation_raw.get("kind")),
        ref=invocation_raw.get("ref", ""),
    )

    inputs = tuple(
        CapabilityInput(
            name=item.get("name", ""),
            type=item.get("type", ""),
            required=bool(item.get("required", False)),
        )
        for item in (raw.get("inputs") or [])
    )

    routing = raw.get("routing") or {}
    target_scope = _compile_target_scope(idx, raw.get("target_scope") or {})

    node = CapabilityNode(
        action_id=action_id,
        name=raw.get("name", action_id),
        category=parse_capability_category(idx, raw.get("category")),
        risk=parse_capability_risk(idx, raw.get("risk")),
        invocation=invocation,
        target_scope=target_scope,
        inputs=inputs,
        preferred_lane=routing.get("preferred_lane"),
        description=raw.get("description"),
        visibility=_compile_optional_enum(
            idx, raw.get("visibility"), RepoVisibility, RepoVisibility.PUBLIC, "visibility"
        ),
        disclosure_mode=_compile_optional_enum(
            idx, raw.get("disclosure_mode"), DisclosureMode, DisclosureMode.PUBLIC, "disclosure_mode"
        ),
    )

    owner = raw.get("owner_repo_id")
    if not owner:
        raise RepoGraphConfigError(f"capability '{action_id}' requires owner_repo_id")

    edges: list[CapabilityEdge] = [
        CapabilityEdge(action_id, owner, CapabilityEdgeKind.OWNS)
    ]
    if target_scope.kind is TargetScopeKind.REPO and target_scope.repo_id:
        edges.append(
            CapabilityEdge(action_id, target_scope.repo_id, CapabilityEdgeKind.TARGETS)
        )
    if raw.get("executes_on"):
        edges.append(
            CapabilityEdge(action_id, raw["executes_on"], CapabilityEdgeKind.EXECUTES)
        )
    for repo in raw.get("requires") or []:
        edges.append(CapabilityEdge(action_id, repo, CapabilityEdgeKind.REQUIRES))
    for repo in raw.get("validated_by") or []:
        edges.append(CapabilityEdge(action_id, repo, CapabilityEdgeKind.VALIDATES))
    for artifact in raw.get("produces") or []:
        edges.append(CapabilityEdge(action_id, artifact, CapabilityEdgeKind.PRODUCES))

    return node, edges


def compile_registry(
    documents: list[dict[str, Any]],
    *,
    known_repo_ids: set[str] | None = None,
) -> CapabilityRegistry:
    nodes: list[CapabilityNode] = []
    edges: list[CapabilityEdge] = []
    for idx, raw in enumerate(documents):
        node, node_edges = compile_capability(idx, raw)
        nodes.append(node)
        edges.extend(node_edges)
    return CapabilityRegistry.build(nodes, edges, known_repo_ids=known_repo_ids)


def load_capability_registry(
    payload: dict[str, Any],
    *,
    known_repo_ids: set[str] | None = None,
) -> CapabilityRegistry:
    """Validate a versioned ``capabilities`` document and compile it."""
    validate_schema_document(payload, expected_kind=SchemaKind.CAPABILITIES)
    documents = payload.get("capabilities") or []
    return compile_registry(documents, known_repo_ids=known_repo_ids)
