"""Edge cases for the ship, the fire, BFS, the bots and the simulator.

Run with: python3 -m unittest discover -s tests -v
"""
import random
import sys
import unittest
from collections import deque
from pathlib import Path

sys.path.append(str(Path(__file__).resolve().parent.parent))

from bfs import bfs
from bots import bot1, bot2, bot3, bot4
from fire import spread_fire
from ship import generate_ship, neighbors
from simulate import run_trial

ALL_BOTS = (bot1, bot2, bot3, bot4)


def parse(picture):
    """Turn rows of '.'/'#' into a square grid; letters mark named open cells."""
    rows = [line.strip() for line in picture.strip().splitlines()]
    # The project code assumes a square D x D grid, so pad with walls.
    side = max(len(rows), max(len(row) for row in rows))
    rows = [row.ljust(side, "#") for row in rows] + ["#" * side] * (side - len(rows))
    grid = [[ch != "#" for ch in row] for row in rows]
    marks = {ch: (r, c) for r, row in enumerate(rows) for c, ch in enumerate(row)
             if ch not in ".#"}
    return grid, marks


def open_cells(grid):
    return [(r, c) for r, row in enumerate(grid) for c, is_open in enumerate(row) if is_open]


def is_step(a, b):
    return abs(a[0] - b[0]) + abs(a[1] - b[1]) == 1


# --------------------------------------------------------------------------
class ShipTests(unittest.TestCase):
    def test_grid_is_square(self):
        for size in (3, 4, 10, 25):
            grid = generate_ship(size, seed=1)
            self.assertEqual(len(grid), size)
            self.assertTrue(all(len(row) == size for row in grid))

    def test_same_seed_same_ship_and_different_seed_differs(self):
        self.assertEqual(generate_ship(20, seed=3), generate_ship(20, seed=3))
        self.assertNotEqual(generate_ship(20, seed=3), generate_ship(20, seed=4))

    def test_every_open_cell_is_reachable(self):
        for seed in range(25):
            grid = generate_ship(15, seed=seed)
            cells = open_cells(grid)
            seen, queue = {cells[0]}, deque([cells[0]])
            while queue:
                cell = queue.popleft()
                for nxt in neighbors(*cell, 15):
                    if grid[nxt[0]][nxt[1]] and nxt not in seen:
                        seen.add(nxt)
                        queue.append(nxt)
            self.assertEqual(len(seen), len(cells), f"seed {seed} is disconnected")

    def test_has_room_for_bot_button_and_fire(self):
        for seed in range(25):
            self.assertGreaterEqual(len(open_cells(generate_ship(5, seed=seed))), 3)

    def test_smallest_ship_opens_its_only_interior_cell(self):
        self.assertTrue(generate_ship(3, seed=0)[1][1])

    def test_dead_end_opening_creates_loops(self):
        # Before dead ends are opened the ship is a tree (cells - 1 corridors
        # between cells). Opening dead ends must add extra connections.
        for seed in range(10):
            grid = generate_ship(20, seed=seed)
            cells = open_cells(grid)
            links = sum(grid[n[0]][n[1]] for cell in cells for n in neighbors(*cell, 20)) // 2
            self.assertGreater(links, len(cells) - 1, f"seed {seed} has no loops")

    def test_neighbors_are_orthogonal_and_in_bounds(self):
        self.assertEqual(set(neighbors(0, 0, 3)), {(1, 0), (0, 1)})
        self.assertEqual(set(neighbors(1, 1, 3)), {(0, 1), (2, 1), (1, 0), (1, 2)})
        self.assertEqual(set(neighbors(2, 2, 3)), {(1, 2), (2, 1)})


