# SPDX-License-Identifier: AGPL-3.0-or-later
# Copyright (C) 2026 ProtocolWarden
"""Per-machine manifest registry for RepoGraph.

The registry tracks which manifest *repo roots* exist on this machine. It is
machine-local config (not committed to any repo) — manifest *contents* live
in git inside each manifest repo.

Default location: ``${XDG_CONFIG_HOME:-~/.config}/repograph/manifests.yaml``.

Schema::

    manifests:
      - /path/to/PlatformManifest
      - /path/to/<your-private-manifest-repo>
"""

from __future__ import annotations

import os
from dataclasses import dataclass, field
from pathlib import Path
from typing import Iterable

import yaml

from .errors import RepoGraphConfigError


_DEFAULT_BASENAME = "manifests.yaml"
_REGISTRY_SUBDIR = "repograph"


def default_registry_path() -> Path:
    """Return the default per-machine registry path.

    Honors ``XDG_CONFIG_HOME``; falls back to ``~/.config``.
    Also honors ``REPOGRAPH_REGISTRY`` for explicit override (tests, CI).
    """
    override = os.environ.get("REPOGRAPH_REGISTRY", "").strip()
    if override:
        return Path(override).expanduser().resolve()
    xdg = os.environ.get("XDG_CONFIG_HOME", "").strip()
    base = Path(xdg).expanduser() if xdg else Path.home() / ".config"
    return (base / _REGISTRY_SUBDIR / _DEFAULT_BASENAME).resolve()


@dataclass
class Registry:
    """Per-machine list of manifest repo roots known to RepoGraph."""

    path: Path
    manifests: list[Path] = field(default_factory=list)

    # ------------------------------------------------------------------
    # Load / save
    # ------------------------------------------------------------------

    @classmethod
    def load(cls, path: Path | None = None) -> "Registry":
        registry_path = (path or default_registry_path()).expanduser().resolve()
        if not registry_path.exists():
            return cls(path=registry_path, manifests=[])
        try:
            raw = yaml.safe_load(registry_path.read_text(encoding="utf-8")) or {}
        except yaml.YAMLError as exc:
            raise RepoGraphConfigError(
                f"registry at {registry_path} is not valid YAML: {exc}"
            ) from exc
        if not isinstance(raw, dict):
            raise RepoGraphConfigError(
                f"registry root must be a mapping (got {type(raw).__name__}): {registry_path}"
            )
        items = raw.get("manifests") or []
        if not isinstance(items, list):
            raise RepoGraphConfigError(
                f"registry 'manifests' must be a list: {registry_path}"
            )
        manifests: list[Path] = []
        for item in items:
            if not isinstance(item, str):
                raise RepoGraphConfigError(
                    f"registry manifest entry must be a string path: {item!r}"
                )
            manifests.append(Path(item).expanduser())
        return cls(path=registry_path, manifests=manifests)

    def save(self) -> None:
        self.path.parent.mkdir(parents=True, exist_ok=True)
        payload = {"manifests": [str(p) for p in self.manifests]}
        self.path.write_text(
            yaml.safe_dump(payload, sort_keys=False, default_flow_style=False),
            encoding="utf-8",
        )

    # ------------------------------------------------------------------
    # Mutations
    # ------------------------------------------------------------------

    def add(self, path: Path | str) -> bool:
        """Register a manifest repo root. Returns True if newly added."""
        resolved = Path(path).expanduser().resolve()
        if not resolved.exists():
            raise RepoGraphConfigError(f"manifest path does not exist: {resolved}")
        if not resolved.is_dir():
            raise RepoGraphConfigError(f"manifest path is not a directory: {resolved}")
        for existing in self.manifests:
            if existing.expanduser().resolve() == resolved:
                return False
        self.manifests.append(resolved)
        self.save()
        return True

    def remove(self, path: Path | str) -> bool:
        """Unregister a manifest. Returns True if removed."""
        resolved = Path(path).expanduser().resolve()
        kept: list[Path] = []
        removed = False
        for existing in self.manifests:
            if existing.expanduser().resolve() == resolved:
                removed = True
                continue
            kept.append(existing)
        if removed:
            self.manifests = kept
            self.save()
        return removed

    def list(self) -> list[Path]:
        return [p.expanduser().resolve() for p in self.manifests]

    # ------------------------------------------------------------------
    # Validation
    # ------------------------------------------------------------------

    def validate(self) -> list[str]:
        """Return a list of human-readable problems with the registry.

        Empty list = healthy. Non-empty = each string is one problem.
        Does NOT raise; callers decide how to react (CLI exits non-zero,
        ``RepoGraph()`` self-init raises).
        """
        issues: list[str] = []
        seen: set[Path] = set()
        for entry in self.manifests:
            resolved = entry.expanduser().resolve()
            if resolved in seen:
                issues.append(f"duplicate manifest entry: {resolved}")
                continue
            seen.add(resolved)
            if not resolved.exists():
                issues.append(f"manifest path does not exist: {resolved}")
                continue
            if not resolved.is_dir():
                issues.append(f"manifest path is not a directory: {resolved}")
                continue
            if discover_manifest_yaml(resolved) is None:
                issues.append(
                    f"no manifest YAML found under {resolved} "
                    "(expected platform_manifest.yaml / private_manifest.yaml "
                    "or src/<pkg>/data/*.yaml or manifests/**/*.yaml)"
                )
        return issues


