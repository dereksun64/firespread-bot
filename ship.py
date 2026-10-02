import random

DIRS = ((1, 0), (-1, 0), (0, 1), (0, -1))


def neighbors(r, c, D):
    for dr, dc in DIRS:
        nr, nc = r + dr, c + dc
        if 0 <= nr < D and 0 <= nc < D:
            yield nr, nc


def generate_ship(D, seed=None):
    """Return a D x D grid of bools (True = open), built per the spec.

    Phase 1 grows a tree: repeatedly open a random blocked cell with exactly
    one open neighbor. We keep a running open-neighbor count per cell and a
    'frontier' list of blocked cells whose count is exactly 1, so each step
    is O(1) instead of rescanning the grid.
    Phase 2 removes dead ends until at least half are gone.
    """
    rng = random.Random(seed)
    opn = [[False] * D for _ in range(D)]
    cnt = [[0] * D for _ in range(D)]  # open neighbors of each cell
    frontier, pos = [], {}              # list + index map = O(1) random removal

    def f_add(cell):
        pos[cell] = len(frontier)
        frontier.append(cell)

    def f_remove(cell):
        i = pos.pop(cell)
        last = frontier.pop()
        if i < len(frontier):
            frontier[i] = last
            pos[last] = i

    def open_cell(r, c):
        opn[r][c] = True
        if (r, c) in pos:
            f_remove((r, c))
        for nr, nc in neighbors(r, c, D):
            cnt[nr][nc] += 1
            if not opn[nr][nc]:
                if cnt[nr][nc] == 1:
                    f_add((nr, nc))
                elif cnt[nr][nc] == 2 and (nr, nc) in pos:
                    f_remove((nr, nc))

    # Phase 1: grow the maze from a random interior cell
    open_cell(rng.randrange(1, D - 1), rng.randrange(1, D - 1))
    while frontier:
        open_cell(*rng.choice(frontier))

    # Phase 2: open a closed neighbor of random dead ends
    def is_dead(r, c):
        return opn[r][c] and cnt[r][c] == 1

    dead = [(r, c) for r in range(D) for c in range(D) if is_dead(r, c)]
    initial = n_dead = len(dead)
    rng.shuffle(dead)
    for r, c in dead:
        if n_dead <= initial / 2:
            break
        if not is_dead(r, c):  # an earlier opening already fixed it
            continue
        a, b = rng.choice([(a, b) for a, b in neighbors(r, c, D) if not opn[a][b]])
        affected = [(a, b)] + list(neighbors(a, b, D))
        before = sum(is_dead(*x) for x in affected)
        open_cell(a, b)
        n_dead += sum(is_dead(*x) for x in affected) - before

    return opn


def show(opn):
    for row in opn:
        print("".join("." if x else "#" for x in row))


if __name__ == "__main__":
    ship = generate_ship(25, seed=1)
    show(ship)
