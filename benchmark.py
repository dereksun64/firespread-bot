"""Time paired trials: python3 benchmark.py --sizes 20 40 60 80."""

import argparse
import random
from time import perf_counter

from bots import bot1, bot2, bot3, bot4
from ship import generate_ship
from simulate import run_trial


def benchmark(sizes, trials, q_values, seed):
    print("size,bot,runs,total_seconds,mean_seconds,max_seconds,timeouts", flush=True)
    for size in sizes:
        randomizer = random.Random(seed)
        timings = {bot.__name__: [] for bot in (bot1, bot2, bot3, bot4)}
        timeouts = dict.fromkeys(timings, 0)
        for _ in range(trials):
            grid = generate_ship(size, seed=randomizer.getrandbits(64))
            fire_seed = randomizer.getrandbits(64)
            cells = [(r, c) for r, row in enumerate(grid) for c, opened in enumerate(row) if opened]
            start, button, fire_start = randomizer.sample(cells, 3)
            for q in q_values:
                for bot in (bot1, bot2, bot3, bot4):
                    began = perf_counter()
                    outcome, _ = run_trial(bot, grid, start, button, {fire_start}, q, fire_seed)
                    timings[bot.__name__].append(perf_counter() - began)
                    timeouts[bot.__name__] += outcome == "timeout"
        for bot, samples in timings.items():
            total = sum(samples)
            print(f"{size},{bot},{len(samples)},{total:.4f},"
                  f"{total / len(samples):.4f},{max(samples):.4f},{timeouts[bot]}", flush=True)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Measure complete trial runtime per bot.")
    parser.add_argument("--sizes", nargs="+", type=int, default=[20, 40, 60, 80])
    parser.add_argument("--trials", type=int, default=3)
    parser.add_argument("--q", nargs="+", type=float, default=[0, 0.1, 0.3, 0.6, 1])
    parser.add_argument("--seed", type=int, default=4)
    args = parser.parse_args()
    if any(size < 3 for size in args.sizes) or args.trials < 1:
        parser.error("sizes must be at least 3 and trials must be positive")
    if any(not 0 <= q <= 1 for q in args.q):
        parser.error("q must be between 0 and 1")
    benchmark(args.sizes, args.trials, args.q, args.seed)
