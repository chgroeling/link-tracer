"""Resolve note input (file path or slug) to a validated slug."""

from __future__ import annotations

import os
from pathlib import Path
from typing import TYPE_CHECKING

from vault_net.consts import _POSSIBLE_EXTENSIONS
from vault_net.domain.models import InputError
from vault_net.domain.services.vault_registry import VaultRegistry

if TYPE_CHECKING:
    from vault_net.domain.models import VaultIndex


def _looks_like_path(input_value: str) -> bool:
    return os.sep in input_value or input_value.startswith(".")


def resolve_note_input(
    note_input: str,
    vault_root: Path,
    vault_index: VaultIndex,
) -> str:
    if _looks_like_path(note_input):
        return _resolve_file_path(note_input, vault_root, vault_index)
    return _resolve_slug(note_input, vault_index)


def _resolve_file_path(
    note_input: str,
    vault_root: Path,
    vault_index: VaultIndex,
) -> str:
    if not note_input.endswith(_POSSIBLE_EXTENSIONS):
        raise InputError(f"File '{note_input}' is not a valid note (must have .md extension)")
    resolved_path = Path(note_input)
    if not resolved_path.is_absolute():
        resolved_path = vault_root / resolved_path
    try:
        resolved_path = resolved_path.resolve()
    except OSError as exc:
        raise InputError(f"Cannot resolve file path '{note_input}': {exc}") from exc
    if not resolved_path.is_relative_to(vault_root):
        raise InputError(f"File '{note_input}' is not inside the vault root '{vault_root}'")
    if not resolved_path.exists():
        raise InputError(f"File '{note_input}' does not exist in the vault")
    registry = VaultRegistry(vault_index)
    slug = registry.get_slug_by_path(str(resolved_path))
    if slug is None:
        raise InputError(
            f"File '{note_input}' was found but has no associated slug (internal error)"
        )
    return slug


def _resolve_slug(note_input: str, vault_index: VaultIndex) -> str:
    registry = VaultRegistry(vault_index)
    file = registry.get_file(note_input)
    if file is None:
        raise KeyError(note_input)
    return file.slug
