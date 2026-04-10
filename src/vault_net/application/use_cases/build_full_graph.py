"""Use case for building the resolved vault graph."""

from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from vault_net.domain.models import VaultGraph, VaultIndex
    from vault_net.domain.protocols import GraphBuilder


class BuildFullGraphUseCase:
    """Build the full vault graph through the graph builder port."""

    def __init__(self, graph_builder: GraphBuilder) -> None:
        self._graph_builder = graph_builder

    def execute(self, vault_index: VaultIndex) -> VaultGraph:
        """Return a resolved graph for the full vault."""
        return self._graph_builder.build_full_graph(vault_index)
