# SPDX-License-Identifier: AGPL-3.0-or-later
# Copyright (C) 2026 ProtocolWarden
"""Manifest-level authorization view.

Implements the three-clause authorization model locked in
PlatformDeployment ADR 0002 P0.4:

    allowed(anchor, repo) =
         repo.owner == anchor              # (1) anchor owns the repo
      OR repo.owner.scope == public         # (2) public is universally visible
      OR repo_name in anchor.also_hosts     # (3) explicit cross-private grant

The "manifest" here is identified by the *repo root path* of the manifest
repo (e.g. ``/home/dev/Documents/GitHub/PlatformManifest``). Each manifest
repo can host one or more YAML files; for authorization we union their
``repos:`` and ``also_hosts:`` declarations under the manifest's repo root.

This is intentionally a *thin* topology — it does not need the full
ontology/topology/projection pipeline. Authorization only cares about:

  - which repos a manifest owns
  - the manifest's scope (public/private)
  - which (manifest, repo) pairs a manifest explicitly grants access to
"""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import Literal

from .errors import RepoGraphConfigError
from .registry import discover_all_manifest_yamls, iter_yaml_documents


VisibilityScope = Literal["public", "private"]


@dataclass(frozen=True)
class AlsoHostsEntry:
    """An entry in a manifest's ``also_hosts:`` list."""

    manifest: str
    repos: tuple[str, ...]


@dataclass(frozen=True)
class ManifestRecord:
    """Authorization-relevant view of a single manifest repo."""

    name: str
    """Canonical name (the manifest repo root's basename)."""

    root: Path
    """Manifest repo root (the path that appears in the registry)."""

    yaml_paths: tuple[Path, ...]
    """All YAML files contributing to this manifest record."""

    visibility_scope: VisibilityScope
    """``public`` or ``private``."""

    repos: tuple[str, ...]
    """Repo names this manifest owns (union across its YAMLs)."""

    also_hosts: tuple[AlsoHostsEntry, ...]
    """Cross-private grants declared by this manifest."""

    repo_local_paths: dict[str, Path] = field(default_factory=dict)
    """Optional repo_name → local_path mapping (for anchor inference)."""

    repo_aliases: dict[str, str] = field(default_factory=dict)
    """Lowercased alias → canonical repo name. Includes the canonical name
    itself (lowercased) and any dict-key form from PM-style YAML. Used by
    :meth:`AuthorizationView.can_anchor_host` so operators can pass either
    form (e.g. ``"mediaforge"`` or ``"MediaForge"``)."""

    @property
    def also_hosts_flattened(self) -> frozenset[str]:
        """All repo names granted via ``also_hosts:`` across entries."""
        return frozenset(r for entry in self.also_hosts for r in entry.repos)


