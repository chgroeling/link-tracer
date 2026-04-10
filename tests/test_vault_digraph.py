"""Unit tests for digraph and edge-list builders."""

from __future__ import annotations

from pathlib import Path

from vault_net import (
    build_vault_digraph,
    scan_vault,
)
from vault_net.transforms import build_vault_edge_list
from vault_net.vault_registry import VaultRegistry


def test_build_vault_digraph_resolves_links_and_omits_missing(tmp_path: Path) -> None:
    """Resolve links into digraph edges and ignore unresolved targets."""
    vault_root = tmp_path / "vault"
    vault_root.mkdir()
    (vault_root / "home.md").write_text("[[about]]\n[[missing]]\n", encoding="utf-8")
    (vault_root / "about.md").write_text("", encoding="utf-8")

    vault_index = scan_vault(vault_root)
    digraph = build_vault_digraph(vault_index)
    home_slug = next(file.slug for file in vault_index.files if file.file_path == "home.md")
    about_slug = next(file.slug for file in vault_index.files if file.file_path == "about.md")

    assert sorted(digraph.edges()) == [(home_slug, about_slug)]


def test_build_vault_digraph_contains_all_slugs(tmp_path: Path) -> None:
    """Digraph includes isolated notes and resolved edges."""
    vault_root = tmp_path / "vault"
    vault_root.mkdir()
    (vault_root / "home.md").write_text("[[about]]\n", encoding="utf-8")
    (vault_root / "about.md").write_text("", encoding="utf-8")
    (vault_root / "isolated.md").write_text("", encoding="utf-8")

    vault_index = scan_vault(vault_root)
    digraph = build_vault_digraph(vault_index)

    slugs = sorted(file.slug for file in vault_index.files)
    home_slug = next(file.slug for file in vault_index.files if file.file_path == "home.md")
    about_slug = next(file.slug for file in vault_index.files if file.file_path == "about.md")

    assert sorted(digraph.nodes()) == slugs
    assert sorted(digraph.edges()) == [(home_slug, about_slug)]


def test_build_vault_edge_list_resolves_to_vault_file_pairs(tmp_path: Path) -> None:
    """Return resolved edges as source/target `VaultFile` pairs."""
    vault_root = tmp_path / "vault"
    vault_root.mkdir()
    (vault_root / "home.md").write_text("[[about]]\n", encoding="utf-8")
    (vault_root / "about.md").write_text("", encoding="utf-8")

    vault_index = scan_vault(vault_root)
    vault_registry = VaultRegistry(vault_index)
    edge_list = build_vault_edge_list(vault_index, vault_registry)

    assert len(edge_list) == 1
    assert edge_list[0][0].file_path == "home.md"
    assert edge_list[0][1].file_path == "about.md"
    assert not hasattr(edge_list[0][0], "links")
    assert not hasattr(edge_list[0][0], "frontmatter")
    assert not hasattr(edge_list[0][0], "stats")


def test_vault_registry_get_slug_for_file(tmp_path: Path) -> None:
    """Return slug for a known scanned note instance."""
    vault_root = tmp_path / "vault"
    vault_root.mkdir()
    (vault_root / "home.md").write_text("", encoding="utf-8")

    vault_index = scan_vault(vault_root)
    lookup = VaultRegistry(vault_index)
    home_file = vault_index.files[0]

    assert lookup.get_slug(home_file) == home_file.slug
