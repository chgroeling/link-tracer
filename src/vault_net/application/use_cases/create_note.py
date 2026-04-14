"""Use case for creating a new note in the vault."""

from __future__ import annotations

from typing import TYPE_CHECKING

import structlog

from vault_net.domain.services.slug_service import generate_slug

if TYPE_CHECKING:
    from pathlib import Path

logger = structlog.get_logger(__name__)


class CreateNoteUseCase:
    """Create a new markdown note in the vault and return its slug."""

    def execute(
        self,
        vault_root: Path,
        name: str,
        *,
        content: str = "",
    ) -> str:
        """Create a note file and return the generated slug.

        Args:
            vault_root: Root directory of the vault.
            name: Relative path for the note (e.g. ``"sub/dir/my-note"``).
                  A ``.md`` extension is appended automatically if missing.
            content: Optional text content to write into the note.

        Returns:
            The generated slug for the newly created note.

        Raises:
            FileExistsError: If a file already exists at the target path.
        """
        if not name.endswith(".md"):
            name = f"{name}.md"

        target = (vault_root / name).resolve()

        # Prevent path traversal outside the vault
        if not str(target).startswith(str(vault_root.resolve())):
            raise ValueError(f"Target path escapes vault root: {name}")

        logger.info("use_case.create_note.start", target=str(target))

        if target.exists():
            raise FileExistsError(f"Note already exists: {target}")

        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text(content, encoding="utf-8")

        stem = target.stem
        slug_counts: dict[str, int] = {}
        slug = generate_slug(stem, slug_counts)

        logger.info("use_case.create_note.done", slug=slug, path=str(target))
        return slug
