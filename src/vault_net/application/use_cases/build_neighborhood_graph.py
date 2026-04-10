"""Use case for extracting a note neighborhood graph."""

from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from vault_net.domain.models import VaultGraph
    from vault_net.domain.protocols import GraphBuilder


class BuildNeighborhoodGraphUseCase:
    """Build a neighborhood graph around a source note slug."""

    def __init__(self, graph_builder: GraphBuilder) -> None:
        self._graph_builder = graph_builder

    def execute(
        self,
        source_slug: str,
        graph: VaultGraph,
        *,
        depth: int = 1,
    ) -> VaultGraph:
        """Return a neighborhood graph rooted at the provided source slug."""
        return self._graph_builder.build_neighborhood_graph(source_slug, graph, depth=depth)
