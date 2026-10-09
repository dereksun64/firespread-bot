# verify and summarize the corrected evidence; run after collect_evidence.py

import csv
import json
import math
from collections import defaultdict
from pathlib import Path

import numpy as np

from simulate import save_results, success_rates


def read_paired(path, expected_trials):
    # group rows by q and trial so every comparison is made on the same ship,
    # positions, and fire seed rather than on unrelated random runs
    with path.open(newline="") as stream:
        rows = list(csv.DictReader(stream))
    groups = defaultdict(dict)
    for row in rows:
        if row["rules"] != "fireproof_button_v1":
            raise ValueError("Unexpected rule set")
        key = (float(row["q"]), int(row["trial"]))
        if row["bot"] in groups[key]:
            raise ValueError("Duplicate bot result")
        groups[key][row["bot"]] = row
        row["q"], row["size"] = float(row["q"]), int(row["size"])
    for group in groups.values():
        if set(group) != {"bot1", "bot2", "bot3", "bot4"}:
            raise ValueError("Incomplete paired scenario")
        metadata = {(r["ship_seed"], r["fire_seed"], r["start"], r["button"],
                     r["fire_start"], r["rules"], r["max_steps"]) for r in group.values()}
        if len(metadata) != 1:
            raise ValueError("Bots did not share a scenario")
    counts = defaultdict(int)
    for q, _ in groups:
        counts[q] += 1
    if any(count != expected_trials for count in counts.values()):
        raise ValueError("Unexpected number of paired trials")
    return rows, groups


if __name__ == "__main__":
    output = Path("results/fireproof")
    sweep, _ = read_paired(output / "sweep.csv", 100)
    focused, pairs = read_paired(output / "focused_q03.csv", 300)
    save_results(success_rates(sweep), output / "sweep_summary.csv")
    save_results(success_rates(focused), output / "focused_summary.csv")
    randomizer = np.random.default_rng(42)  # fixed seed so the intervals come out the same every run
    comparisons = []
    for bot in ("bot1", "bot2", "bot3"):
        # compare Bot 4 to each other bot ship by ship. a "win" is a ship where
        # Bot 4 succeeded and the other bot didn't, a "loss" is the reverse.
        # (this is where the 19-1, 8-1, 4-0 numbers in the report come from)
        wins = losses = 0
        for _, group in sorted(pairs.items()):
            a = group["bot4"]["outcome"] == "success"
            b = group[bot]["outcome"] == "success"
            wins += a and not b
            losses += b and not a
        # McNemar's test: ships where both bots did the same thing tell us nothing
        # about which is better, so we only look at the wins and losses. if the two
        # bots were equally good, each disagreement would be a fair coin flip.
        # p = chance of a split at least as lopsided as ours (counting both
        # directions, hence the 2*). math.comb(n, k) / 2**n is the chance of
        # exactly k heads in n flips.
        n = wins + losses
        p = min(1, 2 * sum(math.comb(n, k) for k in range(min(wins, losses) + 1)) / 2 ** n)
        # bootstrap: pretend our 300 ships are the whole population, redraw 300 ships
        # from them 20,000 times, and see how much (wins - losses) bounces around.
        # each redraw lands in one of three buckets: Bot 4 won, Bot 4 lost, or tie.
        # dividing by 3 turns a count out of 300 into percentage points, and the
        # 2.5th / 97.5th percentiles are the middle 95% of those redraws
        draws = randomizer.multinomial(300, [wins / 300, losses / 300,
                                           1 - n / 300], size=20000)
        intervals = np.quantile((draws[:, 0] - draws[:, 1]) / 3, [0.025, 0.975])
        comparisons.append({"bot": bot, "wins": wins, "losses": losses,
                            "difference_pp": (wins - losses) / 3,
                            "bootstrap_ci_pp": intervals.tolist(), "exact_p": p})
    # Holm correction: we ran 3 comparisons, and the more you run the more likely
    # one looks good by luck. so go through the p-values from smallest to largest
    # and multiply them by 3, 2, 1. the running max keeps a bigger p-value from
    # ending up with a smaller adjusted value than a smaller one before it
    adjusted = 0
    for rank, row in enumerate(sorted(comparisons, key=lambda r: r["exact_p"])):
        adjusted = max(adjusted, min(1, (3 - rank) * row["exact_p"]))
        row["holm_p"] = adjusted
    (output / "paired_q03.json").write_text(json.dumps(comparisons, indent=2) + "\n")
    print(json.dumps(comparisons, indent=2))
    print("Verified", len(sweep), "sweep rows and", len(focused), "focused rows")
