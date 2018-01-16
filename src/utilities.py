import random
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

def checkC4Victory(c4_board, c4_turn):
    """
        Given the current turn and board, checks if someone has won the on-going
        connect 4 game (7x7 board default.
        :param c4_board: nested 7x7 list that represents the current connect 4 gamestate
        :param c4_turn: binary counter to determine the correct team's turn
    """
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

def CheckTTTVictory(x, y, ttt_board):
    """
        Given the last placement and board, checks if someone has won the on-going
        tic tac toe game (3x3 board default)
        :param x, y: coordinates correlating to last placed marker on a 3x3 ttt board
        :param ttt_board: nested 3x3 list to represent the ttt gamestate
    """
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

def setupBattleship(red_board, blue_board):
    """
        Given 2 empty boards for ships for each team, assign ships randomly for each board.
        Order of placement: Carrier -> Battleship -> Submarine -> Destroyer -> Cruiser
        Direction and starting coordinates are randomly set with randint(), and ships are placed accordingly
        :param red_board: 10x10 zeroed 2-dimensional matrix that represents the red team's battleship placement
        :param blue_board: 10x10 zeroed 2-dimensional matrix that represents the blue team's battleship placement
    """
    """RED TEAM"""
    #carrier
    while True:
        startx = int(random.randint(0, 9))
        starty = int(random.randint(0, 9))
        direction = int(random.randint(0, 1))

        #horizontal placement
        if direction is 0:
            try:
                if red_board[startx][starty] == 0 and red_board[startx+1][starty] == 0 and red_board[startx+2][starty] == 0 and red_board[startx+3][starty] == 0 and red_board[startx+4][starty] == 0:
                    red_board[startx][starty] = 1
                    red_board[startx+1][starty] = 1
                    red_board[startx+2][starty] = 1
                    red_board[startx+3][starty] = 1
                    red_board[startx+4][starty] = 1
                    break
            except IndexError:
                continue
        else:
            try:
                if red_board[startx][starty] == 0 and red_board[startx][starty+1] == 0 and red_board[startx][starty+2] == 0 and red_board[startx][starty+3] == 0 and red_board[startx][starty+4] == 0:
                    red_board[startx][starty] = 1
                    red_board[startx][starty+1] = 1
                    red_board[startx][starty+2] = 1
                    red_board[startx][starty+3] = 1
                    red_board[startx][starty+4] = 1
                    break
            except IndexError:
                continue
    #battlship
    while True:
        startx = int(random.randint(0, 9))
        starty = int(random.randint(0, 9))
        direction = int(random.randint(0, 1))

        #horizontal placement
        if direction is 0:
            try:
                #pick for red team
                if red_board[startx][starty] == 0 and red_board[startx+1][starty] == 0 and red_board[startx+2][starty] == 0 and red_board[startx+3][starty] == 0:
                    red_board[startx][starty] = 2
                    red_board[startx+1][starty] = 2
                    red_board[startx+2][starty] = 2
                    red_board[startx+3][starty] = 2
                    break
            except IndexError:
                continue
        else:
            try:
                #pick for red team
                if red_board[startx][starty] == 0 and red_board[startx][starty+1] == 0 and red_board[startx][starty+2] == 0 and red_board[startx][starty+3] == 0:
                    red_board[startx][starty] = 2
                    red_board[startx][starty+1] = 2
                    red_board[startx][starty+2] = 2
                    red_board[startx][starty+3] = 2
                    break
            except IndexError:
                continue
    #submarine
    while True:
        startx = int(random.randint(0, 9))
        starty = int(random.randint(0, 9))
        direction = int(random.randint(0, 1))

        #horizontal placement
        if direction is 0:
            try:
                #pick for red team
                if red_board[startx][starty] == 0 and red_board[startx+1][starty] == 0 and red_board[startx+2][starty] == 0:
                    red_board[startx][starty] = 3
                    red_board[startx+1][starty] = 3
                    red_board[startx+2][starty] = 3
                    break
            except IndexError:
                continue
        else:
            try:
                #pick for red team
                if red_board[startx][starty] == 0 and red_board[startx][starty+1] == 0 and red_board[startx][starty+2] == 0:
                    red_board[startx][starty] = 3
                    red_board[startx][starty+1] = 3
                    red_board[startx][starty+2] = 3
                    break
            except IndexError:
                continue
    #destroyer
    while True:
        startx = int(random.randint(0, 9))
        starty = int(random.randint(0, 9))
        direction = int(random.randint(0, 1))
        #horizontal placement

        if direction is 0:
            try:
                #pick for red team
                if red_board[startx][starty] == 0 and red_board[startx+1][starty] == 0 and red_board[startx+2][starty] == 0:
                    red_board[startx][starty] = 4
                    red_board[startx+1][starty] = 4
                    red_board[startx+2][starty] = 4
                    break
            except IndexError:
                continue
        else:
            try:
                #pick for red team
                if red_board[startx][starty] == 0 and red_board[startx][starty+1] == 0 and red_board[startx][starty+2] == 0:
                    red_board[startx][starty] = 4
                    red_board[startx][starty+1] = 4
                    red_board[startx][starty+2] = 4
                    break
            except IndexError:
                continue
    #cruister
    while True:
        startx = int(random.randint(0, 9))
        starty = int(random.randint(0, 9))
        direction = int(random.randint(0, 1))
        #horizontal placement

        if direction is 0:
            try:
                #pick for red team
                if red_board[startx][starty] == 0 and red_board[startx+1][starty] == 0:
                    red_board[startx][starty] = 5
                    red_board[startx+1][starty] = 5
                    break
            except IndexError:
                continue
        else:
            try:
                #pick for red team
                if red_board[startx][starty] == 0 and red_board[startx][starty+1] == 0:
                    red_board[startx][starty] = 5
                    red_board[startx][starty+1] = 5
                    break
            except IndexError:
                continue
    """BLUE TEAM"""
    #carrier
    while True:
        startx = int(random.randint(0, 9))
        starty = int(random.randint(0, 9))
        direction = int(random.randint(0, 1))

        #horizontal placement
        if direction is 0:
            try:
                #pick for red team
                if blue_board[startx][starty] == 0 and blue_board[startx+1][starty] == 0 and blue_board[startx+2][starty] == 0 and blue_board[startx+3][starty] == 0 and blue_board[startx+4][starty] == 0:
                    blue_board[startx][starty] = 1
                    blue_board[startx+1][starty] = 1
                    blue_board[startx+2][starty] = 1
                    blue_board[startx+3][starty] = 1
                    blue_board[startx+4][starty] = 1
                    break
            except IndexError:
                continue
        else:
            try:
                #pick for red team
                if blue_board[startx][starty] == 0 and blue_board[startx][starty+1] == 0 and blue_board[startx][starty+2] == 0 and blue_board[startx][starty+3] == 0 and blue_board[startx][starty+4] == 0:
                    blue_board[startx][starty] = 1
                    blue_board[startx][starty+1] = 1
                    blue_board[startx][starty+2] = 1
                    blue_board[startx][starty+3] = 1
                    blue_board[startx][starty+4] = 1
                    break
            except IndexError:
                continue
    #battlship
    while True:
        startx = int(random.randint(0, 9))
        starty = int(random.randint(0, 9))
        direction = int(random.randint(0, 1))

        #horizontal placement
        if direction is 0:
            try:
                #pick for red team
                if blue_board[startx][starty] == 0 and blue_board[startx+1][starty] == 0 and blue_board[startx+2][starty] == 0 and blue_board[startx+3][starty] == 0:
                    blue_board[startx][starty] = 2
                    blue_board[startx+1][starty] = 2
                    blue_board[startx+2][starty] = 2
                    blue_board[startx+3][starty] = 2
                    break
            except IndexError:
                continue
        else:
            try:
                #pick for red team
                if blue_board[startx][starty] == 0 and blue_board[startx][starty+1] == 0 and blue_board[startx][starty+2] == 0 and blue_board[startx][starty+3] == 0:
                    blue_board[startx][starty] = 2
                    blue_board[startx][starty+1] = 2
                    blue_board[startx][starty+2] = 2
                    blue_board[startx][starty+3] = 2
                    break
            except IndexError:
                continue
    #submarine
    while True:
        startx = int(random.randint(0, 9))
        starty = int(random.randint(0, 9))
        direction = int(random.randint(0, 1))

        #horizontal placement
        if direction is 0:
            try:
                #pick for red team
                if blue_board[startx][starty] == 0 and blue_board[startx+1][starty] == 0 and blue_board[startx+2][starty] == 0:
                    blue_board[startx][starty] = 3
                    blue_board[startx+1][starty] = 3
                    blue_board[startx+2][starty] = 3
                    break
            except IndexError:
                continue
        else:
            try:
                #pick for red team
                if blue_board[startx][starty] == 0 and blue_board[startx][starty+1] == 0 and blue_board[startx][starty+2] == 0:
                    blue_board[startx][starty] = 3
                    blue_board[startx][starty+1] = 3
                    blue_board[startx][starty+2] = 3
                    break
            except IndexError:
                continue
    #destroyer
    while True:
        startx = int(random.randint(0, 9))
        starty = int(random.randint(0, 9))
        direction = int(random.randint(0, 1))
        #horizontal placement

        if direction is 0:
            try:
                #pick for red team
                if blue_board[startx][starty] == 0 and blue_board[startx+1][starty] == 0 and blue_board[startx+2][starty] == 0:
                    blue_board[startx][starty] = 4
                    blue_board[startx+1][starty] = 4
                    blue_board[startx+2][starty] = 4
                    break
            except IndexError:
                continue
        else:
            try:
                #pick for red team
                if blue_board[startx][starty] == 0 and blue_board[startx][starty+1] == 0 and blue_board[startx][starty+2] == 0:
                    blue_board[startx][starty] = 4
                    blue_board[startx][starty+1] = 4
                    blue_board[startx][starty+2] = 4
                    break
            except IndexError:
                continue
    #cruister
    while True:
        startx = int(random.randint(0, 9))
        starty = int(random.randint(0, 9))
        direction = int(random.randint(0, 1))
        #horizontal placement

        if direction is 0:
            try:
                #pick for red team
                if blue_board[startx][starty] == 0 and blue_board[startx+1][starty] == 0:
                    blue_board[startx][starty] = 5
                    blue_board[startx+1][starty] = 5
                    break
            except IndexError:
                continue
        else:
            try:
                #pick for red team
                if blue_board[startx][starty] == 0 and blue_board[startx][starty+1] == 0:
                    blue_board[startx][starty] = 5
                    blue_board[startx][starty+1] = 5
                    break
            except IndexError:
                continue
    return red_board, blue_board

def checkBSVictory(hit_board, opposing_board):
    """
        Replace all Xs in the hit board with 0s and simply check if the hit board from
        one team matches the ship board of the other team match
    """
    for z in hit_board:
        for i in z:
            if i is 'X':
                i = 0
    if hit_board == opposing_board:
        return True
    else:
        return False

def push(in_list, value):
    """
        Special push method that adds in the element to position after the last non-zero term
        For use with connect 4 only
        usage c4_board[x] = push(c4_board[x], value)
        returns updated list, status (-1 fail 1 success) and last updated index (for victory checking)
    """
    #list is full
    if in_list[len(in_list) - 1] is not 0:
        return in_list, -1
    #find first occurance of 0, replace it, return
    y = in_list.index(0)
    in_list[y] = value
    return in_list, 0

def currentTurn(turn):
    """
        Simply returns the string version of whose turn it is as opposed to adding if/else everywhere
    """
    if turn == 0:
        return "Red Team"
    elif turn == 1:
        return "Blue Team"
