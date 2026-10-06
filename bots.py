"""Project 1 bots.

Every bot has the same signature and answers one question: "where do I step next?"

    next_cell = botN(grid, bot, button, fire, q, state)

    grid    D x D list of bools (True = open), from ship.generate_ship
    bot     (row, col) the bot is standing on
    button  (row, col) of the button
    fire    set of (row, col) cells currently burning
    q       flammability (only Bot 4 uses it)
    state   a dict the CALLER creates once per trial per bot ({}) and passes
            back in every step. Bots use it as scratch memory (Bot 1 keeps its
            plan there, Bot 4 caches the grid as a NumPy array).

The return value is the cell to move to. Returning `bot` itself means "stay".
Bots 1-3 are just bfs.bfs with a different set of forbidden cells.
"""
import numpy as np

from bfs import bfs
from ship import neighbors

_NEAR_ONE = 1 - 1e-12  # probabilities above this are treated as certain fire


def _first_step(path, here):
    """Next cell on a path, or stay put if there is no path / already there."""
    return path[1] if path is not None and len(path) > 1 else here


def _fire_plus_neighbors(fire, size):
    """The burning cells together with every cell adjacent to one."""
    danger = set(fire)
    for r, c in fire:
        danger.update(neighbors(r, c, size))
    return danger


# --------------------------------------------------------------------------
# Bot 1: plan once at t=0 around the initial fire cell, then follow the plan.
# The first call must be made at t=0, when `fire` is just the starting cell.
# --------------------------------------------------------------------------
def bot1(grid, bot, button, fire, q, state):
    if "plan" not in state:
        state["plan"] = bfs(grid, bot, button, fire)
        state["step"] = 0
    plan = state["plan"]
    if plan is None or state["step"] + 1 >= len(plan):
        return bot  # no plan exists (or plan finished): stay put
    state["step"] += 1
    return plan[state["step"]]


# --------------------------------------------------------------------------
# Bot 2: re-plan every step around the cells that are burning right now.
# --------------------------------------------------------------------------
def bot2(grid, bot, button, fire, q, state):
    return _first_step(bfs(grid, bot, button, fire), bot)


# --------------------------------------------------------------------------
# Bot 3: re-plan every step, also avoiding cells next to the fire. If that
# leaves no route, fall back to avoiding only the burning cells.
# --------------------------------------------------------------------------
def bot3(grid, bot, button, fire, q, state):
    path = bfs(grid, bot, button, _fire_plus_neighbors(fire, len(grid)))
    if path is None:
        path = bfs(grid, bot, button, fire)
    return _first_step(path, bot)


# --------------------------------------------------------------------------
# Bot 4: risk-forecast planner.
#   1. Forecast P_t(c) = chance cell c is burning at future time t, using a
#      mean-field approximation (neighbors treated as independent).
#   2. Find the path to the button that maximizes the approximate survival
#      probability. Stepping onto c at time t costs -log(1 - P_t(c)), so the
#      cheapest path is the most likely to survive. The search is a layered
#      dynamic program over (time, cell), done with NumPy array shifts.
#   3. Take only the first step, then re-plan next turn with the new fire.
# --------------------------------------------------------------------------
def _forecast(open_mask, fire, q, horizon, ignitable):
    """Return [P_0, P_1, ..., P_horizon] as D x D arrays."""
    P = np.zeros(open_mask.shape)
    for r, c in fire:
        P[r, c] = 1.0
    layers = [P]
    for _ in range(horizon):
        keep = np.pad(1 - q * P, 1, constant_values=1.0)  # P(neighbor fails to ignite me)
        none_ignite = (keep[:-2, 1:-1] * keep[2:, 1:-1]
                       * keep[1:-1, :-2] * keep[1:-1, 2:])
        P = P + (1 - P) * (1 - none_ignite) * ignitable
        layers.append(P)
    return layers


def _step_cost(P, open_mask):
    """-log(survival) of occupying each cell, inf where it is wall or certain fire."""
    capped = np.minimum(P, _NEAR_ONE)
    cost = -np.log1p(-capped)
    cost[(P >= _NEAR_ONE) | ~open_mask] = np.inf
    return cost


