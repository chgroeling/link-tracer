"""Domain ports used by application use cases."""

from __future__ import annotations

from typing import TYPE_CHECKING, Protocol

if TYPE_CHECKING:
    from pathlib import Path

    import networkx as nx

    from vault_net.domain.models import VaultGraph, VaultIndex


class VaultScanner(Protocol):
    """Port for scanning vault content into a domain index."""

    def scan(
        self,
        vault_root: Path,
        *,
        extra_exclude_dir: tuple[str, ...] = (),
        no_default_excludes: bool = False,
    ) -> VaultIndex:
        """Scan the vault and return a domain index."""


class GraphBuilder(Protocol):
    """Port for graph construction and traversal."""

    def build_vault_digraph(self, vault_index: VaultIndex) -> VaultGraph:
        """Build a resolved directed graph from a vault index."""

    def build_note_ego_graph(
        self,
        source_slug: str,
        vault_digraph: nx.DiGraph[str],
        *,
        depth: int = 1,
    ) -> nx.DiGraph[str]:
        """Build an ego graph around a source slug."""
