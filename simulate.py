"""Run one bot against the ship's fire, one turn at a time."""

import random
import csv
from collections import defaultdict
from pathlib import Path

from fire import spread_fire
from ship import generate_ship


def run_trial(bot_fn, grid, start, button, fire0, q, seed, max_steps=5000, history=None):
    """Return (success/burned/timeout, turns elapsed).

    The grid is shared read-only; bot memory and fire are fresh for each trial.
    A timeout is a simulation cutoff, not proof that escape is impossible.
    """
    if not 0 <= q <= 1:
        raise ValueError("q must be between 0 and 1")
    if max_steps < 0:
        raise ValueError("max_steps must be nonnegative")

    randomizer = random.Random(seed)
    position, fire, state = start, set(fire0), {}
    if position in fire:
        return "burned", 0
    if position == button:
        return "success", 0

    for step in range(1, max_steps + 1):
        previous = position
        position = bot_fn(grid, position, button, fire, q, state)
        if history is not None:
            history.append(dict(step=step, previous=previous, position=position,
                                fire_before=sorted(fire), fire_after=sorted(fire)))
        if position in fire:
            return "burned", step
        if position == button:
            return "success", step
        fire = spread_fire(grid, fire, q, randomizer, button=button)
        if history is not None:
            history[-1]["fire_after"] = sorted(fire)
        if position in fire:
            return "burned", step
    return "timeout", max_steps


def run_experiments(size, q_values, trials, seed=0, max_steps=5000):
    """Return one result dict per bot, q, and trial, using paired scenarios.

    Each trial uses the same ship, positions, and fire seed across bots and q.
    Each run still gets fresh bot state and its own fire random generator.
    """
    from bots import bot1, bot2, bot3, bot4

    q_values = tuple(q_values)
    if size < 3 or trials < 1 or max_steps < 1:
        raise ValueError("size must be at least 3; trials and max_steps must be positive")
    if not q_values or any(not 0 <= q <= 1 for q in q_values):
        raise ValueError("provide q values between 0 and 1")

    randomizer, results = random.Random(seed), []
    for trial in range(trials):
        ship_seed = randomizer.getrandbits(64)
        fire_seed = randomizer.getrandbits(64)
        grid = generate_ship(size, seed=ship_seed)
        cells = [(r, c) for r, row in enumerate(grid) for c, opened in enumerate(row) if opened]
        start, button, fire_start = randomizer.sample(cells, 3)
        for q in q_values:
            for bot_fn in (bot1, bot2, bot3, bot4):
                outcome, steps = run_trial(
                    bot_fn, grid, start, button, {fire_start}, q, fire_seed, max_steps
                )
                results.append(dict(trial=trial, size=size, q=q, bot=bot_fn.__name__,
                                    outcome=outcome, steps=steps, ship_seed=ship_seed,
                                    fire_seed=fire_seed, start=start, button=button,
                                    fire_start=fire_start, rules="fireproof_button_v1",
                                    max_steps=max_steps))
    return results


def success_rates(results):
    """Summarize successes / all trials; timeouts remain in the denominator."""
    groups = defaultdict(list)
    for result in results:
        groups[(result["size"], result["q"], result["bot"])].append(result["outcome"])
    return [dict(size=size, q=q, bot=bot, trials=len(outcomes),
                 successes=outcomes.count("success"), timeouts=outcomes.count("timeout"),
                 success_rate=outcomes.count("success") / len(outcomes))
            for (size, q, bot), outcomes in sorted(groups.items())]


def save_results(results, path):
    """Save raw trials, including seeds and positions for replay."""
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="") as stream:
        writer = csv.DictWriter(stream, fieldnames=list(results[0]))
        writer.writeheader()
        writer.writerows(results)


def plot_success_rates(results, path):
    """Write a static graph; separate lines for each bot and grid size."""
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt

    summary = success_rates(results)
    fig, ax = plt.subplots(figsize=(8, 5))
    for size, bot in sorted({(row["size"], row["bot"]) for row in summary}):
        rows = [row for row in summary if row["size"] == size and row["bot"] == bot]
        ax.plot([row["q"] for row in rows], [row["success_rate"] for row in rows],
                marker="o", label=f"{bot} (D={size})")
    ax.set(xlabel="Flammability q", ylabel="Success rate", xlim=(0, 1), ylim=(0, 1.05),
           title="Bot success rates across flammability values")
    ax.text(0, -0.19, "Successes / all trials; timeouts count as unsuccessful. "
            f"Trials per point: {min(row['trials'] for row in summary)}–"
            f"{max(row['trials'] for row in summary)}.",
            transform=ax.transAxes, fontsize=8)
    ax.grid(alpha=0.25)
    ax.legend()
    fig.tight_layout()
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(path, dpi=160)
    plt.close(fig)


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="Compare all four bots on seeded ships.")
    parser.add_argument("--size", type=int, default=10)
    parser.add_argument("--q", type=float, nargs="+", default=[0.3])
    parser.add_argument("--trials", type=int, default=1)
    parser.add_argument("--seed", type=int, default=4)
    parser.add_argument("--max-steps", type=int, default=5000)
    parser.add_argument("--csv", help="Write raw trial results to this CSV file")
    parser.add_argument("--plot", help="Write the success-rate graph to this image file")
    args = parser.parse_args()
    results = run_experiments(args.size, args.q, args.trials, args.seed, args.max_steps)
    for result in results:
        print(f"trial={result['trial']} q={result['q']} {result['bot']}: "
              f"{result['outcome']} ({result['steps']} steps)")
    if args.csv:
        save_results(results, args.csv)
    if args.plot:
        plot_success_rates(results, args.plot)