def bot4(grid, bot, button, fire, q, state, slack=20, button_immune=False):
    size = len(grid)
    if "open" not in state:  # convert once per trial, not once per step
        state["open"] = np.array(grid, dtype=bool)
    open_mask = state["open"]

    safe_path = bfs(grid, bot, button, fire)
    if safe_path is None:
        return bot  # fire already cuts the bot off from the button: nothing helps
    if len(safe_path) == 1:
        return bot

    # Only look as far ahead as a detour could plausibly be worth it.
    horizon = len(safe_path) - 1 + slack

    ignitable = open_mask.astype(float)
    if button_immune:
        ignitable[button] = 0.0
    P = _forecast(open_mask, fire, q, horizon, ignitable)

    # costs[k] holds the best total cost of being on each cell after k+1 moves.
    cost = np.full(open_mask.shape, np.inf)
    cost[bot] = 0.0
    costs = []
    for t in range(1, horizon + 1):
        step = _step_cost(P[t], open_mask)
        # Entering the button is checked BEFORE the fire advances this turn,
        # so its risk comes from the previous forecast layer.
        p_button = min(P[t - 1][button], _NEAR_ONE)
        step[button] = np.inf if P[t - 1][button] >= _NEAR_ONE else -np.log1p(-p_button)

        padded = np.pad(cost, 1, constant_values=np.inf)
        best_prev = np.minimum(
            np.minimum(padded[:-2, 1:-1], padded[2:, 1:-1]),
            np.minimum(padded[1:-1, :-2], padded[1:-1, 2:]),
        )
        cost = best_prev + step
        costs.append(cost)

    arrival = np.array([layer[button] for layer in costs])
    if not np.isfinite(arrival).any():
        # The forecast says every route is doomed: make a break for it.
        return _first_step(safe_path, bot)

    t_star = int(np.argmin(arrival)) + 1  # best arrival time at the button

    # Walk backward through the layers to recover the FIRST move of that path.
    cell = button
    for t in range(t_star, 1, -1):
        previous = costs[t - 2]  # best costs after t-1 moves
        cell = min(neighbors(cell[0], cell[1], size), key=lambda n: previous[n])
    return cell


# --------------------------------------------------------------------------
# Demo only: one seeded scenario, all four bots facing the same fire.
# Swap `_demo_spread` for your partner's spread_fire once it is wired in.
# --------------------------------------------------------------------------
def _demo_spread(grid, fire, q, rng):
    size = len(grid)
    counts = {}
    for r, c in fire:
        for n in neighbors(r, c, size):
            if grid[n[0]][n[1]] and n not in fire:
                counts[n] = counts.get(n, 0) + 1
    new_fire = set(fire)
    for cell, k in sorted(counts.items()):
        if rng.random() < 1 - (1 - q) ** k:
            new_fire.add(cell)
    return new_fire


def _demo_trial(bot_fn, grid, bot, button, fire0, q, seed, max_steps=5000, **kw):
    import random
    rng = random.Random(seed)
    fire, state = set(fire0), {}
    for t in range(1, max_steps + 1):
        bot = bot_fn(grid, bot, button, fire, q, state, **kw)
        if bot == button:
            return "success", t
        if bot in fire:
            return "burned", t
        fire = _demo_spread(grid, fire, q, rng)
        if bot in fire:
            return "burned", t
    return "timeout", max_steps


if __name__ == "__main__":
    import random
    from ship import generate_ship

    D = 4
    Q = 0.3
    SEED = 4

    ship = generate_ship(D, seed=SEED)
    rng = random.Random(SEED)
    open_cells = [(r, c) for r in range(D) for c in range(D) if ship[r][c]]
    start, btn, fire_start = rng.sample(open_cells, 3)
    print(f"D={D} q={Q} bot={start} button={btn} fire={fire_start}")

    # Map (small ships only): # = wall, . = open, B = bot, X = button, F = fire
    if D <= 20:
        marks = {start: "B", btn: "X", fire_start: "F"}
        print()
        for r in range(D):
            print(" ".join(marks.get((r, c), "." if ship[r][c] else "#") for c in range(D)))
        print()

    for name, fn in [("bot1", bot1), ("bot2", bot2), ("bot3", bot3), ("bot4", bot4)]:
        print(name, _demo_trial(fn, ship, start, btn, {fire_start}, Q, seed=SEED))