import math
import copy
import numpy as np

difficulty = "easy"
sudoku_index = 7

# Load sudokus
sudoku = np.load(f"../data/{difficulty}_puzzle.npy")
print(f"{difficulty}_puzzle.npy has been loaded into the variable sudoku")
print(f"sudoku.shape: {sudoku.shape}, sudoku[0].shape: {sudoku[sudoku_index].shape}, sudoku.dtype: {sudoku.dtype}")

# Load solutions for demonstration
solutions = np.load(f"../data/{difficulty}_solution.npy")
print()

# # Print the first 9x9 sudoku...
print("First sudoku:")
print(sudoku[sudoku_index], "\n")

#
# ...and its solution
print("Solution of first sudoku:")
print(solutions[sudoku_index])


class SudokuSolver:
    def __init__(self, board):
        """
        setups board, 3D-list for possible values
        :param board:
        """
        self.impossible = np.full((9, 9), -1, dtype=int)
        self.final_board = board
        # possible_values represents constraints. Allocate array or 1..9 for all cells (assume every value is possible in every cell)
        self.possible_values = [[[i for i in range(1, 10)] for _ in range(9)] for _ in range(9)]

    def setup(self):
        """
        Will setup the constraints array. Fairly naive; removes numbers that appear in the same row, column and 3x3 square
        """
        for row in range(9):
            for column in range(9):
                if self.final_board[row, column] != 0:
                    if self.valid_move(row, column, self.final_board[row, column]):
                        self.possible_values[row][column] = [self.final_board[row][column]]
                    else:
                        self.possible_values[row][column] = []
                else:
                    # Get unique values from column, remove all from current cell.possible_values
                    for i in np.unique(self.final_board[:, column]):
                        if i in self.possible_values[row][column]:
                            self.possible_values[row][column].remove(i)
                    # same for row
                    for i in np.unique(self.final_board[row, :]):
                        if i in self.possible_values[row][column]:
                            self.possible_values[row][column].remove(i)
                    # same for 3x3 square
                    for i in np.unique(self.final_board[math.floor(row / 3) * 3:math.floor(row / 3) * 3 + 3,
                                       math.floor(column / 3) * 3:math.floor(column / 3) * 3 + 3]):
                        if i in self.possible_values[row][column]:
                            self.possible_values[row][column].remove(i)

        if self.is_invalid():
            self.final_board = self.impossible

    def is_goal(self):
        """
        Will return true if no 0's occur in board (and its not a -1 board).
        We know this must be goal as code would not let us put an invalid choice in a cell, meaning all inputs were valid,
        and no 0's = full board, hence goal is reached

        :return: True if we have completed the sudoku
        """
        return np.all(self.final_board) and -1 not in self.final_board

    def is_invalid(self):
        """
        Check if a -1 exists in the board, or if we run out of possible values for a cell.
        :return: True if above condition is met, else False
        """
        if any(any(len(x) == 0 for x in row) for row in self.possible_values) or -1 in self.final_board:
            return True
        return False

    def get_possible_values(self, row, column):
        """
        Get a copy of the possible values for a given cell
        :param row: row index (0..8)
        :param column: column index (0..8)
        :return: A copy of all potential values at given cell
        """
        if not (0 <= row <= 8 or 0 <= column <= 8):
            raise ValueError(f"Invalid index for selecting row: {row} and column: {column}")

        return self.possible_values[row][column].copy()

    def get_singleton_cells(self):
        """
        Returns the row and column indexes which have no final value but exactly 1 possible value
        :return: Array containing the above. Order is left to right, top to bottom
        """
        out = []

        for row_index, row in enumerate(self.possible_values):
            for column_index, values in enumerate(row):
                if len(values) == 1 and self.final_board[row_index, column_index] == 0:
                    out.append((row_index, column_index))

        return out

    def valid_move(self, row_index, column_index, n):
        """
        Check if a value can be placed in desired cell
        :param row_index: row index (0..8)
        :param column_index: column index (0..8)
        :param n: value to test
        :return: True if valid slot for n, else False
        """

        # Check if the value occurs in the row or column
        for i in range(9):
            # Trigger if value already found in the row/column (and not currently looking at desired cell)
            if self.final_board[row_index, i] == n and i != column_index:
                return False
            if self.final_board[i, column_index] == n and i != row_index:
                return False

        # Check the 3x3 square
        low_horizontal = math.floor(column_index / 3) * 3
        low_vertical = math.floor(row_index / 3) * 3

        for i in range(low_vertical, low_vertical + 3):
            for j in range(low_horizontal, low_horizontal + 3):
                if self.final_board[row_index, i] == n and i != column_index and j != row_index:
                    return False

        return True

    def solve_naked_pairs(self):
        """
        A naked pair is a pair of identical cells in the same row, column, or square that contain exactly 2 options.
        Example: https://www.learn-sudoku.com/naked-pairs.html
        :return: no return
        """

        # rows
        for row_index, row in enumerate(self.possible_values):
            for i in range(0, len(row)):  # try to find identical cell in row
                for j in range(i + 1, len(row)):
                    if row[i] == row[j] and len(row[i]) == 2:
                        # Found a naked pair
                        # Go through row and remove both values from all cells (except naked pair calls)
                        for k in range(len(self.possible_values[row_index])):
                            if k == i or k == j:
                                continue
                            if row[i][0] in self.possible_values[row_index][k]:
                                self.possible_values[row_index][k].remove(row[i][0])
                            if row[i][1] in self.possible_values[row_index][k]:
                                self.possible_values[row_index][k].remove(row[i][1])
                            if self.is_invalid():  # return early if we've removed all possible values for a cell
                                # Could be done after outer-most loop,and does a lot of extra looping
                                # but after doing multiple tests, it has no measurable impact (+ve nor -ve).
                                return

        # columns (same algorithm as row)
        for col_index in range(len(self.possible_values)):
            # as possible values is not numpy array, no neat way to iterate over columns, this will suffice
            for j in range(len(self.possible_values[col_index])):
                for k in range(j + 1, len(self.possible_values[col_index])):
                    if self.possible_values[j][col_index] == self.possible_values[k][col_index] and len(
                            self.possible_values[k][col_index]) == 2:
                        for row_index in range(len(self.possible_values)):
                            if row_index == j or row_index == k:
                                continue
                            if self.possible_values[k][col_index][0] in self.possible_values[row_index][col_index]:
                                self.possible_values[row_index][col_index].remove(self.possible_values[k][col_index][0])
                            if self.possible_values[k][col_index][1] in self.possible_values[row_index][col_index]:
                                self.possible_values[row_index][col_index].remove(self.possible_values[k][col_index][1])
                            if self.is_invalid():
                                return

        # blocks (same algorithm as row)
        # Pre-define 3x3 square offsets, easier than writing complex maths function, as this program is only designed for 9x9 sudoku anyway
        indexes = [[0, 0], [0, 1], [0, 2], [1, 0], [1, 1], [1, 2], [2, 0], [2, 1], [2, 2]]
        for row in range(0, len(self.possible_values), 3):
            for column in range(0, len(self.possible_values), 3):
                for i in range(len(indexes)):
                    for j in range(i + 1, len(indexes)):
                        if self.possible_values[row + indexes[i][0]][column + indexes[i][1]] == \
                                self.possible_values[row + indexes[j][0]][column + indexes[j][1]] and \
                                len(self.possible_values[row + indexes[i][0]][column + indexes[i][1]]) == 2:
                            for x, y in indexes:
                                if (x == indexes[i][0] and y == indexes[i][1]) or (
                                        x == indexes[j][0] and y == indexes[j][1]):
                                    continue
                                if self.possible_values[row + indexes[i][0]][column + indexes[i][1]][0] in \
                                        self.possible_values[row + x][column + y]:
                                    self.possible_values[row + x][column + y].remove(
                                        self.possible_values[row + indexes[i][0]][column + indexes[i][1]][0])
                                if self.possible_values[row + indexes[i][0]][column + indexes[i][1]][1] in \
                                        self.possible_values[row + x][column + y]:
                                    self.possible_values[row + x][column + y].remove(
                                        self.possible_values[row + indexes[i][0]][column + indexes[i][1]][1])
                                if self.is_invalid():
                                    return

    def set_value(self, row, column, value):
        """
        Function to place a value in a cell and update constraints in other cells, where appropriate.
        :param row: row index (0..8)
        :param column: column index (0..8)
        :param value: value to place into board
        :return: class (type: SudokuSolver) with updated board
        """

        if self.is_invalid():
            return self

        # can't place this value in cell as it is not in the possible values for this cell
        if value not in self.possible_values[row][column]:
            self.final_board = self.impossible
            return self

        # create a copy of self so as not to loose current state in case we need to roll back to it
        state = copy.deepcopy(self)

        # place value into cell, update possible_values
        state.possible_values[row][column] = [value]
        state.final_board[row, column] = value

        # Update the constraints for:
        # - row
        for y in range(len(state.possible_values)):
            if y == row:
                continue
            if state.final_board[y, column] == 0 and value in state.possible_values[y][column]:
                state.possible_values[y][column].remove(value)

        # - column
        for x in range(len(state.possible_values)):
            if x == column:
                continue
            if state.final_board[row, x] == 0 and value in state.possible_values[row][x]:
                state.possible_values[row][x].remove(value)

        # - square
        low_vertical = math.floor(row / 3) * 3
        low_horizontal = math.floor(column / 3) * 3

        for i in range(low_vertical, low_vertical + 3):
            for j in range(low_horizontal, low_horizontal + 3):
                if i == row and j == column:
                    continue
                if value in state.possible_values[i][j]:
                    state.possible_values[i][j].remove(value)

        # Hidden Singles
        # check for, and solve, any values that appear only once in a:
        # - square
        for v_low in range(0, len(state.possible_values), 3):
            for h_low in range(0, len(state.possible_values), 3):
                ls = [[] for _ in range(9)]
                for i in range(v_low, v_low + 3):
                    for j in range(h_low, h_low + 3):
                        for value in state.possible_values[i][j]:
                            # acts like a dictionary; counting occurrences of a value in a square by storing indexes
                            ls[value - 1].append((i, j))
                for k in range(len(ls)):
                    # if value only occurred once in square, and cell is currently unfilled (0), we found a hidden single
                    if len(ls[k]) == 1 and state.final_board[ls[k][0][0]][ls[k][0][1]] == 0:
                        state = state.set_value(ls[k][0][0], ls[k][0][1], k + 1)
                        if state.is_invalid():
                            state.final_board = state.impossible
                            return state

        # - row
        for row_index, row in enumerate(state.possible_values):
            ls = [[] for _ in range(9)]
            for column_index, column in enumerate(row):
                for value in column:
                    ls[value - 1].append((row_index, column_index))
            for i in range(len(ls)):
                if len(ls[i]) == 1 and state.final_board[ls[i][0][0]][ls[i][0][1]] == 0:
                    state = state.set_value(ls[i][0][0], ls[i][0][1], i + 1)
                    if state.is_invalid():
                        state.final_board = state.impossible
                        return state

        # - columns
        for i in range(len(state.possible_values)):
            ls = [[] for _ in range(9)]
            for j in range(len(state.possible_values[i])):
                for value in state.possible_values[j][i]:
                    ls[value - 1].append((j, i))
            for k in range(len(ls)):
                if len(ls[k]) == 1 and state.final_board[ls[k][0][0]][ls[k][0][1]] == 0:
                    state = state.set_value(ls[k][0][0], ls[k][0][1], k + 1)
                    if state.is_invalid():
                        state.final_board = state.impossible
                        return state

        state.solve_naked_pairs()

        if state.is_invalid():
            state.final_board = state.impossible
            return state

        # Insert values where we know there are no other possible values for that cell
        singleton_cells = state.get_singleton_cells()
        while len(singleton_cells) > 0:
            (singleton_row, singleton_column) = singleton_cells[0]
            state = state.set_value(singleton_row, singleton_column,
                                    state.possible_values[singleton_row][singleton_column][0])
            singleton_cells = state.get_singleton_cells()

        return state


