import unittest
import sys
import io
from contextlib import redirect_stdout
from tic_tac_toe import TicTacToe

class TestTicTacToe(unittest.TestCase):
    def setUp(self):
        """Create a fresh TicTacToe instance before each test"""
        self.game = TicTacToe()

    def test_initial_board(self):
        """Test that the initial board is empty"""
        self.assertEqual(self.game.board, [' '] * 9)
        self.assertIsNone(self.game.current_winner)

    def test_available_moves(self):
        """Test that all moves are available at the start of the game"""
        self.assertEqual(self.game.available_moves(), list(range(9)))

    def test_make_move(self):
        """Test making a valid move"""
        # Make a move
        result = self.game.make_move(4, 'X')
        self.assertTrue(result)
        self.assertEqual(self.game.board[4], 'X')

    def test_make_invalid_move(self):
        """Test making a move on an already occupied square"""
        # First move
        self.game.make_move(4, 'X')
        
        # Try to make the same move again
        result = self.game.make_move(4, 'O')
        self.assertFalse(result)
        self.assertEqual(self.game.board[4], 'X')

    def test_winner_row(self):
        """Test winning condition for a row"""
        # Set up a winning row
        self.game.board = ['X', 'X', 'X', 
                           ' ', ' ', ' ', 
                           ' ', ' ', ' ']
        
        # Check winner for the last move in the row
        self.assertTrue(self.game.winner(2, 'X'))

    def test_winner_column(self):
        """Test winning condition for a column"""
        # Set up a winning column
        self.game.board = ['X', ' ', ' ', 
                           'X', ' ', ' ', 
                           'X', ' ', ' ']
        
        # Check winner for the last move in the column
        self.assertTrue(self.game.winner(6, 'X'))

    def test_winner_diagonal(self):
        """Test winning condition for a diagonal"""
        # Set up a winning diagonal
        self.game.board = ['X', ' ', ' ', 
                           ' ', 'X', ' ', 
                           ' ', ' ', 'X']
        
        # Check winner for the last move in the diagonal
        self.assertTrue(self.game.winner(8, 'X'))

    def test_check_winner(self):
        """Test the check_winner method"""
        # Winning row
        board1 = ['X', 'X', 'X', 
                  ' ', ' ', ' ', 
                  ' ', ' ', ' ']
        self.assertEqual(self.game.check_winner(board1), 'X')

        # Winning column
        board2 = ['O', ' ', ' ', 
                  'O', ' ', ' ', 
                  'O', ' ', ' ']
        self.assertEqual(self.game.check_winner(board2), 'O')

        # Tie game
        board3 = ['X', 'O', 'X', 
                  'X', 'O', 'O', 
                  'O', 'X', 'X']
        self.assertEqual(self.game.check_winner(board3), 'Tie')

    def test_minimax(self):
        """Test the minimax algorithm"""
        # Scenario where AI should choose a winning move
        board = ['X', 'X', ' ', 
                 'O', 'O', ' ', 
                 ' ', ' ', ' ']
        
        # AI (X) should choose the winning move
        _, best_move = self.game.minimax(board, True)
        self.assertEqual(best_move, 2)

    def test_empty_squares(self):
        """Test empty squares detection"""
        # Initially all squares are empty
        self.assertTrue(self.game.empty_squares())

        # Fill some squares
        self.game.board = ['X', 'O', 'X', 
                           ' ', ' ', ' ', 
                           ' ', ' ', ' ']
        
        # Still has empty squares
        self.assertTrue(self.game.empty_squares())

        # Fill all squares
        self.game.board = ['X', 'O', 'X', 
                           'O', 'X', 'O', 
                           'X', 'O', 'X']
        
        # No empty squares
        self.assertFalse(self.game.empty_squares())

    def test_num_empty_squares(self):
        """Test counting of empty squares"""
        # Initially 9 empty squares
        self.assertEqual(self.game.num_empty_squares(), 9)

        # Fill some squares
        self.game.board = ['X', 'O', 'X', 
                           ' ', ' ', ' ', 
                           ' ', ' ', ' ']
        
        # 6 empty squares now
        self.assertEqual(self.game.num_empty_squares(), 6)

def main():
    unittest.main()

if __name__ == '__main__':
    main()
