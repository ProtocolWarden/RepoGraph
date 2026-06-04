from __future__ import annotations

from repograph import (
    DisclosureMode,
    ProjectionBehavior,
    RepoGraph,
    RepoIdentity,
    RepoVisibility,
    build_boundary_artifact,
    compute_artifact_hash,
)


def test_boundary_artifact_forbids_private_names_but_not_public_aliases() -> None:
    graph = RepoGraph.build(
        nodes=[
            RepoIdentity(
                repo_id="private_impl",
                canonical_name="PrivateImpl",
                visibility=RepoVisibility.PRIVATE,
                disclosure_mode=DisclosureMode.ALIAS_ONLY,
                public_alias="ManagedProjectPublic",
                aliases=("private_impl",),
                projection_behavior=ProjectionBehavior.DROP_FROM_PUBLIC,
            ),
            RepoIdentity(
                repo_id="public_docs",
                canonical_name="PublicDocs",
                visibility=RepoVisibility.PUBLIC,
                disclosure_mode=DisclosureMode.PUBLIC,
                projection_behavior=ProjectionBehavior.PUBLIC_SAFE,
            ),
        ],
        edges=[],
        relationships=[],
    )
    artifact = build_boundary_artifact(
        graph,
        source_graph_id="private-manifest-fixture",
        source_ref_or_commit="abc123",
    )
    assert artifact.schema_kind == "boundary_artifact"
    assert artifact.schema_version == "1.0.0"
    assert artifact.artifact_kind == "boundary_disclosure_artifact"
    assert "PrivateImpl" in artifact.forbidden_names
    assert "private_impl" in artifact.forbidden_names
    assert "ManagedProjectPublic" not in artifact.forbidden_names
    assert "ManagedProjectPublic" in artifact.allowed_aliases
    assert artifact.artifact_hash == compute_artifact_hash(artifact.core_payload())
