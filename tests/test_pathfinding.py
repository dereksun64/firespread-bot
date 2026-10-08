"""Controlled strategy differences and an independent scalar risk oracle."""

import math
import unittest

from bots import bot1, bot2, bot3, bot4, _forecast
from ship import generate_ship, neighbors
from simulate import run_trial


def trace_trial(fn, grid, start, button, fire, q, seed):
    path = [start]

    def traced(*args):
        move = fn(*args)
        path.append(move)
        return move

    outcome = run_trial(traced, grid, start, button, fire, q, seed, 100)
    return outcome, path


def scalar_forecast(grid, fire, q, horizon, button=None):
    cells = [(r, c) for r, row in enumerate(grid) for c, opened in enumerate(row) if opened]
    layers = [{cell: float(cell in fire) for cell in cells}]
    for _ in range(horizon):
        old = layers[-1]
        layers.append({cell: 0.0 if cell == button else old[cell] + (1 - old[cell]) *
                       (1 - math.prod(1 - q * old.get(n, 0)
                                      for n in neighbors(*cell, len(grid))))
                       for cell in cells})
    return layers


def risk_by_first_move(grid, start, button, fire, q, horizon):
    """Scalar forward search, terminating paths on arrival at the button."""
    layers = scalar_forecast(grid, fire, q, horizon, button)
    scores = {}
    for first in neighbors(*start, len(grid)):
        if first not in layers[0] or first in fire:
            continue
        frontier = {start: 0.0}
        best = math.inf
        for t in range(1, horizon + 1):
            following = {}
            for here, cost in frontier.items():
                for cell in neighbors(*here, len(grid)):
                    if cell not in layers[0] or (t == 1 and cell != first):
                        continue
                    probability = layers[t - 1 if cell == button else t][cell]
                    if probability >= 1 - 1e-12:
                        continue
                    candidate = cost - math.log1p(-probability)
                    if cell == button:
                        best = min(best, candidate)
                    else:
                        following[cell] = min(following.get(cell, math.inf), candidate)
            frontier = following
        scores[first] = best
    return scores


class PathfindingTests(unittest.TestCase):
    def test_replanning_escapes_where_fixed_plan_burns(self):
        grid = generate_ship(6, seed=16)
        results = [trace_trial(fn, grid, (2, 2), (3, 3), {(1, 5)}, 0.3, 16)
                   for fn in (bot1, bot2, bot3, bot4)]
        self.assertEqual(results[0][0], ("burned", 2))
        for outcome, path in results[1:]:
            self.assertEqual(outcome, ("success", 10))
            self.assertEqual(path[2], (1, 1))
        self.assertEqual(results[0][1][2], (1, 3))

    def test_buffer_changes_full_path(self):
        grid = [[True] * 5 for _ in range(5)]
        results = [trace_trial(fn, grid, (1, 0), (1, 4), {(0, 2)}, 0, 7)
                   for fn in (bot1, bot2, bot3, bot4)]
        self.assertEqual([result[0] for result in results],
                         [("success", 4), ("success", 4), ("success", 6), ("success", 4)])
        self.assertEqual(results[2][1][1], (2, 0))

    def test_risk_planner_differs_and_matches_scalar_oracle(self):
        grid = generate_ship(6, seed=0)
        start, button, fire, q = (2, 3), (5, 1), {(5, 2)}, 0.3
        self.assertEqual(bot2(grid, start, button, fire, q, {}), (3, 3))
        self.assertEqual(bot3(grid, start, button, fire, q, {}), (3, 3))
        chosen = bot4(grid, start, button, fire, q, {})
        self.assertEqual(chosen, (2, 2))
        # Distance is 7 moves here; Bot 4's default horizon is 27.
        scores = risk_by_first_move(grid, start, button, fire, q, 27)
        self.assertAlmostEqual(scores[chosen], min(scores.values()), places=10)
        self.assertLess(scores[chosen], scores[(3, 3)])

    def test_numpy_forecast_matches_scalar_cell_updates(self):
        import numpy as np

        grid = generate_ship(6, seed=0)
        mask = np.array(grid, dtype=bool)
        for q in (0, 0.3, 1):
            expected = scalar_forecast(grid, {(5, 2)}, q, 8)
            actual = _forecast(mask, {(5, 2)}, q, 8, mask.astype(float))
            for t, layer in enumerate(expected):
                for cell, probability in layer.items():
                    self.assertAlmostEqual(actual[t][cell], probability, places=12)
                self.assertTrue(np.all(actual[t][~mask] == 0))


if __name__ == "__main__":
    unittest.main()
