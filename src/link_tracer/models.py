"""Typed models for link resolution results."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path  # noqa: TC003
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from matterify.models import FileEntry, ScanResults


@dataclass(frozen=True, slots=True)
class ExtractedLink:
    """Represents a serialized obsilink link used in API output."""

    link_type: str
    target: str
    alias: str | None
    heading: str | None
    blockid: str | None

    @classmethod
    def from_obsilink_link(
        cls,
        *,
        link_type: str,
        target: str,
        alias: str | None,
        heading: str | None,
        blockid: str | None,
    ) -> ExtractedLink:
        """Build an ExtractedLink from obsilink Link fields."""
        return cls(
            link_type=link_type,
            target=target,
            alias=alias,
            heading=heading,
            blockid=blockid,
        )


@dataclass(frozen=True, slots=True)
class LinkEdge:
    """Represents a directed edge from one note to a link target."""

    link: ExtractedLink
    resolved: bool
    target_note: str | None = None
    unresolved_reason: str | None = None


@dataclass(frozen=True, slots=True)
class ResolveMetadata:
    """Metadata summary for a resolution result."""

    source_directory: str
    total_files: int
    files_with_frontmatter: int
    files_without_frontmatter: int
    errors: int


@dataclass(frozen=True, slots=True)
class VaultGraph:
    """Vault-wide link graph: edges between notes with summary metadata."""

    vault_root: str
    metadata: ResolveMetadata
    edges: dict[str, list[LinkEdge]]


@dataclass(frozen=True, slots=True)
class VaultIndex:  # type: ignore[no-any-unimported]
    """Immutable vault index with file entries."""

    vault_root: Path
    files: list[FileEntry]  # type: ignore[no-any-unimported]
    source_directory: str

    @classmethod
    def from_scan_result(  # type: ignore[no-any-unimported]
        cls,
        vault_root: Path,
        scan_result: ScanResults,
    ) -> VaultIndex:
        """Build a VaultIndex from a matterify scan result.

        Args:
            vault_root: Root directory of the vault.
            scan_result: ScanResults from matterify.scan_directory().

        Returns:
            VaultIndex with file entries.
        """
        return cls(
            vault_root=vault_root,
            files=scan_result.files,
            source_directory=scan_result.metadata.root,
        )
