from collections import deque

from ship import neighbors


def bfs(grid, start, goal, forbidden=frozenset()):
    """Shortest path from start to goal over open cells, avoiding `forbidden`.

    grid:      D x D list of bools (True = open)
    start:     (r, c)
    goal:      (r, c)
    forbidden: set of (r, c) cells that may not be entered

    Returns the path as a list of cells [start, ..., goal], or None if the
    goal is unreachable. The start cell is always allowed, even if forbidden.
    """
    D = len(grid)
    if start == goal:
        return [start]
    if goal in forbidden:
        return None

    parent = {start: None}
    queue = deque([start])
    while queue:
        cell = queue.popleft()
        for nxt in neighbors(cell[0], cell[1], D):
            if nxt in parent or not grid[nxt[0]][nxt[1]] or nxt in forbidden:
                continue
            parent[nxt] = cell
            if nxt == goal:  # first discovery is the shortest in BFS
                path = [nxt]
                while parent[path[-1]] is not None:
                    path.append(parent[path[-1]])
                return path[::-1]
            queue.append(nxt)
    return None


if __name__ == "__main__":
    import random
    from ship import generate_ship

    D = 20          # change this to try bigger ships
    SEED = 7

    ship = generate_ship(D, seed=SEED)
    rng = random.Random(SEED)
    cells = [(r, c) for r in range(D) for c in range(D) if ship[r][c]]
    bot, button, fire = rng.sample(cells, 3)

    # --- ship info ---
    print(f"Ship: {D} x {D} grid, {len(cells)} open cells, {D * D - len(cells)} blocked")
    print(f"Bot start    (row, col): {bot}")
    print(f"Button       (row, col): {button}")
    print(f"Fire start   (row, col): {fire}")
    print()

    # --- map: # = wall, . = open, B = bot, X = button, F = fire ---
    if D <= 20:
        marks = {bot: "B", button: "X", fire: "F"}
        for r in range(D):
            print("".join(marks.get((r, c), "." if ship[r][c] else "#") for c in range(D)))
        print()

    # --- paths ---
    p_free = bfs(ship, bot, button)
    p_avoid = bfs(ship, bot, button, forbidden={fire})
    print("no forbidden :", len(p_free) - 1, "steps")
    print("   path      :", p_free)
    if p_avoid is None:
        print("avoid fire   : no path (the fire cell blocks the only route)")
    else:
        print("avoid fire   :", len(p_avoid) - 1, "steps")
        print("   path      :", p_avoid)

    assert p_free[0] == bot and p_free[-1] == button
    assert all(abs(a[0] - b[0]) + abs(a[1] - b[1]) == 1 for a, b in zip(p_free, p_free[1:]))
    assert p_avoid is None or fire not in p_avoid
    print("ok")