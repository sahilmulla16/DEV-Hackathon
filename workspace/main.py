from vpython import *
import numpy as np

def create_board():
    board = np.full((3, 3, 3), None)
    scene.caption = '3D Tic-Tac-Toe: Click to place X or O'
    for x in range(3):
        for y in range(3):
            for z in range(3):
                box(pos=vector(x-1, y-1, z-1), size=vector(0.9, 0.9, 0.9), opacity=0.3)
    return board

def check_winner(board):
    for i in range(3):
        for j in range(3):
            # Check X-lines
            if board[i,0,j] and all(board[i,k,j] == board[i,0,j] for k in range(3)):
                return board[i,0,j]
            # Check Y-lines
            if board[0,i,j] and all(board[k,i,j] == board[0,i,j] for k in range(3)):
                return board[0,i,j]
            # Check Z-lines
            if board[i,j,0] and all(board[i,j,k] == board[i,j,0] for k in range(3)):
                return board[i,j,0]
    # Check diagonals
    if board[0,0,0] and board[0,0,0] == board[1,1,1] == board[2,2,2]:
        return board[0,0,0]
    if board[2,0,0] and board[2,0,0] == board[1,1,1] == board[0,2,2]:
        return board[2,0,0]
    if board[0,0,2] and board[0,0,2] == board[1,1,1] == board[2,2,0]:
        return board[0,0,2]
    if board[2,0,2] and board[2,0,2] == board[1,1,1] == board[0,2,0]:
        return board[2,0,2]
    return None

def run_game():
    board = create_board()
    scene.title = '3D Tic-Tac-Toe'
    current_player = 'X'
    game_over = False

    while True:
        if game_over:
            continue
        if scene.mouse.clicked:
            m = scene.mouse.getclick()
            pos = m.pos
            x, y, z = int(pos.x + 1.5), int(pos.y + 1.5), int(pos.z + 1.5)
            if 0 <= x < 3 and 0 <= y < 3 and 0 <= z < 3 and board[x,y,z] is None:
                board[x,y,z] = current_player
                color = color.red if current_player == 'X' else color.blue
                text(pos=vector(x-1, y-1, z-1), text=current_player, color=color, height=0.3)
                winner = check_winner(board)
                if winner:
                    scene.caption = f'Player {winner} wins!'
                    game_over = True
                elif not np.any(board == None):
                    scene.caption = 'Game over: Draw!'
                    game_over = True
                else:
                    current_player = 'O' if current_player == 'X' else 'X'
                    scene.caption = f'Player {current_player} turn'

run_game()