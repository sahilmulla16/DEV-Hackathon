import pygame
import sys

# Initialize Pygame
pygame.init()

# Constants
SIZE = 3
CELL_SIZE = 60
MARGIN = 10
WIDTH = (CELL_SIZE + MARGIN) * SIZE * 3 + MARGIN * 2
HEIGHT = (CELL_SIZE + MARGIN) * SIZE * 3 + MARGIN * 2
BACKGROUND_COLOR = (25, 25, 25)
LINE_COLOR = (50, 50, 50)
X_COLOR = (255, 100, 100)
O_COLOR = (100, 100, 255)
TEXT_COLOR = (255, 255, 255)

# Set up display
screen = pygame.display.set_mode((WIDTH, HEIGHT))
pygame.display.set_caption('3D Tic Tac Toe')
font = pygame.font.SysFont('Arial', 24)

# Game state: 3x3x3 grid
board = [[[None for _ in range(SIZE)] for _ in range(SIZE)] for _ in range(SIZE)]
current_player = 'X'
game_over = False
winner = None

def draw_board():
    screen.fill(BACKGROUND_COLOR)
    for layer in range(SIZE):
        offset_x = (WIDTH // 3) * layer + MARGIN * (layer + 1)
        for row in range(SIZE):
            for col in range(SIZE):
                x = offset_x + col * (CELL_SIZE + MARGIN)
                y = row * (CELL_SIZE + MARGIN) + MARGIN * 2
                pygame.draw.rect(screen, LINE_COLOR, (x, y, CELL_SIZE, CELL_SIZE))
                if board[layer][row][col] == 'X':
                    pygame.draw.line(screen, X_COLOR, (x + 10, y + 10), (x + CELL_SIZE - 10, y + CELL_SIZE - 10), 5)
                    pygame.draw.line(screen, X_COLOR, (x + CELL_SIZE - 10, y + 10), (x + 10, y + CELL_SIZE - 10), 5)
                elif board[layer][row][col] == 'O':
                    center = (x + CELL_SIZE // 2, y + CELL_SIZE // 2)
                    pygame.draw.circle(screen, O_COLOR, center, CELL_SIZE // 2 - 10, 5)

    # Draw labels
    for layer in range(SIZE):
        offset_x = (WIDTH // 3) * layer + MARGIN * (layer + 1)
        text = font.render(f'Layer {layer + 1}', True, TEXT_COLOR)
        screen.blit(text, (offset_x + 10, 10))

    if game_over:
        result_text = f'Winner: {winner}' if winner else 'Draw!'
        text_surface = font.render(result_text, True, TEXT_COLOR)
        pygame.draw.rect(screen, (0, 0, 0), (WIDTH // 2 - 100, HEIGHT // 2 - 25, 200, 50))
        screen.blit(text_surface, (WIDTH // 2 - text_surface.get_width() // 2, HEIGHT // 2 - text_surface.get_height() // 2))


def get_cell(pos):
    x, y = pos
    for layer in range(SIZE):
        offset_x = (WIDTH // 3) * layer + MARGIN * (layer + 1)
        if offset_x <= x < offset_x + (CELL_SIZE + MARGIN) * SIZE:
            col = (x - offset_x) // (CELL_SIZE + MARGIN)
            row = (y - MARGIN * 2) // (CELL_SIZE + MARGIN)
            if 0 <= row < SIZE and 0 <= col < SIZE:
                return layer, int(row), int(col)
    return None

def check_winner():
    global winner
    # Check all lines in 3D: rows, cols, depths, and diagonals
    for i in range(SIZE):
        for j in range(SIZE):
            # Check along depth (fixed row, col)
            if board[0][i][j] == board[1][i][j] == board[2][i][j] and board[0][i][j] is not None:
                winner = board[0][i][j]
                return True
            # Check along row (fixed layer, row)
            if board[i][j][0] == board[i][j][1] == board[i][j][2] and board[i][j][0] is not None:
                winner = board[i][j][0]
                return True
            # Check along col (fixed layer, col)
            if board[i][0][j] == board[i][1][j] == board[i][2][j] and board[i][0][j] is not None:
                winner = board[i][0][j]
                return True

    # Check diagonals in each layer
    for layer in range(SIZE):
        if board[layer][0][0] == board[layer][1][1] == board[layer][2][2] and board[layer][0][0] is not None:
            winner = board[layer][0][0]
            return True
        if board[layer][0][2] == board[layer][1][1] == board[layer][2][0] and board[layer][0][2] is not None:
            winner = board[layer][0][2]
            return True

    # Check 3D diagonals
    if board[0][0][0] == board[1][1][1] == board[2][2][2] and board[0][0][0] is not None:
        winner = board[0][0][0]
        return True
    if board[0][0][2] == board[1][1][1] == board[2][2][0] and board[0][0][2] is not None:
        winner = board[0][0][2]
        return True
    if board[0][2][0] == board[1][1][1] == board[2][0][2] and board[0][2][0] is not None:
        winner = board[0][2][0]
        return True
    if board[0][2][2] == board[1][1][1] == board[2][0][0] and board[0][2][2] is not None:
        winner = board[0][2][2]
        return True

    # Check face diagonals across layers
    for i in range(SIZE):
        if board[0][i][0] == board[1][i][1] == board[2][i][2] and board[0][i][0] is not None:
            winner = board[0][i][0]
            return True
        if board[0][i][2] == board[1][i][1] == board[2][i][0] and board[0][i][2] is not None:
            winner = board[0][i][2]
            return True
        if board[0][0][i] == board[1][1][i] == board[2][2][i] and board[0][0][i] is not None:
            winner = board[0][0][i]
            return True
        if board[0][2][i] == board[1][1][i] == board[2][0][i] and board[0][2][i] is not None:
            winner = board[0][2][i]
            return True

    return False

def is_board_full():
    for layer in range(SIZE):
        for row in range(SIZE):
            for col in range(SIZE):
                if board[layer][row][col] is None:
                    return False
    return True

# Main game loop
running = True
draw_board()
while running:
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False

        if event.type == pygame.MOUSEBUTTONDOWN and not game_over:
            pos = pygame.mouse.get_pos()
            cell = get_cell(pos)
            if cell:
                layer, row, col = cell
                if board[layer][row][col] is None:
                    board[layer][row][col] = current_player
                    if check_winner():
                        game_over = True
                    elif is_board_full():
                        game_over = True
                        winner = None
                    else:
                        current_player = 'O' if current_player == 'X' else 'X'

        if event.type == pygame.KEYDOWN:
            if event.key == pygame.K_r:
                # Reset game
                board = [[[None for _ in range(SIZE)] for _ in range(SIZE)] for _ in range(SIZE)]
                current_player = 'X'
                game_over = False
                winner = None

    draw_board()
    pygame.display.flip()

pygame.quit()
sys.exit()