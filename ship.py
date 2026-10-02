import random

DIRECTIONS = ((1, 0), (-1, 0), (0, 1), (0, -1))


def neighbors(row, column, size):
    for row_offset, column_offset in DIRECTIONS:
        neighbor_row = row + row_offset
        neighbor_column = column + column_offset
        if 0 <= neighbor_row < size and 0 <= neighbor_column < size:
            yield neighbor_row, neighbor_column


def generate_ship(size, seed=None):
    """Return a square Boolean grid where True means an open cell."""
    randomizer = random.Random(seed)
    open_cells = [[False] * size for _ in range(size)]
    open_neighbor_count = [[0] * size for _ in range(size)]
    frontier = []
    frontier_index = {}

    def add_to_frontier(cell):
        frontier_index[cell] = len(frontier)
        frontier.append(cell)

    def remove_from_frontier(cell):
        index = frontier_index.pop(cell)
        last_cell = frontier.pop()
        if index < len(frontier):
            frontier[index] = last_cell
            frontier_index[last_cell] = index

    def open_cell(row, column):
        open_cells[row][column] = True
        if (row, column) in frontier_index:
            remove_from_frontier((row, column))

        for neighbor_row, neighbor_column in neighbors(row, column, size):
            open_neighbor_count[neighbor_row][neighbor_column] += 1
            if not open_cells[neighbor_row][neighbor_column]:
                neighbor = (neighbor_row, neighbor_column)
                if open_neighbor_count[neighbor_row][neighbor_column] == 1:
                    add_to_frontier(neighbor)
                elif (
                    open_neighbor_count[neighbor_row][neighbor_column] == 2
                    and neighbor in frontier_index
                ):
                    remove_from_frontier(neighbor)

    # Grow a connected maze.
    open_cell(randomizer.randrange(1, size - 1), randomizer.randrange(1, size - 1))
    while frontier:
        open_cell(*randomizer.choice(frontier))

    def is_dead_end(row, column):
        return open_cells[row][column] and open_neighbor_count[row][column] == 1

    # Open walls near dead ends until at least half are removed.
    dead_ends = [
        (row, column)
        for row in range(size)
        for column in range(size)
        if is_dead_end(row, column)
    ]
    initial_dead_end_count = dead_end_count = len(dead_ends)
    randomizer.shuffle(dead_ends)

    for row, column in dead_ends:
        if dead_end_count <= initial_dead_end_count / 2:
            break
        if not is_dead_end(row, column):
            continue
        closed_neighbors = [
            cell
            for cell in neighbors(row, column, size)
            if not open_cells[cell[0]][cell[1]]
        ]
        wall_row, wall_column = randomizer.choice(closed_neighbors)
        affected_cells = [(wall_row, wall_column)] + list(
            neighbors(wall_row, wall_column, size)
        )
        dead_ends_before = sum(is_dead_end(*cell) for cell in affected_cells)
        open_cell(wall_row, wall_column)
        dead_end_count += (
            sum(is_dead_end(*cell) for cell in affected_cells) - dead_ends_before
        )

    return open_cells


def show(grid):
    for row in grid:
        print("".join("." if cell else "#" for cell in row))


if __name__ == "__main__":
    ship = generate_ship(25, seed=1)
    show(ship)
