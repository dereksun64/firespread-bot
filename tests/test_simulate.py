"""Run with: python3 -m unittest discover -s tests."""

import unittest

from bots import bot1, bot2, bot3, bot4
from simulate import run_trial


class SimulationTests(unittest.TestCase):
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


if __name__ == "__main__":
    unittest.main()
