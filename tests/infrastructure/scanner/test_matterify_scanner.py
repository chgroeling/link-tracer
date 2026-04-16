"""Infrastructure scanner adapter tests."""

from __future__ import annotations

from pathlib import Path
from unittest.mock import patch

from obsilink import Link, LinkType
from tests.fixtures import FakeFileEntry, FakeScanMetadata, FakeScanResults

from vault_net.domain.models import VaultIndex
from vault_net.infrastructure.scanner.matterify_scanner import MatterifyVaultScanner


def test_scanner_delegates_to_scan_directory() -> None:
    """Adapter calls scan_directory() and returns VaultIndex with note links."""
    vault_root = Path("/tmp/vault")  # noqa: S108
    fake_files = [FakeFileEntry(file_path="note.md")]
    fake_result = FakeScanResults(
        metadata=FakeScanMetadata(root=str(vault_root)),
        files=fake_files,
    )

    scanner = MatterifyVaultScanner()
    with patch(
        "vault_net.infrastructure.scanner.matterify_scanner.scan_directory",
        return_value=fake_result,
    ) as mock_scan:
        vault_index, note_links = scanner.index_files(vault_root)

    assert isinstance(vault_index, VaultIndex)
    assert vault_index.vault_root == vault_root
    assert len(vault_index.files) == 1
    callback = mock_scan.call_args.kwargs.get("callback")
    assert callable(callback)


def test_scanner_converts_custom_data_to_vault_links() -> None:
    """Adapter converts matterify custom_data links into VaultLink values."""
    vault_root = Path("/tmp/vault")  # noqa: S108
    fake_files = [
        FakeFileEntry(
            file_path="note.md",
            custom_data=[
                Link(
                    type=LinkType.WIKILINK,
                    target="other",
                    alias=None,
                    heading="Section",
                    blockid=None,
                ),
            ],
        ),
    ]
    fake_result = FakeScanResults(
        metadata=FakeScanMetadata(root=str(vault_root)),
        files=fake_files,
    )

    scanner = MatterifyVaultScanner()
    with patch(
        "vault_net.infrastructure.scanner.matterify_scanner.scan_directory",
        return_value=fake_result,
    ):
        vault_index, note_links = scanner.index_files(vault_root)

    note = vault_index.files[0]
    assert len(note_links[note.slug]) == 1
    link = note_links[note.slug][0]
    assert link.link_type == "wikilink"
    assert link.target == "other"
    assert link.heading == "Section"
