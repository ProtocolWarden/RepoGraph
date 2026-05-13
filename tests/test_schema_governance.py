from __future__ import annotations

import pytest

from repograph import (
    BoundaryDisclosureArtifact,
    RepoGraphConfigError,
    SchemaKind,
    DisclosureMode,
    ProjectionBehavior,
    RepoGraph,
    RepoIdentity,
    RepoVisibility,
    build_boundary_artifact,
    build_public_projection,
    classify_schema_change,
    compute_artifact_hash,
    ensure_supported_schema_version,
    is_supported_schema_version,
    validate_boundary_artifact_payload,
    schema_version_for,
)
from repograph.diff import RepoGraphDiff


def _graph() -> RepoGraph:
    return RepoGraph.build(
        nodes=[
            RepoIdentity(
                repo_id="public_docs",
                canonical_name="PublicDocs",
                visibility=RepoVisibility.PUBLIC,
                disclosure_mode=DisclosureMode.PUBLIC,
                projection_behavior=ProjectionBehavior.PUBLIC_SAFE,
            ),
            RepoIdentity(
                repo_id="private_impl",
                canonical_name="PrivateImpl",
                visibility=RepoVisibility.PRIVATE,
                disclosure_mode=DisclosureMode.ALIAS_ONLY,
                public_alias="ManagedProjectPublic",
                aliases=("private_impl",),
                projection_behavior=ProjectionBehavior.DROP_FROM_PUBLIC,
            ),
        ],
        edges=[],
        relationships=[],
    )


def test_schema_versions_are_explicit_and_supported() -> None:
    current = schema_version_for(SchemaKind.BOUNDARY_ARTIFACT)
    assert current.version == "1.0.0"
    assert is_supported_schema_version(SchemaKind.PROJECTION, "1.0.0")
    with pytest.raises(RepoGraphConfigError):
        ensure_supported_schema_version(SchemaKind.BOUNDARY_ARTIFACT, "9.9.9")


def test_boundary_artifact_contains_schema_and_hash() -> None:
    artifact = build_boundary_artifact(
        _graph(),
        source_graph_id="PrivateManifest",
        source_ref_or_commit="abc123",
    )
    data = artifact.to_dict()
    assert data["schema_kind"] == "boundary_artifact"
    assert data["schema_version"] == "1.0.0"
    assert data["artifact_kind"] == "boundary_disclosure_artifact"
    assert data["artifact_hash"] == compute_artifact_hash(artifact.core_payload())


def test_projection_manifest_includes_schema_metadata() -> None:
    projection = build_public_projection(_graph(), source_graph_id="PrivateManifest")
    assert projection.manifest["schema_kind"] == "projection"
    assert projection.manifest["schema_version"] == "1.0.0"
    assert projection.manifest["projection_profile"] == "public_safe"
    assert projection.projection_profile == "public_safe"


def test_schema_change_classification_flags_breaking_changes() -> None:
    before = schema_version_for(SchemaKind.PROJECTION)
    after = type(before)(
        schema_kind=before.schema_kind,
        version="2.0.0",
        compatibility_policy=before.compatibility_policy,
        breaking_change_policy=before.breaking_change_policy,
    )
    assert classify_schema_change(before, after) == "breaking"


def test_repo_graph_diff_detects_visibility_escalation() -> None:
    before = _graph()
    after = RepoGraph.build(
        nodes=[
            RepoIdentity(
                repo_id="public_docs",
                canonical_name="PublicDocs",
                visibility=RepoVisibility.PUBLIC,
                disclosure_mode=DisclosureMode.PUBLIC,
                projection_behavior=ProjectionBehavior.PUBLIC_SAFE,
            ),
            RepoIdentity(
                repo_id="private_impl",
                canonical_name="PrivateImpl",
                visibility=RepoVisibility.PUBLIC,
                disclosure_mode=DisclosureMode.PUBLIC,
                projection_behavior=ProjectionBehavior.PUBLIC_SAFE,
            ),
        ],
        edges=[],
        relationships=[],
    )
    diff = RepoGraphDiff.compare(before, after, before_ref="before", after_ref="after")
    assert diff.has_high_severity
    assert any(change.kind == "visibility_changed" for change in diff.changes)


def test_boundary_artifact_validation_rejects_hash_mismatch() -> None:
    artifact = build_boundary_artifact(
        _graph(),
        source_graph_id="PrivateManifest",
        source_ref_or_commit="abc123",
    )
    payload = artifact.to_dict()
    payload["artifact_hash"] = "deadbeef"
    with pytest.raises(RepoGraphConfigError):
        validate_boundary_artifact_payload(payload)


def test_boundary_artifact_validation_rejects_signature_without_verifier() -> None:
    artifact = build_boundary_artifact(
        _graph(),
        source_graph_id="PrivateManifest",
        source_ref_or_commit="abc123",
    )
    payload = artifact.to_dict()
    payload["signature"] = "signed"
    payload["signature_algorithm"] = "ed25519"
    payload["issuer"] = "PrivateManifest"
    payload["signed_at"] = "2026-05-13T00:00:00Z"
    with pytest.raises(RepoGraphConfigError):
        validate_boundary_artifact_payload(payload)
