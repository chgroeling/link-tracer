"""Public application facade wiring default adapters to use cases."""

from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from pathlib import Path

    import networkx as nx

    from vault_net.domain.models import VaultGraph, VaultIndex

from vault_net.application.use_cases.build_note_ego_graph import BuildNoteEgoGraphUseCase
from vault_net.application.use_cases.build_vault_digraph import BuildVaultDigraphUseCase
from vault_net.application.use_cases.scan_vault import ScanVaultUseCase
from vault_net.infrastructure.graph.networkx_graph_builder import NetworkXGraphBuilder
from vault_net.infrastructure.scanner.matterify_scanner import MatterifyVaultScanner


def scan_vault(
    vault_root: Path,
    extra_exclude_dir: tuple[str, ...] = (),
    no_default_excludes: bool = False,
) -> VaultIndex:
    """Scan vault directory and build a domain index."""
    use_case = ScanVaultUseCase(scanner=MatterifyVaultScanner())
    return use_case.execute(
        vault_root,
        extra_exclude_dir=extra_exclude_dir,
        no_default_excludes=no_default_excludes,
    )


def build_vault_digraph(vault_index: VaultIndex) -> VaultGraph:
    """Build a resolved vault graph whose nodes are note slugs."""
    use_case = BuildVaultDigraphUseCase(graph_builder=NetworkXGraphBuilder())
    return use_case.execute(vault_index)


def build_note_ego_graph(
    source_slug: str,
    vault_digraph: nx.DiGraph[str],
    *,
    depth: int = 1,
) -> nx.DiGraph[str]:
    """Return the directed ego graph around `source_slug`."""
    use_case = BuildNoteEgoGraphUseCase(graph_builder=NetworkXGraphBuilder())
    return use_case.execute(source_slug, vault_digraph, depth=depth)
