"""Shared configuration helpers for HyperAI."""

from __future__ import annotations

import os


_TRUTHY_VALUES = {"1", "true", "t", "yes", "y", "on"}
_FALSY_VALUES = {"0", "false", "f", "no", "n", "off"}


def allow_stubs() -> bool:
    """Return whether stub implementations are allowed.

    `HYPERAI_ALLOW_STUBS` controls behavior:
    - unset/empty => True (backward-compatible default)
    - truthy values => True
    - falsy values => False
    """

    value = os.getenv("HYPERAI_ALLOW_STUBS")
    if value is None or not value.strip():
        return True

    normalized = value.strip().lower()
    if normalized in _TRUTHY_VALUES:
        return True
    if normalized in _FALSY_VALUES:
        return False

    return True
