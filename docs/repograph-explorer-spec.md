# RepoGraph Explorer Spec

This document specifies a public-safe graph explorer for RepoGraph-backed data.
It is a renderer for RepoGraph projections, not a second projection engine.

## Constraints

- The explorer consumes projection outputs only.
- The explorer does not read private graph data directly.
- The explorer does not implement redaction logic.
- The public explorer uses `PUBLIC_SAFE` or `PUBLIC_DOCS` only.
- Internal projection profiles are explicitly non-public-safe.
- Any new view must be added as a RepoGraph projection profile first.
- The explorer must not down-convert `AUDIT_FULL` or internal profiles into a
  public surface.

## Allowed inputs

- RepoGraph public projection manifests
- RepoGraph boundary artifacts for provenance display

## Forbidden inputs

- Private graph source files
- Local overlay paths
- Raw private-name configs
- Any input that bypasses projection validation
- Internal projection outputs unless the caller is explicitly using an
  internal-only profile outside the public site

## Safety rule

If the explorer needs a new view, the view must be added as a RepoGraph
projection profile first. The explorer renders the projection; it does not
define one.
