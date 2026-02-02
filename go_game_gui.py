"""
Enhanced Go Game with GUI - Student Project
Features: Human vs AI, Multiple difficulty levels, Move hints, Undo, Save/Load
Board Size: 7x7 (optimal for minimax algorithm)
"""

import pygame
import sys
import time
import json
from copy import deepcopy
from datetime import datetime

# Initialize Pygame
pygame.init()

# Constants
BOARD_SIZE = 7
CELL_SIZE = 70
MARGIN = 80
WINDOW_WIDTH = BOARD_SIZE * CELL_SIZE + 2 * MARGIN
WINDOW_HEIGHT = BOARD_SIZE * CELL_SIZE + 2 * MARGIN + 150  # Extra space for controls
FPS = 60

# Colors
BOARD_COLOR = (220, 179, 92)
LINE_COLOR = (0, 0, 0)
BLACK_STONE = (0, 0, 0)
WHITE_STONE = (255, 255, 255)
HIGHLIGHT_COLOR = (255, 0, 0)
HINT_COLOR = (0, 255, 0)
BUTTON_COLOR = (100, 100, 200)
BUTTON_HOVER = (150, 150, 255)
TEXT_COLOR = (255, 255, 255)
INFO_BG = (50, 50, 50)

# Fonts
TITLE_FONT = pygame.font.Font(None, 36)
BUTTON_FONT = pygame.font.Font(None, 28)
INFO_FONT = pygame.font.Font(None, 24)
SMALL_FONT = pygame.font.Font(None, 20)


