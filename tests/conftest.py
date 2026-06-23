"""Pytest configuration for the DAIOF test suite."""

import os

# The packaged ``hyperai`` modules fall back to stub implementations when the
# optional root-level runtime/protocol impls are unavailable. Enable that
# fallback so the import-dependent tests can run without the real modules.
os.environ.setdefault("HYPERAI_ALLOW_STUBS", "1")
