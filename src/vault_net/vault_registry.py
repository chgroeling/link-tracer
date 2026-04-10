"""Lookup helpers for converting between slugs and vault files."""

from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from vault_net.models import VaultFile, VaultIndex, VaultNote


class VaultRegistry:
    """Provide bidirectional lookup between slugs and `VaultNote` entries."""

    def __init__(self, vault_index: VaultIndex) -> None:
        """Build lookup tables from a vault index."""
        self._slug_to_file: dict[str, VaultNote] = {file.slug: file for file in vault_index.files}
        self._file_path_to_slug: dict[str, str] = {
            file.file_path: file.slug for file in vault_index.files
        }

    def get_file(self, slug: str) -> VaultNote | None:
        """Return the `VaultNote` for a slug, if present."""
        return self._slug_to_file.get(slug)

    def get_slug(self, file: VaultFile) -> str | None:
        """Return the slug for a `VaultFile`, if present."""
        return self._file_path_to_slug.get(file.file_path)
