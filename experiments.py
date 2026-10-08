"""Repeated trials and graphs for the writeup (Section 7, question 2).

For many values of q, generate many random ships, run all four bots on each
one, and graph how often each bot puts the fire out.

    python3 experiments.py                       # default sweep, D=40
    python3 experiments.py --size 60 --trials 500
    python3 experiments.py --q-values 0.2 0.3 0.4 0.5 --trials 2000
    python3 experiments.py --plot-only           # redraw graphs from the CSVs

Outputs (in --out, default results/claude_d40/):
    trials.csv           one row per (q, trial, bot): outcome, steps, distances
    summary.csv          one row per (q, bot): success rate and 95% interval
    success_vs_q.png     the graph the assignment asks for
    gain_over_bot1.png   each bot's success rate minus Bot 1's, to show where
                         the 'interesting' range of q is

Fairness: within one trial every bot gets the same ship, the same bot/button/
fire cells and the same fire seed. The fire never depends on what the bot does,
so all four bots face the identical fire. The same set of trials is also reused
at every q, which makes the curves smoother than independent sampling would.
"""
import argparse
import csv
import math
import os
import random
import time
from multiprocessing import Pool

from bfs import bfs
from bots import bot1, bot2, bot3, bot4
from ship import generate_ship
from simulate import run_trial

BOTS = (("Bot 1", bot1), ("Bot 2", bot2), ("Bot 3", bot3), ("Bot 4", bot4))

# Coarse steps where little changes, finer steps through the middle range.
DEFAULT_Q = ([0.0, 0.05, 0.1, 0.15]
             + [round(0.2 + 0.025 * i, 3) for i in range(21)]   # 0.2 .. 0.7
             + [0.75, 0.8, 0.85, 0.9, 0.95, 1.0])

TRIAL_FIELDS = ["q", "trial", "seed", "bot", "outcome", "steps",
                "bot_to_button", "fire_to_button", "fire_to_bot"]
SUMMARY_FIELDS = ["q", "bot", "trials", "successes", "burned", "timeout",
                  "unreachable", "success_rate", "ci_low", "ci_high"]


# --------------------------------------------------------------------------
# Running trials
# --------------------------------------------------------------------------
def make_scenario(size, seed):
    """One random ship with three distinct open cells: bot, button, fire."""
    grid = generate_ship(size, seed=seed)
    cells = [(r, c) for r, row in enumerate(grid) for c, is_open in enumerate(row) if is_open]
    start, button, fire0 = random.Random(seed).sample(cells, 3)
    return grid, start, button, fire0


def _distance(grid, a, b):
    path = bfs(grid, a, b)
    return len(path) - 1 if path is not None else -1


def run_scenario(task):
    """Run every bot on one (q, trial). Returns a list of trials.csv rows."""
    size, q, trial, seed, max_steps = task
    grid, start, button, fire0 = make_scenario(size, seed)
    distances = (_distance(grid, start, button),
                 _distance(grid, fire0, button),
                 _distance(grid, fire0, start))

    # Burning cells never stop burning, so if the first fire cell already
    # separates the bot from the button, no bot can ever get there. Record the
    # failure directly instead of simulating thousands of idle turns.
    cut_off = bfs(grid, start, button, {fire0}) is None

    rows = []
    for name, bot_fn in BOTS:
        if cut_off:
            outcome, steps = "unreachable", 0
        else:
            outcome, steps = run_trial(bot_fn, grid, start, button, {fire0}, q, seed, max_steps)
        rows.append([q, trial, seed, name, outcome, steps, *distances])
    return rows


