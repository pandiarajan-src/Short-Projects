import random

class TicTacToe:
    def __init__(self):
        self.board = [' ' for _ in range(9)]
        self.current_winner = None

    def print_board(self):
        for row in [self.board[i*3:(i+1)*3] for i in range(3)]:
            print('| ' + ' | '.join(row) + ' |')

    def available_moves(self):
        return [i for i, spot in enumerate(self.board) if spot == ' ']

    def empty_squares(self):
        return ' ' in self.board

    def num_empty_squares(self):
        return self.board.count(' ')

    def make_move(self, square, letter):
        if self.board[square] == ' ':
            self.board[square] = letter
            if self.winner(square, letter):
                self.current_winner = letter
            return True
        return False

    def winner(self, square, letter):
        # Check row
        row_ind = square // 3
        row = self.board[row_ind*3 : (row_ind + 1) * 3]
        if all([spot == letter for spot in row]):
            return True

        # Check column
        col_ind = square % 3
        column = [self.board[col_ind+i*3] for i in range(3)]
        if all([spot == letter for spot in column]):
            return True

        # Check diagonals
        if square % 2 == 0:
            diagonal1 = [self.board[0], self.board[4], self.board[8]]
            if all([spot == letter for spot in diagonal1]):
                return True
            diagonal2 = [self.board[2], self.board[4], self.board[6]]
            if all([spot == letter for spot in diagonal2]):
                return True

        return False

    def minimax(self, board, maximizing_player):
        case = self.check_winner(board)
        if case == 'X':
            return 1, None
        elif case == 'O':
            return -1, None
        elif case == 'Tie':
            return 0, None

        if maximizing_player:
            max_eval = float('-inf')
            best_move = None
            for move in self.get_available_moves(board):
                board_copy = board.copy()
                board_copy[move] = 'X'
                eval, _ = self.minimax(board_copy, False)
                if eval > max_eval:
                    max_eval = eval
                    best_move = move
            return max_eval, best_move
        else:
            min_eval = float('inf')
            best_move = None
            for move in self.get_available_moves(board):
                board_copy = board.copy()
                board_copy[move] = 'O'
                eval, _ = self.minimax(board_copy, True)
                if eval < min_eval:
                    min_eval = eval
                    best_move = move
            return min_eval, best_move

    def get_available_moves(self, board):
        return [i for i, spot in enumerate(board) if spot == ' ']

    def check_winner(self, board):
        # Check rows, columns, and diagonals
        winning_combinations = [
            [0, 1, 2], [3, 4, 5], [6, 7, 8],  # rows
            [0, 3, 6], [1, 4, 7], [2, 5, 8],  # columns
            [0, 4, 8], [2, 4, 6]  # diagonals
        ]

        for combo in winning_combinations:
            if board[combo[0]] == board[combo[1]] == board[combo[2]] != ' ':
                return board[combo[0]]

        if ' ' not in board:
            return 'Tie'
        
        return None

    def print_board_usage(self):
        """Print the board layout with numbered squares for user guidance"""
        print("\nBoard Layout (Enter the number to place your mark):")
        print(" 0 | 1 | 2 ")
        print("---+---+---")
        print(" 3 | 4 | 5 ")
        print("---+---+---")
        print(" 6 | 7 | 8 ")
        print("\nExample: Enter '4' to place your mark in the center square\n")

    def play(self, human_first=False):
        self.print_board_usage()
        
        # Determine player letters based on who goes first
        if human_first:
            human_letter, ai_letter = 'X', 'O'
            print("You are 'X', the AI is 'O'")
        else:
            human_letter, ai_letter = 'O', 'X'
            print("You are 'O', the AI is 'X'")
        
        self.print_board()

        while self.empty_squares():
            # Determine whose turn it is based on human_first
            if human_first:
                # Human's turn (X)
                if len(self.available_moves()) > 0:
                    while True:
                        try:
                            human_move = int(input("Enter your move (0-8): "))
                            if human_move in self.available_moves():
                                break
                            else:
                                print("Invalid move. Try again.")
                        except ValueError:
                            print("Please enter a number between 0-8")

                    self.make_move(human_move, human_letter)
                    self.print_board()

                    if self.current_winner:
                        print(f"{self.current_winner} wins!")
                        return self.current_winner

            # AI's turn
            if len(self.available_moves()) > 0:
                _, move = self.minimax(self.board, ai_letter == 'X')
                self.make_move(move, ai_letter)
                print(f"AI chose square {move}")
                self.print_board()

                if self.current_winner:
                    print(f"{self.current_winner} wins!")
                    return self.current_winner

            # Human's turn (O)
            if not human_first:
                if len(self.available_moves()) > 0:
                    while True:
                        try:
                            human_move = int(input("Enter your move (0-8): "))
                            if human_move in self.available_moves():
                                break
                            else:
                                print("Invalid move. Try again.")
                        except ValueError:
                            print("Please enter a number between 0-8")

                    self.make_move(human_move, human_letter)
                    self.print_board()

                    if self.current_winner:
                        print(f"{self.current_winner} wins!")
                        return self.current_winner

        print("It's a tie!")
        return 'Tie'

def main():
    game = TicTacToe()
    
    print("Welcome to Tic Tac Toe!")
    game.print_board_usage()
    
    while True:
        print("\nChoose who goes first:")
        print("1. AI goes first")
        print("2. You go first")
        print("3. Exit")
        
        choice = input("Enter your choice (1/2/3): ")
        
        if choice == '1':
            game.play(human_first=False)
        elif choice == '2':
            game.play(human_first=True)
        elif choice == '3':
            print("Thanks for playing!")
            break
        else:
            print("Invalid choice. Please try again.")
        
        # Reset the game board for next round
        game.board = [' ' for _ in range(9)]
        game.current_winner = None

if __name__ == "__main__":
    main()
