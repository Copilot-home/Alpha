"""Shared configuration helpers for HyperAI."""

from __future__ import annotations

import os


_TRUTHY_VALUES = {"1", "true", "t", "yes", "y", "on"}


def allow_stubs() -> bool:
    """Return whether stub implementations are allowed.

    Controlled by the ``HYPERAI_ALLOW_STUBS`` environment variable.
    """

    value = os.getenv("HYPERAI_ALLOW_STUBS", "").strip().lower()
    return value in _TRUTHY_VALUES
