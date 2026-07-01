"""Shared configuration helpers for HyperAI."""

from __future__ import annotations

import os


def allow_stubs() -> bool:
    """Return True when stub implementations are allowed."""
    value = os.getenv("HYPERAI_ALLOW_STUBS", "").strip().lower()
    return value in {"1", "true", "yes", "on"}
_TRUTHY_VALUES = {"1", "true", "yes", "on"}


def allow_stubs() -> bool:
    """Return True when stub implementations are allowed.

    `HYPERAI_ALLOW_STUBS` enables stubs only when set to one of
    {1, true, yes, on} (case-insensitive, surrounding whitespace ignored);
    any other value, or leaving it unset, disables them.
    """
    value = os.getenv("HYPERAI_ALLOW_STUBS", "").strip().lower()
    return value in _TRUTHY_VALUES
