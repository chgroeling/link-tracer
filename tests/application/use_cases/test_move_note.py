"""Tests for MoveNoteUseCase."""

from __future__ import annotations

from pathlib import Path
from unittest.mock import MagicMock

import pytest

from vault_net.application.use_cases.move_note import MoveNoteUseCase, MoveResult
from vault_net.domain.models import (
    VaultFileStats,
    VaultGraph,
    VaultGraphMetadata,
    VaultIndex,
    VaultIndexMetadata,
    VaultNote,
)


def _make_note(slug: str, file_path: str) -> VaultNote:
    return VaultNote(
        slug=slug,
        file_path=file_path,
        status="ok",
        error=None,
        file_hash="abc123",
        frontmatter=None,
        stats=VaultFileStats(file_size=100, modified_time=None, access_time=None),
    )


def _make_index(vault_root: Path, notes: list[VaultNote]) -> VaultIndex:
    return VaultIndex(
        vault_root=vault_root,
        metadata=VaultIndexMetadata(
            root=str(vault_root),
            total_files=len(notes),
            files_with_frontmatter=0,
            files_without_frontmatter=len(notes),
            errors=0,
            scan_duration_seconds=0.0,
            avg_duration_per_file_ms=0.0,
            throughput_files_per_second=0.0,
        ),
        files=notes,
    )


def _make_use_case(
    vault_root: Path,
    notes: list[VaultNote],
    note_links: dict[str, list[object]] | None = None,
    predecessor_map: dict[str, list[str]] | None = None,
) -> MoveNoteUseCase:
    index = _make_index(vault_root, notes)
    scanner = MagicMock()
    scanner.index_files.return_value = (index, note_links or {})

    digraph = MagicMock()
    digraph.predecessors.side_effect = lambda slug: (predecessor_map or {}).get(slug, [])

    graph = VaultGraph(
        vault_root=vault_root,
        metadata=VaultGraphMetadata(edge_count=0),
        digraph=digraph,
    )

    graph_builder = MagicMock()
    graph_builder.build_full_graph.return_value = graph

    return MoveNoteUseCase(scanner=scanner, graph_builder=graph_builder)


