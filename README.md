# RepoGraph

RepoGraph is the canonical shared graph-semantics library for the platform.

RepoGraph defines the graph language. It does not own graph instances.

## Ownership

RepoGraph owns:

- ontology definitions (repo identity, visibility, disclosure modes, platform planes)
- topology definitions (edge vocabulary and validation)
- projection/redaction semantics
- boundary disclosure artifact shape and validation
- topography definitions only as shared semantics (when needed)

RepoGraph does not own:

- private graph data (`PrivateManifest` owns that)
- public graph publication (`PlatformManifest` owns that)
- audit execution (`Custodian` consumes artifacts and enforces)
- orchestration or scheduling (`OperationsCenter` / `SwitchBoard`)
- deployment execution (`PlatformDeployment`)
- context packaging execution (`Warehouse`)

## Boundary Artifact Flow

1. `PrivateManifest` declares private graph truth using RepoGraph models.
2. `PrivateManifest` generates boundary disclosure artifacts with RepoGraph semantics.
3. Public repos run `Custodian` with `REPOGRAPH_BOUNDARY_ARTIFACT_FILE`.
4. `Custodian` validates public surfaces against artifact-derived forbidden names.

## Verification

```bash
python -m pip install -e .
python -c "import repograph"
python -m pytest
```
