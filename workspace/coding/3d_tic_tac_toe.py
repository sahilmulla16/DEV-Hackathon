class TicTacToe3D:
    def __init__(self):
        # Initialize a 3x3x3 board with empty spaces
        self.board = [[[" " for _ in range(3)] for _ in range(3)] for _ in range(3)]
        self.current_player = "X"

    def display_board(self):
        """Print the current state of the 3D board."""
        for z in range(3):
            print(f"\n--- Layer {z + 1} ---")
            for x in range(3):
                print(" | ".join(self.board[x][z]))
                if x < 2:
                    print("-----------")

    def is_valid_move(self, x, y, z):
        """Check if the move is within bounds and the cell is empty."""
        if 0 <= x < 3 and 0 <= y < 3 and 0 <= z < 3:
            return self.board[x][z][y] == " "
        return False

    def make_move(self, x, y, z):
        """Place the current player's mark on the board."""
        if not self.is_valid_move(x, y, z):
            return False
        self.board[x][z][y] = self.current_player
        return True

    def check_winner(self):
        """Check all possible lines for a win."""
        # All possible directions in 3D (dx, dy, dz)
        directions = [
            (1, 0, 0), (0, 1, 0), (0, 0, 1),           # axis-aligned
            (1, 1, 0), (1, -1, 0), (1, 0, 1), (1, 0, -1), # face diagonals
            (0, 1, 1), (0, 1, -1),
            (1, 1, 1), (1, 1, -1), (1, -1, 1), (1, -1, -1) # 3D diagonals
        ]

        for x in range(3):
            for y in range(3):
                for z in range(3):
                    if self.board[x][z][y] != " ":
                        for dx, dy, dz in directions:
                            if self.check_direction(x, y, z, dx, dy, dz):
                                return self.board[x][z][y]
        return None

    def check_direction(self, x, y, z, dx, dy, dz):
        """Check if a line starting at (x,y,z) in direction (dx,dy,dz) has 3 same marks."""
        player = self.board[x][z][y]
        for step in range(1, 3):
            nx, ny, nz = x + step * dx, y + step * dy, z + step * dz
            if not (0 <= nx < 3 and 0 <= ny < 3 and 0 <= nz < 3):
                return False
            if self.board[nx][nz][ny] != player:
                return False
        return True

    def is_board_full(self):
        """Check if the board is full (tie)."""
        for x in range(3):
            for z in range(3):
                for y in range(3):
                    if self.board[x][z][y] == " ":
                        return False
        return True

    def play(self):
        """Main game loop."""
        print("Welcome to 3D Tic-Tac-Toe!")
        self.display_board()

        while True:
            print(f"\nPlayer {self.current_player}'s turn")
            try:
                x = int(input("Enter x (0-2): "))
                y = int(input("Enter y (0-2): "))
                z = int(input("Enter z (0-2): "))
            except ValueError:
                print("Invalid input. Please enter numbers between 0 and 2.")
                continue

            if not self.make_move(x, y, z):
                print("Invalid move! Try again.")
                continue

            self.display_board()

            winner = self.check_winner()
            if winner:
                print(f"\nPlayer {winner} wins!")
                break

            if self.is_board_full():
                print("\nThe game is a tie!")
                break

            # Switch player
            self.current_player = "O" if self.current_player == "X" else "X"

if __name__ == "__main__":
    game = TicTacToe3D()
    game.play()
