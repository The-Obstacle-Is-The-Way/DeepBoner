"""Benchmark Advanced mode with different max_rounds settings."""

import asyncio
import os
import time

from src.orchestrators.advanced import AdvancedOrchestrator


async def benchmark(max_rounds: int) -> float:
    """Run benchmark with specified rounds, return elapsed time."""
    os.environ["ADVANCED_MAX_ROUNDS"] = str(max_rounds)

    orch = AdvancedOrchestrator()
    start = time.time()

    print(f"\nStarting benchmark with max_rounds={max_rounds}...")

    try:
        async for event in orch.run("sildenafil erectile dysfunction mechanism"):
            if event.type == "progress":
                print(f"  Progress: {event.message}")
            elif event.type == "complete":
                print("  Complete!")
                break
            elif event.type == "error":
                print(f"  Error: {event.message}")
                break
    except Exception as e:
        print(f"  Exception: {e}")

    return time.time() - start


async def main() -> None:
    """Run benchmarks for different configurations."""
    # Only run a quick test for 3 rounds to verify it works
    rounds = 3
    elapsed = await benchmark(rounds)
    print(f"max_rounds={rounds}: {elapsed:.1f}s ({elapsed / 60:.1f}min)")


if __name__ == "__main__":
    asyncio.run(main())
