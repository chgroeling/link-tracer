"""Use case for extracting a note-centric ego graph."""

from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    import networkx as nx

    from vault_net.domain.protocols import GraphBuilder


class BuildNoteEgoGraphUseCase:
    """Build an ego graph around a source note slug."""

    def __init__(self, graph_builder: GraphBuilder) -> None:
        self._graph_builder = graph_builder

    def execute(
        self,
        source_slug: str,
        vault_digraph: nx.DiGraph[str],
        *,
        depth: int = 1,
    ) -> nx.DiGraph[str]:
        """Return an ego graph rooted at the provided source slug."""
        return self._graph_builder.build_note_ego_graph(source_slug, vault_digraph, depth=depth)