@dataclass
class AuthorizationView:
    """The merged authorization topology built from all registered manifests."""

    manifests: dict[Path, ManifestRecord]
    """Manifest records keyed by canonicalized repo root."""

    repo_owner: dict[str, Path]
    """canonical repo_name → owning manifest repo root."""

    repo_aliases: dict[str, str] = field(default_factory=dict)
    """Lowercased alias → canonical repo name. Spans every manifest's
    aliases so :meth:`can_anchor_host` accepts both ``"MediaForge"`` and
    ``"mediaforge"`` (and any other registered form)."""

    warnings: list[str] = field(default_factory=list)
    """Non-fatal validation issues (e.g. redundant also_hosts grants)."""

    # ------------------------------------------------------------------
    # Lookup
    # ------------------------------------------------------------------

    def get_by_root(self, root: Path) -> ManifestRecord | None:
        return self.manifests.get(_canon(root))

    def get_by_name(self, name: str) -> ManifestRecord | None:
        lowered = name.lower()
        for record in self.manifests.values():
            if record.name.lower() == lowered:
                return record
        return None

    # ------------------------------------------------------------------
    # Authorization
    # ------------------------------------------------------------------

    def can_anchor_host(
        self, anchor_path: Path, repo_name: str
    ) -> tuple[bool, str]:
        """Three-clause authorization check.

        Returns ``(allowed, reason)``. ``reason`` is always operator-actionable.
        """
        anchor = self.get_by_root(anchor_path)
        if anchor is None:
            return (
                False,
                f"anchor manifest path is not registered with RepoGraph: {anchor_path}. "
                "Run `repograph manifest add <path>` to register it.",
            )

        # Normalize input: accept canonical name OR any registered alias
        # (case-insensitive). E.g. both "MediaForge" and "mediaforge" resolve.
        canonical = self.repo_aliases.get(repo_name.lower(), repo_name)
        owner_root = self.repo_owner.get(canonical)
        if owner_root is None:
            return (
                False,
                f"repo {repo_name!r} is not registered in any manifest. "
                "Add it to exactly one manifest's `repos:` list.",
            )
        owner = self.manifests[owner_root]

        if owner.root == anchor.root:
            return True, f"anchor {anchor.name!r} owns repo {canonical!r}"

        if owner.visibility_scope == "public":
            return (
                True,
                f"repo {canonical!r} is owned by public manifest {owner.name!r}",
            )

        # also_hosts grants are stored as the names the operator wrote;
        # normalize both sides through the global alias map to compare.
        also_canonical = {
            self.repo_aliases.get(r.lower(), r) for r in anchor.also_hosts_flattened
        }
        if canonical in also_canonical:
            return (
                True,
                f"anchor {anchor.name!r} has explicit also_hosts grant for "
                f"{canonical!r} (owned by private manifest {owner.name!r})",
            )

        return (
            False,
            f"anchor {anchor.name!r} (scope={anchor.visibility_scope}) cannot host "
            f"cognition about {canonical!r}: owned by private manifest {owner.name!r} "
            "with no `also_hosts` grant to this anchor.",
        )


# ----------------------------------------------------------------------
# Build
# ----------------------------------------------------------------------


def build_authorization_view(manifest_roots: list[Path]) -> AuthorizationView:
    """Parse the manifest YAMLs under each root and build the merged view.

    Runs load-time validations:
      - exactly-one-owner per repo across all manifests (dual claim → fatal)
      - each ``also_hosts`` entry references a real (manifest, repo) pair
        (bad ref → fatal)
      - warns (does not fail) on ``also_hosts`` grants pointing at a repo
        whose owner is public-scoped (redundant grant)
    """
    records_by_root: dict[Path, ManifestRecord] = {}
    repo_owner: dict[str, Path] = {}
    repo_aliases: dict[str, str] = {}
    warnings: list[str] = []

    # First pass: build per-manifest records.
    for raw_root in manifest_roots:
        root = _canon(raw_root)
        if not root.exists():
            raise RepoGraphConfigError(
                f"registered manifest root does not exist: {root}"
            )
        record = _parse_manifest_root(root)
        records_by_root[root] = record

    # Second pass: enforce exactly-one-owner + merge alias maps.
    for root, record in records_by_root.items():
        for repo_name in record.repos:
            prior = repo_owner.get(repo_name)
            if prior is not None and prior != root:
                prior_name = records_by_root[prior].name
                raise RepoGraphConfigError(
                    f"repo {repo_name!r} is claimed by multiple manifests: "
                    f"{prior_name!r} and {record.name!r}. Exactly one owner required."
                )
            repo_owner[repo_name] = root
        for alias, canonical in record.repo_aliases.items():
            prior_canonical = repo_aliases.get(alias)
            if prior_canonical is not None and prior_canonical != canonical:
                raise RepoGraphConfigError(
                    f"alias {alias!r} maps to both {prior_canonical!r} and "
                    f"{canonical!r} across registered manifests. Aliases must "
                    "be globally unique."
                )
            repo_aliases[alias] = canonical

    # Third pass: validate also_hosts refs + redundant-grant warnings.
    # also_hosts.repos may use canonical or alias forms — resolve via target's aliases.
    name_to_root: dict[str, Path] = {r.name.lower(): root for root, r in records_by_root.items()}
    for root, record in records_by_root.items():
        for entry in record.also_hosts:
            target_root = name_to_root.get(entry.manifest.lower())
            if target_root is None:
                raise RepoGraphConfigError(
                    f"manifest {record.name!r} also_hosts references unknown "
                    f"manifest {entry.manifest!r}. Known: "
                    f"{sorted(n for n in name_to_root)}"
                )
            target_record = records_by_root[target_root]
            for repo_name in entry.repos:
                # Resolve via target's aliases (accepts canonical or key form).
                canonical = target_record.repo_aliases.get(repo_name.lower(), repo_name)
                if canonical not in target_record.repos:
                    raise RepoGraphConfigError(
                        f"manifest {record.name!r} also_hosts references "
                        f"repo {repo_name!r} not owned by {entry.manifest!r}. "
                        f"{entry.manifest!r} owns: {sorted(target_record.repos)}"
                    )
                if target_record.visibility_scope == "public":
                    warnings.append(
                        f"manifest {record.name!r} also_hosts grants access to "
                        f"{repo_name!r} from public manifest {entry.manifest!r}; "
                        "this grant is redundant (public is universally visible)."
                    )

    return AuthorizationView(
        manifests=records_by_root,
        repo_owner=repo_owner,
        repo_aliases=repo_aliases,
        warnings=warnings,
    )