class GoBoard:
    """Represents the Go board and game logic"""
    
    def __init__(self, size=7):
        self.size = size
        self.board = [[0 for _ in range(size)] for _ in range(size)]
        self.previous_board = None
        self.current_player = 1  # 1 for Black, 2 for White
        self.captured_black = 0
        self.captured_white = 0
        self.move_history = []
        self.ko_position = None
        
    def copy(self):
        """Create a deep copy of the board"""
        new_board = GoBoard(self.size)
        new_board.board = deepcopy(self.board)
        new_board.previous_board = deepcopy(self.previous_board)
        new_board.current_player = self.current_player
        new_board.captured_black = self.captured_black
        new_board.captured_white = self.captured_white
        new_board.move_history = self.move_history.copy()
        new_board.ko_position = self.ko_position
        return new_board
        
    def is_valid_position(self, row, col):
        """Check if position is within board boundaries"""
        return 0 <= row < self.size and 0 <= col < self.size
    
    def get_neighbors(self, row, col):
        """Get all adjacent positions"""
        neighbors = []
        directions = [(0, 1), (1, 0), (0, -1), (-1, 0)]
        for dr, dc in directions:
            new_row, new_col = row + dr, col + dc
            if self.is_valid_position(new_row, new_col):
                neighbors.append((new_row, new_col))
        return neighbors
    
    def get_group(self, row, col):
        """Get all stones in the same group (connected stones of same color)"""
        if self.board[row][col] == 0:
            return set()
        
        color = self.board[row][col]
        group = set()
        stack = [(row, col)]
        
        while stack:
            r, c = stack.pop()
            if (r, c) in group:
                continue
            group.add((r, c))
            
            for nr, nc in self.get_neighbors(r, c):
                if self.board[nr][nc] == color and (nr, nc) not in group:
                    stack.append((nr, nc))
        
        return group
    
    def count_liberties(self, group):
        """Count liberties (empty adjacent points) for a group"""
        liberties = set()
        for row, col in group:
            for nr, nc in self.get_neighbors(row, col):
                if self.board[nr][nc] == 0:
                    liberties.add((nr, nc))
        return len(liberties)
    
    def remove_captured_stones(self, opponent_color):
        """Remove stones with no liberties and return count"""
        captured_count = 0
        checked = set()
        
        for row in range(self.size):
            for col in range(self.size):
                if self.board[row][col] == opponent_color and (row, col) not in checked:
                    group = self.get_group(row, col)
                    checked.update(group)
                    
                    if self.count_liberties(group) == 0:
                        for r, c in group:
                            self.board[r][c] = 0
                        captured_count += len(group)
        
        return captured_count
    
    def would_be_suicide(self, row, col, color):
        """Check if placing a stone would be suicide"""
        # Temporarily place the stone
        self.board[row][col] = color
        
        # Check if this group would have liberties
        group = self.get_group(row, col)
        liberties = self.count_liberties(group)
        
        # Also check if it captures opponent stones
        opponent_color = 3 - color
        would_capture = False
        for nr, nc in self.get_neighbors(row, col):
            if self.board[nr][nc] == opponent_color:
                opp_group = self.get_group(nr, nc)
                if self.count_liberties(opp_group) == 0:
                    would_capture = True
                    break
        
        # Remove the temporary stone
        self.board[row][col] = 0
        
        return liberties == 0 and not would_capture
    
    def is_valid_move(self, row, col):
        """Check if a move is valid"""
        # Position must be empty
        if self.board[row][col] != 0:
            return False
        
        # Check for ko rule
        if self.ko_position == (row, col):
            return False
        
        # Check for suicide
        if self.would_be_suicide(row, col, self.current_player):
            return False
        
        return True
    
    def make_move(self, row, col):
        """Place a stone and update game state"""
        if not self.is_valid_move(row, col):
            return False
        
        # Save previous board state
        self.previous_board = deepcopy(self.board)
        
        # Place the stone
        self.board[row][col] = self.current_player
        
        # Remove captured opponent stones
        opponent_color = 3 - self.current_player
        captured = self.remove_captured_stones(opponent_color)
        
        if self.current_player == 1:
            self.captured_white += captured
        else:
            self.captured_black += captured
        
        # Check for ko
        if captured == 1:
            # Find the captured position
            for r in range(self.size):
                for c in range(self.size):
                    if self.previous_board[r][c] == opponent_color and self.board[r][c] == 0:
                        self.ko_position = (r, c)
                        break
        else:
            self.ko_position = None
        
        # Add to history
        self.move_history.append((row, col, self.current_player))
        
        # Switch player
        self.current_player = 3 - self.current_player
        
        return True
    
    def undo_move(self):
        """Undo the last move"""
        if not self.move_history or self.previous_board is None:
            return False
        
        # Remove last move from history
        self.move_history.pop()
        
        # Restore previous board
        self.board = deepcopy(self.previous_board)
        
        # Switch back player
        self.current_player = 3 - self.current_player
        
        # Recalculate captured stones
        self.captured_black = 0
        self.captured_white = 0
        for _, _, player in self.move_history:
            # This is simplified; in a full implementation, you'd track captures per move
            pass
        
        self.ko_position = None
        return True
    
    def get_score(self):
        """Calculate territory score (simplified Chinese rules)"""
        black_score = 0
        white_score = 0
        
        # Count stones on board
        for row in range(self.size):
            for col in range(self.size):
                if self.board[row][col] == 1:
                    black_score += 1
                elif self.board[row][col] == 2:
                    white_score += 1
        
        # Add captured stones
        black_score += self.captured_white
        white_score += self.captured_black
        
        # Add komi (compensation for white going second)
        white_score += 2.5
        
        return black_score, white_score
    
    def get_valid_moves(self):
        """Get all valid moves for current player"""
        valid_moves = []
        for row in range(self.size):
            for col in range(self.size):
                if self.is_valid_move(row, col):
                    valid_moves.append((row, col))
        return valid_moves


