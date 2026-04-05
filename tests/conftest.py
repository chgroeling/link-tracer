"""Pytest configuration and shared fixtures."""

from __future__ import annotations

import logging

import pytest
import structlog


@pytest.fixture(autouse=True)
def clean_vault_env(monkeypatch: pytest.MonkeyPatch) -> None:
    """Remove VAULT_ROOT from environment for test isolation."""
    monkeypatch.delenv("VAULT_ROOT", raising=False)


@pytest.fixture(autouse=True)
def disable_structlog() -> None:
    """Suppress structlog output so it doesn't pollute CLI JSON output."""
    structlog.configure(
        wrapper_class=structlog.make_filtering_bound_logger(logging.CRITICAL),
    )
