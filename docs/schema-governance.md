# RepoGraph Schema Governance

RepoGraph schema governance keeps semantic evolution explicit and testable.

## Schema kinds

- `ontology`
- `topology`
- `projection`
- `boundary_artifact`

## Rules

- New enum values require a minor schema bump.
- Removed enum values are breaking.
- Projection rule removal is breaking.
- Boundary-artifact field removal is breaking.
- Projection safety downgrade is forbidden unless handled as an explicit breaking change.
- Unknown future schema versions fail closed.
- Unsupported old schema versions fail clearly.

## Versioning model

Each schema kind carries a `schema_kind` and `schema_version`.
Boundary artifacts and public projections include those fields so consumers can
validate them before using the payload.

## Drift detection

RepoGraph includes a drift comparison layer for graph states, public
projections, and boundary artifacts. It reports entity, edge, visibility,
projection-profile, and boundary-artifact changes in machine-readable form so
consumers can treat semantic drift as a first-class review signal.

## Compatibility posture

RepoGraph is fail-closed on schema compatibility. It does not auto-upgrade or
guess at unknown schema shapes.
