import chess
import pygame
import sys
import os
import numpy as np

class ChessAI:
    def __init__(self, depth: int = 3):
        self.depth = depth
        self.piece_values = {
            chess.PAWN: 100,
            chess.KNIGHT: 320,
            chess.BISHOP: 330,
            chess.ROOK: 500,
            chess.QUEEN: 900,
            chess.KING: 20000
        }

    def evaluate_board(self, board: chess.Board) -> float:
        if board.is_checkmate():
            return -10000 if board.turn == chess.WHITE else 10000

        score = 0
        for square in chess.SQUARES:
            piece = board.piece_at(square)
            if piece:
                value = self.piece_values[piece.piece_type]
                score += value if piece.color == chess.WHITE else -value

        score += self.evaluate_mobility(board)
        return score

    def evaluate_mobility(self, board: chess.Board) -> float:
        mobility_bonus = 0
        center_squares = [chess.D4, chess.E4, chess.D5, chess.E5]
        
        for square in center_squares:
            if board.piece_at(square):
                mobility_bonus += 50 if board.piece_at(square).color == chess.WHITE else -50

        mobility_bonus += len(list(board.legal_moves)) * 10
        return mobility_bonus

    def minimax(self, board: chess.Board, depth: int, maximizing_player: bool):
        if depth == 0 or board.is_game_over():
            return self.evaluate_board(board), None

        if maximizing_player:
            max_eval = float('-inf')
            best_move = None
            for move in board.legal_moves:
                board.push(move)
                eval_score, _ = self.minimax(board, depth - 1, False)
                board.pop()
                
                if eval_score > max_eval:
                    max_eval = eval_score
                    best_move = move
            return max_eval, best_move
        else:
            min_eval = float('inf')
            best_move = None
            for move in board.legal_moves:
                board.push(move)
                eval_score, _ = self.minimax(board, depth - 1, True)
                board.pop()
                
                if eval_score < min_eval:
                    min_eval = eval_score
                    best_move = move
            return min_eval, best_move

    def get_best_move(self, board: chess.Board):
        _, best_move = self.minimax(board, self.depth, board.turn == chess.WHITE)
        return best_move

