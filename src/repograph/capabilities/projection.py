# SPDX-License-Identifier: AGPL-3.0-or-later
# Copyright (C) 2026 ProtocolWarden
"""Capability registry projection.

Public-safe projection drops capabilities that are not public — same boundary
discipline the repo graph already applies to private entities.
"""

from __future__ import annotations

from ..projection.models import DEFAULT_PROJECTION_PROFILE_RULES, ProjectionProfileKind
from .models import CapabilityRegistry


def project_capability_registry(
    registry: CapabilityRegistry,
    profile_kind: ProjectionProfileKind,
) -> CapabilityRegistry:
    rules = DEFAULT_PROJECTION_PROFILE_RULES[profile_kind]
    public_safe = rules.output_safety_class == "public_safe"

    kept = [
        node
        for node in registry.list_capabilities()
        if not public_safe or node.is_public
    ]
    kept_ids = {node.action_id for node in kept}
    edges = [edge for edge in registry.edges if edge.source_id in kept_ids]
    return CapabilityRegistry.build(kept, edges)
