import random

# build reproducible connected maze-like ship layouts for the simulator
# Row/column offsets for the four non-diagonal neighboring cells.
DIRECTIONS = ((1, 0), (-1, 0), (0, 1), (0, -1))

def neighbors(row, column, size):
    # yield every in-bounds up, down, left, and right neighbor
    for row_offset, column_offset in DIRECTIONS:
        # Apply one direction offset to the current cell.
        neighbor_row = row + row_offset
        neighbor_column = column + column_offset

        # Ignore neighbors outside the square grid.
        if 0 <= neighbor_row < size and 0 <= neighbor_column < size:
            yield neighbor_row, neighbor_column

def generate_ship(size, seed=None):
    # return a square Boolean grid where True means an open cell
    # Keep all randomness local so the optional seed gives repeatable ships.
    randomizer = random.Random(seed)

    # The finished grid starts completely blocked.
    open_cells = [[False] * size for _ in range(size)]

    # Store how many open neighbors each cell currently has.
    open_neighbor_count = [[0] * size for _ in range(size)]

    # Keep blocked cells with exactly one open neighbor ready to be opened.
    frontier = []

    # Map each frontier cell to its list index for fast removal.
    frontier_index = {}

    def add_to_frontier(cell):
        # Record the cell's position before adding it to the end of the list.
        frontier_index[cell] = len(frontier)
        frontier.append(cell)

    def remove_from_frontier(cell):
        # Find and forget the index of the cell being removed.
        index = frontier_index.pop(cell)

        # Remove the final item, then use it to fill any gap in the list.
        last_cell = frontier.pop()
        if index < len(frontier):
            frontier[index] = last_cell
            frontier_index[last_cell] = index

    def open_cell(row, column):
        # Mark the selected cell as part of the ship.
        open_cells[row][column] = True

        # It cannot remain a frontier cell now that it is open.
        if (row, column) in frontier_index:
            remove_from_frontier((row, column))

        # Update the open-neighbor count for every cell next to it.
        for neighbor_row, neighbor_column in neighbors(row, column, size):
            open_neighbor_count[neighbor_row][neighbor_column] += 1

            # Only blocked cells can join or leave the frontier.
            if not open_cells[neighbor_row][neighbor_column]:
                neighbor = (neighbor_row, neighbor_column)

                # One open neighbor makes this cell eligible for maze growth.
                if open_neighbor_count[neighbor_row][neighbor_column] == 1:
                    add_to_frontier(neighbor)

                # Two open neighbors would create a loop, so remove it.
                elif (
                    open_neighbor_count[neighbor_row][neighbor_column] == 2
                    and neighbor in frontier_index
                ):
                    remove_from_frontier(neighbor)

    # Start from one random interior cell, leaving the initial border untouched.
    open_cell(randomizer.randrange(1, size - 1), randomizer.randrange(1, size - 1))

    # Repeatedly open a random eligible cell to grow one connected maze.
    while frontier:
        open_cell(*randomizer.choice(frontier))

    def is_dead_end(row, column):
        # A dead end is an open cell with only one open neighbor.
        return open_cells[row][column] and open_neighbor_count[row][column] == 1

    # Collect dead ends before changing the maze in the second phase.
    dead_ends = [
        (row, column)
        for row in range(size)
        for column in range(size)
        if is_dead_end(row, column)
    ]

    # Track the original and current number of dead ends.
    initial_dead_end_count = dead_end_count = len(dead_ends)

    # Process dead ends in a random order.
    randomizer.shuffle(dead_ends)

    for row, column in dead_ends:
        # Stop after removing at least half of the original dead ends.
        if dead_end_count <= initial_dead_end_count / 2:
            break

        # Earlier openings may already have removed this dead end.
        if not is_dead_end(row, column):
            continue

        # Pick one blocked neighbor of the dead end to open.
        closed_neighbors = [
            cell
            for cell in neighbors(row, column, size)
            if not open_cells[cell[0]][cell[1]]
        ]
        wall_row, wall_column = randomizer.choice(closed_neighbors)

        # Only this wall and its neighbors can gain or lose dead-end status.
        affected_cells = [(wall_row, wall_column)] + list(
            neighbors(wall_row, wall_column, size)
        )

        # Count local dead ends before and after opening the wall.
        dead_ends_before = sum(is_dead_end(*cell) for cell in affected_cells)
        open_cell(wall_row, wall_column)
        dead_end_count += (
            sum(is_dead_end(*cell) for cell in affected_cells) - dead_ends_before
        )

    # Return the completed Boolean grid.
    return open_cells


def show(grid):
    # print open cells as dots and blocked cells as number signs
    for row in grid:
        print("".join("·" if cell else "█" for cell in row))


if __name__ == "__main__":
    # Generate and print one reproducible example when this file is run directly.
    ship = generate_ship(20, seed=1)
    show(ship)