# --------------------------------------------------------------------------
class FireTests(unittest.TestCase):
    def setUp(self):
        self.open3 = [[True] * 3 for _ in range(3)]

    def test_q_zero_never_spreads(self):
        fire = {(1, 1)}
        for _ in range(50):
            fire = spread_fire(self.open3, fire, 0, random.Random(0))
        self.assertEqual(fire, {(1, 1)})

    def test_q_one_ignites_every_open_neighbor_but_not_diagonals(self):
        result = spread_fire(self.open3, {(1, 1)}, 1, random.Random(0))
        self.assertEqual(result, {(1, 1), (0, 1), (2, 1), (1, 0), (1, 2)})

    def test_fire_does_not_enter_or_cross_walls(self):
        grid, marks = parse("""
            F#.
            ##.
            ...
        """)
        fire = {marks["F"]}
        for _ in range(10):
            fire = spread_fire(grid, fire, 1, random.Random(0))
        self.assertEqual(fire, {marks["F"]})

    def test_update_is_simultaneous(self):
        # In a corridor at q=1 the fire moves exactly one cell per step. If
        # newly lit cells were used within the same step it would jump ahead.
        grid, _ = parse("......")
        fire = {(0, 0)}
        for step in range(1, 6):
            fire = spread_fire(grid, fire, 1, random.Random(0))
            self.assertEqual(fire, {(0, c) for c in range(step + 1)})

    def test_burning_cells_stay_burning(self):
        grid = generate_ship(12, seed=2)
        rng = random.Random(5)
        fire = {open_cells(grid)[0]}
        for _ in range(40):
            new_fire = spread_fire(grid, fire, 0.4, rng)
            self.assertTrue(fire <= new_fire)
            self.assertTrue(all(grid[r][c] for r, c in new_fire))
            fire = new_fire

    def test_input_set_is_not_modified(self):
        fire = {(1, 1)}
        spread_fire(self.open3, fire, 1, random.Random(0))
        self.assertEqual(fire, {(1, 1)})

    def test_button_never_burns_but_its_neighbors_do(self):
        fire = {(1, 0)}
        for _ in range(10):
            fire = spread_fire(self.open3, fire, 1, random.Random(0), button=(1, 1))
        self.assertEqual(fire, set(open_cells(self.open3)) - {(1, 1)})

    def test_ignition_chance_matches_formula(self):
        # (1, 1) has K burning neighbors; it should light with 1 - (1 - q)^K.
        q, samples, rng = 0.3, 20000, random.Random(11)
        burning = [(0, 1), (1, 0), (1, 2), (2, 1)]
        for k in range(1, 5):
            fire = set(burning[:k])
            hits = sum((1, 1) in spread_fire(self.open3, fire, q, rng) for _ in range(samples))
            self.assertAlmostEqual(hits / samples, 1 - (1 - q) ** k, delta=0.015, msg=f"K={k}")

    def test_invalid_q_is_rejected(self):
        for q in (-0.1, 1.1):
            with self.assertRaises(ValueError):
                spread_fire(self.open3, {(1, 1)}, q)


# --------------------------------------------------------------------------
class BfsTests(unittest.TestCase):
    def test_start_equals_goal(self):
        self.assertEqual(bfs([[True]], (0, 0), (0, 0)), [(0, 0)])

    def test_path_is_shortest_and_made_of_single_steps(self):
        grid, m = parse("""
            S....
            .###.
            ....G
        """)
        path = bfs(grid, m["S"], m["G"])
        self.assertEqual((path[0], path[-1]), (m["S"], m["G"]))
        self.assertEqual(len(path) - 1, 6)
        self.assertTrue(all(is_step(a, b) for a, b in zip(path, path[1:])))

    def test_walls_can_make_the_goal_unreachable(self):
        grid, m = parse("""
            S#G
            .#.
        """)
        self.assertIsNone(bfs(grid, m["S"], m["G"]))

    def test_forbidden_cells_force_a_detour_or_block_entirely(self):
        grid, m = parse("""
            S.G
            ...
        """)
        self.assertEqual(len(bfs(grid, m["S"], m["G"], {(0, 1)})) - 1, 4)
        self.assertIsNone(bfs(grid, m["S"], m["G"], {(0, 1), (1, 1)}))

    def test_forbidden_goal_has_no_path(self):
        grid, _ = parse("...")
        self.assertIsNone(bfs(grid, (0, 0), (0, 2), {(0, 2)}))

    def test_start_may_be_forbidden(self):
        grid, _ = parse("...")
        self.assertEqual(bfs(grid, (0, 0), (0, 2), {(0, 0)}), [(0, 0), (0, 1), (0, 2)])

    def test_matches_brute_force_distance_on_random_ships(self):
        for seed in range(10):
            grid = generate_ship(12, seed=seed)
            start, goal = random.Random(seed).sample(open_cells(grid), 2)
            dist, queue = {start: 0}, deque([start])
            while queue:
                cell = queue.popleft()
                for nxt in neighbors(*cell, 12):
                    if grid[nxt[0]][nxt[1]] and nxt not in dist:
                        dist[nxt] = dist[cell] + 1
                        queue.append(nxt)
            self.assertEqual(len(bfs(grid, start, goal)) - 1, dist[goal])


