"""Matterify-backed implementation of the vault scanner port."""

from __future__ import annotations

import time
from pathlib import Path
from typing import TYPE_CHECKING, Any, cast

import structlog
from matterify import scan_directory
from matterify.constants import BLACKLIST
from obsilink import extract_links

from vault_net.domain.models import (
    VaultFileStats,
    VaultIndex,
    VaultIndexMetadata,
    VaultLink,
    VaultNote,
)
from vault_net.domain.services.slug import generate_slug

if TYPE_CHECKING:
    from matterify.models import FileStats, ScanResults

logger = structlog.get_logger(__name__)


def _to_vault_link(link: Any) -> VaultLink:
    """Convert an obsilink link object into a domain `VaultLink`."""
    return VaultLink(
        link_type=link.type.value,
        target=link.target,
        alias=link.alias,
        heading=link.heading,
        blockid=link.blockid,
    )


def _convert_scan_to_index(vault_root: Path, scan_result: ScanResults) -> VaultIndex:
    """Convert a matterify scan result to a `VaultIndex`."""
    meta = scan_result.metadata
    files_with_frontmatter = cast("int", meta.files_with_frontmatter)
    files_without_frontmatter = cast("int", meta.files_without_frontmatter)
    metadata = VaultIndexMetadata(
        root=meta.root,
        total_files=meta.total_files,
        files_with_frontmatter=files_with_frontmatter,
        files_without_frontmatter=files_without_frontmatter,
        errors=meta.errors,
        scan_duration_seconds=meta.scan_duration_seconds,
        avg_duration_per_file_ms=meta.avg_duration_per_file_ms,
        throughput_files_per_second=meta.throughput_files_per_second,
    )

    files: list[VaultNote] = []
    slug_counts: dict[str, int] = {}
    for entry in scan_result.files:
        raw_links = getattr(entry, "custom_data", None) or []
        entry_stats = cast("FileStats", entry.stats)
        entry_hash = cast("str", entry.file_hash)

        filename = Path(entry.file_path).name
        slug = generate_slug(filename, slug_counts)
        files.append(
            VaultNote(
                file_path=entry.file_path,
                frontmatter=entry.frontmatter,
                status=entry.status,
                error=entry.error,
                stats=VaultFileStats(
                    file_size=entry_stats.file_size,
                    modified_time=entry_stats.modified_time,
                    access_time=entry_stats.access_time,
                ),
                file_hash=entry_hash,
                links=[_to_vault_link(link) for link in raw_links if link.is_file],
                slug=slug,
            )
        )

    return VaultIndex(vault_root=vault_root, metadata=metadata, files=files)


class MatterifyVaultScanner:
    """Scanner adapter that uses matterify and obsilink."""

    def scan(
        self,
        vault_root: Path,
        *,
        extra_exclude_dir: tuple[str, ...] = (),
        no_default_excludes: bool = False,
    ) -> VaultIndex:
        """Scan vault directory and build a domain index."""
        start = time.monotonic()
        logger.debug("scan_vault.start", vault_root=str(vault_root))

        base = () if no_default_excludes else BLACKLIST
        scan_result = scan_directory(
            vault_root,
            exclude=base + extra_exclude_dir,
            compute_hash=True,
            compute_stats=True,
            compute_frontmatter=True,
            callback=extract_links,
        )

        index = _convert_scan_to_index(vault_root, scan_result)
        duration = time.monotonic() - start
        logger.debug(
            "scan_vault.complete",
            duration=round(duration, 4),
            file_count=len(index.files),
        )
        return index
