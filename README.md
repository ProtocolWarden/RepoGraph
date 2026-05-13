# RepoGraph

RepoGraph is the canonical shared graph-semantics library for the platform.
It defines the graph language. It does not own graph instances.

## What It Owns

- ontology definitions for repo identity, visibility, disclosure modes, and platform planes
- topology definitions for edge kinds and validation
- projection/redaction semantics
- boundary disclosure artifact shape and validation
- shared topography definitions when deployment consumers need them

## What It Does Not Own

- private graph data
- public graph publication
- audit execution
- orchestration or scheduling
- deployment execution
- context packaging execution

## Boundary Artifact Flow

1. A source manifest declares graph truth using RepoGraph models.
2. That manifest generates boundary disclosure artifacts with RepoGraph semantics.
3. Public repos run `Custodian` with `REPOGRAPH_BOUNDARY_ARTIFACT_FILE`.
4. `Custodian` validates public surfaces against artifact-derived forbidden names.

## Verification

```bash
python -m pip install -e .
python -c "import repograph"
python -m pytest
```

## Standards

- [LICENSE](LICENSE)
- [CODE_OF_CONDUCT.md](CODE_OF_CONDUCT.md)
- [CONTRIBUTING.md](CONTRIBUTING.md)
- [SECURITY.md](SECURITY.md)
