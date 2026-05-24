# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/).

## [Unreleased]

### Fixed

- Removed unused `DisclosureMode` import from `topology/validation.py` (RUFF F401)
- Added custodian config with C32 exclusion for `DisclosureMode.SECRET` enum (false positive)
- Added `tests/conftest.py` venv guard (S4)
- Added `.hooks/pre-commit` log.md enforcement (W6)
- Removed unused `default_registry_path` import and a placeholder-free f-string in `cli.py` (RUFF F401/F541)
- Genericized illustrative private-repo names in `authorization.py` docstrings and
  `tests/test_authorization.py` to a neutral placeholder (`MediaForge`) — public repo (B1)
- Added direct unit tests for authorization data structures (`tests/test_authorization_models.py`),
  the CLI entrypoints (`tests/test_cli.py`), and the registry discovery helpers
- Added `.hooks/pre-push` custodian regression guard
- Marked `registry.py` as the env-access config layer (`c13_allowed_paths`) for the
  `REPOGRAPH_REGISTRY` / `XDG_CONFIG_HOME` lookups (C13)
