# Log

## 2026-05-22 — P2: manifest registry + authorization API

Branch: `feat/p2-manifest-registry-auth`.

- New `repograph.registry` module: per-machine `manifests.yaml` registry under
  `${XDG_CONFIG_HOME:-~/.config}/repograph/`, with `REPOGRAPH_REGISTRY` env
  override for tests. `Registry.add/remove/list/validate`.
- New `repograph.authorization` module: `AuthorizationView` with three-clause
  `can_anchor_host(anchor_path, repo_name)` per ADR 0002 P0.4. Builds a thin
  topology over registered manifests' YAMLs (owner index + also_hosts graph).
- New top-level manifest fields parsed: `visibility_scope` (public/private),
  `also_hosts: [{manifest, repos}]`. Backward-compat: scope is derived from
  `repos[*].visibility` when all-public; otherwise explicit declaration is
  required.
- `RepoGraph` extended with `can_anchor_host()`, `find_anchor_for_path()`,
  and lazy registry self-init via `_ensure_authorization()`. `RepoGraph.build()`
  preserved for explicit-construction tests.
- Load-time validations (fatal): dual-ownership across manifests; bad
  `also_hosts` (manifest, repo) refs; public manifest hosting a non-public
  repo. Non-fatal warning: redundant `also_hosts` grants pointing at public
  repos.
- New `repograph` Typer CLI with `manifest add|remove|list|validate|show`.
  Added `typer>=0.12` dep + `[project.scripts] repograph = "repograph.cli:app"`.
- Tests: `tests/test_registry.py`, `tests/test_authorization.py` — 21 new
  tests, all 38 pass.

## 2026-05-21 — Add closing fence to console-context block

Added <!-- /console-context --> end marker so OperatorConsole only replaces its
managed block and leaves repo-owned content below it untouched.

_Chronological continuity log. Decisions, stop points, what changed and why._
_Not a task tracker — that's backlog.md. Keep entries concise and dated._

## Recent Decisions

_Log significant choices here so they survive context resets._

| Decision | Rationale | Date |
|----------|-----------|------|
| [what was decided] | [why] | [date] |

## Stop Points

_Where did you leave off? What should be verified next session?_

- [what to pick up next]

## Notes

_Free-form scratch. Clear periodically — old entries can be deleted once no longer relevant._

---

## 2026-05-13 — Custodian phase 2 — README, CHANGELOG, docs/README, D11/T1/T6/T7 exclusions

- README restructured with What RepoGraph Is/Is Not, Getting Started, Architecture Overview sections.
- CHANGELOG.md added.
- docs/README.md added (R6 fix).
- .custodian/config.yaml: added D11 exclusions for intentional symmetric APIs; T1/T6/T7 exclusions for diff.py and errors.py.

## 2026-05-13 — Add custodian config and phase 1 fixes

- Added .custodian/config.yaml — first custodian config for this repo.
- C32 false positive excluded: DisclosureMode.SECRET is a graph enum value, not a credential.
- RUFF F401: removed unused DisclosureMode import from topology/validation.py.
- S4: added tests/conftest.py with venv guard.
- W6: added .hooks/pre-commit with log.md enforcement; ran git config core.hooksPath .hooks.

## 2026-05-13 — Add CLAUDE.md and .custodian/tmp*.yaml to .gitignore

- Added CLAUDE.md to .gitignore
- Added .custodian/tmp*.yaml to exclude custodian audit temp files
