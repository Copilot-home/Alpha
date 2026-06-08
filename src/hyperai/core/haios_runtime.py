#!/usr/bin/env python3
"""
HAIOS Runtime - Runtime Environment for Digital Organisms
========================================================

Creator: Nguyễn Đức Cường (alpha_prime_omega)
Original Creation: October 30, 2025
Verification: 4287
"""

# Import from package implementation
import importlib
import warnings


def _load_runtime_module():
    try:
        return importlib.import_module("haios_runtime")
    except ModuleNotFoundError:
        return None


_runtime_module = _load_runtime_module()
_runtime_impl = (
    getattr(_runtime_module, "HAIOSRuntime", None) if _runtime_module else None
)

if _runtime_impl:
    HAIOSRuntime = _runtime_impl
else:
    warnings.warn(
        "HAIOSRuntime implementation not found; using stub runtime. "
        "Ensure haios_runtime.py is available in the project root or packaged module.",
        RuntimeWarning,
    )

    class HAIOSRuntime:
        """Stub implementation of HAIOSRuntime"""

        def __init__(self):
            self.version = "1.0.0"
            self.creator = "alpha_prime_omega"


__all__ = ["HAIOSRuntime"]
