# SPDX-License-Identifier: AGPL-3.0-or-later
# Copyright (C) 2026 ProtocolWarden
"""``repograph`` CLI — manifest registry management.

Subcommands::

    repograph manifest add <path>      # register a manifest repo root
    repograph manifest list            # show known manifests
    repograph manifest remove <path>   # unregister
    repograph manifest validate        # run load-time validations
    repograph manifest show <path>     # summary (scope, repos, also_hosts)
"""

from __future__ import annotations

from pathlib import Path

import typer

from .authorization import build_authorization_view
from .errors import RepoGraphConfigError
from .registry import Registry

app = typer.Typer(
    name="repograph",
    help="RepoGraph — manifest registry and topology authorization.",
    no_args_is_help=True,
    add_completion=False,
)

manifest_app = typer.Typer(
    name="manifest",
    help="Manage the per-machine manifest registry.",
    no_args_is_help=True,
    add_completion=False,
)
app.add_typer(manifest_app, name="manifest")


@manifest_app.command("add")
def manifest_add(
    path: Path = typer.Argument(..., help="Manifest repo root to register."),
) -> None:
    """Register a manifest repo root with the local RepoGraph registry."""
    try:
        registry = Registry.load()
        added = registry.add(path)
    except RepoGraphConfigError as exc:
        typer.echo(f"repograph: {exc}", err=True)
        raise typer.Exit(code=1)
    resolved = Path(path).expanduser().resolve()
    if added:
        typer.echo(f"added: {resolved}")
    else:
        typer.echo(f"already registered: {resolved}")


@manifest_app.command("remove")
def manifest_remove(
    path: Path = typer.Argument(..., help="Manifest repo root to unregister."),
) -> None:
    """Unregister a manifest repo root."""
    registry = Registry.load()
    removed = registry.remove(path)
    resolved = Path(path).expanduser().resolve()
    if removed:
        typer.echo(f"removed: {resolved}")
    else:
        typer.echo(f"not registered: {resolved}", err=True)
        raise typer.Exit(code=1)


@manifest_app.command("list")
def manifest_list() -> None:
    """Print all registered manifest repo roots."""
    registry = Registry.load()
    if not registry.manifests:
        typer.echo(f"(empty) registry at {registry.path}")
        return
    typer.echo(f"# registry: {registry.path}")
    for entry in registry.list():
        typer.echo(str(entry))


@manifest_app.command("validate")
def manifest_validate() -> None:
    """Run registry + load-time validations. Exits non-zero on errors."""
    registry = Registry.load()
    issues = registry.validate()
    if issues:
        for issue in issues:
            typer.echo(f"registry: {issue}", err=True)
        raise typer.Exit(code=1)

    try:
        view = build_authorization_view(registry.list())
    except RepoGraphConfigError as exc:
        typer.echo(f"manifest topology: {exc}", err=True)
        raise typer.Exit(code=1)

    for w in view.warnings:
        typer.echo(f"warning: {w}", err=True)

    typer.echo(
        f"ok: {len(view.manifests)} manifest(s), {len(view.repo_owner)} repo(s) registered."
    )


@manifest_app.command("show")
def manifest_show(
    path: Path = typer.Argument(..., help="Registered manifest repo root."),
) -> None:
    """Print a summary of a registered manifest (scope, repos, also_hosts)."""
    registry = Registry.load()
    target = Path(path).expanduser().resolve()
    if target not in {p.expanduser().resolve() for p in registry.manifests}:
        typer.echo(f"manifest not registered: {target}", err=True)
        raise typer.Exit(code=1)
    try:
        view = build_authorization_view(registry.list())
    except RepoGraphConfigError as exc:
        typer.echo(f"manifest topology: {exc}", err=True)
        raise typer.Exit(code=1)
    record = view.get_by_root(target)
    if record is None:
        typer.echo(f"no record for {target}", err=True)
        raise typer.Exit(code=1)
    typer.echo(f"name: {record.name}")
    typer.echo(f"root: {record.root}")
    typer.echo(f"visibility_scope: {record.visibility_scope}")
    typer.echo("yaml_files:")
    for y in record.yaml_paths:
        typer.echo(f"  - {y}")
    typer.echo(f"repos ({len(record.repos)}):")
    for r in record.repos:
        typer.echo(f"  - {r}")
    if record.also_hosts:
        typer.echo("also_hosts:")
        for entry in record.also_hosts:
            typer.echo(f"  - manifest: {entry.manifest}")
            for r in entry.repos:
                typer.echo(f"      - {r}")
    else:
        typer.echo("also_hosts: (none)")


if __name__ == "__main__":  # pragma: no cover
    app()
