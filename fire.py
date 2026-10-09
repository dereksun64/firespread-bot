# fire-spread rules for the ship simulation

import random

from ship import neighbors


def spread_fire(open_cells, fire_cells, q, randomizer=None, button=None):
    # return the set of burning cells after one simultaneous fire step
    # the button cell (if given) can never catch fire. Its open neighbors burn
    # normally, so the fire can still surround the button and cut it off
    if not 0 <= q <= 1:
        raise ValueError("q must be between 0 and 1")

    if randomizer is None:
        randomizer = random.Random()

    size = len(open_cells)
    # read from this snapshot throughout the loop so all new ignitions happen
    # simultaneously; a cell ignited this turn cannot ignite another cell yet
    current_fire_cells = set(fire_cells)
    next_fire_cells = set(current_fire_cells)

    for row in range(size):
        for column in range(size):
            if (not open_cells[row][column]
                    or (row, column) in current_fire_cells
                    or (row, column) == button):
                continue

            burning_neighbor_count = sum(
                (neighbor_row, neighbor_column) in current_fire_cells
                for neighbor_row, neighbor_column in neighbors(row, column, size)
            )
            # a cell avoids ignition only if every burning neighbor fails to
            # ignite it, which gives 1 - (1 - q)^K for K burning neighbors
            ignition_chance = 1 - (1 - q) ** burning_neighbor_count

            if randomizer.random() < ignition_chance:
                next_fire_cells.add((row, column))

    return next_fire_cells
