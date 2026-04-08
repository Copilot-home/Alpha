#!/usr/bin/env python3
"""
HAIOS Runtime - Runtime Environment for Digital Organisms
========================================================

Creator: Nguyễn Đức Cường (alpha_prime_omega)
Original Creation: October 30, 2025
Verification: 4287
"""

import os
import sys
import warnings
from pathlib import Path
import importlib
import warnings


# Import from root-level implementation
def _allow_stubs() -> bool:
    return os.getenv("HYPERAI_ALLOW_STUBS") == "1"


try:
    from haios_runtime import HAIOSRuntime as HAIOSRuntimeImpl

    HAIOSRuntime = HAIOSRuntimeImpl
except ImportError as exc:
    if _allow_stubs():
        warnings.warn(
            "haios_runtime import failed; using stub HAIOSRuntime. "
            "Install project dependencies or set HYPERAI_ALLOW_STUBS=1 "
            "explicitly to acknowledge stub usage.",
            RuntimeWarning,
            stacklevel=2,
        )

        # If haios_runtime doesn't exist, provide a stub
        class HAIOSRuntime:
            """Stub implementation of HAIOSRuntime"""

            def __init__(self):
                self.version = "1.0.0"
                self.creator = "alpha_prime_omega"
    else:
        raise ImportError(
            "Missing haios_runtime dependency. Install the project dependencies "
            "or set HYPERAI_ALLOW_STUBS=1 to allow stub implementations."
        ) from exc
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