# --------------------------------------------------------------------------
class BotTests(unittest.TestCase):
    def test_bot1_plans_once_and_ignores_later_fire(self):
        grid = [[True] * 5 for _ in range(5)]
        state = {}
        first = bot1(grid, (0, 0), (0, 4), {(2, 4)}, 0.5, state)
        plan = list(state["plan"])
        self.assertEqual(first, plan[1])
        # The fire now covers the next cell of the plan; Bot 1 walks in anyway.
        self.assertEqual(bot1(grid, first, (0, 4), {(2, 4), plan[2]}, 0.5, state), plan[2])

    def test_bot1_avoids_the_initial_fire_cell(self):
        grid, m = parse("""
            SF.G
            ....
        """)
        bot1(grid, m["S"], m["G"], {m["F"]}, 0.5, state := {})
        self.assertNotIn(m["F"], state["plan"])
        self.assertEqual(len(state["plan"]) - 1, 5)

    def test_bots_stay_put_when_fire_blocks_the_only_route(self):
        grid, m = parse("S.F.G")
        for bot_fn in ALL_BOTS:
            with self.subTest(bot=bot_fn.__name__):
                self.assertEqual(bot_fn(grid, m["S"], m["G"], {m["F"]}, 0.5, {}), m["S"])

    def test_bot2_reroutes_around_new_fire(self):
        grid, m = parse("""
            S.x.G
            .....
        """)
        self.assertEqual(bot2(grid, m["S"], m["G"], set(), 0.5, {}), (0, 1))
        # With (0, 1) burning the only safe first step is down.
        self.assertEqual(bot2(grid, m["S"], m["G"], {(0, 1)}, 0.5, {}), (1, 0))

    def test_bot3_keeps_a_one_cell_buffer_when_it_can(self):
        # (1, 2) is on the direct route and next to the fire. Bot 2 walks
        # through it (4 steps); Bot 3 goes around through row 0 (6 steps).
        grid, m = parse("""
            .....
            S...G
            ..F..
            .....
            .....
        """)

        def walk(bot_fn):
            position, visited = m["S"], []
            while position != m["G"] and len(visited) < 20:
                position = bot_fn(grid, position, m["G"], {m["F"]}, 0.5, {})
                visited.append(position)
            return visited

        self.assertEqual(walk(bot2), [(1, 1), (1, 2), (1, 3), (1, 4)])
        self.assertEqual(len(walk(bot3)), 6)
        self.assertNotIn((1, 2), walk(bot3))

    def test_bot3_falls_back_to_plain_shortest_path(self):
        # One corridor, fire next to it: no buffered route exists, so Bot 3
        # must still advance exactly like Bot 2 instead of freezing.
        grid, m = parse("""
            S...G
            ##F##
        """)
        args = (grid, m["S"], m["G"], {m["F"]}, 0.5)
        self.assertEqual(bot3(*args, {}), (0, 1))
        self.assertEqual(bot3(*args, {}), bot2(*args, {}))

    def test_bot3_still_enters_a_button_that_is_next_to_fire(self):
        grid, m = parse("S.GF")
        self.assertEqual(bot3(grid, (0, 1), m["G"], {m["F"]}, 0.5, {}), m["G"])

    def test_bot4_weighs_fire_risk_against_path_length(self):
        # Short route: straight along row 1 (6 steps), passing right under the
        # fire. Long route: down and around through row 4 (12 steps).
        grid, m = parse("""
            ###F###
            S.....G
            .#####.
            .#####.
            .......
        """)
        args = (grid, m["S"], m["G"], {m["F"]})
        # Bot 2 only sees that the short route is not burning yet.
        self.assertEqual(bot2(*args, 0.9, {}), (1, 1))
        # Bot 4 expects a fast fire to cut the short route, so it goes around...
        self.assertEqual(bot4(*args, 0.9, {}), (2, 0))
        # ...but takes the short route when the fire cannot spread at all.
        self.assertEqual(bot4(*args, 0, {}), (1, 1))

    def test_bot4_long_way_round_survives_and_is_not_slower_than_backtracking(self):
        # Same ship. Bot 2 starts down the short route, gets cut off and has to
        # turn back; Bot 4 commits to the long route from the first step.
        grid, m = parse("""
            ###F###
            S.....G
            .#####.
            .#####.
            .......
        """)
        for seed in range(30):
            outcome4, steps4 = run_trial(bot4, grid, m["S"], m["G"], {m["F"]}, 0.9, seed)
            outcome2, steps2 = run_trial(bot2, grid, m["S"], m["G"], {m["F"]}, 0.9, seed)
            self.assertEqual((outcome4, steps4), ("success", 12), f"seed {seed}")
            if outcome2 == "success" and steps2 > 6:
                self.assertGreater(steps2, steps4, f"seed {seed}")

    def test_bot4_never_steps_into_fire_even_when_doomed(self):
        grid, m = parse("""
            FFF
            FS.
            FFG
        """)
        fire = {cell for cell in open_cells(grid) if cell not in (m["S"], m["G"], (1, 2))}
        self.assertEqual(bot4(grid, m["S"], m["G"], fire, 1, {}), (1, 2))

    def test_every_move_is_legal_on_random_ships(self):
        # A legal move is: stay, or step to an adjacent open cell. Bots 2-4 must
        # also never choose a cell that is burning when they decide.
        for seed in range(12):
            grid = generate_ship(14, seed=seed)
            start, button, fire0 = random.Random(seed).sample(open_cells(grid), 3)
            for bot_fn in ALL_BOTS:
                rng = random.Random(seed)
                position, fire, state = start, {fire0}, {}
                for _ in range(200):
                    move = bot_fn(grid, position, button, fire, 0.35, state)
                    label = f"{bot_fn.__name__} seed {seed}"
                    self.assertTrue(move == position or is_step(move, position), label)
                    self.assertTrue(grid[move[0]][move[1]], label)
                    if bot_fn is not bot1:
                        self.assertNotIn(move, fire - {position}, label)
                    position = move
                    if position == button or position in fire:
                        break
                    fire = spread_fire(grid, fire, 0.35, rng, button=button)
                    if position in fire:
                        break

    def test_bots_do_not_modify_the_grid_or_fire(self):
        grid = generate_ship(10, seed=1)
        start, button, fire0 = random.Random(1).sample(open_cells(grid), 3)
        snapshot, fire = [row[:] for row in grid], {fire0}
        for bot_fn in ALL_BOTS:
            bot_fn(grid, start, button, fire, 0.5, {})
        self.assertEqual(grid, snapshot)
        self.assertEqual(fire, {fire0})


