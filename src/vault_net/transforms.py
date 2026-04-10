"""Graph transform functions for alternative output representations."""

from __future__ import annotations

from typing import TYPE_CHECKING

import networkx as nx

from vault_net.models import LayerEntry, VaultLayered
from vault_net.vault_digraph import build_vault_digraph

if TYPE_CHECKING:
    from pathlib import Path

    from vault_net.models import VaultFile, VaultIndex
    from vault_net.vault_registry import VaultRegistry

__all__ = ["build_vault_edge_list", "to_layered"]


def build_vault_edge_list(
    vault_index: VaultIndex,
    vault_registry: VaultRegistry,
) -> list[list[VaultFile]]:
    """Return a deduplicated resolved edge list as `VaultFile` pairs."""
    digraph = build_vault_digraph(vault_index)
    slug_edges = sorted(digraph.edges())

    edges: list[list[VaultFile]] = []
    for source_slug, target_slug in slug_edges:
        source_file = vault_registry.get_file(source_slug)
        target_file = vault_registry.get_file(target_slug)
        if source_file is None or target_file is None:
            continue
        edges.append([source_file.to_file(), target_file.to_file()])

    return edges


def to_layered(source_slug: str, graph: nx.DiGraph[str], vault_root: Path) -> VaultLayered:
    """Transform an ego graph into a flat BFS depth-layer list."""
    layers: list[LayerEntry] = []
    for depth, nodes in enumerate(nx.bfs_layers(graph.to_undirected(), [source_slug])):
        layers.extend(LayerEntry(depth=depth, note=str(node)) for node in nodes)

    return VaultLayered(
        source_note=source_slug,
        vault_root=str(vault_root),
        total_files=graph.number_of_nodes(),
        layers=layers,
    )
