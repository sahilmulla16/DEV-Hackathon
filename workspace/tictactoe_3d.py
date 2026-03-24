class TicTacToe3D:
    def __init__(self):
        self.board = [[[" " for _ in range(3)] for _ in range(3)] for _ in range(3)]
        self.current_player = "X"

    def print_board(self):
        for layer in range(3):
            print(f"Layer {layer + 1}:")
            for row in self.board[layer]:
                print("|" + "|".join(row) + "|")
            print("\n")

    def is_valid_move(self, layer, row, col):
        return 0 <= layer < 3 and 0 <= row < 3 and 0 <= col < 3 and self.board[layer][row][col] == " "

    def make_move(self, layer, row, col):
        if not self.is_valid_move(layer, row, col):
            return False
        self.board[layer][row][col] = self.current_player
        return True

    def check_winner(self):
        for layer in range(3):
            for i in range(3):
                if self.board[layer][i][0] == self.board[layer][i][1] == self.board[layer][i][2] != " ":
                    return self.board[layer][i][0]
                if self.board[layer][0][i] == self.board[layer][1][i] == self.board[layer][2][i] != " ":
                    return self.board[layer][0][i]
        for i in range(3):
            if self.board[0][i][i] == self.board[1][i][i] == self.board[2][i][i] != " ":
                return self.board[0][i][i]
            if self.board[0][i][2-i] == self.board[1][i][2-i] == self.board[2][i][2-i] != " ":
                return self.board[0][i][2-i]
        for col in range(3):
            for row in range(3):
                if self.board[0][row][col] == self.board[1][row][col] == self.board[2][row][col] != " ":
                    return self.board[0][row][col]
        if self.board[0][0][0] == self.board[1][1][1] == self.board[2][2][2] != " ":
            return self.board[0][0][0]
        if self.board[0][0][2] == self.board[1][1][1] == self.board[2][2][0] != " ":
            return self.board[0][0][2]
        if self.board[0][2][0] == self.board[1][1][1] == self.board[2][0][2] != " ":
            return self.board[0][2][0]
        if self.board[0][2][2] == self.board[1][1][1] == self.board[2][0][0] != " ":
            return self.board[0][2][2]
        return None

    def is_full(self):
        for layer in range(3):
            for row in range(3):
                for col in range(3):
                    if self.board[layer][row][col] == " ":
                        return False
        return True

    def play(self):
        print("Welcome to 3D Tic-Tac-Toe!")
        while True:
            self.print_board()
            print(f"Player {self.current_player}'s turn.")
            try:
                layer = int(input("Enter layer (1-3): ")) - 1
                row = int(input("Enter row (1-3): ")) - 1
                col = int(input("Enter column (1-3): ")) - 1
            except ValueError:
                print("Invalid input. Please enter numbers.")
                continue

            if not self.make_move(layer, row, col):
                print("Invalid move. Try again.")
                continue

            winner = self.check_winner()
            if winner:
                self.print_board()
                print(f"Player {winner} wins!")
                break

            if self.is_full():
                self.print_board()
                print("It's a draw!")
                break

            self.current_player = "O" if self.current_player == "X" else "X"

if __name__ == "__main__":
    game = TicTacToe3D()
    game.play()