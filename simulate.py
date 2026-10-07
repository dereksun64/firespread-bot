"""Run one bot against the ship's fire, one turn at a time."""

import random

from fire import spread_fire


def run_trial(bot_fn, grid, start, button, fire0, q, seed, max_steps=5000):
    """Return (success/burned/timeout, turns elapsed).

    The grid is shared read-only; bot memory and fire are fresh for each trial.
    A timeout is a simulation cutoff, not proof that escape is impossible.
    """
    if not 0 <= q <= 1:
        raise ValueError("q must be between 0 and 1")
    if max_steps < 0:
        raise ValueError("max_steps must be nonnegative")

    randomizer = random.Random(seed)
    position, fire, state = start, set(fire0), {}
    if position in fire:
        return "burned", 0
    if position == button:
        return "success", 0

    for step in range(1, max_steps + 1):
        position = bot_fn(grid, position, button, fire, q, state)
        if position in fire:
            return "burned", step
        if position == button:
            return "success", step
        fire = spread_fire(grid, fire, q, randomizer)
        if position in fire:
            return "burned", step
    return "timeout", max_steps


if __name__ == "__main__":
    from bots import bot1, bot2, bot3, bot4
    from ship import generate_ship

    size, q, seed = 10, 0.3, 4
    grid = generate_ship(size, seed=seed)
    cells = [(r, c) for r, row in enumerate(grid) for c, opened in enumerate(row) if opened]
    start, button, fire_start = random.Random(seed).sample(cells, 3)
    print(f"D={size} q={q} bot={start} button={button} fire={fire_start}")
    for bot_fn in (bot1, bot2, bot3, bot4):
        print(bot_fn.__name__, run_trial(bot_fn, grid, start, button, {fire_start}, q, seed))
