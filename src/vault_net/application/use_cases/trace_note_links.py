"""Use case for tracing links from a single note."""

from __future__ import annotations

import time
from typing import TYPE_CHECKING

import structlog

from vault_net.domain.models import InputError, NoteLinkTrace
from vault_net.domain.services.resolve_note_input import resolve_note_input

if TYPE_CHECKING:
    from pathlib import Path

    from vault_net.domain.protocols import GraphBuilder, VaultScanner

logger = structlog.get_logger(__name__)


class TraceNoteLinksUseCase:
    """Orchestrate vault scan, full graph build, and neighborhood extraction."""

    def __init__(self, scanner: VaultScanner, graph_builder: GraphBuilder) -> None:
        self._scanner = scanner
        self._graph_builder = graph_builder

    def execute(
        self,
        vault_root: Path,
        note_input: str,
        *,
        depth: int = 1,
        extra_exclude_dir: tuple[str, ...] = (),
        no_default_excludes: bool = False,
    ) -> NoteLinkTrace:
        """Scan vault, build graph, and extract neighborhood around note input."""
        start = time.monotonic()
        logger.info(
            "use_case.trace_note_links.start",
            note_input=note_input,
            vault_root=str(vault_root),
            depth=depth,
        )

        logger.debug("use_case.trace_note_links.step.scanning")
        vault_index = self._scanner.scan(
            vault_root,
            extra_exclude_dir=extra_exclude_dir,
            no_default_excludes=no_default_excludes,
        )

        logger.debug("use_case.trace_note_links.step.building_full_graph")
        full_graph = self._graph_builder.build_full_graph(vault_index)

        logger.debug("use_case.trace_note_links.step.resolving_note_input")
        try:
            source_slug = resolve_note_input(note_input, vault_root, vault_index)
        except InputError as exc:
            raise InputError(f"Invalid note input '{note_input}': {exc}") from exc

        logger.debug(
            "use_case.trace_note_links.step.extracting_neighborhood",
            resolved_slug=source_slug,
        )
        neighborhood_graph = self._graph_builder.build_neighborhood_graph(
            source_slug, full_graph, depth=depth
        )

        duration = time.monotonic() - start
        logger.info(
            "use_case.trace_note_links.complete",
            duration=round(duration, 4),
            total_files=vault_index.metadata.total_files,
            neighborhood_nodes=neighborhood_graph.digraph.number_of_nodes(),
        )

        return NoteLinkTrace(
            source_slug=source_slug,
            vault_index=vault_index,
            neighborhood_graph=neighborhood_graph,
        )
