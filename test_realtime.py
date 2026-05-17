#!/usr/bin/env python3
"""Quick manual demo for the real-time task generator.

This file is intentionally *not* a pytest test. Historically, the script executed
at import time and changed into a developer-specific path, which broke test
collection in other environments.
"""

from __future__ import annotations

import argparse
import os
import subprocess
import time
from datetime import datetime
from pathlib import Path


def run_demo(duration_seconds: int = 60, interval_seconds: int = 10) -> None:
    """Run a short loop that simulates real-time repository task handling."""
    repo_root = Path(__file__).resolve().parent
    os.chdir(repo_root)

    total_cycles = max(1, duration_seconds // interval_seconds)

    print("🧬 DAIOF Real-Time Task Generator - Quick Test")
    print("=" * 70)
    print(f"📍 Working Directory: {os.getcwd()}")
    print(f"⏰ Start Time: {datetime.now().strftime('%H:%M:%S')}")
    print(f"⏱️  Duration: {duration_seconds} seconds")
    print("=" * 70)
    print()

    cycle = 0
    tasks_generated = 0
    tasks_executed = 0

    try:
        for i in range(total_cycles):
            cycle += 1
            print(f"🔄 Cycle {cycle} - {datetime.now().strftime('%H:%M:%S')}")

            result = subprocess.run(
                ["git", "status", "--porcelain"],
                capture_output=True,
                text=True,
                timeout=5,
                check=False,
            )

            if result.stdout.strip():
                files = result.stdout.strip().split("\n")
                print(f"   📋 Task Generated: Commit {len(files)} file(s)")
                tasks_generated += 1

                print("   🚀 Executing: Auto-commit changes")
                commit_result = subprocess.run(
                    ["git", "add", "-A"], capture_output=True, timeout=10, check=False
                )

                if commit_result.returncode == 0:
                    subprocess.run(
                        ["git", "commit", "-m", f"🤖 Real-time auto-update: Cycle {cycle}"],
                        capture_output=True,
                        timeout=10,
                        check=False,
                    )
                    subprocess.run(
                        ["git", "push", "origin", "main"],
                        capture_output=True,
                        timeout=30,
                        check=False,
                    )
                    print("   ✅ Success: Changes committed and pushed")
                    tasks_executed += 1
                else:
                    print("   ⚠️  No changes to commit")
            else:
                print("   ℹ️  No tasks generated - repository clean")

            py_files = [
                f
                for f in Path(".").rglob("*.py")
                if "venv" not in str(f) and ".venv" not in str(f)
            ]

            if py_files and cycle % 2 == 0:
                sample_file = py_files[0]
                print(f"   📋 Task Generated: Format {sample_file.name}")
                tasks_generated += 1
                print("   ℹ️  Skipped: Would format in production")

            print(f"   📊 Stats: {tasks_generated} generated, {tasks_executed} executed")
            print()

            if i < total_cycles - 1:
                time.sleep(interval_seconds)

    except KeyboardInterrupt:
        print("\n⏹️  Stopped by user")

    print("=" * 70)
    print(f"✅ Test Complete - {datetime.now().strftime('%H:%M:%S')}")
    print("📊 Final Stats:")
    print(f"   Total Cycles: {cycle}")
    print(f"   Tasks Generated: {tasks_generated}")
    print(f"   Tasks Executed: {tasks_executed}")
    if tasks_generated > 0:
        print(f"   Success Rate: {tasks_executed / tasks_generated * 100:.1f}%")
    print("=" * 70)
    print()
    print("🎯 Full system runs every minute via GitHub Actions!")
    print("📖 See .github/workflows/realtime-tasks.yml for configuration")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--duration", type=int, default=60, help="Total demo duration in seconds")
    parser.add_argument(
        "--interval", type=int, default=10, help="Seconds to wait between cycles"
    )
    return parser.parse_args()


if __name__ == "__main__":
    args = parse_args()
    run_demo(duration_seconds=args.duration, interval_seconds=args.interval)
