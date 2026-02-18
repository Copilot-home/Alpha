"""Shared configuration helpers for HyperAI."""

from __future__ import annotations

import os


def allow_stubs() -> bool:
    """Return True when stub implementations are allowed."""
    value = os.getenv("HYPERAI_ALLOW_STUBS", "").strip().lower()
    return value in {"1", "true", "yes", "on"}
