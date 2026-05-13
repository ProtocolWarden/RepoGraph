# SPDX-License-Identifier: AGPL-3.0-or-later
# Copyright (C) 2026 ProtocolWarden
"""RepoGraph schema governance primitives."""

from .compatibility import (
    classify_schema_change,
    ensure_supported_schema_version,
    is_supported_schema_version,
)
from .kinds import BreakingChangePolicy, CompatibilityPolicy, SchemaKind
from .validation import (
    canonical_json,
    compute_artifact_hash,
    validate_boundary_artifact_payload,
    validate_schema_document,
)
from .versions import CURRENT_SCHEMA_VERSIONS, SchemaVersion, schema_version_for

__all__ = [
    "BreakingChangePolicy",
    "CompatibilityPolicy",
    "CURRENT_SCHEMA_VERSIONS",
    "SchemaKind",
    "SchemaVersion",
    "canonical_json",
    "classify_schema_change",
    "compute_artifact_hash",
    "ensure_supported_schema_version",
    "is_supported_schema_version",
    "schema_version_for",
    "validate_boundary_artifact_payload",
    "validate_schema_document",
]
