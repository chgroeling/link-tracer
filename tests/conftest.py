"""Pytest configuration and shared fixtures."""

import pytest


@pytest.fixture(autouse=True)
def clean_vault_env(monkeypatch: pytest.MonkeyPatch) -> None:
    """Remove VAULT_DIR from environment for test isolation."""
    monkeypatch.delenv("VAULT_DIR", raising=False)
