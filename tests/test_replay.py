import unittest

from replay import hindsight_path


class HindsightTests(unittest.TestCase):
    def test_button_can_be_reached_before_it_ignites(self):
        grid = [[True] * 3 for _ in range(3)]
        self.assertEqual(hindsight_path(grid, (1, 0), (1, 1), (1, 2), 1, 0),
                         [(1, 0), (1, 1)])

    def test_early_button_ignition_makes_escape_impossible(self):
        grid = [[True] * 3 for _ in range(3)]
        self.assertIsNone(hindsight_path(grid, (2, 0), (0, 2), (0, 1), 1, 0))

    def test_recovers_multi_turn_route(self):
        grid = [[True] * 3 for _ in range(3)]
        path = hindsight_path(grid, (2, 0), (0, 2), (0, 1), 0, 0)
        self.assertEqual(len(path), 5)
        self.assertEqual(path[0], (2, 0))
        self.assertEqual(path[-1], (0, 2))
