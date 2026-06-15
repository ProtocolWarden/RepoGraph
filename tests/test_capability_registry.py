from __future__ import annotations

import pytest

from repograph import (
    DEFAULT_PROJECTION_PROFILE_RULES,
    CapabilityEdge,
    CapabilityEdgeKind,
    CapabilityInvocation,
    CapabilityInvocationKind,
    CapabilityNode,
    CapabilityCategory,
    CapabilityRegistry,
    CapabilityRisk,
    EntityKind,
    ProjectionProfileKind,
    RepoGraphConfigError,
    TargetScope,
    TargetScopeKind,
    compute_artifact_hash,
)

# Direct submodule imports: per-symbol/per-module coverage of the capability
# plane (compiler, models, validation, enums, projection) rather than relying
# only on the top-level re-export surface.
from repograph.capabilities.compiler import (
    compile_capability,
    compile_registry,
    load_capability_registry,
)
from repograph.capabilities.enums import REPO_TARGETING_EDGE_KINDS
from repograph.capabilities.models import CapabilityInput
from repograph.capabilities.projection import project_capability_registry
from repograph.capabilities.validation import (
    parse_capability_category,
    parse_capability_invocation_kind,
    parse_capability_risk,
    parse_target_scope_kind,
    validate_capability_registry,
)

_ALL_REPOS = {
    "operations_center",
    "media_forge",
    "team_executor",
    "context_lifecycle",
    "custodian",
}


def _asset_audit(**overrides) -> dict:
    doc = {
        "action_id": "asset_audit",
        "name": "MediaForge Audit",
        "owner_repo_id": "operations_center",
        "target_scope": {"kind": "repo", "repo_id": "media_forge"},
        "executes_on": "team_executor",
        "requires": ["context_lifecycle"],
        "validated_by": ["custodian"],
        "produces": ["investigation_capsule", "audit_report"],
        "category": "audit",
        "risk": "read_only",
        "routing": {"preferred_lane": "review"},
        "invocation": {
            "kind": "entrypoint",
            "ref": "operations_center.entrypoints.asset_audit",
        },
        "visibility": "public",
        "disclosure_mode": "public",
    }
    doc.update(overrides)
    return doc


def _fleet_node(action_id: str = "x") -> CapabilityNode:
    return CapabilityNode(
        action_id=action_id,
        name=action_id,
        category=CapabilityCategory.AUDIT,
        risk=CapabilityRisk.READ_ONLY,
        invocation=CapabilityInvocation(CapabilityInvocationKind.ENTRYPOINT, "m.ref"),
        target_scope=TargetScope(TargetScopeKind.FLEET),
    )


# 1. authoring fields compile to the correct typed edges
def test_authoring_compiles_to_typed_edges() -> None:
    registry = compile_registry([_asset_audit()])
    edges = {(e.kind, e.target_id) for e in registry.edges_for("asset_audit")}
    assert (CapabilityEdgeKind.OWNS, "operations_center") in edges
    assert (CapabilityEdgeKind.TARGETS, "media_forge") in edges
    assert (CapabilityEdgeKind.EXECUTES, "team_executor") in edges
    assert (CapabilityEdgeKind.REQUIRES, "context_lifecycle") in edges
    assert (CapabilityEdgeKind.VALIDATES, "custodian") in edges
    assert (CapabilityEdgeKind.PRODUCES, "investigation_capsule") in edges
    assert (CapabilityEdgeKind.PRODUCES, "audit_report") in edges
    assert registry.owner_of("asset_audit") == "operations_center"
    assert registry.capability("asset_audit").kind is EntityKind.CAPABILITY


# 2. exactly-one owner enforced (0 or 2 -> fail)
def test_zero_owners_fails() -> None:
    with pytest.raises(RepoGraphConfigError):
        CapabilityRegistry.build([_fleet_node()], [])


