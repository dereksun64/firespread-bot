# replay one paired CSV scenario and optionally save its complete history

import argparse
import ast
import csv
import json
import random
from pathlib import Path

from bots import bot1, bot2, bot3, bot4
from fire import spread_fire
from ship import generate_ship, neighbors
from simulate import run_trial


def hindsight_path(grid, start, button, fire_start, q, seed, max_steps=5000):
    # find an escape with advance knowledge of one realized fire sequence
    # None means no escape within the cutoff, not necessarily forever
    # this oracle is for diagnosis and cannot be used as an informed bot
    fire, reachable = {fire_start}, {start}
    randomizer, parents = random.Random(seed), []
    for _ in range(max_steps):
        # consider staying as well as moving: the diagnostic oracle is allowed
        # to choose any legal action after seeing the realized future fire
        candidates = {}
        for here in sorted(reachable):
            for cell in (here, *neighbors(*here, len(grid))):
                if grid[cell[0]][cell[1]] and cell not in fire:
                    candidates.setdefault(cell, here)
        if button in candidates:
            path = [button, candidates[button]]
            for previous in reversed(parents):
                path.append(previous[path[-1]])
            return path[::-1]
        # advance the same seeded fire process used by the saved simulation
        fire = spread_fire(grid, fire, q, randomizer, button=button)
        if button in fire:
            return None  # The button stays burning; no later success is possible.
        surviving = {cell: parent for cell, parent in candidates.items() if cell not in fire}
        if not surviving:
            return None
        parents.append(surviving)
        reachable = set(surviving)
    return None


def replay(path, trial, q):
    with open(path, newline="") as stream:
        rows = [row for row in csv.DictReader(stream)
                if int(row["trial"]) == trial and float(row["q"]) == q]
    if len(rows) != 4:
        raise ValueError("Expected one saved row for each of the four bots")
    if any(row.get("rules") != "fireproof_button_v1" for row in rows):
        raise ValueError("This CSV uses legacy burnable-button rules. Regenerate results "
                         "with the fireproof-button simulator before replaying.")
    bots = {fn.__name__: fn for fn in (bot1, bot2, bot3, bot4)}
    scenario = rows[0]
    grid = generate_ship(int(scenario["size"]), seed=int(scenario["ship_seed"]))
    start, button, fire_start = [ast.literal_eval(scenario[key])
                                 for key in ("start", "button", "fire_start")]
    runs = {}
    for row in rows:
        # re-run every bot from a fresh state, then reject any mismatch with
        # the recorded outcome or any move that is not an adjacent open cell
        history = []
        outcome, steps = run_trial(bots[row["bot"]], grid, start, button, {fire_start},
                                   q, int(row["fire_seed"]),
                                   max_steps=int(row["max_steps"]), history=history)
        if (outcome, steps) != (row["outcome"], int(row["steps"])):
            raise ValueError(f"Replay differs from saved result for {row['bot']}")
        for turn in history:
            old, new = turn["previous"], turn["position"]
            if not grid[new[0]][new[1]] or (new != old and new not in neighbors(*old, len(grid))):
                raise ValueError("Illegal bot move in replay")
        runs[row["bot"]] = {"outcome": outcome, "steps": steps, "history": history}
    return {"trial": trial, "q": q, "grid": grid, "start": start, "button": button,
            "fire_start": fire_start, "ship_seed": int(scenario["ship_seed"]),
            "fire_seed": int(scenario["fire_seed"]), "runs": runs}


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="Replay one paired CSV scenario and optionally save its complete history."
    )
    parser.add_argument("--csv", default="results/fireproof/sweep.csv")
    parser.add_argument("--trial", type=int, required=True)
    parser.add_argument("--q", type=float, required=True)
    parser.add_argument("--output", help="Save full fire and position histories as JSON")
    parser.add_argument("--hindsight", action="store_true", help="Search escape routes with future fire known")
    args = parser.parse_args()
    result = replay(args.csv, args.trial, args.q)
    if args.hindsight:
        result["hindsight_path"] = hindsight_path(
            result["grid"], tuple(result["start"]), tuple(result["button"]),
            tuple(result["fire_start"]), result["q"], result["fire_seed"])
        path = result["hindsight_path"]
        print("Hindsight escape:", "none within 5000 turns" if path is None else f"{len(path)-1} moves")
    for name, run in result["runs"].items():
        print(f"{name}: {run['outcome']} in {run['steps']} turns")
        if run["outcome"] == "burned":
            last = run["history"][-1]
            phase = "entered existing fire" if last["position"] in last["fire_before"] else "caught by spread"
            print(f"  {phase} at {last['position']}")
    if args.output:
        path = Path(args.output)
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(json.dumps(result) + "\n")
