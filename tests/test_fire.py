import random

import fire


def test_fire_spreads_to_all_open_neighbors_when_q_is_one():
    open_cells = [
        [False, True, False],
        [True, True, True],
        [False, True, False],
    ]
    spread_fire = getattr(fire, "spread_fire", lambda *args, **kwargs: set())

    result = spread_fire(open_cells, {(1, 1)}, q=1, randomizer=random.Random(1))

    assert result == {(1, 1), (0, 1), (1, 0), (1, 2), (2, 1)}


if __name__ == "__main__":
    test_fire_spreads_to_all_open_neighbors_when_q_is_one()
    print("test passed")
