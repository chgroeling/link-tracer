"""Use case for tracing links from a single note."""

from __future__ import annotations

from typing import TYPE_CHECKING

from vault_net.domain.models import NoteLinkTrace

if TYPE_CHECKING:
    from pathlib import Path

    from vault_net.domain.protocols import GraphBuilder, VaultScanner


class TraceNoteLinksUseCase:
    """Orchestrate vault scan, full graph build, and neighborhood extraction."""

    def __init__(self, scanner: VaultScanner, graph_builder: GraphBuilder) -> None:
        self._scanner = scanner
        self._graph_builder = graph_builder

    def execute(
        self,
        vault_root: Path,
        source_slug: str,
        *,
        depth: int = 1,
        extra_exclude_dir: tuple[str, ...] = (),
        no_default_excludes: bool = False,
    ) -> NoteLinkTrace:
        """Scan vault, build graph, and extract neighborhood around source slug."""
        vault_index = self._scanner.scan(
            vault_root,
            extra_exclude_dir=extra_exclude_dir,
            no_default_excludes=no_default_excludes,
        )

        full_graph = self._graph_builder.build_full_graph(vault_index)
        neighborhood_graph = self._graph_builder.build_neighborhood_graph(
            source_slug, full_graph, depth=depth
        )

        return NoteLinkTrace(
            source_slug=source_slug,
            vault_index=vault_index,
            neighborhood_graph=neighborhood_graph,
        )
