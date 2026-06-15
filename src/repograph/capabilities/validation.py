# SPDX-License-Identifier: AGPL-3.0-or-later
# Copyright (C) 2026 ProtocolWarden
"""Capability registry validation.

RepoGraph validates *shape* and graph invariants. It stays import-free of the
fleet: ``invocation.ref`` is recorded as an opaque string and resolved by
Custodian (detector CAP1), not here. When ``known_repo_ids`` is supplied,
repo-targeting edges are also checked to resolve.
"""

from __future__ import annotations

from typing import Any

from ..errors import RepoGraphConfigError
from .enums import (
    REPO_TARGETING_EDGE_KINDS,
    CapabilityCategory,
    CapabilityEdgeKind,
    CapabilityInvocationKind,
    CapabilityRisk,
    TargetScopeKind,
)


def parse_capability_category(idx: int, raw: Any) -> CapabilityCategory:
    try:
        return CapabilityCategory(raw)
    except ValueError as exc:
        raise RepoGraphConfigError(
            f"capability #{idx} has unknown category '{raw}'; "
            f"allowed: {[c.value for c in CapabilityCategory]}"
        ) from exc


def parse_capability_risk(idx: int, raw: Any) -> CapabilityRisk:
    try:
        return CapabilityRisk(raw)
    except ValueError as exc:
        raise RepoGraphConfigError(
            f"capability #{idx} has unknown risk '{raw}'; "
            f"allowed: {[r.value for r in CapabilityRisk]}"
        ) from exc


def parse_capability_invocation_kind(idx: int, raw: Any) -> CapabilityInvocationKind:
    try:
        return CapabilityInvocationKind(raw)
    except ValueError as exc:
        raise RepoGraphConfigError(
            f"capability #{idx} has unknown invocation kind '{raw}'; "
            f"allowed: {[k.value for k in CapabilityInvocationKind]}"
        ) from exc


def parse_target_scope_kind(idx: int, raw: Any) -> TargetScopeKind:
    try:
        return TargetScopeKind(raw)
    except ValueError as exc:
        raise RepoGraphConfigError(
            f"capability #{idx} has unknown target_scope kind '{raw}'; "
            f"allowed: {[k.value for k in TargetScopeKind]}"
        ) from exc


def validate_capability_registry(
    registry: Any,
    nodes: list[Any],
    *,
    known_repo_ids: set[str] | None = None,
) -> None:
    seen: set[str] = set()
    for node in nodes:
        if node.action_id in seen:
            raise RepoGraphConfigError(f"duplicate capability action_id: {node.action_id}")
        seen.add(node.action_id)

    owns_count: dict[str, int] = {action_id: 0 for action_id in registry.nodes}
    for edge in registry.edges:
        if edge.source_id not in registry.nodes:
            raise RepoGraphConfigError(
                f"capability edge references unknown capability '{edge.source_id}'"
            )
        if edge.kind is CapabilityEdgeKind.OWNS:
            owns_count[edge.source_id] += 1
        if (
            known_repo_ids is not None
            and edge.kind in REPO_TARGETING_EDGE_KINDS
            and edge.target_id not in known_repo_ids
        ):
            raise RepoGraphConfigError(
                f"capability '{edge.source_id}' {edge.kind.value} edge references "
                f"unknown repo '{edge.target_id}'"
            )

    for action_id, count in owns_count.items():
        if count != 1:
            raise RepoGraphConfigError(
                f"capability '{action_id}' must have exactly one owns edge, found {count}"
            )

    # target_scope <-> targets-edge consistency: a concrete repo target emits
    # exactly one resolvable targets edge; repo_set / fleet emit none (the scope
    # is dynamic and lives on the node, not as an edge).
    for node in nodes:
        targets = [
            e.target_id
            for e in registry.edges
            if e.source_id == node.action_id and e.kind is CapabilityEdgeKind.TARGETS
        ]
        if node.target_scope.kind is TargetScopeKind.REPO:
            if node.target_scope.repo_id not in targets:
                raise RepoGraphConfigError(
                    f"capability '{node.action_id}' target_scope repo "
                    f"'{node.target_scope.repo_id}' has no matching targets edge"
                )
        elif targets:
            raise RepoGraphConfigError(
                f"capability '{node.action_id}' target_scope "
                f"kind={node.target_scope.kind.value!r} must not emit a targets edge"
            )