def test_two_owners_fails() -> None:
    with pytest.raises(RepoGraphConfigError):
        CapabilityRegistry.build(
            [_fleet_node()],
            [
                CapabilityEdge("x", "operations_center", CapabilityEdgeKind.OWNS),
                CapabilityEdge("x", "custodian", CapabilityEdgeKind.OWNS),
            ],
        )


def test_single_owner_passes() -> None:
    registry = CapabilityRegistry.build(
        [_fleet_node()],
        [CapabilityEdge("x", "operations_center", CapabilityEdgeKind.OWNS)],
    )
    assert registry.owner_of("x") == "operations_center"


# 3. unknown enum fails closed
@pytest.mark.parametrize(
    "field,bad",
    [
        ("category", "bogus"),
        ("risk", "bogus"),
        ("invocation", {"kind": "bogus", "ref": "r"}),
        ("target_scope", {"kind": "bogus"}),
        ("visibility", "bogus"),
    ],
)
def test_unknown_enum_fails_closed(field: str, bad) -> None:
    with pytest.raises(RepoGraphConfigError):
        compile_registry([_asset_audit(**{field: bad})])


# 4. repo target resolves (missing -> fail)
def test_repo_targets_resolve_when_known() -> None:
    registry = compile_registry([_asset_audit()], known_repo_ids=_ALL_REPOS)
    assert registry.owner_of("asset_audit") == "operations_center"


def test_unresolved_repo_target_fails() -> None:
    with pytest.raises(RepoGraphConfigError):
        compile_registry([_asset_audit()], known_repo_ids={"operations_center"})


def test_produces_targets_are_artifacts_not_repo_checked() -> None:
    # investigation_capsule / audit_report are artifacts, absent from the repo
    # set, yet resolution still passes because PRODUCES is not repo-targeting.
    registry = compile_registry([_asset_audit()], known_repo_ids=_ALL_REPOS)
    produced = registry.targets_by_kind("asset_audit", CapabilityEdgeKind.PRODUCES)
    assert "investigation_capsule" in produced
    assert "audit_report" in produced


# 5. repo_set selector validates but does NOT expand to membership
def test_repo_set_selector_not_expanded() -> None:
    doc = _asset_audit(target_scope={"kind": "repo_set", "selector": {"visibility": "public"}})
    registry = compile_registry([doc])
    node = registry.capability("asset_audit")
    assert node.target_scope.kind is TargetScopeKind.REPO_SET
    assert node.target_scope.selector == (("visibility", "public"),)
    assert not [
        e for e in registry.edges_for("asset_audit") if e.kind is CapabilityEdgeKind.TARGETS
    ]
    # membership is dynamic: resolution passes without any "public" repo present
    compile_registry(
        [doc],
        known_repo_ids={"operations_center", "team_executor", "context_lifecycle", "custodian"},
    )


# 6. fleet target rejects stray repo_id / selector
def test_fleet_rejects_repo_id() -> None:
    with pytest.raises(RepoGraphConfigError):
        compile_registry([_asset_audit(target_scope={"kind": "fleet", "repo_id": "x"})])


def test_fleet_rejects_selector() -> None:
    with pytest.raises(RepoGraphConfigError):
        compile_registry(
            [_asset_audit(target_scope={"kind": "fleet", "selector": {"visibility": "public"}})]
        )


def test_repo_scope_requires_repo_id() -> None:
    with pytest.raises(RepoGraphConfigError):
        compile_registry([_asset_audit(target_scope={"kind": "repo"})])


# 7. public projection drops private; capability entity kind is public-safe
def test_public_projection_drops_private() -> None:
    public = _asset_audit()
    private = _asset_audit(
        action_id="secret_audit",
        visibility="private",
        disclosure_mode="private",
        target_scope={"kind": "fleet"},
    )
    registry = compile_registry([public, private])

    projected = project_capability_registry(registry, ProjectionProfileKind.PUBLIC_SAFE)
    ids = {n.action_id for n in projected.list_capabilities()}
    assert "asset_audit" in ids
    assert "secret_audit" not in ids
    # private capability's edges are dropped with it
    assert all(e.source_id == "asset_audit" for e in projected.edges)


