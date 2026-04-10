"""Single-note graph extraction helpers."""

from __future__ import annotations

import networkx as nx


def build_note_ego_graph(
    source_slug: str,
    vault_digraph: nx.DiGraph[str],
    *,
    depth: int = 1,
) -> nx.DiGraph[str]:
    """Return the directed ego graph around `source_slug`.

    Args:
        source_slug: Source note slug to center the ego graph on.
        vault_digraph: Full vault graph with slug nodes.
        depth: Max traversal radius.

    Returns:
        A directed subgraph containing nodes within `depth` hops when
        traversing the graph in an undirected neighborhood.

    Raises:
        ValueError: If `depth` is negative.
        KeyError: If `source_slug` is not present in `vault_digraph`.
    """
    if depth < 0:
        raise ValueError(f"depth must be >= 0, got {depth}")
    if source_slug not in vault_digraph:
        raise KeyError(source_slug)

    ego = nx.ego_graph(vault_digraph, source_slug, radius=depth, undirected=True)
    return nx.DiGraph(ego)


__all__ = ["build_note_ego_graph"]
