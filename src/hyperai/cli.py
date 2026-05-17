"""
Command-line interface for the HYPERAI Framework.
"""

from __future__ import annotations

import argparse
from importlib import metadata


def _get_version() -> str:
    try:
        return metadata.version("hyperai-framework")
    except metadata.PackageNotFoundError:
        return "0.0.0"


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        prog="hyperai",
        description="HYPERAI Framework command-line interface.",
    )
    parser.add_argument(
        "--version",
        action="version",
        version=f"hyperai {_get_version()}",
    )
    parser.add_argument(
        "--info",
        action="store_true",
        help="Show basic framework information.",
    )
    args = parser.parse_args(argv)

    if args.info:
        print("HYPERAI Framework (DAIOF)")
        print("A framework for creating self-evolving, self-maintaining AI entities.")
        return 0

    parser.print_help()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
