# Log
## 2026-06-04 — Console reconciliation: scrub + enforce

Reconciled `.console/` per the console-reconciliation spec (scrub-target boundary, I2).

- Scrubbed scrub-target private identifiers from `.console/log.md` historical entries
  (three hits in the 2026-05-22 and 2026-05-23 narration). Genericized in place to
  "a private downstream repo" / "canonical name" / "lowercased repo form" while
  preserving meaning. Numbered detector-ID forms (the `VF2`-style codes) left untouched by design.
- Log is under the 400-line budget, so no prune was performed.
- `.custodian/config.yaml`: set `audit.reconcile_enforce: true` (opt-in R1/R2 detectors)
  now that this repo's tracked `.console/` is scrub-clean.
- Verified `git grep` for scrub-target identifiers over `.console` and `docs` is empty.

## 2026-05-23 — Custodian guard to zero + pre-push hook onboarded

Drove `custodian-multi` from 30 findings to `0 findings | clean` on branch `chore/custodian-clean`.

- C13: `registry.py` resolves the registry path from `REPOGRAPH_REGISTRY` / `XDG_CONFIG_HOME`; it IS the config/env-access layer, so added it to `c13_allowed_paths` (rationale in config). No code change.
- RUFF: removed unused `default_registry_path` import (F401) and a placeholder-free f-string (F541) in `cli.py`.
- B1 (PUBLIC repo): the illustrative example names referencing a private downstream repo (canonical, lowercased, and snake_case forms, plus their A/B variants) in `authorization.py` docstrings and `tests/test_authorization.py` are now forbidden by the boundary artifact. Genericized to the neutral placeholder `MediaForge` (and `mediaforge`/`media_forge`/`MediaForgeA/B`), preserving the alias-resolution semantics each test asserts. Repo's own name "RepoGraph" is not forbidden, so no privacy exclude needed.
- T1/T6/T7: wrote genuine unit tests rather than over-excluding — `tests/test_authorization_models.py` (direct-import coverage of `AlsoHostsEntry`/`ManifestRecord`/`AuthorizationView`), `tests/test_cli.py` (CliRunner coverage of all `manifest_*` commands), and appended registry-discovery tests to `tests/test_registry.py` (`discover_manifest_yaml`, `discover_all_manifest_yamls`, `iter_yaml_documents`). `cli.py` added to T1 exclude only because T1 keys on the python symbol name while CliRunner invokes commands by CLI string ("manifest add"); behaviour is fully tested.
- Hooks: added `.hooks/pre-push` (custodian regression guard, fail-closed on missing boundary artifact); `pre-commit` already present. `core.hooksPath` set to `.hooks`.
- 61 tests pass; audit clean.

## 2026-05-22 — can_anchor_host accepts canonical_name OR snake_case key (alias resolution)

Follow-up to e2e test of ADR 0002. Operators naturally refer to repos by either form: the canonical_name or its lowercased form (the dict key in PM-style YAML, or just the lowercased canonical). Before this change, only canonical_name resolved; other forms returned "not registered in any manifest", which masked real boundary violations behind a misleading error.

Changes:
- `ManifestRecord` gains `repo_aliases: dict[str, str]` (lowercased alias → canonical).
- `AuthorizationView` gains a global `repo_aliases` map merged across all registered manifests.
- `_iter_repos` now yields `(canonical, fields, aliases)` — for PM-style dict YAML, the dict key is registered as an alias when it differs from canonical_name. Caller signature updated at three call sites.
- `can_anchor_host` normalizes the input through the global alias map before lookup; reasons always name the canonical form.
- `also_hosts` validation likewise resolves entries through aliases.
- Load-time check: alias-to-canonical mapping must be consistent both within a manifest and across registered manifests (fatal if conflict).

5 new tests in `test_authorization.py`: canonical match, alias match, case-insensitive variants, block-reason names canonical even when called via alias, alias conflict fatal. 43/43 passing (was 38).

E2E re-verified: `capture(repos_touched=[<lowercased repo form>])` from a PM anchor now raises BoundaryViolation with the canonical name in the reason, instead of the previous misleading "not registered".


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
