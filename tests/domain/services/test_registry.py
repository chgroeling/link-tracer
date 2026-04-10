"""Domain service tests for registry lookup behavior."""

from __future__ import annotations

from pathlib import Path

from vault_net.domain.services.vault_registry import VaultRegistry
from vault_net.infrastructure.scanner.matterify_scanner import MatterifyVaultScanner


def test_vault_registry_provides_bidirectional_lookup(tmp_path: Path) -> None:
    """Registry resolves both slug->file and file->slug lookups."""
    vault_root = tmp_path / "vault"
    vault_root.mkdir()
    (vault_root / "home.md").write_text("", encoding="utf-8")

    scanner = MatterifyVaultScanner()
    vault_index = scanner.scan(vault_root)
    lookup = VaultRegistry(vault_index)
    home_note = vault_index.files[0]

    assert lookup.get_file(home_note.slug) == home_note
    assert lookup.get_slug(home_note) == home_note.slug
    assert lookup.get_file("missing") is None
    assert lookup.get_slug(home_note.to_file()) == home_note.slug
