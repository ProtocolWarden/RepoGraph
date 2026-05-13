# SPDX-License-Identifier: AGPL-3.0-or-later
# Copyright (C) 2026 ProtocolWarden
"""RepoGraph diff and drift reporting."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from .ontology.enums import DisclosureMode, RepoVisibility
from .ontology.models import RepoIdentity
from .projection.models import BoundaryDisclosureArtifact, ProjectionBehavior, PublicGraphProjection
from .topology.models import GraphEdge, RepoGraph


@dataclass(frozen=True)
class GraphChange:
    kind: str
    subject: str
    severity: str
    detail: str


@dataclass(frozen=True)
class GraphDiffResult:
    before_ref: str | None
    after_ref: str | None
    changes: tuple[GraphChange, ...] = field(default_factory=tuple)

    @property
    def has_high_severity(self) -> bool:
        return any(change.severity in {"high", "critical"} for change in self.changes)

    def to_dict(self) -> dict[str, Any]:
        return {
            "before_ref": self.before_ref,
            "after_ref": self.after_ref,
            "has_high_severity": self.has_high_severity,
            "changes": [change.__dict__ for change in self.changes],
        }

    def highest_severity(self) -> str:
        order = {"low": 0, "medium": 1, "high": 2, "critical": 3}
        return max(
            (change.severity for change in self.changes),
            key=lambda severity: order.get(severity, -1),
            default="low",
        )


class RepoGraphDiff:
    @staticmethod
    def compare(
        before: RepoGraph,
        after: RepoGraph,
        *,
        before_ref: str | None = None,
        after_ref: str | None = None,
    ) -> GraphDiffResult:
        changes: list[GraphChange] = []
        before_ids = set(before.nodes)
        after_ids = set(after.nodes)

        for repo_id in sorted(after_ids - before_ids):
            changes.append(GraphChange("entity_added", repo_id, "medium", "new entity"))
        for repo_id in sorted(before_ids - after_ids):
            changes.append(GraphChange("entity_removed", repo_id, "high", "entity removed"))
        for repo_id in sorted(before_ids & after_ids):
            changes.extend(_compare_nodes(repo_id, before.nodes[repo_id], after.nodes[repo_id]))

        before_rel = {r.relationship_id: r for r in before.list_relationships()}
        after_rel = {r.relationship_id: r for r in after.list_relationships()}
        for rel_id in sorted(after_rel.keys() - before_rel.keys()):
            changes.append(GraphChange("edge_added", rel_id, "medium", "relationship added"))
        for rel_id in sorted(before_rel.keys() - after_rel.keys()):
            changes.append(GraphChange("edge_removed", rel_id, "high", "relationship removed"))
        for rel_id in sorted(before_rel.keys() & after_rel.keys()):
            changes.extend(_compare_relationship(rel_id, before_rel[rel_id], after_rel[rel_id]))

        return GraphDiffResult(before_ref=before_ref, after_ref=after_ref, changes=tuple(changes))

    @staticmethod
    def compare_public_projection(
        before: PublicGraphProjection,
        after: PublicGraphProjection,
        *,
        before_ref: str | None = None,
        after_ref: str | None = None,
    ) -> GraphDiffResult:
        changes = list(
            RepoGraphDiff.compare(
                before.graph,
                after.graph,
                before_ref=before_ref,
                after_ref=after_ref,
            ).changes
        )
        changes.extend(_compare_projection_state(before, after))
        return GraphDiffResult(before_ref=before_ref, after_ref=after_ref, changes=tuple(changes))

    @staticmethod
    def compare_boundary_artifacts(
        before: BoundaryDisclosureArtifact,
        after: BoundaryDisclosureArtifact,
        *,
        before_ref: str | None = None,
        after_ref: str | None = None,
    ) -> GraphDiffResult:
        changes = _compare_boundary_artifact(before, after)
        return GraphDiffResult(before_ref=before_ref, after_ref=after_ref, changes=tuple(changes))


def _compare_nodes(repo_id: str, before: RepoIdentity, after: RepoIdentity) -> list[GraphChange]:
    out: list[GraphChange] = []
    fields = ("canonical_name", "visibility", "disclosure_mode", "public_alias", "aliases", "kind", "repo_kind")
    for field_name in fields:
        before_value = getattr(before, field_name)
        after_value = getattr(after, field_name)
        if before_value != after_value:
            severity = "medium"
            kind = "entity_changed"
            if field_name == "visibility" and _is_visibility_escalation(before.visibility, after.visibility):
                severity = "high"
                kind = "visibility_changed"
            elif field_name == "disclosure_mode" and _is_visibility_escalation_mode(before.disclosure_mode, after.disclosure_mode):
                severity = "high"
                kind = "disclosure_mode_changed"
            elif field_name == "repo_kind":
                kind = "ownership_changed"
            out.append(
                GraphChange(
                    kind,
                    repo_id,
                    severity,
                    f"{field_name}: {before_value!r} -> {after_value!r}",
                )
            )
    return out


def _compare_relationship(rel_id: str, before: GraphEdge, after: GraphEdge) -> list[GraphChange]:
    out: list[GraphChange] = []
    fields = ("source_id", "target_id", "kind", "visibility", "disclosure_mode", "projection_behavior")
    for field_name in fields:
        before_value = getattr(before, field_name)
        after_value = getattr(after, field_name)
        if before_value != after_value:
            severity = "medium"
            kind = "edge_changed"
            if field_name == "visibility" and _is_visibility_escalation(before.visibility, after.visibility):
                severity = "high"
                kind = "edge_visibility_changed"
            elif field_name == "projection_behavior" and after.projection_behavior is not ProjectionBehavior.PUBLIC_SAFE:
                severity = "high"
                kind = "projection_downgraded"
            out.append(
                GraphChange(
                    kind,
                    rel_id,
                    severity,
                    f"{field_name}: {before_value!r} -> {after_value!r}",
                )
            )
    return out


def _compare_projection_state(before: PublicGraphProjection, after: PublicGraphProjection) -> list[GraphChange]:
    out: list[GraphChange] = []
    if before.projection_profile != after.projection_profile:
        out.append(
            GraphChange(
                "projection_profile_changed",
                "projection",
                "high" if after.projection_profile != "public_safe" else "medium",
                f"projection_profile: {before.projection_profile!r} -> {after.projection_profile!r}",
            )
        )
    if before.redaction_report != after.redaction_report:
        out.append(
            GraphChange(
                "redaction_report_changed",
                "projection",
                "medium",
                "redaction report changed",
            )
        )
    if before.manifest != after.manifest:
        out.append(
            GraphChange(
                "public_projection_changed",
                "projection",
                "medium",
                "public projection manifest changed",
            )
        )
    if before.boundary_artifact != after.boundary_artifact:
        out.extend(_compare_boundary_artifact(before.boundary_artifact, after.boundary_artifact))
    return out


def _compare_boundary_artifact(
    before: BoundaryDisclosureArtifact,
    after: BoundaryDisclosureArtifact,
) -> list[GraphChange]:
    out: list[GraphChange] = []
    fields = (
        "schema_kind",
        "schema_version",
        "artifact_kind",
        "source_graph_id",
        "source_ref_or_commit",
        "forbidden_names",
        "allowed_aliases",
        "redacted_entities",
        "redaction_rules_applied",
        "artifact_hash",
        "signature",
        "signature_algorithm",
        "issuer",
        "signed_at",
    )
    for field_name in fields:
        before_value = getattr(before, field_name)
        after_value = getattr(after, field_name)
        if before_value == after_value:
            continue
        severity = "medium"
        kind = "boundary_artifact_changed"
        if field_name in {"schema_version", "artifact_hash", "signature", "signature_algorithm"}:
            severity = "high"
        if field_name == "schema_version" and before_value != after_value:
            kind = "schema_version_changed"
        elif field_name == "artifact_hash":
            kind = "boundary_artifact_hash_changed"
        elif field_name == "forbidden_names":
            kind = "boundary_forbidden_name_leak"
            severity = "high"
        elif field_name == "allowed_aliases":
            kind = "boundary_allowed_aliases_changed"
        elif field_name == "redaction_rules_applied":
            kind = "boundary_redaction_rules_changed"
        elif field_name == "source_graph_id":
            kind = "boundary_artifact_source_changed"
        elif field_name == "source_ref_or_commit":
            kind = "boundary_artifact_provenance_changed"
        out.append(
            GraphChange(
                kind,
                "boundary_artifact",
                severity,
                f"{field_name}: {before_value!r} -> {after_value!r}",
            )
        )
    return out


def _is_visibility_escalation(before: RepoVisibility, after: RepoVisibility) -> bool:
    rank = {
        RepoVisibility.PRIVATE: 0,
        RepoVisibility.LOCAL: 0,
        RepoVisibility.INTERNAL: 1,
        RepoVisibility.RESTRICTED: 1,
        RepoVisibility.PUBLIC: 2,
    }
    return rank.get(after, 0) > rank.get(before, 0)


def _is_visibility_escalation_mode(before: DisclosureMode, after: DisclosureMode) -> bool:
    rank = {
        DisclosureMode.SECRET: 0,
        DisclosureMode.LOCAL_ONLY: 0,
        DisclosureMode.PRIVATE: 1,
        DisclosureMode.ALIAS_ONLY: 1,
        DisclosureMode.PUBLIC: 2,
    }
    return rank.get(after, 0) > rank.get(before, 0)
