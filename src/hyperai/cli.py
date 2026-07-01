"""Command-line interface for the HYPERAI framework."""

from __future__ import annotations

import argparse

from . import __version__


def main(argv: list[str] | None = None) -> int:
    """Entry point for the `hyperai` CLI."""
    parser = argparse.ArgumentParser(
        prog="hyperai",
        description="HYPERAI Framework command-line interface.",
    )
    parser.add_argument(
        "--version",
        action="version",
        version=f"hyperai {__version__}",
    )
    parser.add_argument(
        "--info",
        action="store_true",
        help="Show basic framework information.",
    )
    args = parser.parse_args(argv)

    if args.info:
        print("HYPERAI Framework (DAIOF)")
        print(
            "A framework for creating self-evolving, " "self-maintaining AI entities."
        )
        return 0

    parser.print_help()
    return 0


__all__ = ["main"]

if __name__ == "__main__":
    raise SystemExit(main())
