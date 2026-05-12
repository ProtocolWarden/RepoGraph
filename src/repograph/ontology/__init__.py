# SPDX-License-Identifier: AGPL-3.0-or-later
# Copyright (C) 2026 ProtocolWarden
"""Ontology vocabulary and models."""

from .enums import (
    DisclosureMode,
    EntityKind,
    ManifestKind,
    OwnerKind,
    PlatformPlane,
    RepoKind,
    RepoVisibility,
    Source,
    Visibility,
)
from .models import LOCAL_ANNOTATION_FIELDS, ManifestHeader, RepoIdentity, RepoNode
from .validation import (
    enforce_platform_public_only,
    parse_disclosure_mode,
    parse_entity_projection_behavior,
    parse_kind,
    parse_owner_kind,
    parse_plane,
    parse_visibility,
)

__all__ = [
    "DisclosureMode",
    "EntityKind",
    "LOCAL_ANNOTATION_FIELDS",
    "ManifestHeader",
    "ManifestKind",
    "OwnerKind",
    "PlatformPlane",
    "RepoIdentity",
    "RepoKind",
    "RepoNode",
    "RepoVisibility",
    "Source",
    "Visibility",
    "enforce_platform_public_only",
    "parse_disclosure_mode",
    "parse_entity_projection_behavior",
    "parse_kind",
    "parse_owner_kind",
    "parse_plane",
    "parse_visibility",
]
