"""Infrastructure scanner adapter tests."""

from __future__ import annotations

from pathlib import Path
from unittest.mock import patch

from obsilink import Link, LinkType
from tests.fixtures import FakeFileEntry, FakeScanMetadata, FakeScanResults

from vault_net.consts import SLUG_LENGTH
from vault_net.domain.models import VaultIndex
from vault_net.infrastructure.scanner.matterify_scanner import MatterifyVaultScanner


def test_scanner_delegates_to_scan_directory() -> None:
    """Adapter calls scan_directory() and returns VaultIndex."""
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
        vault_index = scanner.scan(vault_root)

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
        vault_index = scanner.scan(vault_root)

    assert len(vault_index.files[0].links) == 1
    link = vault_index.files[0].links[0]
    assert link.link_type == "wikilink"
    assert link.target == "other"
    assert link.heading == "Section"


def test_scanner_slug_collision_with_reserved_name() -> None:
    """Third colliding filename skips already reserved _0 slug."""
    vault_root = Path("/tmp/vault")  # noqa: S108
    fake_files = [
        FakeFileEntry(file_path="folder1/longname.md"),
        FakeFileEntry(file_path="folder2/longname.txt"),
        FakeFileEntry(file_path="folder3/longname_0.md"),
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
        vault_index = scanner.scan(vault_root)

    slugs = {f.file_path: f.slug for f in vault_index.files}
    assert slugs["folder1/longname.md"] == "longname"
    assert slugs["folder2/longname.txt"] == "longna_0"
    assert slugs["folder3/longname_0.md"] == "longna_1"


def test_scanner_slug_max_length_constraint() -> None:
    """All generated slugs remain within configured max length."""
    vault_root = Path("/tmp/vault")  # noqa: S108
    fake_files = [
        FakeFileEntry(file_path="longname.md"),
        FakeFileEntry(file_path="longname.txt"),
        FakeFileEntry(file_path="abcdefghijk.md"),
        FakeFileEntry(file_path="abcdefghijk.txt"),
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
        vault_index = scanner.scan(vault_root)

    for file in vault_index.files:
        assert len(file.slug) <= SLUG_LENGTH, (
            f"Slug '{file.slug}' for {file.file_path} exceeds max length {SLUG_LENGTH}"
        )

    slugs = {f.file_path: f.slug for f in vault_index.files}
    assert slugs["longname.md"] == "longname"
    assert slugs["longname.txt"] == "longna_0"
    assert slugs["abcdefghijk.md"] == "abcdefgh"
    assert slugs["abcdefghijk.txt"] == "abcdef_0"


def test_scanner_slug_many_collisions() -> None:
    """Slug generation handles 10+ collisions correctly."""
    vault_root = Path("/tmp/vault")  # noqa: S108
    fake_files = [FakeFileEntry(file_path=f"folder{i}/filename{i}.txt") for i in range(12)]
    fake_result = FakeScanResults(
        metadata=FakeScanMetadata(root=str(vault_root)),
        files=fake_files,
    )

    scanner = MatterifyVaultScanner()
    with patch(
        "vault_net.infrastructure.scanner.matterify_scanner.scan_directory",
        return_value=fake_result,
    ):
        vault_index = scanner.scan(vault_root)

    slugs = [f.slug for f in vault_index.files]
    assert len(slugs) == len(set(slugs)), "All slugs must be unique"

    for slug in slugs:
        assert len(slug) <= SLUG_LENGTH, f"Slug '{slug}' exceeds max length {SLUG_LENGTH}"

    slugs_map = {f.file_path: f.slug for f in vault_index.files}
    assert slugs_map["folder0/filename0.txt"] == "filename"
    assert slugs_map["folder1/filename1.txt"] == "filena_0"
    assert slugs_map["folder9/filename9.txt"] == "filena_8"
    assert slugs_map["folder10/filename10.txt"] == "filena_9"
    assert slugs_map["folder11/filename11.txt"] == "filen_10"
