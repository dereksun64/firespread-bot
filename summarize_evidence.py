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
    randomizer = np.random.default_rng(42)
    comparisons = []
    for bot in ("bot1", "bot2", "bot3"):
        wins = losses = 0
        for _, group in sorted(pairs.items()):
            a = group["bot4"]["outcome"] == "success"
            b = group[bot]["outcome"] == "success"
            wins += a and not b
            losses += b and not a
        # McNemar's exact test uses only discordant pairs; ties provide no
        # evidence that one of the two bots outperformed the other
        n = wins + losses
        p = min(1, 2 * sum(math.comb(n, k) for k in range(min(wins, losses) + 1)) / 2 ** n)
        draws = randomizer.multinomial(300, [wins / 300, losses / 300,
                                           1 - n / 300], size=20000)
        intervals = np.quantile((draws[:, 0] - draws[:, 1]) / 3, [0.025, 0.975])
        comparisons.append({"bot": bot, "wins": wins, "losses": losses,
                            "difference_pp": (wins - losses) / 3,
                            "bootstrap_ci_pp": intervals.tolist(), "exact_p": p})
    # apply Holm's step-down correction to the three planned comparisons
    adjusted = 0
    for rank, row in enumerate(sorted(comparisons, key=lambda r: r["exact_p"])):
        adjusted = max(adjusted, min(1, (3 - rank) * row["exact_p"]))
        row["holm_p"] = adjusted
    (output / "paired_q03.json").write_text(json.dumps(comparisons, indent=2) + "\n")
    print(json.dumps(comparisons, indent=2))
    print("Verified", len(sweep), "sweep rows and", len(focused), "focused rows")