def run_experiments(size, q_values, trials, base_seed, max_steps, workers, out_dir):
    tasks = [(size, q, i, base_seed + i, max_steps) for q in q_values for i in range(trials)]
    path = os.path.join(out_dir, "trials.csv")
    started = time.time()
    with open(path, "w", newline="") as handle, Pool(workers) as pool:
        writer = csv.writer(handle)
        writer.writerow(TRIAL_FIELDS)
        for done, rows in enumerate(pool.imap_unordered(run_scenario, tasks, chunksize=8), 1):
            writer.writerows(rows)
            if done % max(1, len(tasks) // 20) == 0 or done == len(tasks):
                print(f"  {done}/{len(tasks)} scenarios  ({time.time() - started:.0f}s)", flush=True)
    return path


# --------------------------------------------------------------------------
# Summarizing
# --------------------------------------------------------------------------
def wilson_interval(successes, n, z=1.96):
    """95% confidence interval for a success frequency (Wilson score)."""
    if n == 0:
        return 0.0, 1.0
    p = successes / n
    denom = 1 + z * z / n
    center = (p + z * z / (2 * n)) / denom
    half = z * math.sqrt(p * (1 - p) / n + z * z / (4 * n * n)) / denom
    return max(0.0, center - half), min(1.0, center + half)


def summarize(trials_path, out_dir):
    counts = {}  # (q, bot) -> {outcome: count}
    with open(trials_path, newline="") as handle:
        for row in csv.DictReader(handle):
            bucket = counts.setdefault((float(row["q"]), row["bot"]), {})
            bucket[row["outcome"]] = bucket.get(row["outcome"], 0) + 1

    summary = []
    for (q, bot), bucket in sorted(counts.items()):
        n = sum(bucket.values())
        wins = bucket.get("success", 0)
        low, high = wilson_interval(wins, n)
        summary.append({
            "q": q, "bot": bot, "trials": n, "successes": wins,
            "burned": bucket.get("burned", 0), "timeout": bucket.get("timeout", 0),
            "unreachable": bucket.get("unreachable", 0),
            "success_rate": round(wins / n, 4), "ci_low": round(low, 4), "ci_high": round(high, 4),
        })

    path = os.path.join(out_dir, "summary.csv")
    with open(path, "w", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=SUMMARY_FIELDS)
        writer.writeheader()
        writer.writerows(summary)
    return path


def read_summary(path):
    series = {}  # bot -> list of rows sorted by q
    with open(path, newline="") as handle:
        for row in csv.DictReader(handle):
            series.setdefault(row["bot"], []).append({
                "q": float(row["q"]), "n": int(row["trials"]),
                "rate": float(row["success_rate"]),
                "low": float(row["ci_low"]), "high": float(row["ci_high"]),
            })
    for rows in series.values():
        rows.sort(key=lambda r: r["q"])
    return series


# --------------------------------------------------------------------------
# Graphs
# --------------------------------------------------------------------------
STYLE = {  # color plus a marker and line style, so bots differ without color too
    "Bot 1": ("#2a78d6", "o", "-"),
    "Bot 2": ("#eb6834", "s", "--"),
    "Bot 3": ("#1baf7a", "^", "-."),
    "Bot 4": ("#4a3aa7", "D", "-"),
}
INK, MUTED, GRID = "#0b0b0b", "#52514e", "#e4e3df"


def _new_axes(plt, title, subtitle, ylabel):
    fig, ax = plt.subplots(figsize=(9, 5.4), dpi=160)
    fig.subplots_adjust(top=0.84, left=0.09, right=0.97, bottom=0.12)
    fig.text(0.09, 0.95, title, fontsize=13, fontweight="bold", color=INK, va="top")
    fig.text(0.09, 0.895, subtitle, fontsize=9.5, color=MUTED, va="top")
    ax.set_xlabel("Flammability q", color=MUTED)
    ax.set_ylabel(ylabel, color=MUTED)
    ax.set_xlim(-0.01, 1.01)
    ax.set_xticks([i / 10 for i in range(11)])
    ax.grid(True, color=GRID, linewidth=0.8)
    ax.set_axisbelow(True)
    for side in ("top", "right"):
        ax.spines[side].set_visible(False)
    for side in ("left", "bottom"):
        ax.spines[side].set_color(GRID)
    ax.tick_params(colors=MUTED, length=0)
    return fig, ax


def plot_success(series, size, out_dir):
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt

    n = min(r["n"] for rows in series.values() for r in rows)
    fig, ax = _new_axes(
        plt, "How often each bot puts the fire out",
        f"{size} x {size} ships, {n} random ships per value of q; "
        "shaded bands are 95% confidence intervals",
        "Success frequency")
    for bot, rows in series.items():
        color, marker, line = STYLE[bot]
        qs = [r["q"] for r in rows]
        ax.fill_between(qs, [r["low"] for r in rows], [r["high"] for r in rows],
                        color=color, alpha=0.13, linewidth=0)
        ax.plot(qs, [r["rate"] for r in rows], line, color=color, marker=marker,
                markersize=4.5, linewidth=1.8, label=bot)
    ax.set_ylim(0, 1.02)
    ax.legend(frameon=False, labelcolor=INK, loc="upper right")
    path = os.path.join(out_dir, "success_vs_q.png")
    fig.savefig(path, facecolor="white")
    plt.close(fig)
    return path


def plot_gain(series, size, out_dir):
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt

    base = {r["q"]: r["rate"] for r in series["Bot 1"]}
    n = min(r["n"] for rows in series.values() for r in rows)
    fig, ax = _new_axes(
        plt, "Where the bots differ: success frequency minus Bot 1's",
        f"{size} x {size} ships, {n} random ships per value of q; "
        "every bot faced the same ships and fires",
        "Difference from Bot 1 (percentage points)")
    ax.axhline(0, color=MUTED, linewidth=1)
    for bot, rows in series.items():
        if bot == "Bot 1":
            continue
        color, marker, line = STYLE[bot]
        ax.plot([r["q"] for r in rows], [100 * (r["rate"] - base[r["q"]]) for r in rows],
                line, color=color, marker=marker, markersize=4.5, linewidth=1.8, label=bot)
    ax.legend(frameon=False, labelcolor=INK, loc="upper right")
    path = os.path.join(out_dir, "gain_over_bot1.png")
    fig.savefig(path, facecolor="white")
    plt.close(fig)
    return path


# --------------------------------------------------------------------------
def main():
    parser = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    parser.add_argument("--size", type=int, default=40, help="ship is size x size (default 40)")
    parser.add_argument("--trials", type=int, default=300, help="random ships per value of q")
    parser.add_argument("--q-values", type=float, nargs="+", default=DEFAULT_Q)
    parser.add_argument("--seed", type=int, default=0, help="first trial seed")
    parser.add_argument("--max-steps", type=int, default=5000)
    parser.add_argument("--workers", type=int, default=os.cpu_count())
    parser.add_argument("--out", default="results/claude_d40")
    parser.add_argument("--plot-only", action="store_true",
                        help="skip the simulations; redraw from the CSVs in --out")
    args = parser.parse_args()

    os.makedirs(args.out, exist_ok=True)
    trials_path = os.path.join(args.out, "trials.csv")
    if not args.plot_only:
        print(f"D={args.size}, {len(args.q_values)} values of q, {args.trials} ships each, "
              f"{args.workers} workers")
        trials_path = run_experiments(args.size, args.q_values, args.trials, args.seed,
                                      args.max_steps, args.workers, args.out)
        with open(os.path.join(args.out, "size.txt"), "w") as handle:
            handle.write(str(args.size))

    size_file = os.path.join(args.out, "size.txt")
    size = int(open(size_file).read()) if os.path.exists(size_file) else args.size
    summary_path = summarize(trials_path, args.out)
    series = read_summary(summary_path)
    for path in (trials_path, summary_path,
                 plot_success(series, size, args.out), plot_gain(series, size, args.out)):
        print("wrote", path)


if __name__ == "__main__":
    main()