# ----------------------------------------------------------------------
# Manifest YAML discovery within a manifest repo root
# ----------------------------------------------------------------------


_CANDIDATE_GLOBS: tuple[str, ...] = (
    "platform_manifest.yaml",
    "private_manifest.yaml",
    "project_manifest.yaml",
    "manifest.yaml",
    "src/*/data/platform_manifest.yaml",
    "src/*/data/private_manifest.yaml",
    "src/*/data/project_manifest.yaml",
    "manifests/*.yaml",
    "manifests/*/*.yaml",
)


def discover_manifest_yaml(repo_root: Path) -> Path | None:
    """Find the canonical manifest YAML inside a manifest repo root.

    Returns the first hit by the candidate glob order. Returns ``None`` if
    nothing recognizable is found.
    """
    for pattern in _CANDIDATE_GLOBS:
        for hit in sorted(repo_root.glob(pattern)):
            if hit.is_file():
                return hit
    return None


def discover_all_manifest_yamls(repo_root: Path) -> list[Path]:
    """Return all manifest YAMLs under a manifest repo root (in glob order).

    A single private manifest repo may host more than one manifest YAML
    (e.g. one per managed project). Authorization needs all of them.
    """
    seen: set[Path] = set()
    results: list[Path] = []
    for pattern in _CANDIDATE_GLOBS:
        for hit in sorted(repo_root.glob(pattern)):
            if not hit.is_file():
                continue
            resolved = hit.resolve()
            if resolved in seen:
                continue
            seen.add(resolved)
            results.append(resolved)
    return results


# ----------------------------------------------------------------------
# Private-manifest role resolution
# ----------------------------------------------------------------------

_PRIVATE_MANIFEST_ENV = "PRIVATE_MANIFEST_DIR"
_PRIVATE_MANIFEST_PREFIX = "private_manifest"


def resolve_private_manifest(registry: "Registry | None" = None) -> Path | None:
    """Resolve the active private-manifest repo root, or ``None``.

    The platform references the private-manifest *role*, never a baked-in
    repo-instance name. Resolution order:

    1. ``$PRIVATE_MANIFEST_DIR`` — explicit operator override (must be an
       existing directory; a set-but-bogus value resolves to ``None`` rather
       than silently falling through to discovery).
    2. Registry discovery — the first registered manifest repo root hosting
       any manifest YAML whose basename starts with ``private_manifest``
       (matched on the manifest *type* filename, never a repo name).

    Best-effort by design: callers that require a private manifest should
    treat ``None`` as their own failure condition.
    """
    env = os.environ.get(_PRIVATE_MANIFEST_ENV, "").strip()
    if env:
        root = Path(env).expanduser()
        return root.resolve() if root.is_dir() else None
    if registry is None:
        try:
            registry = Registry.load()
        except RepoGraphConfigError:
            return None
    for root in registry.manifests:
        root = Path(root).expanduser()
        if not root.is_dir():
            continue
        yamls = discover_all_manifest_yamls(root)
        if any(y.name.startswith(_PRIVATE_MANIFEST_PREFIX) for y in yamls):
            return root.resolve()
    return None


def iter_yaml_documents(paths: Iterable[Path]) -> list[tuple[Path, dict]]:
    """Load YAML docs from the given paths. Skips files that don't parse to a mapping."""
    results: list[tuple[Path, dict]] = []
    for p in paths:
        try:
            raw = yaml.safe_load(p.read_text(encoding="utf-8"))
        except yaml.YAMLError as exc:
            raise RepoGraphConfigError(f"manifest YAML {p} parse error: {exc}") from exc
        if isinstance(raw, dict):
            results.append((p, raw))
    return results
