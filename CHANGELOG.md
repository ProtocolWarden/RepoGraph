# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/).

## [Unreleased]

### Fixed

- Removed unused `DisclosureMode` import from `topology/validation.py` (RUFF F401)
- Added custodian config with C32 exclusion for `DisclosureMode.SECRET` enum (false positive)
- Added `tests/conftest.py` venv guard (S4)
- Added `.hooks/pre-commit` log.md enforcement (W6)
