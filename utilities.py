"""
    //-- Begin Connect4 Diagonal checking helper functions
"""
def get_rows(grid):
    return [[c for c in r] for r in grid]

def get_cols(grid):
    return zip(*grid)

def get_backward_diagonals(grid):
    b = [None] * (len(grid) - 1)
    grid = [b[i:] + r + b[:i] for i, r in enumerate(get_rows(grid))]
    return [[c for c in r if not c is None] for r in get_cols(grid)]

def get_forward_diagonals(grid):
    b = [None] * (len(grid) - 1)
    grid = [b[:i] + r + b[i:] for i, r in enumerate(get_rows(grid))]
    return [[c for c in r if not c is None] for r in get_cols(grid)]

"""
    //-- End Connect4 Diagonal checking helper functions
"""

"""
    Given the current turn and board, checks if someone has won the on-going
    connect 4 game (7x7 board default)
"""
def checkC4Victory(c4_board, c4_turn):
    if c4_turn is 0:
        check = 1
    else:
        check = 2
    count = 0

    #vertical check
    for x in c4_board:
        for y in x:
            if y == check:
                count += 1
                if count == 4:
                    #print("Vertical Win")
                    return True
        count = 0

    count = 0
    #horizontal check
    for x in range(0, 7):
        for y in c4_board:
            if y[x] == check:
                count += 1
                if count == 4:
                    #print("Horizontal Win")
                    return True
            else:
                count = 0

    #Check all diagonals
    count = 0
    diags = get_backward_diagonals(c4_board)
    for x in diags:
        for y in x:
            if y == check:
                count += 1
                if count == 4:
                    #print("Backward diagonal win")
                    return True
            else:
                count = 0
        count = 0

    diags = get_forward_diagonals(c4_board)
    for x in diags:
        for y in x:
            if y == check:
                count += 1
                if count == 4:
                    #print("Forward diagonal win")
                    return True
            else:
                count = 0
        count = 0

    #it all failed :(
    return False

"""
    Given the last placement and board, checks if someone has won the on-going
    tic tac toe game (3x3 board default)
"""
def CheckTTTVictory(x, y, ttt_board):
    #check if previous move caused a win on vertical line
    if (ttt_board[0][y] == ttt_board[1][y] == ttt_board[2][y]):
        if (ttt_board[0][y] == "-" or ttt_board[1][y] == "-" or ttt_board[2][y] == "-"):
            return False
        return True

    #check if previous move caused a win on horizontal line
    if ttt_board[x][0] == ttt_board[x][1] == ttt_board[x][2]:
        if ttt_board[x][0] == "-" or ttt_board[x][1] == "-" or ttt_board[x][2] == "-":
            return False
        return True

    #check if previous move was on the main diagonal and caused a win
    if x == y and ttt_board[0][0] == ttt_board[1][1] == ttt_board[2][2]:
        if x == y and ttt_board[0][0] == "-" or ttt_board[1][1] == "-" or ttt_board[2][2] == "-":
            return False
        return True

    #check if previous move was on the secondary diagonal and caused a win
    if x + y == 2 and ttt_board[0][2] == ttt_board[1][1] == ttt_board[2][0]:
        if x + y == 2 and ttt_board[0][2] == "-" or ttt_board[1][1] == "-" or ttt_board[2][0] == "-":
            return False
        return True

    return False

"""
    Special push method that adds in the element to position after the last non-zero term
    For use with connect 4 only
    usage c4_board[x] = push(c4_board[x], value)
    returns updated list, status (-1 fail 1 success) and last updated index (for victory checking)
"""
def push(in_list, value):
    #list is full
    #print in_list
    if in_list[len(in_list) - 1] is not 0:
        return in_list, -1, -1

    if in_list[0] is 0:
        in_list[0] = value
        return in_list, 0, 0

    for x in range(0, len(in_list)-1):
        y = x+1 #leading pointer
        if in_list[x] is not 0 and in_list[y] is 0:
            in_list[y] = value
            return in_list, 0, y
    return in_list, 0, -1

"""
    Simply returns the string version of whose turn it is as opposed to adding if/else everywhere
"""
def currentTurn(turn):
    if turn == 0:
        return "Red Team"
    elif turn == 1:
        return "Blue Team"
