# SPDX-License-Identifier: AGPL-3.0-or-later
# Copyright (C) 2026 ProtocolWarden
"""Topology edge vocabulary."""

from __future__ import annotations

from enum import Enum


class EdgeCategory(str, Enum):
    ARTIFACT_FLOW = "artifact_flow"
    CONTROL_FLOW = "control_flow"
    CONTRACT_FLOW = "contract_flow"
    MANIFEST_FLOW = "manifest_flow"
    OBSERVABILITY_FLOW = "observability_flow"
    DEPLOYMENT_FLOW = "deployment_flow"
    DOCUMENTATION_FLOW = "documentation_flow"
    VALIDATION_FLOW = "validation_flow"


class EdgeKind(str, Enum):
    CONSUMES_MANIFEST = "consumes_manifest"
    PUBLISHES_PROJECTION = "publishes_projection"
    READS_ARTIFACT = "reads_artifact"
    WRITES_ARTIFACT = "writes_artifact"
    READS_HEARTBEAT = "reads_heartbeat"
    SUBSCRIBES_TO_HEARTBEAT = "subscribes_to_heartbeat"
    DISPATCHES_REQUEST = "dispatches_request"
    POLL_STATUS = "poll_status"
    POLLS_STATUS = "poll_status"
    INDEXES_OUTPUT = "indexes_output"
    VALIDATES_OUTPUT = "validates_output"
    OWNS_SCHEMA = "owns_schema"
    IMPLEMENTS_ADAPTER = "implements_adapter"
    INVOKES_RUNTIME = "invokes_runtime"
    PRODUCES_ARTIFACT = "produces_artifact"
    REPORTS_TO = "reports_to"
    DEPLOYS = "deploys"
    HOSTS = "hosts"
    PROJECTS_TO = "projects_to"
    REDACTS_FROM = "redacts_from"
    IMPLEMENTS = "implements"
    DOCUMENTS = "documents"
    ORCHESTRATES = "orchestrates"
    REFERENCES_SCHEMA_FROM = "references_schema_from"
    MANAGES = "manages"
    PRODUCES_ARTIFACTS_FOR = "produces_artifacts_for"
    CONSUMES_MANIFEST_FROM = "consumes_manifest_from"
    VALIDATES_WITH = "validates_with"
    LOADS_PLUGIN_FROM = "loads_plugin_from"


OntologyRelationshipKind = EdgeKind


class RepoEdgeType(str, Enum):
    DEPENDS_ON_CONTRACTS_FROM = "depends_on_contracts_from"
    DISPATCHES_TO = "dispatches_to"
    ROUTES_THROUGH = "routes_through"
    BUNDLES_ASSETS_FROM = "bundles_assets_from"


RELATIONSHIP_EDGE_CATEGORIES: dict[EdgeKind, EdgeCategory] = {
    EdgeKind.CONSUMES_MANIFEST: EdgeCategory.MANIFEST_FLOW,
    EdgeKind.CONSUMES_MANIFEST_FROM: EdgeCategory.MANIFEST_FLOW,
    EdgeKind.PUBLISHES_PROJECTION: EdgeCategory.VALIDATION_FLOW,
    EdgeKind.READS_ARTIFACT: EdgeCategory.ARTIFACT_FLOW,
    EdgeKind.WRITES_ARTIFACT: EdgeCategory.ARTIFACT_FLOW,
    EdgeKind.READS_HEARTBEAT: EdgeCategory.OBSERVABILITY_FLOW,
    EdgeKind.SUBSCRIBES_TO_HEARTBEAT: EdgeCategory.OBSERVABILITY_FLOW,
    EdgeKind.DISPATCHES_REQUEST: EdgeCategory.CONTROL_FLOW,
    EdgeKind.POLLS_STATUS: EdgeCategory.OBSERVABILITY_FLOW,
    EdgeKind.INDEXES_OUTPUT: EdgeCategory.OBSERVABILITY_FLOW,
    EdgeKind.VALIDATES_OUTPUT: EdgeCategory.VALIDATION_FLOW,
    EdgeKind.OWNS_SCHEMA: EdgeCategory.CONTRACT_FLOW,
    EdgeKind.IMPLEMENTS_ADAPTER: EdgeCategory.CONTROL_FLOW,
    EdgeKind.INVOKES_RUNTIME: EdgeCategory.CONTROL_FLOW,
    EdgeKind.PRODUCES_ARTIFACT: EdgeCategory.ARTIFACT_FLOW,
    EdgeKind.PRODUCES_ARTIFACTS_FOR: EdgeCategory.ARTIFACT_FLOW,
    EdgeKind.REPORTS_TO: EdgeCategory.OBSERVABILITY_FLOW,
    EdgeKind.DEPLOYS: EdgeCategory.DEPLOYMENT_FLOW,
    EdgeKind.HOSTS: EdgeCategory.DEPLOYMENT_FLOW,
    EdgeKind.PROJECTS_TO: EdgeCategory.VALIDATION_FLOW,
    EdgeKind.REDACTS_FROM: EdgeCategory.VALIDATION_FLOW,
    EdgeKind.IMPLEMENTS: EdgeCategory.CONTRACT_FLOW,
    EdgeKind.DOCUMENTS: EdgeCategory.DOCUMENTATION_FLOW,
    EdgeKind.ORCHESTRATES: EdgeCategory.CONTROL_FLOW,
    EdgeKind.REFERENCES_SCHEMA_FROM: EdgeCategory.CONTRACT_FLOW,
    EdgeKind.MANAGES: EdgeCategory.CONTROL_FLOW,
    EdgeKind.VALIDATES_WITH: EdgeCategory.VALIDATION_FLOW,
    EdgeKind.LOADS_PLUGIN_FROM: EdgeCategory.CONTROL_FLOW,
}