def pick_next_cell(state):
    """
    Choose the best cell to try values on.
    :param state: A SudokuSolver class
    :return: A tuple of form (row, column) with index of the cell we should try values for
    """
    indexes = [[] for _ in range(9)]

    # Iterate over board, indexing each 0 cell in a list, based on the amount of possible values for that cell
    # e.g. for cell (1,1) with possible_values = [1,2,3], we set indexes[3] to be
    for index, row in enumerate(state.possible_values):
        for item_index, item in enumerate(row):
            if state.final_board[index, item_index] == 0:
                indexes[len(item)].append((index, item_index))

    out = None

    for item in indexes:
        if item != []:
            out = item
            break

    return out[0]


def order_values(state, index):
    """
    Order the possible values for a cell by certain set of rules.
    :param state: A SudokuSolver class
    :param index: A tuple of form (row, column) with index of the cell we are ordering values for
    :return: an array of values from possible_values of index
    """

    values = state.possible_values[index[0]][index[1]]

    # Create dictionary, keys will be values found at the index of possible_values.
    # Each item will be an array of length 3;
    # index 0 is count for the # of times the key occurs in the row, index 1 is column, 2 is square
    values_hash_rows = {}

    # We knw that a value must occur at least once in a row, column and square, given it was found in possible_values
    for value in values:
        values_hash_rows[value] = [1, 1, 1]

    # Row
    for row_index in range(len(state.possible_values)):
        if row_index == index[0]:
            continue
        for item in state.possible_values[row_index][index[1]]:
            if item in values_hash_rows.keys():
                values_hash_rows[item][0] += 1

    # column
    for column_index in range(len(state.possible_values)):
        if column_index == index[1]:
            continue
        for item in state.possible_values[index[0]][column_index]:
            if item in values_hash_rows.keys():
                values_hash_rows[item][1] += 1


    # square
    low_vertical = math.floor(index[0] / 3) * 3
    low_horizontal = math.floor(index[1] / 3) * 3

    for i in range(low_vertical, low_vertical + 3):
        for j in range(low_horizontal, low_horizontal + 3):
            if i == index[0] and j == index[1]:
                continue
            for item in state.possible_values[i][j]:
                if item in values_hash_rows.keys():
                    values_hash_rows[item][2] += 1

    # Overwrite dictionary keys with the new value being the minimum number of occurrences in a row, column or square
    for key, value in values_hash_rows.items():
        values_hash_rows[key] = min(value)

    # create list from dict, sort it by the number occurences for each value
    values, count = zip(*sorted(list(values_hash_rows.items()), key=lambda x: x[1]))

    return values


