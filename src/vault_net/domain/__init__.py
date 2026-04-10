"""Domain layer: entities, ports, and pure services."""

from vault_net.domain.models import (
    VaultFile,
    VaultFileStats,
    VaultGraph,
    VaultGraphMetadata,
    VaultIndex,
    VaultIndexMetadata,
    VaultLink,
    VaultNote,
)
from vault_net.domain.protocols import GraphBuilder, VaultScanner
from vault_net.domain.services.registry import VaultRegistry

__all__ = [
    "GraphBuilder",
    "VaultFile",
    "VaultFileStats",
    "VaultGraph",
    "VaultGraphMetadata",
    "VaultIndex",
    "VaultIndexMetadata",
    "VaultLink",
    "VaultNote",
    "VaultRegistry",
    "VaultScanner",
]
