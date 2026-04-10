"""Use case for scanning a vault into a domain index."""

from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from pathlib import Path

    from vault_net.domain.models import VaultIndex
    from vault_net.domain.protocols import VaultScanner


class ScanVaultUseCase:
    """Orchestrate vault scanning through the scanner port."""

    def __init__(self, scanner: VaultScanner) -> None:
        self._scanner = scanner

    def execute(
        self,
        vault_root: Path,
        *,
        extra_exclude_dir: tuple[str, ...] = (),
        no_default_excludes: bool = False,
    ) -> VaultIndex:
        """Scan the vault and return the resulting index."""
        return self._scanner.scan(
            vault_root,
            extra_exclude_dir=extra_exclude_dir,
            no_default_excludes=no_default_excludes,
        )
