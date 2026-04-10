"""Unit tests for the vault_edge_list module."""

from __future__ import annotations

from pathlib import Path

from vault_net import build_vault_edge_list, build_vault_slug_edge_list, scan_vault
from vault_net.vault_registry import VaultRegistry


def test_build_vault_slug_edge_list_resolves_to_slug_pairs(tmp_path: Path) -> None:
    """Return resolved edges as source/target slug pairs."""
    vault_root = tmp_path / "vault"
    vault_root.mkdir()
    (vault_root / "home.md").write_text("[[about]]\n[[missing]]\n", encoding="utf-8")
    (vault_root / "about.md").write_text("", encoding="utf-8")

    vault_index = scan_vault(vault_root)
    edge_list = build_vault_slug_edge_list(vault_index)

    assert edge_list == [["home.md", "about.md"]]


def test_build_vault_slug_edge_list_deduplicates_edges(tmp_path: Path) -> None:
    """Collapse repeated links to a single edge pair."""
    vault_root = tmp_path / "vault"
    vault_root.mkdir()
    (vault_root / "home.md").write_text("[[about]]\n[[about]]\n[[about.md]]\n", encoding="utf-8")
    (vault_root / "about.md").write_text("", encoding="utf-8")

    vault_index = scan_vault(vault_root)
    edge_list = build_vault_slug_edge_list(vault_index)

    assert edge_list == [["home.md", "about.md"]]


def test_build_vault_slug_edge_list_skips_self_loop(tmp_path: Path) -> None:
    """Skip resolved self-loop edges from the output."""
    vault_root = tmp_path / "vault"
    vault_root.mkdir()
    (vault_root / "home.md").write_text("[[home]]\n", encoding="utf-8")

    vault_index = scan_vault(vault_root)
    edge_list = build_vault_slug_edge_list(vault_index)

    assert edge_list == []


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
