"""Shared fixtures and markers for the unified evaluation harness."""

from __future__ import annotations

import pytest


def pytest_configure(config: pytest.Config) -> None:
    config.addinivalue_line("markers", "ollama: tests that require a running Ollama server")


@pytest.fixture
def ollama_required() -> None:
    """Skip if Ollama should not be called."""
    import os

    if os.environ.get("OLLAMA_SKIP", "").lower() in {"1", "true", "yes"}:
        pytest.skip("OLLAMA_SKIP is set")
