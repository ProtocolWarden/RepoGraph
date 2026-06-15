# SPDX-License-Identifier: AGPL-3.0-or-later
# Copyright (C) 2026 ProtocolWarden
"""Capability registry — the fleet's action plane.

A capability describes *what the ecosystem can do*, independent of how the
action executes. It is a first-class graph node with exactly one accountable
owner and typed edges to participating repos/artifacts. This package owns the
language; instances live in the platform/private manifests, and Custodian
(CAP1) verifies that ``invocation.ref`` resolves in the owning repo.
"""

from .compiler import (
    compile_capability,
    compile_registry,
    load_capability_registry,
)
from .enums import (
    LANE_REQUIRING_RISKS,
    REPO_TARGETING_EDGE_KINDS,
    CapabilityCategory,
    CapabilityEdgeKind,
    CapabilityInvocationKind,
    CapabilityRisk,
    TargetScopeKind,
)
from .models import (
    CapabilityEdge,
    CapabilityInput,
    CapabilityInvocation,
    CapabilityNode,
    CapabilityRegistry,
    TargetScope,
)
from .projection import project_capability_registry
from .validation import (
    parse_capability_category,
    parse_capability_invocation_kind,
    parse_capability_risk,
    parse_target_scope_kind,
    validate_capability_registry,
)

__all__ = [
    "CapabilityCategory",
    "CapabilityEdge",
    "CapabilityEdgeKind",
    "CapabilityInput",
    "CapabilityInvocation",
    "CapabilityInvocationKind",
    "CapabilityNode",
    "CapabilityRegistry",
    "CapabilityRisk",
    "LANE_REQUIRING_RISKS",
    "REPO_TARGETING_EDGE_KINDS",
    "TargetScope",
    "TargetScopeKind",
    "compile_capability",
    "compile_registry",
    "load_capability_registry",
    "parse_capability_category",
    "parse_capability_invocation_kind",
    "parse_capability_risk",
    "parse_target_scope_kind",
    "project_capability_registry",
    "validate_capability_registry",
]
