import random
import unittest

import fire


def test_fire_spreads_to_all_open_neighbors_when_q_is_one():
    open_cells = [
        [False, True, False],
        [True, True, True],
        [False, True, False],
    ]
    result = fire.spread_fire(open_cells, {(1, 1)}, q=1, randomizer=random.Random(1))

    assert result == {(1, 1), (0, 1), (1, 0), (1, 2), (2, 1)}


class FireTests(unittest.TestCase):
    def test_button_is_fireproof_but_neighbors_burn(self):
        grid = [[True] * 3 for _ in range(3)]
        result = fire.spread_fire(grid, {(1, 1)}, 1, random.Random(1), button=(1, 2))
        self.assertNotIn((1, 2), result)
        self.assertIn((0, 1), result)

    def test_open_neighbors_ignite(self):
        test_fire_spreads_to_all_open_neighbors_when_q_is_one()

    def test_spread_is_simultaneous_and_walls_do_not_ignite(self):
        grid = [[True, True, True], [False, False, False], [False, False, False]]
        self.assertEqual(fire.spread_fire(grid, {(0, 0)}, 1, random.Random(1)),
                         {(0, 0), (0, 1)})

    def test_zero_flammability_preserves_fire(self):
        grid = [[True] * 3 for _ in range(3)]
        self.assertEqual(fire.spread_fire(grid, {(1, 1)}, 0, random.Random(1)), {(1, 1)})


if __name__ == "__main__":
    unittest.main()
