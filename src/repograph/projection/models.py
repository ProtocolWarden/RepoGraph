# SPDX-License-Identifier: AGPL-3.0-or-later
# Copyright (C) 2026 ProtocolWarden
"""Projection models."""

from __future__ import annotations

from dataclasses import asdict, dataclass
from datetime import datetime, timezone
from enum import Enum
from typing import Any


class ProjectionBehavior(str, Enum):
    PUBLIC_SAFE = "public_safe"
    PRIVATE_ONLY = "private_only"
    LOCAL_ONLY = "local_only"
    REDACT = "redact"
    REDACTED_PUBLIC_STUB = "redacted_public_stub"
    DROP_FROM_PUBLIC = "drop_from_public"


class ProjectionProfile(str, Enum):
    PUBLIC = "public"
    PRIVATE = "private"
    LOCAL = "local"


@dataclass(frozen=True)
class BoundaryDisclosureArtifact:
    source_graph_id: str
    source_ref_or_commit: str | None
    generated_at: str
    forbidden_names: tuple[str, ...]
    allowed_aliases: tuple[str, ...]
    redacted_entities: tuple[str, ...]
    redaction_rules_applied: tuple[str, ...]

    @classmethod
    def create(
        cls,
        *,
        source_graph_id: str,
        source_ref_or_commit: str | None,
        forbidden_names: list[str],
        allowed_aliases: list[str],
        redacted_entities: list[str],
        redaction_rules_applied: list[str],
    ) -> "BoundaryDisclosureArtifact":
        return cls(
            source_graph_id=source_graph_id,
            source_ref_or_commit=source_ref_or_commit,
            generated_at=datetime.now(timezone.utc).isoformat(),
            forbidden_names=tuple(forbidden_names),
            allowed_aliases=tuple(allowed_aliases),
            redacted_entities=tuple(redacted_entities),
            redaction_rules_applied=tuple(redaction_rules_applied),
        )

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(frozen=True)
class PublicGraphProjection:
    graph: Any
    manifest: dict[str, Any]
    redaction_report: tuple[str, ...]
    boundary_artifact: BoundaryDisclosureArtifact
