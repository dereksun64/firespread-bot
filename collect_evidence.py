"""Reproduce the fireproof-button evidence sweep and q=0.3 follow-up.

Run from the repository root: python3 -u collect_evidence.py
Checkpoints are saved after each batch; this command restarts the experiment.
"""

from pathlib import Path
from time import perf_counter

from simulate import run_experiments, save_results, plot_success_rates, success_rates


if __name__ == "__main__":
    output = Path("results/fireproof")
    began = perf_counter()
    results = []
    for batch in range(10):
        rows = run_experiments(60, [i / 10 for i in range(11)], 10, seed=600 + batch)
        for row in rows:
            row["trial"] += 10 * batch
        results.extend(rows)
        save_results(results, output / "sweep.csv")
        print(f"Full sweep: {10 * (batch + 1)}/100 ships; "
              f"{perf_counter() - began:.1f}s", flush=True)
    plot_success_rates(results, output / "sweep.png")
    focused = [row for row in results if row["q"] == 0.3]
    for batch in range(10):
        rows = run_experiments(60, [0.3], 20, seed=700 + batch)
        for row in rows:
            row["trial"] += 100 + 20 * batch
        focused.extend(rows)
        save_results(focused, output / "focused_q03.csv")
        print(f"Follow-up: {20 * (batch + 1)}/200 new ships; "
              f"{perf_counter() - began:.1f}s", flush=True)
    print("FINAL SUCCESS RATES", flush=True)
    for row in success_rates(results):
        print(row, flush=True)
    print("FOCUSED q=0.3", flush=True)
    for row in success_rates(focused):
        print(row, flush=True)
