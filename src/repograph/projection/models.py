# SPDX-License-Identifier: AGPL-3.0-or-later
# Copyright (C) 2026 ProtocolWarden
"""Projection models."""

from __future__ import annotations

from dataclasses import asdict, dataclass
from datetime import datetime, timezone
from enum import Enum
from typing import Any

from ..schema.kinds import SchemaKind
from ..schema.validation import compute_artifact_hash
from ..schema.versions import schema_version_for


class ProjectionBehavior(str, Enum):
    PUBLIC_SAFE = "public_safe"
    PRIVATE_ONLY = "private_only"
    LOCAL_ONLY = "local_only"
    REDACT = "redact"
    REDACTED_PUBLIC_STUB = "redacted_public_stub"
    DROP_FROM_PUBLIC = "drop_from_public"


class ProjectionProfileKind(str, Enum):
    PUBLIC_SAFE = "public_safe"
    PUBLIC_DOCS = "public_docs"
    AUDIT_FULL = "audit_full"
    OPERATOR_INTERNAL = "operator_internal"
    DEPLOYMENT_LOCAL = "deployment_local"
    OBSERVABILITY_INTERNAL = "observability_internal"


@dataclass(frozen=True)
class ProjectionProfileRules:
    allowed_entity_kinds: tuple[str, ...]
    allowed_edge_kinds: tuple[str, ...]
    allowed_fields: tuple[str, ...]
    redaction_rules: tuple[str, ...]
    collapse_rules: tuple[str, ...]
    visibility_transformations: tuple[str, ...]
    output_safety_class: str


@dataclass(frozen=True)
class ProjectionProfile:
    kind: ProjectionProfileKind
    schema_kind: str = SchemaKind.PROJECTION.value
    schema_version: str = schema_version_for(SchemaKind.PROJECTION).version
    rules: ProjectionProfileRules = ProjectionProfileRules(
        allowed_entity_kinds=(),
        allowed_edge_kinds=(),
        allowed_fields=(),
        redaction_rules=(),
        collapse_rules=(),
        visibility_transformations=(),
        output_safety_class="public_safe",
    )
    description: str | None = None


DEFAULT_PROJECTION_PROFILE_RULES: dict[ProjectionProfileKind, ProjectionProfileRules] = {
    ProjectionProfileKind.PUBLIC_SAFE: ProjectionProfileRules(
        allowed_entity_kinds=("Repository", "Project", "Manifest", "Capability"),
        allowed_edge_kinds=("consumes_manifest", "publishes_projection", "reads_artifact", "writes_artifact", "deploys", "hosts"),
        allowed_fields=("canonical_name", "visibility", "projection_behavior", "public_alias", "github_url", "description", "owner", "scope", "runtime_role", "kind", "metadata"),
        redaction_rules=("hide_private_names", "hide_local_paths", "drop_secret_refs", "collapse_private_entities"),
        collapse_rules=("private_entity_to_public_placeholder",),
        visibility_transformations=("private_to_public_placeholder",),
        output_safety_class="public_safe",
    ),
    ProjectionProfileKind.PUBLIC_DOCS: ProjectionProfileRules(
        allowed_entity_kinds=("Repository", "Project", "Manifest", "Capability"),
        allowed_edge_kinds=("consumes_manifest", "publishes_projection", "reads_artifact", "writes_artifact", "deploys", "hosts"),
        allowed_fields=("canonical_name", "visibility", "projection_behavior", "public_alias", "github_url", "description", "owner", "scope", "runtime_role", "kind", "metadata"),
        redaction_rules=("hide_private_names", "hide_local_paths", "drop_secret_refs"),
        collapse_rules=("private_entity_to_public_placeholder",),
        visibility_transformations=("private_to_public_placeholder",),
        output_safety_class="public_safe",
    ),
    ProjectionProfileKind.AUDIT_FULL: ProjectionProfileRules(
        allowed_entity_kinds=("Repository", "Project", "Manifest", "Artifact", "Audit"),
        allowed_edge_kinds=("consumes_manifest", "publishes_projection", "reads_artifact", "writes_artifact", "deploys", "hosts", "validates_output", "reports_to"),
        allowed_fields=("canonical_name", "visibility", "projection_behavior", "public_alias", "github_url", "description", "owner", "scope", "runtime_role", "kind", "metadata", "local_path", "local_port", "env_file", "endpoint_override", "cache_path"),
        redaction_rules=("retain_sensitive_fields_for_audit",),
        collapse_rules=(),
        visibility_transformations=("retain_internal_visibility",),
        output_safety_class="non_public_safe",
    ),
    ProjectionProfileKind.OPERATOR_INTERNAL: ProjectionProfileRules(
        allowed_entity_kinds=("Repository", "Project", "Manifest", "Run", "Audit", "Evidence"),
        allowed_edge_kinds=("consumes_manifest", "publishes_projection", "reads_artifact", "writes_artifact", "reports_to", "validates_output"),
        allowed_fields=("canonical_name", "visibility", "projection_behavior", "public_alias", "github_url", "description", "owner", "scope", "runtime_role", "kind", "metadata", "local_path", "local_port", "env_file", "endpoint_override", "cache_path"),
        redaction_rules=("retain_operator_internal_context",),
        collapse_rules=(),
        visibility_transformations=("retain_internal_visibility",),
        output_safety_class="non_public_safe",
    ),
    ProjectionProfileKind.DEPLOYMENT_LOCAL: ProjectionProfileRules(
        allowed_entity_kinds=("Repository", "Project", "Manifest", "DeploymentLayer"),
        allowed_edge_kinds=("deploys", "hosts", "consumes_manifest", "reads_artifact", "writes_artifact"),
        allowed_fields=("canonical_name", "visibility", "projection_behavior", "public_alias", "description", "kind", "metadata", "local_path", "local_port", "env_file", "endpoint_override", "cache_path", "gpu_required", "runtime_hints"),
        redaction_rules=("retain_topography_only",),
        collapse_rules=(),
        visibility_transformations=("retain_local_visibility",),
        output_safety_class="non_public_safe",
    ),
    ProjectionProfileKind.OBSERVABILITY_INTERNAL: ProjectionProfileRules(
        allowed_entity_kinds=("Repository", "Project", "Manifest", "Run", "Audit", "Evidence"),
        allowed_edge_kinds=("reads_artifact", "writes_artifact", "reports_to", "indexes_output", "polls_status"),
        allowed_fields=("canonical_name", "visibility", "projection_behavior", "kind", "metadata", "description"),
        redaction_rules=("retain_internal_observability_context",),
        collapse_rules=(),
        visibility_transformations=("retain_internal_visibility",),
        output_safety_class="non_public_safe",
    ),
}


