"""Tests for resolve_note_input."""

from __future__ import annotations

from pathlib import Path
from unittest.mock import MagicMock

import pytest

from vault_net.domain.models import InputError, VaultIndex, VaultNote
from vault_net.domain.services.resolve_note_input import (
    _looks_like_path,
    _resolve_file_path,
    _resolve_slug,
    resolve_note_input,
)


class TestLooksLikePath:
    """Test path detection heuristic."""

    def test_true_for_path_with_forward_slash(self) -> None:
        assert _looks_like_path("docs/my-note.md") is True

    def test_true_for_path_with_backslash_on_windows(self) -> None:
        import os

        if os.sep == "\\":
            assert _looks_like_path("docs\\my-note.md") is True
        else:
            pytest.skip("Backslash path only relevant on Windows")

    def test_true_for_relative_path_starting_with_dot(self) -> None:
        assert _looks_like_path("./my-note.md") is True
        assert _looks_like_path("../my-note.md") is True

    def test_false_for_simple_slug(self) -> None:
        assert _looks_like_path("my-note") is False
        assert _looks_like_path("test-slug-123") is False


class TestResolveSlug:
    """Test slug resolution."""

    def test_returns_slug_for_known_slug(self) -> None:
        mock_note = MagicMock(spec=VaultNote)
        mock_note.slug = "test-slug"
        mock_vault_index = MagicMock(spec=VaultIndex)
        mock_vault_index.files = [mock_note]

        result = _resolve_slug("test-slug", mock_vault_index)

        assert result == "test-slug"

    def test_raises_key_error_for_unknown_slug(self) -> None:
        mock_vault_index = MagicMock(spec=VaultIndex)
        mock_vault_index.files = []

        with pytest.raises(KeyError, match="unknown-slug"):
            _resolve_slug("unknown-slug", mock_vault_index)


class TestResolveFilePath:
    """Test file path resolution."""

    def test_raises_error_for_non_markdown_file(self, tmp_path: Path) -> None:
        mock_vault_index = MagicMock(spec=VaultIndex)
        mock_vault_index.files = []

        with pytest.raises(InputError, match="not a valid note"):
            _resolve_file_path("docs/my-note.txt", tmp_path, mock_vault_index)

    def test_raises_error_for_file_outside_vault(self, tmp_path: Path) -> None:
        mock_vault_index = MagicMock(spec=VaultIndex)
        mock_vault_index.files = []
        outside_dir = tmp_path / "outside"
        outside_dir.mkdir()
        outside_file = outside_dir / "note.md"
        outside_file.write_text("# Outside")
        vault_root = tmp_path / "vault"
        vault_root.mkdir()

        with pytest.raises(InputError, match="not inside the vault"):
            _resolve_file_path(str(outside_file), vault_root, mock_vault_index)

    def test_raises_error_for_nonexistent_file(self, tmp_path: Path) -> None:
        mock_vault_index = MagicMock(spec=VaultIndex)
        mock_vault_index.files = []

        with pytest.raises(InputError, match="does not exist"):
            _resolve_file_path("nonexistent.md", tmp_path, mock_vault_index)

    def test_resolves_relative_path_against_vault_root(self, tmp_path: Path) -> None:
        vault_root = tmp_path / "vault"
        vault_root.mkdir()
        note_file = vault_root / "my-note.md"
        note_file.write_text("# Test")

        mock_note = MagicMock(spec=VaultNote)
        mock_note.slug = "my-note"
        mock_note.file_path = str(note_file)
        mock_vault_index = MagicMock(spec=VaultIndex)
        mock_vault_index.files = [mock_note]

        result = _resolve_file_path("my-note.md", vault_root, mock_vault_index)

        assert result == "my-note"

    def test_resolves_nested_relative_path(self, tmp_path: Path) -> None:
        vault_root = tmp_path / "vault"
        vault_root.mkdir()
        docs_dir = vault_root / "docs"
        docs_dir.mkdir()
        note_file = docs_dir / "my-note.md"
        note_file.write_text("# Test")

        mock_note = MagicMock(spec=VaultNote)
        mock_note.slug = "my-note"
        mock_note.file_path = str(note_file)
        mock_vault_index = MagicMock(spec=VaultIndex)
        mock_vault_index.files = [mock_note]

        result = _resolve_file_path("docs/my-note.md", vault_root, mock_vault_index)

        assert result == "my-note"


class TestResolveNoteInput:
    """Test the main resolve_note_input function."""

    def test_delegates_to_resolve_slug_for_simple_input(self, tmp_path: Path) -> None:
        mock_note = MagicMock(spec=VaultNote)
        mock_note.slug = "test-slug"
        mock_vault_index = MagicMock(spec=VaultIndex)
        mock_vault_index.files = [mock_note]

        result = resolve_note_input("test-slug", tmp_path, mock_vault_index)

        assert result == "test-slug"

    def test_delegates_to_resolve_file_path_for_path_input(self, tmp_path: Path) -> None:
        vault_root = tmp_path / "vault"
        vault_root.mkdir()
        note_file = vault_root / "my-note.md"
        note_file.write_text("# Test")

        mock_note = MagicMock(spec=VaultNote)
        mock_note.slug = "my-note"
        mock_note.file_path = str(note_file)
        mock_vault_index = MagicMock(spec=VaultIndex)
        mock_vault_index.files = [mock_note]

        result = resolve_note_input("./my-note.md", vault_root, mock_vault_index)

        assert result == "my-note"

    def test_raises_key_error_for_unknown_slug(self, tmp_path: Path) -> None:
        mock_vault_index = MagicMock(spec=VaultIndex)
        mock_vault_index.files = []

        with pytest.raises(KeyError):
            resolve_note_input("unknown-slug", tmp_path, mock_vault_index)

    def test_raises_input_error_for_invalid_file(self, tmp_path: Path) -> None:
        mock_vault_index = MagicMock(spec=VaultIndex)
        mock_vault_index.files = []

        with pytest.raises(InputError, match="does not exist"):
            resolve_note_input("./nonexistent.md", tmp_path, mock_vault_index)
