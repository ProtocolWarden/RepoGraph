# SPDX-License-Identifier: AGPL-3.0-or-later
# Copyright (C) 2026 ProtocolWarden
"""Projection helpers and boundary artifact generation."""

from .boundary import BoundaryDisclosureArtifact, build_boundary_artifact
from .models import (
    DEFAULT_PROJECTION_PROFILE_RULES,
    ProjectionBehavior,
    ProjectionProfile,
    ProjectionProfileKind,
    ProjectionProfileRules,
    PublicGraphProjection,
    build_projection_profile,
)
from .redaction import public_name
from .rules import PUBLIC_RELATIONSHIP_BEHAVIORS, default_projection_behavior_for_visibility
from .validation import can_project_node, can_project_relationship, parse_projection_behavior
from .rules import build_public_projection, to_public_manifest_dict

__all__ = [
    "BoundaryDisclosureArtifact",
    "DEFAULT_PROJECTION_PROFILE_RULES",
    "ProjectionBehavior",
    "ProjectionProfile",
    "ProjectionProfileKind",
    "ProjectionProfileRules",
    "PUBLIC_RELATIONSHIP_BEHAVIORS",
    "PublicGraphProjection",
    "build_boundary_artifact",
    "build_public_projection",
    "build_projection_profile",
    "can_project_node",
    "can_project_relationship",
    "default_projection_behavior_for_visibility",
    "parse_projection_behavior",
    "public_name",
    "to_public_manifest_dict",
]
