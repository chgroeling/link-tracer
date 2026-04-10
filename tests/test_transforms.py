"""Tests for graph transform functions."""

from __future__ import annotations

from pathlib import Path

import networkx as nx

from vault_net.models import LayerEntry, VaultLayered
from vault_net.transforms import to_layered


def test_to_layered_returns_vault_layered_type() -> None:
    """Return value is a VaultLayered instance."""
    graph = nx.DiGraph()
    graph.add_node("home.md")
    result = to_layered("home.md", graph, Path("/vault"))
    assert isinstance(result, VaultLayered)


def test_to_layered_preserves_vault_root_and_total_files() -> None:
    """source note, root and size are forwarded correctly."""
    graph = nx.DiGraph()
    graph.add_edge("home.md", "about.md")

    result = to_layered("home.md", graph, Path("/vault"))
    assert result.source_note == "home.md"
    assert result.vault_root == "/vault"
    assert result.total_files == 2


def test_to_layered_empty_graph_yields_source_at_depth_zero() -> None:
    """Source note is always depth zero."""
    graph = nx.DiGraph()
    graph.add_node("home.md")
    result = to_layered("home.md", graph, Path("/vault"))
    assert result.layers == [LayerEntry(depth=0, note="home.md")]


def test_to_layered_backlinks_appear_at_depth_one() -> None:
    """Reverse neighbors are included via undirected BFS."""
    graph = nx.DiGraph()
    graph.add_edge("other.md", "home.md")
    result = to_layered("home.md", graph, Path("/vault"))
    depths = {entry.note: entry.depth for entry in result.layers}
    assert depths["home.md"] == 0
    assert depths["other.md"] == 1


def test_to_layered_two_hop_note_appears_at_depth_two() -> None:
    """Two hops from source yields depth two."""
    graph = nx.DiGraph()
    graph.add_edge("home.md", "about.md")
    graph.add_edge("about.md", "projects.md")
    result = to_layered("home.md", graph, Path("/vault"))
    depths = {entry.note: entry.depth for entry in result.layers}
    assert depths["home.md"] == 0
    assert depths["about.md"] == 1
    assert depths["projects.md"] == 2
