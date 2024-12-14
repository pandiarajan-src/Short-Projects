# Tic Tac Toe with Minimax AI

## Game Description
This is a Tic Tac Toe game where:
- The AI uses the Minimax algorithm to play optimally
- You can choose to go first or let the AI go first
- The game supports multiple rounds
- Board layout is shown at the start to help you understand square numbering

## Board Layout
```
 0 | 1 | 2 
---+---+---
 3 | 4 | 5 
---+---+---
 6 | 7 | 8 
```

## How to Play
1. Run the game using `python tic_tac_toe.py`
2. Choose from the menu:
   - Option 1: AI goes first (AI plays X)
   - Option 2: You go first (You play X)
   - Option 3: Exit the game
3. When prompted, enter a number between 0-8 corresponding to the square you want to place your mark
4. The game continues until there's a winner or a tie
5. After each game, you can choose to play again or exit

## Requirements
- Python 3.7+

## How to Run
```bash
python tic_tac_toe.py
```

## Game Rules
- Choose who goes first at the start of each game
- First to get 3 in a row (horizontally, vertically, or diagonally) wins
- If all squares are filled without a winner, it's a tie
