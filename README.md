# RepoGraph

RepoGraph is the canonical shared graph-semantics library for the platform.
It defines the graph language. It does not own graph instances.

## What RepoGraph Is

The shared semantic foundation for platform graph operations. RepoGraph defines
ontology, topology, projection, and boundary disclosure schemas that all other
platform components consume. It is a library, not a service — it has no runtime,
no scheduler, and no state.

## What RepoGraph Is Not

- Not a graph database or graph instance owner
- Not a deployment or orchestration component
- Not a public API surface — consumers import from it, not HTTP-call it
- Not responsible for audit execution or policy enforcement

## Getting Started

```bash
python -m pip install -e .
python -c "import repograph"
python -m pytest
```

## Architecture Overview

RepoGraph is organized into five layers:

| Layer | Package | Role |
|-------|---------|------|
| Ontology | `repograph.ontology` | Core enums and models (identity, visibility, planes) |
| Topology | `repograph.topology` | Edge kinds, graph validation, relationship models |
| Projection | `repograph.projection` | Redaction and public-safe surface rules |
| Schema | `repograph.schema` | Version-gated boundary artifact schemas |
| Topography | `repograph.topography` | Deployment-consumer topology definitions |

See [docs/policy-plane.md](docs/policy-plane.md) for the policy boundary and
[docs/schema-governance.md](docs/schema-governance.md) for schema versioning rules.

## What It Owns

- ontology definitions for repo identity, visibility, disclosure modes, and platform planes
- topology definitions for edge kinds and validation
- projection/redaction semantics
- boundary disclosure artifact shape and validation
- shared topography definitions when deployment consumers need them

RepoGraph keeps policy adjacent to semantics, not buried inside config soup.
See [docs/policy-plane.md](docs/policy-plane.md) for the policy boundary.

## What It Does Not Own

- private graph data
- public graph publication
- audit execution
- orchestration or scheduling
- deployment execution
- context packaging execution

## Boundary Artifact Flow

1. A source manifest declares graph truth using RepoGraph models.
2. That manifest generates versioned boundary disclosure artifacts with RepoGraph semantics.
3. The artifact carries schema metadata, provenance, and a payload hash.
4. Public repos run `Custodian` with `REPOGRAPH_BOUNDARY_ARTIFACT_FILE`.
5. `Custodian` validates public surfaces against artifact-derived forbidden names.

For the public-safe explorer contract, see
[docs/repograph-explorer-spec.md](docs/repograph-explorer-spec.md).

## Schema Governance

RepoGraph version-gates ontology, topology, projection, and boundary artifacts.
Breaking changes require an explicit schema version bump. Unsupported versions
fail closed. See [docs/schema-governance.md](docs/schema-governance.md).

## Standards

- [LICENSE](LICENSE)
- [CODE_OF_CONDUCT.md](CODE_OF_CONDUCT.md)
- [CONTRIBUTING.md](CONTRIBUTING.md)
- [SECURITY.md](SECURITY.md)