class TestMoveNoteUseCase:
    """Verify MoveNoteUseCase behavior."""

    def test_moves_note_to_new_path(self, tmp_path: Path) -> None:
        """Move a note file to a new location."""
        note_file = tmp_path / "hello.md"
        note_file.write_text("# Hello", encoding="utf-8")
        note = _make_note("HELLO__", "hello.md")

        use_case = _make_use_case(tmp_path, [note])
        result = use_case.execute(tmp_path, "HELLO__", "world.md")

        assert result.old_path == "hello.md"
        assert result.new_path == "world.md"
        assert not note_file.exists()
        assert (tmp_path / "world.md").exists()
        assert (tmp_path / "world.md").read_text(encoding="utf-8") == "# Hello"

    def test_appends_md_extension(self, tmp_path: Path) -> None:
        """Append .md when the destination omits it."""
        note_file = tmp_path / "hello.md"
        note_file.write_text("content", encoding="utf-8")
        note = _make_note("HELLO__", "hello.md")

        use_case = _make_use_case(tmp_path, [note])
        result = use_case.execute(tmp_path, "HELLO__", "world")

        assert result.new_path == "world.md"
        assert (tmp_path / "world.md").exists()

    def test_moves_to_subdirectory(self, tmp_path: Path) -> None:
        """Move a note into a new subdirectory."""
        note_file = tmp_path / "hello.md"
        note_file.write_text("content", encoding="utf-8")
        note = _make_note("HELLO__", "hello.md")

        use_case = _make_use_case(tmp_path, [note])
        result = use_case.execute(tmp_path, "HELLO__", "sub/dir/hello")

        assert result.new_path == "sub/dir/hello.md"
        assert not note_file.exists()
        assert (tmp_path / "sub" / "dir" / "hello.md").exists()

    def test_raises_key_error_for_unknown_slug(self, tmp_path: Path) -> None:
        """Raise KeyError when the slug cannot be resolved."""
        use_case = _make_use_case(tmp_path, [])

        with pytest.raises(KeyError):
            use_case.execute(tmp_path, "NONEXISTENT", "dest")

    def test_raises_file_not_found_when_source_missing(self, tmp_path: Path) -> None:
        """Raise FileNotFoundError when the source file doesn't exist on disk."""
        note = _make_note("GONE__", "gone.md")
        use_case = _make_use_case(tmp_path, [note])

        with pytest.raises(FileNotFoundError, match="does not exist"):
            use_case.execute(tmp_path, "GONE__", "dest")

    def test_raises_file_exists_when_destination_exists(self, tmp_path: Path) -> None:
        """Raise FileExistsError when the destination already exists."""
        (tmp_path / "src.md").write_text("source", encoding="utf-8")
        (tmp_path / "dest.md").write_text("existing", encoding="utf-8")
        note = _make_note("SRC__", "src.md")

        use_case = _make_use_case(tmp_path, [note])

        with pytest.raises(FileExistsError, match="already exists"):
            use_case.execute(tmp_path, "SRC__", "dest.md")

    def test_raises_value_error_on_path_traversal(self, tmp_path: Path) -> None:
        """Reject destinations that escape the vault root."""
        (tmp_path / "note.md").write_text("content", encoding="utf-8")
        note = _make_note("NOTE__", "note.md")

        use_case = _make_use_case(tmp_path, [note])

        with pytest.raises(ValueError, match="escapes vault root"):
            use_case.execute(tmp_path, "NOTE__", "../../etc/passwd")

    def test_updates_backlinks_in_referring_files(self, tmp_path: Path) -> None:
        """Rewrite wikilinks in files that reference the moved note."""
        source = tmp_path / "old-name.md"
        source.write_text("# Old Name", encoding="utf-8")

        referrer = tmp_path / "referrer.md"
        referrer.write_text("See [[old-name]] for details.", encoding="utf-8")

        source_note = _make_note("OLD_NAME_", "old-name.md")
        referrer_note = _make_note("REFERRER_", "referrer.md")

        use_case = _make_use_case(
            tmp_path,
            [source_note, referrer_note],
            predecessor_map={"OLD_NAME_": ["REFERRER_"]},
        )
        result = use_case.execute(tmp_path, "OLD_NAME_", "new-name")

        assert result.old_path == "old-name.md"
        assert result.new_path == "new-name.md"
        assert result.updated_files == ["referrer.md"]

        updated_content = referrer.read_text(encoding="utf-8")
        assert "[[new-name]]" in updated_content
        assert "[[old-name]]" not in updated_content

    def test_updates_multiple_backlinks(self, tmp_path: Path) -> None:
        """Rewrite backlinks across multiple referring files."""
        source = tmp_path / "target.md"
        source.write_text("# Target", encoding="utf-8")

        ref_a = tmp_path / "ref-a.md"
        ref_a.write_text("Link to [[target]] here.", encoding="utf-8")

        ref_b = tmp_path / "ref-b.md"
        ref_b.write_text("Also see [[target]].", encoding="utf-8")

        source_note = _make_note("TARGET_", "target.md")
        ref_a_note = _make_note("REF_A_", "ref-a.md")
        ref_b_note = _make_note("REF_B_", "ref-b.md")

        use_case = _make_use_case(
            tmp_path,
            [source_note, ref_a_note, ref_b_note],
            predecessor_map={"TARGET_": ["REF_A_", "REF_B_"]},
        )
        result = use_case.execute(tmp_path, "TARGET_", "moved/new-target")

        assert len(result.updated_files) == 2
        assert "[[new-target]]" in ref_a.read_text(encoding="utf-8")
        assert "[[new-target]]" in ref_b.read_text(encoding="utf-8")

    def test_preserves_link_heading_and_alias(self, tmp_path: Path) -> None:
        """Preserve heading fragments and aliases during backlink rewrite."""
        source = tmp_path / "note.md"
        source.write_text("# Note", encoding="utf-8")

        referrer = tmp_path / "referrer.md"
        referrer.write_text(
            "See [[note#section]] and [[note|my alias]].",
            encoding="utf-8",
        )

        source_note = _make_note("NOTE_", "note.md")
        referrer_note = _make_note("REFERRER_", "referrer.md")

        use_case = _make_use_case(
            tmp_path,
            [source_note, referrer_note],
            predecessor_map={"NOTE_": ["REFERRER_"]},
        )
        result = use_case.execute(tmp_path, "NOTE_", "renamed")

        updated = referrer.read_text(encoding="utf-8")
        assert "[[renamed#section]]" in updated
        assert "[[renamed|my alias]]" in updated
        assert result.updated_files == ["referrer.md"]

    def test_no_backlinks_returns_empty_updated_files(self, tmp_path: Path) -> None:
        """No updated files when there are no backlinks."""
        source = tmp_path / "lonely.md"
        source.write_text("content", encoding="utf-8")
        note = _make_note("LONELY_", "lonely.md")

        use_case = _make_use_case(tmp_path, [note], predecessor_map={})
        result = use_case.execute(tmp_path, "LONELY_", "new-lonely")

        assert result.updated_files == []
        assert (tmp_path / "new-lonely.md").exists()

    def test_returns_move_result(self, tmp_path: Path) -> None:
        """Return a MoveResult dataclass with correct fields."""
        (tmp_path / "a.md").write_text("content", encoding="utf-8")
        note = _make_note("A_", "a.md")

        use_case = _make_use_case(tmp_path, [note])
        result = use_case.execute(tmp_path, "A_", "b")

        assert isinstance(result, MoveResult)
        assert result.old_path == "a.md"
        assert result.new_path == "b.md"
        assert isinstance(result.updated_files, list)
