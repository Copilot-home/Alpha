#!/usr/bin/env python3
"""Tests for hyperai shared configuration helpers."""

import importlib.util
import os
import unittest
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
CONFIG_MODULE_PATH = PROJECT_ROOT / "src" / "hyperai" / "config.py"

spec = importlib.util.spec_from_file_location("hyperai_config", CONFIG_MODULE_PATH)
config_module = importlib.util.module_from_spec(spec)
assert spec is not None and spec.loader is not None
spec.loader.exec_module(config_module)
allow_stubs = config_module.allow_stubs


class TestAllowStubs(unittest.TestCase):
    """Validate HYPERAI_ALLOW_STUBS parsing behavior."""

    def setUp(self):
        self._original = os.environ.get("HYPERAI_ALLOW_STUBS")

    def tearDown(self):
        if self._original is None:
            os.environ.pop("HYPERAI_ALLOW_STUBS", None)
        else:
            os.environ["HYPERAI_ALLOW_STUBS"] = self._original

    def test_truthy_values(self):
        for value in ("1", "true", "TRUE", " yes ", "On"):
            with self.subTest(value=value):
                os.environ["HYPERAI_ALLOW_STUBS"] = value
                self.assertTrue(allow_stubs())

    def test_falsy_values(self):
        for value in ("0", "false", "off", "no", "random", " false ", " NO ", " Off "):
            with self.subTest(value=value):
                os.environ["HYPERAI_ALLOW_STUBS"] = value
                self.assertFalse(allow_stubs())

    def test_missing_env_var_defaults_false(self):
        os.environ.pop("HYPERAI_ALLOW_STUBS", None)
        self.assertFalse(allow_stubs())


if __name__ == "__main__":
    unittest.main()
