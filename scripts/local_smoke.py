#!/usr/bin/env python3
"""Local smoke test for DAIOF core imports."""

from __future__ import annotations

import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO_ROOT))

from digital_ai_organism_framework import DigitalGenome, DigitalOrganism


def main() -> None:
    genome = DigitalGenome()
    organism = DigitalOrganism(name="local_smoke_organism", genome=genome)
    organism.live_cycle(time_delta=1.0)
    print("OK")


if __name__ == "__main__":
    main()