# ----------------------------------------------------------------------
# Parsing helpers
# ----------------------------------------------------------------------


def _canon(p: Path) -> Path:
    return Path(p).expanduser().resolve()


def _parse_manifest_root(root: Path) -> ManifestRecord:
    yaml_paths = discover_all_manifest_yamls(root)
    if not yaml_paths:
        raise RepoGraphConfigError(
            f"no manifest YAML found under registered manifest root {root}"
        )
    docs = iter_yaml_documents(yaml_paths)

    # Union repos / also_hosts across all docs in this root; visibility_scope
    # must be consistent (or derivable) across them.
    scopes: set[str] = set()
    repos: list[str] = []
    repos_seen: set[str] = set()
    also_hosts: list[AlsoHostsEntry] = []
    repo_local_paths: dict[str, Path] = {}
    repo_aliases: dict[str, str] = {}

    def _register_alias(alias: str, canonical: str) -> None:
        lower = alias.lower()
        prior = repo_aliases.get(lower)
        if prior is not None and prior != canonical:
            raise RepoGraphConfigError(
                f"manifest at {root}: alias {alias!r} maps to both "
                f"{prior!r} and {canonical!r}. Aliases must be unique."
            )
        repo_aliases[lower] = canonical

    for path, raw in docs:
        scope = _extract_scope(raw, path)
        if scope is not None:
            scopes.add(scope)

        for repo_name, fields, aliases in _iter_repos(raw, path):
            if repo_name in repos_seen:
                continue
            repos_seen.add(repo_name)
            repos.append(repo_name)
            local = _opt_local_path(fields)
            if local is not None:
                repo_local_paths[repo_name] = local
            # Register both canonical and any aliases (lowercased).
            _register_alias(repo_name, repo_name)
            for alias in aliases:
                _register_alias(alias, repo_name)

        for entry in _extract_also_hosts(raw, path):
            also_hosts.append(entry)

    # Derive scope if not declared (backward-compat with pre-P2 manifests):
    # if every repo declares visibility=public → infer public; otherwise
    # require explicit declaration to disambiguate.
    if not scopes:
        derived = _derive_scope_from_repos(docs)
        if derived is None:
            raise RepoGraphConfigError(
                f"manifest at {root} declares no `visibility_scope` and scope "
                "could not be inferred from repos[*].visibility (mixed or absent). "
                "Add a top-level `visibility_scope: public|private`."
            )
        scopes.add(derived)

    if len(scopes) > 1:
        raise RepoGraphConfigError(
            f"manifest at {root} has conflicting visibility_scope across its "
            f"YAML files: {sorted(scopes)}"
        )
    scope_value = next(iter(scopes))
    if scope_value not in ("public", "private"):
        raise RepoGraphConfigError(
            f"manifest at {root} has invalid visibility_scope={scope_value!r}; "
            "expected 'public' or 'private'."
        )

    # Per-repo visibility must agree with manifest scope (when declared).
    for path, raw in docs:
        for repo_name, fields, _aliases in _iter_repos(raw, path):
            vis = fields.get("visibility") if isinstance(fields, dict) else None
            if vis is None:
                continue
            if scope_value == "public" and vis != "public":
                # Public manifests may not host private repos (clause 2 leak).
                raise RepoGraphConfigError(
                    f"repo {repo_name!r} in {path} declares visibility={vis!r} "
                    "but its manifest has visibility_scope=public; public "
                    "manifests may only own public repos."
                )

    return ManifestRecord(
        name=root.name,
        root=root,
        yaml_paths=tuple(yaml_paths),
        visibility_scope=scope_value,  # type: ignore[arg-type]
        repos=tuple(repos),
        also_hosts=tuple(also_hosts),
        repo_local_paths=repo_local_paths,
        repo_aliases=repo_aliases,
    )


