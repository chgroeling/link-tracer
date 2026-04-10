"""Use case for building the resolved vault digraph."""

from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from vault_net.domain.models import VaultGraph, VaultIndex
    from vault_net.domain.protocols import GraphBuilder


class BuildVaultDigraphUseCase:
    """Build the vault-level digraph through the graph builder port."""

    def __init__(self, graph_builder: GraphBuilder) -> None:
        self._graph_builder = graph_builder

    def execute(self, vault_index: VaultIndex) -> VaultGraph:
        """Return a resolved directed graph for the full vault."""
        return self._graph_builder.build_vault_digraph(vault_index)
