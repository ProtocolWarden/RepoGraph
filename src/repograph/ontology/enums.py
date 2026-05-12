# SPDX-License-Identifier: AGPL-3.0-or-later
# Copyright (C) 2026 ProtocolWarden
"""Canonical and compatibility ontology enums."""

from __future__ import annotations

from enum import Enum


class ManifestKind(str, Enum):
    PLATFORM = "platform"
    PRIVATE = "private"
    PROJECT = "project"
    WORK_SCOPE = "work_scope"
    LOCAL = "local"


class RepoVisibility(str, Enum):
    PUBLIC = "public"
    PRIVATE = "private"
    LOCAL = "local"
    INTERNAL = "internal"
    RESTRICTED = "restricted"


Visibility = RepoVisibility


class Source(str, Enum):
    PLATFORM = "platform"
    PRIVATE = "private"
    PROJECT = "project"
    WORK_SCOPE = "work_scope"


class PlatformPlane(str, Enum):
    CONTROL_PLANE = "control_plane"
    CONTRACT_PLANE = "contract_plane"
    MANIFEST_PLANE = "manifest_plane"
    DEPLOYMENT_PLANE = "deployment_plane"
    GOVERNANCE_PLANE = "governance_plane"
    CONTEXT_PACKAGING = "context_packaging"
    MANAGED_PROJECT = "managed_project"
    CAPABILITY_PROVIDER = "capability_provider"
    DOCS_SURFACE = "docs_surface"
    CONTROL = "control"
    ONTOLOGY = "ontology"
    TOPOLOGY = "topology"
    TOPOGRAPHY = "topography"
    GOVERNANCE = "governance"
    DOCUMENTATION = "documentation"
    RUNTIME = "runtime"
    UTILITY = "utility"


class RepoKind(str, Enum):
    PLATFORM_CORE = "platform_core"
    CONTRACT_LIBRARY = "contract_library"
    MANIFEST_REPO = "manifest_repo"
    PRIVATE_MANIFEST_REPO = "private_manifest_repo"
    DEPLOYMENT_REPO = "deployment_repo"
    GOVERNANCE_REPO = "governance_repo"
    CONTEXT_PACKAGING_UTILITY = "context_packaging_utility"
    MANAGED_PROJECT = "managed_project"
    CAPABILITY_PROVIDER = "capability_provider"
    DOCS_REPO = "docs_repo"


class DisclosureMode(str, Enum):
    PUBLIC = "public"
    ALIAS_ONLY = "alias_only"
    PRIVATE = "private"
    LOCAL_ONLY = "local_only"
    SECRET = "secret"


class OwnerKind(str, Enum):
    PROTOCOL = "protocol"
    CONTROL_PLANE = "control_plane"
    MANIFEST = "manifest"
    DEPLOYMENT = "deployment"
    GOVERNANCE = "governance"
    MANAGED_PROJECT = "managed_project"
    UTILITY = "utility"
    DOCUMENTATION = "documentation"


class EntityKind(str, Enum):
    REPOSITORY = "Repository"
    PROJECT = "Project"
    MANAGED_PROJECT = "ManagedProject"
    MANAGED_REPOSITORY = "ManagedRepository"
    PUBLIC_REPOSITORY = "PublicRepository"
    PRIVATE_REPOSITORY = "PrivateRepository"
    PROTOCOL_REPOSITORY = "ProtocolRepository"
    ARTIFACT_PRODUCER = "ArtifactProducer"
    DEPLOYMENT_LAYER = "DeploymentLayer"
    EXECUTION_BACKEND = "ExecutionBackend"
    MANIFEST = "Manifest"
    ARTIFACT = "Artifact"
    RUN = "Run"
    AUDIT = "Audit"
    EVIDENCE = "Evidence"
    BINDING = "Binding"
    VISIBILITY_POLICY = "VisibilityPolicy"
    PROJECTION_RULE = "ProjectionRule"
    REDACTION_RULE = "RedactionRule"
    MIRROR_RELATIONSHIP = "MirrorRelationship"
    SUPERSET_RELATIONSHIP = "SupersetRelationship"
