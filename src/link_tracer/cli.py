"""CLI entry point for link-tracer."""

from __future__ import annotations

import json
import os
from pathlib import Path

import click
from dotenv import dotenv_values, find_dotenv

from link_tracer.api import trace_links
from link_tracer.models import TraceOptions


def resolve_vault_dir(cli_value: Path | None) -> Path:
    """Resolve vault directory with precedence: CLI > .vault > env var."""
    if cli_value:
        resolved = cli_value if cli_value.is_absolute() else (Path.cwd() / cli_value).resolve()
        if not resolved.exists():
            raise click.UsageError(f"Vault directory does not exist: {resolved}")
        return resolved

    vault_path = find_dotenv(filename=".vault", usecwd=True)
    if vault_path:
        values = dotenv_values(vault_path)
        vault_dir_value = values.get("VAULT_DIR")
        if vault_dir_value:
            vault_file = Path(vault_path)
            path = Path(vault_dir_value)
            resolved = path if path.is_absolute() else (vault_file.parent / path).resolve()
            if not resolved.exists():
                raise click.UsageError(f"Vault directory does not exist: {resolved}")
            return resolved

    env_value = os.environ.get("VAULT_DIR")
    if env_value:
        path = Path(env_value)
        resolved = path if path.is_absolute() else (Path.cwd() / path).resolve()
        if not resolved.exists():
            raise click.UsageError(f"Vault directory does not exist: {resolved}")
        return resolved

    raise click.UsageError(
        "No vault directory provided. "
        "Use --vault-dir, set VAULT_DIR env var, or create a .vault file."
    )


@click.command()
@click.argument("note", type=click.Path(exists=True, path_type=Path))
@click.option(
    "--vault-dir",
    type=click.Path(path_type=Path),
    default=None,
    help="Vault root directory (overrides VAULT_DIR env and .vault file)",
)
@click.option("--follow-chain", is_flag=True, help="Follow links recursively")
@click.option("--max-depth", type=int, default=None, help="Traversal depth limit")
@click.option("--pretty", is_flag=True, help="Pretty-print JSON output")
def main(
    note: Path, vault_dir: Path | None, follow_chain: bool, max_depth: int | None, pretty: bool
) -> int:
    """Trace Obsidian note links to filesystem sources."""
    vault_root = resolve_vault_dir(vault_dir)
    options = TraceOptions(follow_chain=follow_chain, max_depth=max_depth)
    payload = trace_links(note_path=note, vault_root=vault_root, options=options)
    click.echo(json.dumps(payload, indent=2 if pretty else None))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
