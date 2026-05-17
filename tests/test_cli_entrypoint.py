#!/usr/bin/env python3
"""Tests for hyperai CLI entrypoint."""

import io
import unittest
from contextlib import redirect_stdout

from hyperai.cli import main


class TestHyperAICLI(unittest.TestCase):
    def test_info_flag_prints_framework_info(self):
        stream = io.StringIO()
        with redirect_stdout(stream):
            exit_code = main(["--info"])

        output = stream.getvalue()
        self.assertEqual(exit_code, 0)
        self.assertIn("HYPERAI Framework (DAIOF)", output)

    def test_no_args_shows_help(self):
        stream = io.StringIO()
        with redirect_stdout(stream):
            exit_code = main([])

        output = stream.getvalue()
        self.assertEqual(exit_code, 0)
        self.assertIn("usage: hyperai", output)


if __name__ == "__main__":
    unittest.main()
