#!/usr/bin/env python3
"""
Digital Organism - Complete Self-Sustaining Entity
=================================================

Creator: Nguyễn Đức Cường (alpha_prime_omega)
Original Creation: October 30, 2025
Verification: 4287
"""

# Import from package implementation
from ..digital_ai_organism_framework import DigitalOrganism
import importlib
import warnings


def _load_framework_module():
    try:
        return importlib.import_module("digital_ai_organism_framework")
    except ModuleNotFoundError:
        return None


_framework_module = _load_framework_module()
_organism_impl = (
    getattr(_framework_module, "DigitalOrganism", None) if _framework_module else None
)

if _organism_impl:
    DigitalOrganism = _organism_impl
else:
    warnings.warn(
        "DigitalOrganism implementation not found; using stub organism. "
        "Ensure digital_ai_organism_framework.py is available in the project root or packaged module.",
        RuntimeWarning,
    )

    class DigitalOrganism:
        """Stub implementation of DigitalOrganism."""

        def __init__(self):
            self.creator = "alpha_prime_omega"
            self.verification = 4287


__all__ = ["DigitalOrganism"]