def build_projection_profile(kind: ProjectionProfileKind) -> ProjectionProfile:
    return ProjectionProfile(kind=kind, rules=DEFAULT_PROJECTION_PROFILE_RULES[kind])


@dataclass(frozen=True)
class BoundaryDisclosureArtifact:
    schema_kind: str
    schema_version: str
    artifact_kind: str
    source_graph_id: str
    source_ref_or_commit: str | None
    generated_at: str
    artifact_hash: str | None
    signature: str | None
    signature_algorithm: str | None
    issuer: str | None
    signed_at: str | None
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
        schema_version: str | None = None,
        artifact_hash: str | None = None,
        signature: str | None = None,
        signature_algorithm: str | None = None,
        issuer: str | None = None,
        signed_at: str | None = None,
    ) -> "BoundaryDisclosureArtifact":
        artifact = cls(
            schema_kind=SchemaKind.BOUNDARY_ARTIFACT.value,
            schema_version=schema_version or schema_version_for(SchemaKind.BOUNDARY_ARTIFACT).version,
            artifact_kind="boundary_disclosure_artifact",
            source_graph_id=source_graph_id,
            source_ref_or_commit=source_ref_or_commit,
            generated_at=datetime.now(timezone.utc).isoformat(),
            artifact_hash=artifact_hash,
            signature=signature,
            signature_algorithm=signature_algorithm,
            issuer=issuer,
            signed_at=signed_at,
            forbidden_names=tuple(forbidden_names),
            allowed_aliases=tuple(allowed_aliases),
            redacted_entities=tuple(redacted_entities),
            redaction_rules_applied=tuple(redaction_rules_applied),
        )
        if artifact.artifact_hash is None:
            return artifact.with_hash()
        return artifact

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)

    def core_payload(self) -> dict[str, Any]:
        payload = self.to_dict()
        payload.pop("artifact_hash", None)
        payload.pop("signature", None)
        payload.pop("signed_at", None)
        return payload

    def with_hash(self) -> "BoundaryDisclosureArtifact":
        return BoundaryDisclosureArtifact(
            schema_kind=self.schema_kind,
            schema_version=self.schema_version,
            artifact_kind=self.artifact_kind,
            source_graph_id=self.source_graph_id,
            source_ref_or_commit=self.source_ref_or_commit,
            generated_at=self.generated_at,
            artifact_hash=compute_artifact_hash(self.core_payload()),
            signature=self.signature,
            signature_algorithm=self.signature_algorithm,
            issuer=self.issuer,
            signed_at=self.signed_at,
            forbidden_names=self.forbidden_names,
            allowed_aliases=self.allowed_aliases,
            redacted_entities=self.redacted_entities,
            redaction_rules_applied=self.redaction_rules_applied,
        )


@dataclass(frozen=True)
class PublicGraphProjection:
    graph: Any
    manifest: dict[str, Any]
    redaction_report: tuple[str, ...]
    boundary_artifact: BoundaryDisclosureArtifact
    projection_profile: str
