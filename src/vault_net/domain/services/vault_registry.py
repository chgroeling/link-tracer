"""Lookup services for converting between slugs and files."""

from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from vault_net.domain.models import VaultFile, VaultIndex, VaultNote


class VaultRegistry:
    """Provide bidirectional lookup between slugs and `VaultNote` entries."""

    def __init__(self, vault_index: VaultIndex) -> None:
        self._slug_to_file: dict[str, VaultNote] = {file.slug: file for file in vault_index.files}
        self._file_path_to_slug: dict[str, str] = {
            file.file_path: file.slug for file in vault_index.files
        }

    def get_file(self, slug: str) -> VaultNote | None:
        """Return the note for a slug, if present."""
        return self._slug_to_file.get(slug)

    def get_slug(self, file: VaultFile) -> str | None:
        """Return the slug for a file identity, if present."""
        return self._file_path_to_slug.get(file.file_path)

    def get_slug_by_path(self, file_path: str) -> str | None:
        """Return the slug for a file path, if present."""
        return self._file_path_to_slug.get(file_path)
