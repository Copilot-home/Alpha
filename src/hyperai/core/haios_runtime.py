#!/usr/bin/env python3
"""
HAIOS Runtime - Runtime Environment for Digital Organisms
========================================================

Creator: Nguyễn Đức Cường (alpha_prime_omega)
Original Creation: October 30, 2025
Verification: 4287
"""

import importlib
import sys
import warnings
from pathlib import Path

from hyperai.config import allow_stubs as _allow_stubs

# Add root directory to path to import from root-level modules
root_dir = Path(__file__).parent.parent.parent.parent
sys.path.insert(0, str(root_dir))


def _load_runtime_module():
    module_name = "haios_runtime"
    try:
        return importlib.import_module(module_name)
    except ImportError as exc:
        if getattr(exc, "name", None) == module_name:
            return None
        raise


_runtime_module = _load_runtime_module()
_runtime_impl = (
    getattr(_runtime_module, "HAIOSRuntime", None) if _runtime_module else None
)

if _runtime_impl:
    HAIOSRuntime = _runtime_impl
elif _allow_stubs():
    warnings.warn(
        "HAIOSRuntime implementation not found; using stub runtime. "
        "Ensure haios_runtime.py is available in the project root or "
        "packaged module.",
        RuntimeWarning,
    )

    class HAIOSRuntime:
        """Stub implementation of HAIOSRuntime."""

        def __init__(self):
            self.version = "1.0.0"
            self.creator = "alpha_prime_omega"

else:
    raise ModuleNotFoundError(
        "HAIOSRuntime implementation not found and stubs are disabled. "
        "Set HYPERAI_ALLOW_STUBS=1 to allow the fallback stub."
    )


__all__ = ["HAIOSRuntime"]
