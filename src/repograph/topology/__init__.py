# SPDX-License-Identifier: AGPL-3.0-or-later
# Copyright (C) 2026 ProtocolWarden
"""Topology vocabulary and graph models."""

from .edges import EdgeCategory, EdgeKind, OntologyRelationshipKind, RELATIONSHIP_EDGE_CATEGORIES, RepoEdgeType
from .models import GraphEdge, OntologyRelationship, RepoEdge, RepoGraph
from .validation import (
    parse_relationship_kind,
    parse_relationship_projection_behavior,
    parse_repo_edge_type,
    validate_graph_topology,
)

__all__ = [
    "EdgeCategory",
    "EdgeKind",
    "GraphEdge",
    "OntologyRelationship",
    "OntologyRelationshipKind",
    "RELATIONSHIP_EDGE_CATEGORIES",
    "RepoEdge",
    "RepoEdgeType",
    "RepoGraph",
    "parse_relationship_kind",
    "parse_relationship_projection_behavior",
    "parse_repo_edge_type",
    "validate_graph_topology",
]
