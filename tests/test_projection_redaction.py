from __future__ import annotations

from repograph import (
    DisclosureMode,
    GraphEdge,
    OntologyRelationshipKind,
    ProjectionBehavior,
    RepoGraph,
    RepoIdentity,
    RepoVisibility,
    build_public_projection,
)


def test_alias_only_private_repo_projects_as_public_placeholder() -> None:
    graph = RepoGraph.build(
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
        relationships=[
            GraphEdge(
                relationship_id="docs",
                source_id="public_docs",
                target_id="private_impl",
                kind=OntologyRelationshipKind.DOCUMENTS,
                visibility=RepoVisibility.PRIVATE,
                disclosure_mode=DisclosureMode.PRIVATE,
                projection_behavior=ProjectionBehavior.DROP_FROM_PUBLIC,
            )
        ],
    )
    projection = build_public_projection(graph, source_graph_id="private-manifest-fixture")
    assert projection.manifest["schema_kind"] == "projection"
    assert projection.manifest["schema_version"] == "1.0.0"
    assert projection.manifest["projection_profile"] == "public_safe"
    assert projection.manifest["repos"]["private_impl"]["canonical_name"] == "ManagedProjectPublic"
    assert "repo:private_impl" not in projection.redaction_report
    assert "edge:docs" in projection.redaction_report
    assert "PrivateImpl" not in str(projection.manifest)
