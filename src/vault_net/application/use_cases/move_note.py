"""Use case for moving a note to a new path and updating backlinks."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import TYPE_CHECKING

import structlog
from obsilink import Link, extract_links, replace_links

from vault_net.domain.services.vault_registry import VaultRegistry

if TYPE_CHECKING:
    from vault_net.domain.protocols import GraphBuilder, VaultScanner

logger = structlog.get_logger(__name__)


@dataclass(frozen=True, slots=True)
class MoveResult:
    """Result of moving a note."""

    old_path: str
    new_path: str
    updated_files: list[str]


class MoveNoteUseCase:
    """Move a note to a new path and update backlinks in referring notes."""

    def __init__(self, scanner: VaultScanner, graph_builder: GraphBuilder) -> None:
        self._scanner = scanner
        self._graph_builder = graph_builder

    def execute(
        self,
        vault_root: Path,
        note_input: str,
        destination: str,
        *,
        extra_exclude: tuple[str, ...] = (),
        no_default_excludes: bool = False,
    ) -> MoveResult:
        """Move a note and rewrite backlinks in files that reference it.

        Args:
            vault_root: Root directory of the vault.
            note_input: Slug or relative file path identifying the note.
            destination: New relative path for the note inside the vault.
                A ``.md`` extension is appended automatically if missing.
            extra_exclude: Additional glob patterns to exclude from scanning.
            no_default_excludes: Disable built-in default exclusions.

        Returns:
            A `MoveResult` with the old path, new path, and updated files.

        Raises:
            KeyError: If the slug or path cannot be resolved.
            FileNotFoundError: If the source file does not exist on disk.
            FileExistsError: If a file already exists at the destination.
            ValueError: If the destination escapes the vault root.
        """
        logger.info("use_case.move_note.start", note_input=note_input, destination=destination)

        if not destination.endswith(".md"):
            destination = f"{destination}.md"

        vault_index, note_links = self._scanner.index_files(
            vault_root,
            extra_exclude=extra_exclude,
            no_default_excludes=no_default_excludes,
        )

        registry = VaultRegistry(vault_index)
        slug = registry.resolve_to_slug(note_input, vault_root)
        if slug is None:
            raise KeyError(note_input)
        note = registry.get_note(slug)
        if note is None:
            raise KeyError(note_input)

        source_abs = (vault_root / note.file_path).resolve()
        if not source_abs.exists():
            raise FileNotFoundError(f"Note file does not exist: {source_abs}")

        dest_abs = (vault_root / destination).resolve()
        if not str(dest_abs).startswith(str(vault_root.resolve())):
            raise ValueError(f"Destination escapes vault root: {destination}")
        if dest_abs.exists():
            raise FileExistsError(f"Destination already exists: {dest_abs}")

        # Build graph to find backlinks
        full_graph = self._graph_builder.build_full_graph(vault_index, note_links)
        backlink_slugs = list(full_graph.digraph.predecessors(slug))

        # Move the file
        dest_abs.parent.mkdir(parents=True, exist_ok=True)
        source_abs.rename(dest_abs)
        logger.info("use_case.move_note.moved", old=str(source_abs), new=str(dest_abs))

        # Compute old and new targets (stem without extension, as Obsidian uses)
        old_stem = Path(note.file_path).stem
        new_stem = Path(destination).stem

        # Update backlinks in referring files
        updated_files: list[str] = []
        for bl_slug in backlink_slugs:
            bl_note = registry.get_note(bl_slug)
            if bl_note is None:
                continue
            bl_abs = vault_root / bl_note.file_path
            if not bl_abs.exists():
                continue
            content = bl_abs.read_text(encoding="utf-8")
            links = extract_links(content)

            replacements: list[tuple[Link, Link]] = []
            for link in links:
                if not link.is_file:
                    continue
                link_target_stem = Path(link.target).stem
                if link_target_stem.lower() == old_stem.lower():
                    new_link = Link(
                        type=link.type,
                        target=new_stem,
                        alias=link.alias,
                        heading=link.heading,
                        blockid=link.blockid,
                    )
                    replacements.append((link, new_link))

            if replacements:
                new_content, applied = replace_links(content, replacements)
                if any(applied):
                    bl_abs.write_text(new_content, encoding="utf-8")
                    updated_files.append(bl_note.file_path)
                    logger.info(
                        "use_case.move_note.backlink_updated",
                        file=bl_note.file_path,
                        replacements=sum(applied),
                    )

        logger.info(
            "use_case.move_note.done",
            old_path=note.file_path,
            new_path=destination,
            updated_count=len(updated_files),
        )
        return MoveResult(
            old_path=note.file_path,
            new_path=destination,
            updated_files=updated_files,
        )
