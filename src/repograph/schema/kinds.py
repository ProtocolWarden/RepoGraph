# SPDX-License-Identifier: AGPL-3.0-or-later
# Copyright (C) 2026 ProtocolWarden
"""Schema domains and governance policies."""

from __future__ import annotations

from enum import Enum


class SchemaKind(str, Enum):
    ONTOLOGY = "ontology"
    TOPOLOGY = "topology"
    PROJECTION = "projection"
    BOUNDARY_ARTIFACT = "boundary_artifact"
    CAPABILITIES = "capabilities"


class CompatibilityPolicy(str, Enum):
    FAIL_CLOSED = "fail_closed"
    MINOR_WITH_DEFAULTS = "minor_with_defaults"


class BreakingChangePolicy(str, Enum):
    MINOR_BUMP_REQUIRED = "minor_bump_required"
    BREAKING = "breaking"
