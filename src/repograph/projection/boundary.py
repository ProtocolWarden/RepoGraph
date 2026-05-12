# SPDX-License-Identifier: AGPL-3.0-or-later
# Copyright (C) 2026 ProtocolWarden
"""Boundary artifact generation."""

from __future__ import annotations

from ..ontology.enums import DisclosureMode, RepoVisibility
from typing import TYPE_CHECKING

from .models import BoundaryDisclosureArtifact

if TYPE_CHECKING:
    from ..topology.models import RepoGraph


def _dedupe(values: list[str]) -> list[str]:
    seen: set[str] = set()
    out: list[str] = []
    for value in values:
        if not value or value in seen:
            continue
        seen.add(value)
        out.append(value)
    return out


def build_boundary_artifact(
    graph: RepoGraph,
    *,
    source_graph_id: str,
    source_ref_or_commit: str | None = None,
) -> BoundaryDisclosureArtifact:
    forbidden: list[str] = []
    aliases: list[str] = []
    redacted: list[str] = []
    rules = [
        "forbid_non_public_canonical_names",
        "forbid_non_public_aliases",
        "allow_public_alias_only_placeholders",
    ]
    for node in graph.list_nodes():
        if node.public_alias:
            aliases.append(node.public_alias)
        if node.visibility is RepoVisibility.PUBLIC and node.disclosure_mode is DisclosureMode.PUBLIC:
            continue
        forbidden.append(node.canonical_name)
        forbidden.extend(node.all_aliases)
        if node.disclosure_mode is DisclosureMode.ALIAS_ONLY and node.public_alias:
            redacted.append(f"{node.repo_id}:alias_only->{node.public_alias}")
            continue
        redacted.append(node.repo_id)
    return BoundaryDisclosureArtifact.create(
        source_graph_id=source_graph_id,
        source_ref_or_commit=source_ref_or_commit,
        forbidden_names=_dedupe(forbidden),
        allowed_aliases=_dedupe(aliases),
        redacted_entities=_dedupe(redacted),
        redaction_rules_applied=rules,
    )
