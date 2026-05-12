# SPDX-License-Identifier: AGPL-3.0-or-later
# Copyright (C) 2026 ProtocolWarden
"""Ontology-shaped identity models."""

from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING

from ..errors import RepoGraphConfigError
from .enums import (
    DisclosureMode,
    EntityKind,
    ManifestKind,
    OwnerKind,
    PlatformPlane,
    RepoKind,
    RepoVisibility,
    Source,
)

if TYPE_CHECKING:
    from ..topology.models import RepoGraph

MetadataValue = str | int | float | bool


LOCAL_ANNOTATION_FIELDS: frozenset[str] = frozenset({
    "local_path",
    "local_port",
    "env_file",
    "endpoint_override",
    "cache_path",
    "gpu_required",
    "runtime_hints",
    "local_endpoint",
})


@dataclass(frozen=True)
class ManifestHeader:
    manifest_kind: ManifestKind
    manifest_version: str


@dataclass(frozen=True)
class RepoIdentity:
    repo_id: str
    canonical_name: str
    visibility: RepoVisibility = RepoVisibility.PUBLIC
    disclosure_mode: DisclosureMode = DisclosureMode.PUBLIC
    plane: PlatformPlane | None = None
    repo_kind: RepoKind | None = None
    public_alias: str | None = None
    aliases: tuple[str, ...] = ()
    description: str | None = None
    legacy_names: tuple[str, ...] = ()
    github_url: str | None = None
    runtime_role: str | None = None
    kind: EntityKind = EntityKind.REPOSITORY
    owner: str | None = None
    scope: str | None = None
    metadata: tuple[tuple[str, MetadataValue], ...] = ()
    projection_policy: str | None = None
    projection_behavior: object | None = None
    redaction_label: str | None = None
    private_binding_refs: tuple[str, ...] = ()
    local_overlay_refs: tuple[str, ...] = ()
    source: Source = Source.PLATFORM
    owner_kind: OwnerKind | None = None
    local_path: str | None = None
    local_port: int | None = None
    env_file: str | None = None
    endpoint_override: str | None = None
    cache_path: str | None = None
    gpu_required: bool | None = None
    runtime_hints: tuple[tuple[str, MetadataValue], ...] = ()

    def __post_init__(self) -> None:
        if (
            self.disclosure_mode is DisclosureMode.ALIAS_ONLY
            and not self.public_alias
        ):
            raise RepoGraphConfigError(
                f"repo '{self.repo_id}' requires public_alias when disclosure_mode='alias_only'"
            )
        if self.visibility is RepoVisibility.LOCAL and self.disclosure_mode is DisclosureMode.PUBLIC:
            raise RepoGraphConfigError(
                f"repo '{self.repo_id}' cannot be local visibility with public disclosure"
            )
        lowered = {self.repo_id.lower(), self.canonical_name.lower()}
        if "warehouse" in lowered:
            if self.repo_kind not in (None, RepoKind.CONTEXT_PACKAGING_UTILITY):
                raise RepoGraphConfigError(
                    "Warehouse must classify as context_packaging_utility"
                )
            if self.plane in {
                PlatformPlane.CONTROL,
                PlatformPlane.CONTROL_PLANE,
                PlatformPlane.ONTOLOGY,
                PlatformPlane.TOPOLOGY,
                PlatformPlane.MANIFEST_PLANE,
            }:
                raise RepoGraphConfigError(
                    "Warehouse may not classify as control, ontology, topology, or manifest authority"
                )
            if self.owner_kind in {OwnerKind.CONTROL_PLANE, OwnerKind.MANIFEST, OwnerKind.GOVERNANCE}:
                raise RepoGraphConfigError(
                    "Warehouse may not classify as control-plane, manifest, or governance owner"
                )

    @property
    def all_aliases(self) -> tuple[str, ...]:
        seen: set[str] = set()
        values: list[str] = []
        for value in (*self.aliases, *self.legacy_names):
            if not value or value in seen:
                continue
            seen.add(value)
            values.append(value)
        return tuple(values)


RepoNode = RepoIdentity


@dataclass(frozen=True)
class PrivateManifest:
    header: ManifestHeader
    graph: "RepoGraph"