class MinimaxAI:
    """AI player using minimax algorithm with alpha-beta pruning"""
    
    def __init__(self, depth=2, player=2):
        self.depth = depth
        self.player = player
        self.opponent = 3 - player
        self.nodes_evaluated = 0
        
    def evaluate_board(self, board):
        """Evaluate board position with multiple heuristics"""
        score = 0
        
        # 1. Territory control (stones on board)
        for row in range(board.size):
            for col in range(board.size):
                if board.board[row][col] == self.player:
                    # Center positions are more valuable
                    center_bonus = (3.5 - abs(row - 3)) + (3.5 - abs(col - 3))
                    score += 10 + center_bonus
                elif board.board[row][col] == self.opponent:
                    center_bonus = (3.5 - abs(row - 3)) + (3.5 - abs(col - 3))
                    score -= 10 + center_bonus
        
        # 2. Captured stones
        if self.player == 1:
            score += board.captured_white * 15
            score -= board.captured_black * 15
        else:
            score += board.captured_black * 15
            score -= board.captured_white * 15
        
        # 3. Liberty count (groups with more liberties are stronger)
        for row in range(board.size):
            for col in range(board.size):
                if board.board[row][col] == self.player:
                    group = board.get_group(row, col)
                    liberties = board.count_liberties(group)
                    score += liberties * 2
                elif board.board[row][col] == self.opponent:
                    group = board.get_group(row, col)
                    liberties = board.count_liberties(group)
                    score -= liberties * 2
        
        # 4. Corner and edge control
        corners = [(0, 0), (0, board.size-1), (board.size-1, 0), (board.size-1, board.size-1)]
        for r, c in corners:
            if board.board[r][c] == self.player:
                score += 5
            elif board.board[r][c] == self.opponent:
                score -= 5
        
        return score
    
    def minimax(self, board, depth, alpha, beta, maximizing):
        """Minimax with alpha-beta pruning"""
        self.nodes_evaluated += 1
        
        if depth == 0:
            return self.evaluate_board(board), None
        
        valid_moves = board.get_valid_moves()
        
        if not valid_moves:
            return self.evaluate_board(board), None
        
        best_move = None
        
        if maximizing:
            max_eval = float('-inf')
            for move in valid_moves:
                new_board = board.copy()
                new_board.make_move(move[0], move[1])
                
                eval_score, _ = self.minimax(new_board, depth - 1, alpha, beta, False)
                
                if eval_score > max_eval:
                    max_eval = eval_score
                    best_move = move
                
                alpha = max(alpha, eval_score)
                if beta <= alpha:
                    break  # Beta cutoff
            
            return max_eval, best_move
        else:
            min_eval = float('inf')
            for move in valid_moves:
                new_board = board.copy()
                new_board.make_move(move[0], move[1])
                
                eval_score, _ = self.minimax(new_board, depth - 1, alpha, beta, True)
                
                if eval_score < min_eval:
                    min_eval = eval_score
                    best_move = move
                
                beta = min(beta, eval_score)
                if beta <= alpha:
                    break  # Alpha cutoff
            
            return min_eval, best_move
    
    def get_best_move(self, board):
        """Get the best move for current board state"""
        self.nodes_evaluated = 0
        start_time = time.time()
        
        _, best_move = self.minimax(board, self.depth, float('-inf'), float('inf'), True)
        
        elapsed_time = time.time() - start_time
        
        return best_move, self.nodes_evaluated, elapsed_time


class Button:
    """Simple button class for GUI"""
    
    def __init__(self, x, y, width, height, text, color, hover_color):
        self.rect = pygame.Rect(x, y, width, height)
        self.text = text
        self.color = color
        self.hover_color = hover_color
        self.is_hovered = False
    
    def draw(self, screen):
        color = self.hover_color if self.is_hovered else self.color
        pygame.draw.rect(screen, color, self.rect, border_radius=5)
        pygame.draw.rect(screen, LINE_COLOR, self.rect, 2, border_radius=5)
        
        text_surface = BUTTON_FONT.render(self.text, True, TEXT_COLOR)
        text_rect = text_surface.get_rect(center=self.rect.center)
        screen.blit(text_surface, text_rect)
    
    def handle_event(self, event):
        if event.type == pygame.MOUSEMOTION:
            self.is_hovered = self.rect.collidepoint(event.pos)
        elif event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            if self.rect.collidepoint(event.pos):
                return True
        return False


