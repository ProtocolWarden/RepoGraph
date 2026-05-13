# Security Policy

## Supported Versions

| Version | Supported |
|---------|-----------|
| `main`  | ✅ Yes     |

Only the current `main` branch receives security fixes.

## Reporting a Vulnerability

Do not open a public issue for security vulnerabilities.

Report issues privately by emailing **coding.projects.1642@proton.me**.

Include:
- a description of the issue
- reproduction steps
- expected impact
- any relevant boundary-artifact or projection details

## Scope

RepoGraph is a shared semantics library. The primary security surface is:

- malformed ontology / topology / projection data
- boundary-artifact validation and redaction logic
- import-time execution in consumers that load RepoGraph models

## Hardening Guidance

- Treat graph-model changes like schema changes
- Keep private graph data out of this repo
- Validate boundary artifacts before they reach public repos
