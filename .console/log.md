# Log

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