class GoGame:
    """Main game class with GUI"""
    
    def __init__(self):
        self.screen = pygame.display.set_mode((WINDOW_WIDTH, WINDOW_HEIGHT))
        pygame.display.set_caption("Go Game - 7x7 Board - AI vs Human")
        self.clock = pygame.time.Clock()
        
        self.board = GoBoard(BOARD_SIZE)
        self.ai = None
        self.game_mode = None  # 'pvp', 'pva_black', 'pva_white'
        self.difficulty = 2  # Default medium
        self.show_menu = True
        self.show_hint = False
        self.hint_move = None
        self.last_move = None
        self.ai_thinking = False
        self.game_over = False
        self.winner_text = ""
        
        # Create game buttons
        button_y = WINDOW_HEIGHT - 120
        self.buttons = {
            'undo': Button(20, button_y, 120, 40, 'Undo', BUTTON_COLOR, BUTTON_HOVER),
            'hint': Button(150, button_y, 120, 40, 'Hint', BUTTON_COLOR, BUTTON_HOVER),
            'save': Button(280, button_y, 120, 40, 'Save', BUTTON_COLOR, BUTTON_HOVER),
            'load': Button(410, button_y, 120, 40, 'Load', BUTTON_COLOR, BUTTON_HOVER),
            'menu': Button(540, button_y, 120, 40, 'Menu', BUTTON_COLOR, BUTTON_HOVER),
        }
        
        # Create menu buttons (persistent)
        self.mode_buttons = [
            Button(WINDOW_WIDTH // 2 - 150, 200, 300, 50, "Human (Black) vs AI (White)", BUTTON_COLOR, BUTTON_HOVER),
            Button(WINDOW_WIDTH // 2 - 150, 270, 300, 50, "AI (Black) vs Human (White)", BUTTON_COLOR, BUTTON_HOVER),
            Button(WINDOW_WIDTH // 2 - 150, 340, 300, 50, "Human vs Human", BUTTON_COLOR, BUTTON_HOVER),
        ]
        
        self.diff_buttons = [
            Button(WINDOW_WIDTH // 2 - 200, 460, 120, 40, "Easy", BUTTON_COLOR, BUTTON_HOVER),
            Button(WINDOW_WIDTH // 2 - 60, 460, 120, 40, "Medium", BUTTON_COLOR, BUTTON_HOVER),
            Button(WINDOW_WIDTH // 2 + 80, 460, 120, 40, "Hard", BUTTON_COLOR, BUTTON_HOVER),
        ]
    
    def draw_board(self):
        """Draw the Go board"""
        # Background
        self.screen.fill(BOARD_COLOR)
        
        # Draw grid lines
        for i in range(BOARD_SIZE):
            # Vertical lines
            start_x = MARGIN + i * CELL_SIZE
            pygame.draw.line(self.screen, LINE_COLOR, 
                           (start_x, MARGIN), 
                           (start_x, MARGIN + (BOARD_SIZE - 1) * CELL_SIZE), 2)
            
            # Horizontal lines
            start_y = MARGIN + i * CELL_SIZE
            pygame.draw.line(self.screen, LINE_COLOR, 
                           (MARGIN, start_y), 
                           (MARGIN + (BOARD_SIZE - 1) * CELL_SIZE, start_y), 2)
        
        # Draw star points (if board has them)
        if BOARD_SIZE == 7:
            star_points = [(1, 1), (1, 5), (5, 1), (5, 5), (3, 3)]
            for row, col in star_points:
                x = MARGIN + col * CELL_SIZE
                y = MARGIN + row * CELL_SIZE
                pygame.draw.circle(self.screen, LINE_COLOR, (x, y), 4)
    
    def draw_stones(self):
        """Draw all stones on the board"""
        for row in range(BOARD_SIZE):
            for col in range(BOARD_SIZE):
                if self.board.board[row][col] != 0:
                    x = MARGIN + col * CELL_SIZE
                    y = MARGIN + row * CELL_SIZE
                    color = BLACK_STONE if self.board.board[row][col] == 1 else WHITE_STONE
                    
                    # Draw stone
                    pygame.draw.circle(self.screen, color, (x, y), CELL_SIZE // 3)
                    pygame.draw.circle(self.screen, LINE_COLOR, (x, y), CELL_SIZE // 3, 2)
                    
                    # Highlight last move
                    if self.last_move and self.last_move == (row, col):
                        pygame.draw.circle(self.screen, HIGHLIGHT_COLOR, (x, y), CELL_SIZE // 6, 3)
        
        # Draw hint
        if self.show_hint and self.hint_move:
            row, col = self.hint_move
            x = MARGIN + col * CELL_SIZE
            y = MARGIN + row * CELL_SIZE
            pygame.draw.circle(self.screen, HINT_COLOR, (x, y), CELL_SIZE // 4, 4)
    
    def draw_info(self):
        """Draw game information"""
        # Info panel background
        info_rect = pygame.Rect(0, 0, WINDOW_WIDTH, MARGIN // 2)
        pygame.draw.rect(self.screen, INFO_BG, info_rect)
        
        # Current player
        player_text = "Black's Turn" if self.board.current_player == 1 else "White's Turn"
        if self.ai_thinking:
            player_text = "AI Thinking..."
        if self.game_over:
            player_text = self.winner_text
        
        text_surface = INFO_FONT.render(player_text, True, TEXT_COLOR)
        self.screen.blit(text_surface, (20, 10))
        
        # Captured stones
        captured_text = f"Captured - Black: {self.board.captured_black}  White: {self.board.captured_white}"
        text_surface = SMALL_FONT.render(captured_text, True, TEXT_COLOR)
        self.screen.blit(text_surface, (WINDOW_WIDTH - 300, 10))
        
        # Score
        black_score, white_score = self.board.get_score()
        score_text = f"Score - Black: {black_score:.1f}  White: {white_score:.1f}"
        text_surface = SMALL_FONT.render(score_text, True, TEXT_COLOR)
        self.screen.blit(text_surface, (20, 35))
    
    def draw_buttons(self):
        """Draw all buttons"""
        for button in self.buttons.values():
            button.draw(self.screen)
    
    def draw_menu(self):
        """Draw main menu"""
        self.screen.fill(INFO_BG)
        
        # Title
        title_text = TITLE_FONT.render("Go Game - 7x7", True, TEXT_COLOR)
        title_rect = title_text.get_rect(center=(WINDOW_WIDTH // 2, 80))
        self.screen.blit(title_text, title_rect)
        
        # Mode selection
        mode_text = INFO_FONT.render("Select Game Mode:", True, TEXT_COLOR)
        self.screen.blit(mode_text, (WINDOW_WIDTH // 2 - 100, 150))
        
        # Difficulty selection
        diff_text = INFO_FONT.render("AI Difficulty:", True, TEXT_COLOR)
        self.screen.blit(diff_text, (WINDOW_WIDTH // 2 - 70, 420))
        
        # Highlight selected difficulty
        for i, button in enumerate(self.diff_buttons):
            button.color = (50, 200, 50) if i == self.difficulty - 1 else BUTTON_COLOR
        
        # Draw all buttons
        for button in self.mode_buttons + self.diff_buttons:
            button.draw(self.screen)
        
        # Handle events
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                return 'quit'
            
            # Check mode buttons
            if self.mode_buttons[0].handle_event(event):
                self.game_mode = 'pva_black'
                self.start_game()
                print("Starting: Human (Black) vs AI (White)")
            elif self.mode_buttons[1].handle_event(event):
                self.game_mode = 'pva_white'
                self.start_game()
                print("Starting: AI (Black) vs Human (White)")
            elif self.mode_buttons[2].handle_event(event):
                self.game_mode = 'pvp'
                self.start_game()
                print("Starting: Human vs Human")
            
            # Check difficulty buttons
            if self.diff_buttons[0].handle_event(event):
                self.difficulty = 1
                print("Difficulty set to: Easy")
            elif self.diff_buttons[1].handle_event(event):
                self.difficulty = 2
                print("Difficulty set to: Medium")
            elif self.diff_buttons[2].handle_event(event):
                self.difficulty = 3
                print("Difficulty set to: Hard")
            
            # Update hover states for all buttons
            if event.type == pygame.MOUSEMOTION:
                for button in self.mode_buttons + self.diff_buttons:
                    button.is_hovered = button.rect.collidepoint(event.pos)
        
        return 'menu'
    
    def start_game(self):
        """Initialize a new game"""
        self.board = GoBoard(BOARD_SIZE)
        self.show_menu = False
        self.game_over = False
        self.last_move = None
        self.hint_move = None
        self.show_hint = False
        
        # Create AI with selected difficulty
        if self.game_mode in ['pva_black', 'pva_white']:
            ai_player = 2 if self.game_mode == 'pva_black' else 1
            self.ai = MinimaxAI(depth=self.difficulty, player=ai_player)
            
            # If AI plays first, make its move
            if self.game_mode == 'pva_white':
                self.make_ai_move()
    
    def get_board_position(self, mouse_pos):
        """Convert mouse position to board coordinates"""
        x, y = mouse_pos
        col = round((x - MARGIN) / CELL_SIZE)
        row = round((y - MARGIN) / CELL_SIZE)
        
        if 0 <= row < BOARD_SIZE and 0 <= col < BOARD_SIZE:
            return row, col
        return None
    
    def make_ai_move(self):
        """Let AI make a move"""
        if self.ai and not self.game_over:
            self.ai_thinking = True
            pygame.display.flip()
            
            best_move, nodes, think_time = self.ai.get_best_move(self.board)
            
            if best_move:
                self.board.make_move(best_move[0], best_move[1])
                self.last_move = best_move
                print(f"AI move: {best_move}, evaluated {nodes} nodes in {think_time:.2f}s")
            
            self.ai_thinking = False
            self.check_game_over()
    
    def get_hint(self):
        """Get move suggestion from AI"""
        if self.ai:
            hint_ai = MinimaxAI(depth=self.difficulty, player=self.board.current_player)
            best_move, _, _ = hint_ai.get_best_move(self.board)
            return best_move
        return None
    
    def save_game(self):
        """Save current game state"""
        save_data = {
            'board': self.board.board,
            'current_player': self.board.current_player,
            'captured_black': self.board.captured_black,
            'captured_white': self.board.captured_white,
            'move_history': self.board.move_history,
            'game_mode': self.game_mode,
            'difficulty': self.difficulty,
            'timestamp': datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        }
        
        filename = f"go_game_save_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        with open(filename, 'w') as f:
            json.dump(save_data, f, indent=2)
        
        print(f"Game saved to {filename}")
        return filename
    
    def load_game(self, filename='go_game_save.json'):
        """Load game state from file"""
        try:
            with open(filename, 'r') as f:
                save_data = json.load(f)
            
            self.board.board = save_data['board']
            self.board.current_player = save_data['current_player']
            self.board.captured_black = save_data['captured_black']
            self.board.captured_white = save_data['captured_white']
            self.board.move_history = save_data['move_history']
            self.game_mode = save_data['game_mode']
            self.difficulty = save_data['difficulty']
            
            if self.game_mode in ['pva_black', 'pva_white']:
                ai_player = 2 if self.game_mode == 'pva_black' else 1
                self.ai = MinimaxAI(depth=self.difficulty, player=ai_player)
            
            print(f"Game loaded from {filename}")
            self.show_menu = False
            return True
        except FileNotFoundError:
            print(f"Save file {filename} not found")
            return False
    
    def check_game_over(self):
        """Check if game is over and determine winner"""
        # Simple check: if no valid moves for both players
        valid_moves = self.board.get_valid_moves()
        
        if not valid_moves:
            self.game_over = True
            black_score, white_score = self.board.get_score()
            
            if black_score > white_score:
                self.winner_text = f"Black Wins! ({black_score:.1f} vs {white_score:.1f})"
            elif white_score > black_score:
                self.winner_text = f"White Wins! ({white_score:.1f} vs {black_score:.1f})"
            else:
                self.winner_text = "Draw!"
    
    def handle_events(self):
        """Handle all pygame events"""
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                return False
            
            # Handle button clicks
            if self.buttons['undo'].handle_event(event):
                if self.board.undo_move():
                    # If playing against AI, undo twice to undo AI move too
                    if self.game_mode in ['pva_black', 'pva_white']:
                        self.board.undo_move()
                    self.last_move = None
                    self.game_over = False
            
            elif self.buttons['hint'].handle_event(event):
                self.show_hint = not self.show_hint
                if self.show_hint:
                    self.hint_move = self.get_hint()
            
            elif self.buttons['save'].handle_event(event):
                self.save_game()
            
            elif self.buttons['load'].handle_event(event):
                self.load_game()
            
            elif self.buttons['menu'].handle_event(event):
                self.show_menu = True
            
            # Handle board clicks
            elif event.type == pygame.MOUSEBUTTONDOWN and not self.ai_thinking and not self.game_over:
                pos = self.get_board_position(event.pos)
                if pos:
                    row, col = pos
                    
                    # Check if it's human's turn
                    human_turn = False
                    if self.game_mode == 'pvp':
                        human_turn = True
                    elif self.game_mode == 'pva_black' and self.board.current_player == 1:
                        human_turn = True
                    elif self.game_mode == 'pva_white' and self.board.current_player == 2:
                        human_turn = True
                    
                    if human_turn:
                        if self.board.make_move(row, col):
                            self.last_move = (row, col)
                            self.show_hint = False
                            self.hint_move = None
                            self.check_game_over()
                            
                            # Let AI respond
                            if self.game_mode in ['pva_black', 'pva_white'] and not self.game_over:
                                pygame.time.wait(300)  # Small delay for better UX
                                self.make_ai_move()
            
            # Update button hover states
            for button in self.buttons.values():
                if event.type == pygame.MOUSEMOTION:
                    button.is_hovered = button.rect.collidepoint(event.pos)
        
        return True
    
    def run(self):
        """Main game loop"""
        running = True
        
        while running:
            if self.show_menu:
                result = self.draw_menu()
                if result == 'quit':
                    running = False
            else:
                self.draw_board()
                self.draw_stones()
                self.draw_info()
                self.draw_buttons()
                
                running = self.handle_events()
            
            pygame.display.flip()
            self.clock.tick(FPS)
        
        pygame.quit()
        sys.exit()


def main():
    """Entry point"""
    game = GoGame()
    game.run()


if __name__ == "__main__":
    main()