class ChessGUI:
    def __init__(self):
        pygame.init()
        
        # Screen dimensions
        self.WIDTH = 800
        self.HEIGHT = 800
        self.DIMENSION = 8
        self.SQ_SIZE = self.HEIGHT // self.DIMENSION
        
        # Colors
        self.LIGHT_SQUARE = (240, 217, 181)  # Soft beige
        self.DARK_SQUARE = (181, 136, 99)    # Dark brown
        self.HIGHLIGHT_COLOR = (100, 249, 83, 100)  # Translucent green
        
        # Screen setup
        self.screen = pygame.display.set_mode((self.WIDTH, self.HEIGHT))
        pygame.display.set_caption('Chess AI')
        
        # Piece images
        self.IMAGES = {}
        self.load_images()
        
        # Game state
        self.board = chess.Board()
        self.ai = ChessAI(depth=3)
        
        # Move selection
        self.selected_square = None
        self.valid_moves = []

    def load_images(self):
        # Piece image loading
        pieces = ['wp', 'wR', 'wN', 'wB', 'wQ', 'wK', 
                  'bp', 'bR', 'bN', 'bB', 'bQ', 'bK']
        
        for piece in pieces:
            image_path = f'assets/pieces/{piece}.png'
            if os.path.exists(image_path):
                self.IMAGES[piece] = pygame.transform.scale(
                    pygame.image.load(image_path), 
                    (self.SQ_SIZE, self.SQ_SIZE)
                )

    def get_square_under_mouse(self):
        x, y = pygame.mouse.get_pos()
        col = x // self.SQ_SIZE
        row = y // self.SQ_SIZE
        return chess.square(col, 7 - row)

    def draw_board(self):
        # Draw checkered board
        for row in range(self.DIMENSION):
            for col in range(self.DIMENSION):
                color = self.LIGHT_SQUARE if (row + col) % 2 == 0 else self.DARK_SQUARE
                rect = pygame.Rect(col * self.SQ_SIZE, row * self.SQ_SIZE, 
                                   self.SQ_SIZE, self.SQ_SIZE)
                pygame.draw.rect(self.screen, color, rect)

    def draw_pieces(self):
        for square in chess.SQUARES:
            piece = self.board.piece_at(square)
            if piece:
                # Convert square to screen coordinates
                col = chess.square_file(square)
                row = 7 - chess.square_rank(square)
                
                color_prefix = 'w' if piece.color == chess.WHITE else 'b'
                piece_type = {
                    chess.PAWN: 'p', 
                    chess.ROOK: 'R', 
                    chess.KNIGHT: 'N', 
                    chess.BISHOP: 'B', 
                    chess.QUEEN: 'Q', 
                    chess.KING: 'K'
                }[piece.piece_type]
                
                image_key = color_prefix + piece_type
                if image_key in self.IMAGES:
                    self.screen.blit(
                        self.IMAGES[image_key], 
                        pygame.Rect(col * self.SQ_SIZE, row * self.SQ_SIZE, 
                                    self.SQ_SIZE, self.SQ_SIZE)
                    )

    def draw_valid_moves(self):
        if self.selected_square is not None:
            # Highlight selected square
            col = chess.square_file(self.selected_square)
            row = 7 - chess.square_rank(self.selected_square)
            
            highlight_surf = pygame.Surface((self.SQ_SIZE, self.SQ_SIZE), pygame.SRCALPHA)
            highlight_surf.fill(self.HIGHLIGHT_COLOR)
            self.screen.blit(highlight_surf, 
                             pygame.Rect(col * self.SQ_SIZE, row * self.SQ_SIZE, 
                                         self.SQ_SIZE, self.SQ_SIZE))

            # Draw possible moves
            for move in self.board.legal_moves:
                if move.from_square == self.selected_square:
                    to_col = chess.square_file(move.to_square)
                    to_row = 7 - chess.square_rank(move.to_square)
                    
                    move_surf = pygame.Surface((self.SQ_SIZE, self.SQ_SIZE), pygame.SRCALPHA)
                    move_surf.fill((100, 249, 83, 100))  # Translucent green
                    
                    self.screen.blit(move_surf, 
                                     pygame.Rect(to_col * self.SQ_SIZE, to_row * self.SQ_SIZE, 
                                                 self.SQ_SIZE, self.SQ_SIZE))

    def handle_mouse_click(self, square):
        if self.selected_square is None:
            # First click - select piece
            piece = self.board.piece_at(square)
            if piece and piece.color == self.board.turn:
                self.selected_square = square
        else:
            # Second click - attempt move
            move = chess.Move(self.selected_square, square)
            
            # Handle promotions
            if move in self.board.legal_moves:
                self.board.push(move)
                
                # AI move
                if not self.board.is_game_over():
                    ai_move = self.ai.get_best_move(self.board)
                    self.board.push(ai_move)
            
            self.selected_square = None

    def game_loop(self):
        clock = pygame.time.Clock()
        running = True

        while running:
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    running = False
                
                # Mouse click handling
                if event.type == pygame.MOUSEBUTTONDOWN:
                    if event.button == 1:  # Left mouse button
                        square = self.get_square_under_mouse()
                        self.handle_mouse_click(square)

            # Clear screen
            self.screen.fill((255, 255, 255))
            
            # Draw game elements
            self.draw_board()
            self.draw_pieces()
            self.draw_valid_moves()
            
            # Game over check
            if self.board.is_checkmate():
                font = pygame.font.Font(None, 74)
                winner = "Black" if self.board.turn == chess.WHITE else "White"
                text = font.render(f"{winner} Wins by Checkmate!", True, (255, 0, 0))
                text_rect = text.get_rect(center=(self.WIDTH/2, self.HEIGHT/2))
                self.screen.blit(text, text_rect)
            
            pygame.display.flip()
            clock.tick(60)

        pygame.quit()
        sys.exit()

def main():
    chess_gui = ChessGUI()
    chess_gui.game_loop()

if __name__ == "__main__":
    main()