def _extract_scope(raw: dict, path: Path) -> str | None:
    val = raw.get("visibility_scope")
    if val is None:
        return None
    if not isinstance(val, str):
        raise RepoGraphConfigError(
            f"{path}: visibility_scope must be a string ('public' or 'private')"
        )
    return val


def _derive_scope_from_repos(docs: list[tuple[Path, dict]]) -> str | None:
    saw_any = False
    all_public = True
    for _path, raw in docs:
        for _name, fields, _aliases in _iter_repos(raw, _path):
            saw_any = True
            vis = fields.get("visibility") if isinstance(fields, dict) else None
            if vis != "public":
                all_public = False
    if not saw_any:
        return None
    return "public" if all_public else None


def _iter_repos(raw: dict, path: Path):
    """Yield ``(canonical_name, fields, aliases)`` for every repo entry.

    ``aliases`` is a list of additional names that operators commonly
    use to refer to this repo (the dict-key form for PM-style YAML, etc).
    Empty if no additional aliases.
    """
    repos_raw = raw.get("repos")
    if repos_raw is None:
        return
    if isinstance(repos_raw, dict):
        # PM-style: {repo_id: {canonical_name, ...}}
        for repo_id, fields in repos_raw.items():
            if not isinstance(fields, dict):
                # Skip ill-typed entries; upstream loaders will reject.
                continue
            canonical = fields.get("canonical_name") or str(repo_id)
            aliases = [str(repo_id)] if str(repo_id) != str(canonical) else []
            yield str(canonical), fields, aliases
    elif isinstance(repos_raw, list):
        # P0.4-style: [{name: X}, ...]
        for item in repos_raw:
            if isinstance(item, dict):
                name = item.get("name") or item.get("canonical_name")
                if name:
                    aliases = []
                    alt = item.get("canonical_name") if item.get("name") else None
                    if alt and alt != name:
                        aliases.append(str(alt))
                    yield str(name), item, aliases
            elif isinstance(item, str):
                yield item, {}, []
    else:
        raise RepoGraphConfigError(
            f"{path}: 'repos' must be a mapping or a list"
        )


def _extract_also_hosts(raw: dict, path: Path) -> list[AlsoHostsEntry]:
    items = raw.get("also_hosts")
    if items is None:
        return []
    if not isinstance(items, list):
        raise RepoGraphConfigError(
            f"{path}: 'also_hosts' must be a list of {{manifest, repos}} entries"
        )
    out: list[AlsoHostsEntry] = []
    for idx, item in enumerate(items):
        if not isinstance(item, dict):
            raise RepoGraphConfigError(
                f"{path}: also_hosts[{idx}] must be a mapping"
            )
        manifest = item.get("manifest")
        repos = item.get("repos") or []
        if not isinstance(manifest, str) or not manifest:
            raise RepoGraphConfigError(
                f"{path}: also_hosts[{idx}].manifest must be a non-empty string"
            )
        if not isinstance(repos, list) or not all(isinstance(r, str) for r in repos):
            raise RepoGraphConfigError(
                f"{path}: also_hosts[{idx}].repos must be a list of strings"
            )
        out.append(AlsoHostsEntry(manifest=manifest, repos=tuple(repos)))
    return out


def _opt_local_path(fields: dict) -> Path | None:
    lp = fields.get("local_path")
    if lp is None:
        return None
    if not isinstance(lp, str):
        return None
    return Path(lp).expanduser()