def depth_first_search(state):
    """
    Recursive function that implements a depth first search on sudoku, with help from constraint propagation.
    Based on function of same name from eight queens revisited notebook
    :param state: A SudokuSolver class
    :return: None if given sudoku has no solution, else returns a finished solution
    """
    if state.is_invalid():
        return None

    index = pick_next_cell(state)
    values = order_values(state, index)

    # if no values can go in the cell we choose, then sudoku is unsolvable
    for value in values:
        # Place value in cell
        new_state = state.set_value(index[0], index[1], value)
        if new_state.is_goal():
            return new_state
        # then if not invalid, recurse deeper, and try all values in the next cell.
        # If the deeper state is not invalid, (i.e. it is goal) return it back up the tree
        if not new_state.is_invalid():
            deep_state = depth_first_search(new_state)
            if deep_state is not None and deep_state.is_goal():
                return deep_state

    return None


def sudoku_solver(board):
    """
    Solves a Sudoku puzzle and returns its unique solution.

    Input
        sudoku : 9x9 numpy array
            Empty cells are designated by 0.

    Output
        9x9 numpy array of integers
            It contains the solution, if there is one. If there is no solution, all array entries should be -1.
    """

    # YOUR CODE HERE
    s = SudokuSolver(board)
    s.setup()
    print(s.possible_values)
    if s.is_invalid():
        return s.impossible
    solved_sudoku = depth_first_search(s)
    if solved_sudoku is None:
        return s.impossible

    return solved_sudoku.final_board


print(sudoku_solver(np.array([
    [9, 0, 6, 0, 7, 0, 4, 0, 3],
    [0, 0, 0, 4, 0, 0, 2, 0, 0],
    [0, 7, 0, 0, 2, 3, 0, 1, 0],
    [5, 0, 0, 0, 0, 0, 1, 0, 0],
    [0, 4, 0, 2, 0, 8, 0, 6, 0],
    [0, 0, 3, 0, 0, 0, 0, 0, 5],
    [0, 3, 0, 7, 0, 0, 0, 5, 0],
    [0, 0, 7, 0, 0, 5, 0, 0, 0],
    [4, 0, 5, 0, 1, 0, 7, 0, 8],
])))