def test_audit_full_projection_retains_private() -> None:
    registry = compile_registry(
        [
            _asset_audit(),
            _asset_audit(
                action_id="secret_audit",
                visibility="private",
                disclosure_mode="private",
                target_scope={"kind": "fleet"},
            ),
        ]
    )
    projected = project_capability_registry(registry, ProjectionProfileKind.AUDIT_FULL)
    assert {"asset_audit", "secret_audit"} <= {
        n.action_id for n in projected.list_capabilities()
    }


def test_capability_entity_kind_is_public_safe() -> None:
    rules = DEFAULT_PROJECTION_PROFILE_RULES[ProjectionProfileKind.PUBLIC_SAFE]
    assert "Capability" in rules.allowed_entity_kinds


# 8. boundary hash covers the capability block
def test_boundary_hash_covers_capability_block() -> None:
    base = compute_artifact_hash(compile_registry([_asset_audit()]).to_payload())
    changed = compute_artifact_hash(
        compile_registry([_asset_audit(risk="mutates_repo")]).to_payload()
    )
    assert base != changed
    # deterministic across identical inputs
    assert base == compute_artifact_hash(compile_registry([_asset_audit()]).to_payload())


# extra invariants
def test_dangerous_risk_requires_explicit_lane() -> None:
    with pytest.raises(RepoGraphConfigError):
        compile_registry([_asset_audit(risk="mutates_fleet", routing={})])
    compile_registry([_asset_audit(risk="mutates_fleet", routing={"preferred_lane": "migration"})])


def test_duplicate_action_id_fails() -> None:
    with pytest.raises(RepoGraphConfigError):
        compile_registry([_asset_audit(), _asset_audit()])


def test_load_registry_validates_schema_header() -> None:
    payload = {
        "schema_kind": "capabilities",
        "schema_version": "1.0.0",
        "capabilities": [_asset_audit()],
    }
    registry = load_capability_registry(payload)
    assert registry.capability("asset_audit") is not None

    with pytest.raises(RepoGraphConfigError):
        load_capability_registry(
            {"schema_kind": "ontology", "schema_version": "1.0.0", "capabilities": []}
        )


def test_missing_invocation_ref_fails() -> None:
    with pytest.raises(RepoGraphConfigError):
        compile_registry([_asset_audit(invocation={"kind": "entrypoint", "ref": ""})])


# direct per-symbol coverage (compiler / models / validation / enums)
def test_compile_capability_returns_node_and_edges() -> None:
    node, edges = compile_capability(0, _asset_audit())
    assert node.action_id == "asset_audit"
    assert sum(1 for e in edges if e.kind is CapabilityEdgeKind.OWNS) == 1


def test_capability_input_is_compiled() -> None:
    doc = _asset_audit(
        inputs=[{"name": "target_repo", "type": "repo_id", "required": True}]
    )
    node = compile_registry([doc]).capability("asset_audit")
    assert node.inputs == (
        CapabilityInput(name="target_repo", type="repo_id", required=True),
    )


@pytest.mark.parametrize(
    "parser",
    [
        parse_capability_category,
        parse_capability_risk,
        parse_capability_invocation_kind,
        parse_target_scope_kind,
    ],
)
def test_parse_helpers_reject_unknown(parser) -> None:
    with pytest.raises(RepoGraphConfigError):
        parser(0, "definitely-not-valid")


def test_repo_targeting_edge_kinds_exclude_produces() -> None:
    assert CapabilityEdgeKind.PRODUCES not in REPO_TARGETING_EDGE_KINDS
    assert CapabilityEdgeKind.OWNS in REPO_TARGETING_EDGE_KINDS


def test_validate_capability_registry_is_callable_directly() -> None:
    registry = compile_registry([_asset_audit()])
    # idempotent: re-validating an already-built registry does not raise
    validate_capability_registry(
        registry, list(registry.nodes.values()), known_repo_ids=_ALL_REPOS
    )
    assert registry.owner_of("asset_audit") == "operations_center"
