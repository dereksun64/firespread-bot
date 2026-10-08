"""Run with: python3 -m unittest discover -s tests."""

import unittest
import csv
import tempfile
from pathlib import Path
from unittest.mock import patch

from bots import bot1, bot2, bot3, bot4
from simulate import run_experiments, run_trial, save_results, success_rates


class SimulationTests(unittest.TestCase):
    def test_trial_passes_fireproof_button_to_spread(self):
        grid = [[True] * 3 for _ in range(3)]
        stay = lambda grid, bot, button, fire, q, state: bot
        history = []
        run_trial(stay, grid, (2, 0), (1, 2), {(1, 1)}, 1, 0, 1, history)
        self.assertNotIn((1, 2), history[0]["fire_after"])

    def test_history_records_final_spread_without_changing_result(self):
        grid = [[True] * 3 for _ in range(3)]
        stay = lambda grid, bot, button, fire, q, state: bot
        history = []
        args = (stay, grid, (1, 0), (2, 2), {(1, 1)}, 1, 0)
        self.assertEqual(run_trial(*args, history=history), run_trial(*args))
        self.assertEqual(len(history), 1)
        self.assertNotIn((1, 0), history[0]["fire_before"])
        self.assertIn((1, 0), history[0]["fire_after"])

    def test_summary_counts_failures_and_timeouts(self):
        results = [dict(size=5, q=0.3, bot="bot1", outcome=outcome)
                   for outcome in ("success", "burned", "timeout", "success")]
        row = success_rates(results)[0]
        self.assertEqual(row["success_rate"], 0.5)
        self.assertEqual(row["trials"], 4)
        self.assertEqual(row["timeouts"], 1)

    def test_csv_preserves_trial_metadata(self):
        results = run_experiments(5, [0], 1, seed=7)
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "trials.csv"
            save_results(results, path)
            with path.open(newline="") as stream:
                rows = list(csv.DictReader(stream))
            self.assertEqual(len(rows), 4)
            self.assertEqual(rows[0]["ship_seed"], str(results[0]["ship_seed"]))
            self.assertEqual(rows[0]["start"], str(results[0]["start"]))

    def test_button_pressed_before_fire_spreads(self):
        grid = [[True] * 3 for _ in range(3)]
        for bot_fn in (bot1, bot2, bot3, bot4):
            with self.subTest(bot=bot_fn.__name__):
                self.assertEqual(
                    run_trial(bot_fn, grid, (1, 0), (1, 1), {(1, 2)}, 1, 0),
                    ("success", 1),
                )

    def test_burning_after_spread(self):
        grid = [[True] * 3 for _ in range(3)]
        stay = lambda grid, bot, button, fire, q, state: bot
        self.assertEqual(run_trial(stay, grid, (1, 0), (2, 2), {(1, 1)}, 1, 0),
                         ("burned", 1))

    def test_entering_burning_button_fails(self):
        grid = [[True] * 3 for _ in range(3)]
        enter_button = lambda grid, bot, button, fire, q, state: button
        self.assertEqual(run_trial(enter_button, grid, (1, 0), (1, 1), {(1, 1)}, 0, 0),
                         ("burned", 1))

    def test_timeout(self):
        grid = [[True] * 3 for _ in range(3)]
        stay = lambda grid, bot, button, fire, q, state: bot
        self.assertEqual(run_trial(stay, grid, (1, 0), (2, 2), {(0, 2)}, 0, 0, 3),
                         ("timeout", 3))

    def test_persistent_state_and_fresh_trials(self):
        grid = [[True] * 5 for _ in range(5)]
        for bot_fn in (bot1, bot2, bot3, bot4):
            with self.subTest(bot=bot_fn.__name__):
                args = (bot_fn, grid, (1, 0), (1, 4), {(0, 2)}, 0, 7)
                expected = ("success", 6 if bot_fn is bot3 else 4)
                self.assertEqual(run_trial(*args), expected)
                self.assertEqual(run_trial(*args), expected)

    def test_seed_reproduces_fire_history(self):
        grid = [[True] * 5 for _ in range(5)]
        histories = []
        for _ in range(2):
            history = []

            def stay(grid, bot, button, fire, q, state):
                history.append(frozenset(fire))
                return bot

            result = run_trial(stay, grid, (4, 0), (4, 4), {(0, 0)}, 0.3, 12, 20)
            histories.append((result, history))
        self.assertEqual(histories[0], histories[1])

    def test_experiments_pair_scenarios_and_pass_fire_seed(self):
        with patch("simulate.run_trial", return_value=("success", 2)) as trial:
            results = run_experiments(5, [0, 0.5, 1], 2, seed=7)
        self.assertEqual(len(results), 24)
        self.assertEqual(trial.call_count, 24)
        for index in range(0, 24, 12):
            calls = trial.call_args_list[index:index + 12]
            baseline = calls[0].args
            for call in calls:
                self.assertIs(call.args[1], baseline[1])
                self.assertEqual(call.args[2:5], baseline[2:5])
                self.assertEqual(call.args[6], baseline[6])
            self.assertEqual(len(set(baseline[2:4]) | baseline[4]), 3)
        self.assertNotEqual(results[0]["ship_seed"], results[12]["ship_seed"])

    def test_experiments_reproduce_actual_results(self):
        args = (5, [0, 0.5, 1], 3, 11, 30)
        self.assertEqual(run_experiments(*args), run_experiments(*args))

    def test_experiments_reject_invalid_settings(self):
        for args in ((2, [0], 1), (5, [], 1), (5, [1.1], 1), (5, [0], 0)):
            with self.subTest(args=args), self.assertRaises(ValueError):
                run_experiments(*args)


if __name__ == "__main__":
    unittest.main()
