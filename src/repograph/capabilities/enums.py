# SPDX-License-Identifier: AGPL-3.0-or-later
# Copyright (C) 2026 ProtocolWarden
"""Capability registry vocabulary.

The capability plane is graph-native: a capability is a first-class node with
typed edges to repos/artifacts, NOT a property hung off a repo. These enums are
the language; instances live in the platform/private manifests.
"""

from __future__ import annotations

from enum import Enum


class CapabilityCategory(str, Enum):
    AUDIT = "audit"
    ORCHESTRATION = "orchestration"
    EXECUTION = "execution"
    MIGRATION = "migration"
    VERIFICATION = "verification"
    MAINTENANCE = "maintenance"


class CapabilityRisk(str, Enum):
    READ_ONLY = "read_only"
    MUTATES_REPO = "mutates_repo"
    MUTATES_FLEET = "mutates_fleet"
    IRREVERSIBLE = "irreversible"


class CapabilityEdgeKind(str, Enum):
    OWNS = "owns"
    TARGETS = "targets"
    EXECUTES = "executes"
    REQUIRES = "requires"
    VALIDATES = "validates"
    PRODUCES = "produces"


class CapabilityInvocationKind(str, Enum):
    ENTRYPOINT = "entrypoint"
    CLI = "cli"
    EXECUTOR = "executor"


class TargetScopeKind(str, Enum):
    REPO = "repo"
    REPO_SET = "repo_set"
    FLEET = "fleet"


# Edge kinds whose ``target_id`` must resolve to a known repo. PRODUCES is
# excluded: its target is an artifact identifier, not a repo.
REPO_TARGETING_EDGE_KINDS: frozenset[CapabilityEdgeKind] = frozenset({
    CapabilityEdgeKind.OWNS,
    CapabilityEdgeKind.TARGETS,
    CapabilityEdgeKind.EXECUTES,
    CapabilityEdgeKind.REQUIRES,
    CapabilityEdgeKind.VALIDATES,
})


# Risk levels that demand an explicit, deliberate route — dangerous actions must
# not ride the default lane.
LANE_REQUIRING_RISKS: frozenset[CapabilityRisk] = frozenset({
    CapabilityRisk.MUTATES_FLEET,
    CapabilityRisk.IRREVERSIBLE,
})
