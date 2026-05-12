from __future__ import annotations

import pytest

from repograph import (
    DisclosureMode,
    GraphEdge,
    OntologyRelationshipKind,
    ProjectionBehavior,
    RepoEdge,
    RepoEdgeType,
    RepoGraph,
    RepoGraphConfigError,
    RepoIdentity,
    RepoVisibility,
)


def _node(repo_id: str) -> RepoIdentity:
    return RepoIdentity(
        repo_id=repo_id,
        canonical_name=repo_id,
        visibility=RepoVisibility.PUBLIC,
        disclosure_mode=DisclosureMode.PUBLIC,
        projection_behavior=ProjectionBehavior.PUBLIC_SAFE,
    )


def test_unknown_repo_edge_kind_fails() -> None:
    with pytest.raises(ValueError):
        RepoEdgeType("bogus")


def test_missing_source_target_fails() -> None:
    with pytest.raises(RepoGraphConfigError):
        RepoGraph.build(
            nodes=[_node("a")],
            edges=[RepoEdge(src="a", dst="ghost", type=RepoEdgeType.DISPATCHES_TO)],
            relationships=[],
        )


def test_non_import_api_edges_are_valid_relationships() -> None:
    graph = RepoGraph.build(
        nodes=[_node("producer"), _node("observer")],
        edges=[],
        relationships=[
            GraphEdge(
                relationship_id="heartbeat",
                source_id="observer",
                target_id="producer",
                kind=OntologyRelationshipKind.READS_HEARTBEAT,
                visibility=RepoVisibility.PUBLIC,
                disclosure_mode=DisclosureMode.PUBLIC,
                projection_behavior=ProjectionBehavior.PUBLIC_SAFE,
            )
        ],
    )
    assert graph.relationships_by_kind(OntologyRelationshipKind.READS_HEARTBEAT)
