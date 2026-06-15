# SPDX-License-Identifier: AGPL-3.0-or-later
# Copyright (C) 2026 ProtocolWarden
"""Schema version definitions."""

from __future__ import annotations

from dataclasses import dataclass

from .kinds import BreakingChangePolicy, CompatibilityPolicy, SchemaKind


@dataclass(frozen=True)
class SchemaVersion:
    schema_kind: SchemaKind
    version: str
    compatibility_policy: CompatibilityPolicy = CompatibilityPolicy.FAIL_CLOSED
    breaking_change_policy: BreakingChangePolicy = BreakingChangePolicy.MINOR_BUMP_REQUIRED


CURRENT_SCHEMA_VERSIONS: dict[SchemaKind, SchemaVersion] = {
    SchemaKind.ONTOLOGY: SchemaVersion(SchemaKind.ONTOLOGY, "1.0.0"),
    SchemaKind.TOPOLOGY: SchemaVersion(SchemaKind.TOPOLOGY, "1.0.0"),
    SchemaKind.PROJECTION: SchemaVersion(SchemaKind.PROJECTION, "1.0.0"),
    SchemaKind.BOUNDARY_ARTIFACT: SchemaVersion(SchemaKind.BOUNDARY_ARTIFACT, "1.0.0"),
    SchemaKind.CAPABILITIES: SchemaVersion(SchemaKind.CAPABILITIES, "1.0.0"),
}


def schema_version_for(kind: SchemaKind) -> SchemaVersion:
    return CURRENT_SCHEMA_VERSIONS[kind]
