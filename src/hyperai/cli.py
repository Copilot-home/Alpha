"""Command-line interface for the HYPERAI framework."""

from __future__ import annotations

import argparse

from . import __version__


def main() -> int:
    """Entry point for the `hyperai` CLI."""
    parser = argparse.ArgumentParser(
        prog="hyperai",
        description="HYPERAI framework command-line interface.",
    )
    parser.add_argument(
        "--version",
        action="store_true",
        help="Show the HYPERAI version and exit.",
    )
    args = parser.parse_args()

    if args.version:
        print(__version__)
        return 0

    parser.print_help()
    return 0


__all__ = ["main"]