# --------------------------------------------------------------------------
class SimulatorTests(unittest.TestCase):
    def test_start_on_button_or_in_fire(self):
        grid, _ = parse("...")
        self.assertEqual(run_trial(bot2, grid, (0, 0), (0, 0), {(0, 2)}, 1, 0), ("success", 0))
        self.assertEqual(run_trial(bot2, grid, (0, 0), (0, 2), {(0, 0)}, 1, 0), ("burned", 0))

    def test_invalid_arguments_are_rejected(self):
        grid, _ = parse("...")
        with self.assertRaises(ValueError):
            run_trial(bot2, grid, (0, 0), (0, 2), {(0, 1)}, 1.5, 0)
        with self.assertRaises(ValueError):
            run_trial(bot2, grid, (0, 0), (0, 2), {(0, 1)}, 0.5, 0, max_steps=-1)

    def test_zero_steps_allowed_is_a_timeout(self):
        grid = [[True] * 3 for _ in range(3)]
        self.assertEqual(run_trial(bot2, grid, (0, 0), (2, 2), {(0, 2)}, 0, 0, 0), ("timeout", 0))

    def test_button_press_wins_even_as_fire_arrives(self):
        # The bot reaches the button on the same turn the fire would reach it;
        # the press comes first in the turn order, so this is a success.
        grid, m = parse("S.G.F")
        for bot_fn in ALL_BOTS:
            with self.subTest(bot=bot_fn.__name__):
                self.assertEqual(run_trial(bot_fn, grid, m["S"], m["G"], {m["F"]}, 1, 0),
                                 ("success", 2))

    def test_fireproof_button_shields_a_corridor(self):
        # The fire is closer to the button than the bot is, but the button
        # cannot burn, so in a corridor the fire cannot get past it.
        grid, m = parse("S...G.F")
        for bot_fn in ALL_BOTS:
            with self.subTest(bot=bot_fn.__name__):
                self.assertEqual(run_trial(bot_fn, grid, m["S"], m["G"], {m["F"]}, 1, 0),
                                 ("success", 4))

    def test_fire_between_bot_and_button_is_fatal_in_a_corridor(self):
        grid, m = parse("S.....F.G")
        for bot_fn in ALL_BOTS:
            with self.subTest(bot=bot_fn.__name__):
                self.assertEqual(run_trial(bot_fn, grid, m["S"], m["G"], {m["F"]}, 1, 0)[0],
                                 "burned")

    def test_button_cell_never_burns_during_a_trial(self):
        grid = [[True] * 4 for _ in range(4)]
        seen = []

        def watcher(grid, bot, button, fire, q, state):
            seen.append(button in fire)
            return bot

        run_trial(watcher, grid, (3, 3), (0, 0), {(0, 1)}, 1, 0, 3)
        self.assertEqual(seen, [False, False, False])

    def test_fire_spreads_only_after_the_bot_moves(self):
        grid, _ = parse(".....")
        seen = []

        def watcher(grid, bot, button, fire, q, state):
            seen.append(len(fire))
            return bot

        run_trial(watcher, grid, (0, 0), (0, 1), {(0, 4)}, 1, 0, 2)
        self.assertEqual(seen, [1, 2])

    def test_no_fire_spread_means_every_bot_succeeds_in_shortest_time(self):
        for seed in range(8):
            grid = generate_ship(14, seed=seed)
            start, button, fire0 = random.Random(seed).sample(open_cells(grid), 3)
            shortest = bfs(grid, start, button, {fire0})
            if shortest is None:
                continue
            for bot_fn in (bot1, bot2, bot4):
                with self.subTest(bot=bot_fn.__name__, seed=seed):
                    self.assertEqual(run_trial(bot_fn, grid, start, button, {fire0}, 0, seed),
                                     ("success", len(shortest) - 1))
            self.assertEqual(run_trial(bot3, grid, start, button, {fire0}, 0, seed)[0], "success")

    def test_all_bots_face_the_same_fire(self):
        grid = generate_ship(12, seed=4)
        start, button, fire0 = random.Random(4).sample(open_cells(grid), 3)
        histories = []
        for mover in (lambda *a: a[1], bot2):
            history = []

            def recorder(grid, bot, button, fire, q, state, mover=mover):
                history.append(frozenset(fire))
                return mover(grid, bot, button, fire, q, state)

            run_trial(recorder, grid, start, button, {fire0}, 0.3, 9, 30)
            histories.append(history)
        shared = min(len(h) for h in histories)
        self.assertGreater(shared, 1)
        self.assertEqual(histories[0][:shared], histories[1][:shared])

    def test_repeated_trials_give_identical_results(self):
        grid = generate_ship(14, seed=6)
        start, button, fire0 = random.Random(6).sample(open_cells(grid), 3)
        for bot_fn in ALL_BOTS:
            args = (bot_fn, grid, start, button, {fire0}, 0.4, 21)
            self.assertEqual(run_trial(*args), run_trial(*args))


if __name__ == "__main__":
    unittest.main()
