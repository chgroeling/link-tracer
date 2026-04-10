"""Unit tests for digraph and edge-list builders."""

from __future__ import annotations

from pathlib import Path

from vault_net import build_vault_digraph, build_vault_edge_list, scan_vault
from vault_net.models import VaultGraph, VaultIndex
from vault_net.vault_registry import VaultRegistry


def _create_vault(tmp_path: Path, notes: dict[str, str]) -> Path:
    """Create a temporary vault from relative file paths to markdown content."""
    vault_root = tmp_path / "vault"
    vault_root.mkdir()

    for file_path, content in notes.items():
        note_path = vault_root / file_path
        note_path.parent.mkdir(parents=True, exist_ok=True)
        note_path.write_text(content, encoding="utf-8")

    return vault_root


def _slug_for(vault_index: VaultIndex, file_path: str) -> str:
    """Return slug for a scanned file path."""
    return next(file.slug for file in vault_index.files if file.file_path == file_path)


def test_build_vault_digraph_resolves_known_links_only(tmp_path: Path) -> None:
    """Resolved links are included and unresolved targets are omitted."""
    vault_root = _create_vault(
        tmp_path,
        {
            "home.md": "[[about]]\n[[missing]]\n",
            "about.md": "",
        },
    )

    vault_index = scan_vault(vault_root)
    vault_graph = build_vault_digraph(vault_index)
    home_slug = _slug_for(vault_index, "home.md")
    about_slug = _slug_for(vault_index, "about.md")

    assert isinstance(vault_graph, VaultGraph)
    assert sorted(vault_graph.digraph.edges()) == [(home_slug, about_slug)]
    assert vault_graph.metadata.edge_count == 1


def test_build_vault_digraph_includes_isolated_notes(tmp_path: Path) -> None:
    """Digraph includes all scanned notes, including isolated ones."""
    vault_root = _create_vault(
        tmp_path,
        {
            "home.md": "[[about]]\n",
            "about.md": "",
            "isolated.md": "",
        },
    )

    vault_index = scan_vault(vault_root)
    vault_graph = build_vault_digraph(vault_index)
    home_slug = _slug_for(vault_index, "home.md")
    about_slug = _slug_for(vault_index, "about.md")

    assert sorted(vault_graph.digraph.nodes()) == sorted(file.slug for file in vault_index.files)
    assert sorted(vault_graph.digraph.edges()) == [(home_slug, about_slug)]


def test_build_vault_digraph_skips_self_loops_and_deduplicates_edges(tmp_path: Path) -> None:
    """Self-links are filtered and repeated links collapse into one edge."""
    vault_root = _create_vault(
        tmp_path,
        {
            "home.md": "[[home]]\n[[about]]\n[[about]]\n",
            "about.md": "",
        },
    )

    vault_index = scan_vault(vault_root)
    vault_graph = build_vault_digraph(vault_index)
    home_slug = _slug_for(vault_index, "home.md")
    about_slug = _slug_for(vault_index, "about.md")

    assert sorted(vault_graph.digraph.edges()) == [(home_slug, about_slug)]
    assert vault_graph.metadata.edge_count == 1


def test_build_vault_edge_list_returns_lightweight_vault_file_pairs(tmp_path: Path) -> None:
    """Edge list is represented as source/target `VaultFile` pairs."""
    vault_root = _create_vault(
        tmp_path,
        {
            "home.md": "[[about]]\n",
            "about.md": "",
        },
    )

    vault_index = scan_vault(vault_root)
    vault_registry = VaultRegistry(vault_index)
    vault_graph = build_vault_digraph(vault_index)
    edges = build_vault_edge_list(vault_graph, vault_registry)

    assert len(edges) == 1
    assert edges[0][0].file_path == "home.md"
    assert edges[0][1].file_path == "about.md"
    assert not hasattr(edges[0][0], "links")
    assert not hasattr(edges[0][0], "frontmatter")
    assert not hasattr(edges[0][0], "stats")


def test_vault_registry_provides_bidirectional_lookup(tmp_path: Path) -> None:
    """Registry can resolve both slug->file and file->slug lookups."""
    vault_root = _create_vault(tmp_path, {"home.md": ""})

    vault_index = scan_vault(vault_root)
    lookup = VaultRegistry(vault_index)
    home_note = vault_index.files[0]

    assert lookup.get_file(home_note.slug) == home_note
    assert lookup.get_slug(home_note) == home_note.slug
    assert lookup.get_file("missing") is None
    assert lookup.get_slug(home_note.to_file()) == home_note.slug
