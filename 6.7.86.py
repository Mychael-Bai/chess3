import tkinter as tk
import os
import pygame.mixer

class ChineseChess:

    def __init__(self):

        # Add these new variables for replay functionality
        self.move_history = []  # List to store moves for current game
        self.replay_mode = False
        self.current_replay_index = 0
        self.saved_board_states = []  # To store board states for replay
        self.game_over = False  # Add this line

        pygame.mixer.init()

        # Get absolute path
        current_dir = os.path.dirname(os.path.abspath(__file__))
        sound_path = os.path.join(current_dir, "piece_sound5.wav")

        try:
            if os.path.exists(sound_path):
                self.move_sound = pygame.mixer.Sound(sound_path)
                print(f"Sound loaded successfully from: {sound_path}")
            else:
                print(f"Sound file not found at: {sound_path}")
                print(f"Current directory: {current_dir}")
                print(f"Files in directory: {os.listdir(current_dir)}")
                self.move_sound = None
        except Exception as e:
            print(f"Error loading sound: {str(e)}")
            self.move_sound = None

        self.window = tk.Tk()
        self.window.title("Chinese Chess 6.7.86(amazing yet not strong)")
        
        self.game_history = []  # List to store all games
        
        # Board dimensions and styling
        self.board_size = 9  # 9x10 board
        self.cell_size = 54
        self.piece_radius = 23  # Smaller pieces to fit on intersections
        self.board_margin = 60  # Margin around the board
        # Calculate total canvas size including margins
        self.canvas_width = self.cell_size * 8 + 2 * self.board_margin
        self.canvas_height = self.cell_size * 9 + 2 * self.board_margin
        
        # Create main horizontal frame to hold board and button side by side
        self.main_frame = tk.Frame(self.window)
        self.main_frame.pack(pady=20)
        
        # Create left frame for the board
        self.board_frame = tk.Frame(self.main_frame)
        self.board_frame.pack(side=tk.LEFT, padx=(20, 0))
        
        # Create canvas for the game board
        self.canvas = tk.Canvas(
            self.board_frame, 
            width=self.canvas_width,
            height=self.canvas_height,
            bg='#f0d5b0'
        )
        self.canvas.pack()
        
        # Create right frame for the button with padding
        self.button_frame = tk.Frame(self.main_frame)
        self.button_frame.pack(side=tk.LEFT, padx=20)  # Add padding between board and button

        # Create restart button
        button_size = self.piece_radius * 2  # Same size as a piece
        self.restart_button = tk.Button(
            self.button_frame,
            text="再来一盘",  # Keep the original Chinese text
            command=self.restart_game,
            font=('SimSun', 12),  # Chinese font, size 16
            width=8,
            height=1
        )
        self.restart_button.pack()
        
        # Create replay button
        self.replay_button = tk.Button(
            self.button_frame,
            text="复盘",
            command=self.start_replay,
            font=('SimSun', 12),
            width=8,
            height=1
        )
        self.replay_button.pack(pady=5)

        # Create previous move button (initially disabled)
        self.prev_move_button = tk.Button(
            self.button_frame,
            text="上一步",
            command=self.prev_replay_move,
            font=('SimSun', 12),
            width=8,
            height=1,
            state=tk.DISABLED
        )
        self.prev_move_button.pack(pady=5)
                                
        # Create next move button (initially disabled)
        self.next_move_button = tk.Button(
            self.button_frame,
            text="下一步",
            command=self.next_replay_move,
            font=('SimSun', 12),
            width=8,
            height=1,
            state=tk.DISABLED
        )
        self.next_move_button.pack(pady=5)

        self.set_button_states_for_gameplay()

        # Initialize game state
        self.selected_piece = None
        self.highlighted_positions = []
        self.current_player = 'red'  # Red moves first
        self.initialize_board()
        self.draw_board()
                    
        # Bind mouse event
        self.canvas.bind('<Button-1>', self.on_click)

    def show_centered_warning(self, title, message):
        """Shows a warning messagebox centered on the game board"""
        # Wait for any pending events to be processed
        self.window.update_idletasks()
        
        # Create custom messagebox
        warn_window = tk.Toplevel()
        warn_window.title(title)
        warn_window.geometry('300x100')  # Set size of warning window
        
        # Configure the warning window
        warn_window.transient(self.window)
        warn_window.grab_set()
        
        # Add message and OK button
        
        # Add message and OK button with custom fonts
        tk.Label(
            warn_window, 
            text=message, 
            padx=20, 
            pady=10,
            font=('SimSun', 12),  # Chinese font, size 16, bold
            fg='#000000'  # Black text
        ).pack()
        
        tk.Button(warn_window, text="OK", command=warn_window.destroy, width=10).pack(pady=10)
        
        # Wait for the warning window to be ready
        warn_window.update_idletasks()
        
        # Get the coordinates of the main window and board
        window_x = self.window.winfo_x()
        window_y = self.window.winfo_y()
        
        # Calculate the board's center position
        board_x = window_x + self.board_frame.winfo_x() + self.canvas.winfo_x()
        board_y = window_y + self.board_frame.winfo_y() + self.canvas.winfo_y()
        board_width = self.canvas.winfo_width()
        board_height = self.canvas.winfo_height()
        
        # Get the size of the warning window
        warn_width = warn_window.winfo_width()
        warn_height = warn_window.winfo_height()
        
        # Calculate the center position
        x = board_x + (board_width - warn_width) // 2
        y = board_y + (board_height - warn_height) // 2
        
        # Position the warning window
        warn_window.geometry(f"+{x}+{y}")
        
        # Make window modal and wait for it to close
        warn_window.focus_set()
        warn_window.wait_window()        

    def evaluate_checkmate_potential(self, color):
        """Evaluate how close we are to achieving checkmate"""
        opposing_color = 'red' if color == 'black' else 'black'
        kings = self.find_kings()
        opponent_king_pos = kings[0] if color == 'black' else kings[1]
        score = 0
        
        if not opponent_king_pos:
            return 0
            
        king_row, king_col = opponent_king_pos
        
        # Count attacking pieces near opponent's king
        attackers = 0
        attack_value = 0
        for dr in range(-2, 3):
            for dc in range(-2, 3):
                r, c = king_row + dr, king_col + dc
                if 0 <= r < 10 and 0 <= c < 9:
                    piece = self.board[r][c]
                    if piece and piece[0] == color[0].upper():
                        attackers += 1
                        # Higher value for powerful pieces near the king
                        if piece[1] in ['車', '馬', '炮']:
                            attack_value += 50
                        else:
                            attack_value += 20
        
        score += attackers * 30 + attack_value
        
        # Bonus if opponent's king has limited mobility
        escape_moves = 0
        for dr in [-1, 0, 1]:
            for dc in [-1, 0, 1]:
                r, c = king_row + dr, king_col + dc
                if 0 <= r < 10 and 0 <= c < 9:
                    if (r, c) != (king_row, king_col):
                        if self.is_valid_move((king_row, king_col), (r, c)):
                            # Try the move
                            original_piece = self.board[r][c]
                            self.board[r][c] = self.board[king_row][king_col]
                            self.board[king_row][king_col] = None
                            
                            if not self.is_in_check(opposing_color):
                                escape_moves += 1
                                
                            # Restore the position
                            self.board[king_row][king_col] = self.board[r][c]
                            self.board[r][c] = original_piece
        
        # Higher score when opponent has fewer escape moves
        score += (9 - escape_moves) * 50
        
        # Extra bonus if opponent is in check
        if self.is_in_check(opposing_color):
            score += 200
            
        return score

    def handle_game_end(self):
        """Handle end of game tasks"""
        self.game_over = True
        self.show_centered_warning("游戏结束", "绝 杀 ！")
        # Enable replay button after checkmate
        self.replay_button.config(state=tk.NORMAL)

    def set_button_states_for_gameplay(self):
        """Set button states for normal gameplay"""
        self.restart_button.config(state=tk.NORMAL)      # Keep restart button enabled

        # Enable replay button if game is over, disable otherwise
        if self.game_over:
            self.replay_button.config(state=tk.NORMAL)
        else:
            self.replay_button.config(state=tk.DISABLED)
                    
        self.prev_move_button.config(state=tk.DISABLED)  # Disable previous move button
        self.next_move_button.config(state=tk.DISABLED)  # Disable next move button

    def add_move_to_history(self, from_pos, to_pos, piece):
        """Record a move and board state"""
        move = {
            'from_pos': from_pos,
            'to_pos': to_pos,
            'piece': piece,
            'board_state': [row[:] for row in self.board]  # Deep copy of board
        }
        self.move_history.append(move)

    def start_replay(self):


        """Start replay mode"""
        if not self.move_history:
            self.show_centered_warning("提示", "没有可以回放的历史记录")
            return
            
        self.replay_mode = True
        self.current_replay_index = 0
        self.highlighted_positions = []  # Clear all highlights

        # Disable normal game buttons during replay
        self.replay_button.config(state=tk.DISABLED)
        self.next_move_button.config(state=tk.NORMAL)
        self.prev_move_button.config(state=tk.DISABLED)
        
        # Reset board to initial state
        self.initialize_board()
        self.draw_board()

    def next_replay_move(self):
        """Show next move in replay"""
        if not self.replay_mode or self.current_replay_index >= len(self.move_history):
            self.end_replay()
            return
            
        move = self.move_history[self.current_replay_index]
        # Restore board state
        for i in range(len(self.board)):
            self.board[i] = move['board_state'][i][:]
        
        # Highlight the move
        self.highlighted_positions = [move['from_pos'], move['to_pos']]
        self.current_replay_index += 1
        
        # Enable previous button as we're not at the start
        self.prev_move_button.config(state=tk.NORMAL)
        
        # If last move
        if self.current_replay_index >= len(self.move_history):
            self.next_move_button.config(state=tk.DISABLED)
        
        self.draw_board()

    def prev_replay_move(self):
        """Show previous move in replay"""
        if not self.replay_mode or self.current_replay_index <= 0:
            return
            
        self.current_replay_index -= 1
        
        # If at the beginning, disable prev button
        if self.current_replay_index == 0:
            self.prev_move_button.config(state=tk.DISABLED)
        
        # Always enable next button when we go back
        self.next_move_button.config(state=tk.NORMAL)
        
        # If there are moves to show, display the board state at that index
        if self.current_replay_index > 0:
            move = self.move_history[self.current_replay_index - 1]
            # Restore board state
            for i in range(len(self.board)):
                self.board[i] = move['board_state'][i][:]
        else:
            # If we're at the beginning, show initial board
            self.initialize_board()
        
        # Update highlights if not at the beginning
        if self.current_replay_index > 0:
            move = self.move_history[self.current_replay_index - 1]
            self.highlighted_positions = [move['from_pos'], move['to_pos']]
        else:
            self.highlighted_positions = []
        
        self.draw_board()

    def end_replay(self):
        """End replay mode"""
        self.replay_mode = False
        self.current_replay_index = 0

        # Set button states for normal gameplay
        self.set_button_states_for_gameplay()
        
        self.initialize_board()
        self.draw_board()
            
    def on_click(self, event):

        if self.replay_mode or self.game_over:  # Add game_over check
            return  # Ignore clicks when game is over or in replay mode

        # Convert click coordinates to board position (remove the center_offset from here)
        col = round((event.x - self.board_margin) / self.cell_size)
        row = round((event.y - self.board_margin) / self.cell_size)
        
        # Ensure click is within board bounds
        if 0 <= row < 10 and 0 <= col < 9:
            clicked_piece = self.board[row][col]
            
            # If a piece is already selected
            if self.selected_piece:
                start_row, start_col = self.selected_piece
                
                # If clicking on another piece of the same color, select that piece instead
                if (clicked_piece and 
                    clicked_piece[0] == self.current_player[0].upper()):
                    self.selected_piece = (row, col)
                    self.highlighted_positions = [(row, col)]  # Reset highlights for new selection
                    self.draw_board()
                # If clicking on a valid move position
                elif self.is_valid_move(self.selected_piece, (row, col)):
                    # Store the current state to check for check
                    original_piece = self.board[row][col]
                    
                    # Make the move temporarily
                    self.board[row][col] = self.board[start_row][start_col]
                    self.board[start_row][start_col] = None
                    
                    # Check if the move puts own king in check
                    if self.is_in_check(self.current_player):
                        # Undo the move if it puts own king in check
                        self.board[start_row][start_col] = self.board[row][col]
                        self.board[row][col] = original_piece


                        if self.current_player == 'red':
                            self.show_centered_warning("Invalid Move", "你正在被将军")
                        else:
                            self.show_centered_warning("Invalid Move", "黑方正在被将军")

                    else:
                        # Keep both the original and new positions highlighted
                        self.highlighted_positions = [(start_row, start_col), (row, col)]
                              

                                        
                        # Play move sound
                        if hasattr(self, 'move_sound') and self.move_sound:
                            self.move_sound.play()
                            

                        # Switch players
                        self.current_player = 'black' if self.current_player == 'red' else 'red'
                        
                        # Add this line to record the move
                        self.add_move_to_history(
                            (start_row, start_col),
                            (row, col),
                            self.board[row][col]
                        )

                        # Add this code:
                        if self.current_player == 'black':
                            # Add a small delay before AI move
                            self.window.after(500, self.make_ai_move)


                    # Reset selected piece
                    self.selected_piece = None
                    
                    # Redraw board
                    self.draw_board()
            
            # If no piece is selected and clicked on own piece, select it
            elif clicked_piece and clicked_piece[0] == self.current_player[0].upper():
                self.selected_piece = (row, col)
                self.highlighted_positions = [(row, col)]  # Initialize highlights with selected piece
                self.draw_board()        

    def evaluate_board(self):
                
        piece_values = {
            '將': 0, '帥': 0,      # Kings - valued at 0 since they can't be captured
            '車': 900,            # Chariot - most valuable piece
            '馬': 400,            # Horse
            '炮': 500,            # Cannon
            '象': 200, '相': 200,  # Elephants
            '士': 200, '仕': 200,  # Advisors
            '卒': 100, '兵': 100   # Pawns - base value, will get bonus when advanced
        }
        
        score = 0
        for row in range(10):
            for col in range(9):
                piece = self.board[row][col]
                if piece:
                    value = piece_values[piece[1]]
                    if piece[0] == 'B':  # Black pieces (AI)
                        score += value
                        # Bonus for advanced positions
                        if piece[1] in ['卒', '炮']:
                            score += (row * 10)  # Encourage forward movement
                    else:  # Red pieces (Human)
                        score -= value
                        if piece[1] in ['兵', '炮']:
                            score -= ((9 - row) * 10)
        
        return score

    def get_all_valid_moves(self, color):
        """Get all valid moves for a given color"""
        moves = []
        for from_row in range(10):
            for from_col in range(9):
                piece = self.board[from_row][from_col]
                if piece and piece[0] == color[0].upper():
                    for to_row in range(10):
                        for to_col in range(9):
                            if self.is_valid_move((from_row, from_col), (to_row, to_col)):
                                moves.append(((from_row, from_col), (to_row, to_col)))
        return moves

    def _move_sorting_score(self, move):
        from_pos, to_pos = move
        from_piece = self.board[from_pos[0]][from_pos[1]]
        to_piece = self.board[to_pos[0]][to_pos[1]]
        
        score = 0
        piece_values = {
            '將': 0, '帥': 0,
            '車': 900,
            '馬': 400,
            '炮': 500,
            '象': 200, '相': 200,
            '士': 200, '仕': 200,
            '卒': 100, '兵': 100
        }
        
        # Try the move
        original_piece = self.board[to_pos[0]][to_pos[1]]
        self.board[to_pos[0]][to_pos[1]] = from_piece
        self.board[from_pos[0]][from_pos[1]] = None
        
        # Highest priority for checkmate
        if self.is_checkmate('red'):
            score += 10000
        # High priority for check
        elif self.is_in_check('red'):
            score += 1000
            # Additional bonus if the opponent has limited escape moves
            escape_moves = 0
            kings = self.find_kings()
            king_pos = kings[0]  # Red king
            if king_pos:
                king_row, king_col = king_pos
                for dr in [-1, 0, 1]:
                    for dc in [-1, 0, 1]:
                        r, c = king_row + dr, king_col + dc
                        if 0 <= r < 10 and 0 <= c < 9:
                            if self.is_valid_move((king_row, king_col), (r, c)):
                                escape_moves += 1
            score += (9 - escape_moves) * 100
        
        # Evaluate material gain/loss
        if to_piece:  # Capture move
            score += piece_values[to_piece[1]] * 10
        
        # Position improvement
        if from_piece[1] in ['車', '馬', '炮']:
            if 2 <= to_pos[1] <= 6:  # Central files
                score += 30
            if from_piece[0] == 'B' and to_pos[0] > 4:  # Crossing river
                score += 40
        
        # Restore position
        self.board[from_pos[0]][from_pos[1]] = from_piece
        self.board[to_pos[0]][to_pos[1]] = original_piece
        
        return score

    def evaluate_king_safety(self, color):
        """Evaluate king safety and surrounding protection"""
        kings = self.find_kings()
        king_pos = kings[1] if color == 'black' else kings[0]
        if not king_pos:
            return -9999
        
        king_row, king_col = king_pos
        safety = 0
        
        # Check protecting pieces
        for dr in [-1, 0, 1]:
            for dc in [-1, 0, 1]:
                r, c = king_row + dr, king_col + dc
                if 0 <= r < 10 and 0 <= c < 9:
                    piece = self.board[r][c]
                    if piece and piece[0] == color[0].upper():
                        safety += 30
        
        # Penalty for exposed king
        if self.is_in_check(color):
            safety -= 200
        
        return safety

    def evaluate_position_simple(self):
        piece_values = {
            '將': 0, '帥': 0,
            '車': 900,
            '馬': 400,
            '炮': 500,
            '象': 200, '相': 200,
            '士': 200, '仕': 200,
            '卒': 100, '兵': 100
        }
        
        score = 0
        
        # Material and position evaluation
        for row in range(10):
            for col in range(9):
                piece = self.board[row][col]
                if piece:
                    value = piece_values[piece[1]]
                    position_bonus = 0
                    
                    if piece[1] in ['車', '馬', '炮']:
                        # Bonus for controlling center files
                        if 2 <= col <= 6:
                            position_bonus += 20
                        # Bonus for penetration
                        if piece[0] == 'B' and row > 4:
                            position_bonus += 50
                        elif piece[0] == 'R' and row < 5:
                            position_bonus += 50
                    
                    # Calculate piece safety
                    safety_score = self.evaluate_piece_safety(row, col, piece, 'black' if piece[0] == 'B' else 'red')
                    
                    if piece[0] == 'B':  # Black pieces (AI)
                        score += value + position_bonus + safety_score
                        if piece[1] == '卒':
                            if row > 4:  # Crossed river
                                score += 50 + (row - 4) * 20
                            else:
                                score += row * 10
                    else:  # Red pieces (Human)
                        score -= value + position_bonus + safety_score
                        if piece[1] == '兵':
                            if row < 5:
                                score -= 50 + (4 - row) * 20
                            else:
                                score -= (9 - row) * 10
        
        # Add checkmate potential evaluation
        checkmate_score = self.evaluate_checkmate_potential('black') - self.evaluate_checkmate_potential('red')
        score += checkmate_score * 2  # Give high weight to checkmate potential
        
        # King safety evaluation
        king_safety = self.evaluate_king_safety('black') - self.evaluate_king_safety('red')
        score += king_safety
        
        return score

    def minimax(self, depth, alpha, beta, maximizing_player):
        """Minimax algorithm with alpha-beta pruning and simplified evaluation"""
        if depth == 0:
            return self.evaluate_position_simple()
        
        if maximizing_player:
            max_eval = float('-inf')
            moves = self.get_all_valid_moves('black')
            
            for from_pos, to_pos in moves:
                # Store and make move
                moving_piece = self.board[from_pos[0]][from_pos[1]]
                captured_piece = self.board[to_pos[0]][to_pos[1]]
                self.board[to_pos[0]][to_pos[1]] = moving_piece
                self.board[from_pos[0]][from_pos[1]] = None
                
                if not self.is_in_check('black'):
                    eval = self.minimax(depth - 1, alpha, beta, False)
                    max_eval = max(max_eval, eval)
                    alpha = max(alpha, eval)
                
                # Restore position
                self.board[from_pos[0]][from_pos[1]] = moving_piece
                self.board[to_pos[0]][to_pos[1]] = captured_piece
                
                if beta <= alpha:
                    break
            return max_eval if max_eval != float('-inf') else self.evaluate_position_simple()
        else:
            min_eval = float('inf')
            moves = self.get_all_valid_moves('red')
            
            for from_pos, to_pos in moves:
                moving_piece = self.board[from_pos[0]][from_pos[1]]
                captured_piece = self.board[to_pos[0]][to_pos[1]]
                self.board[to_pos[0]][to_pos[1]] = moving_piece
                self.board[from_pos[0]][from_pos[1]] = None
                
                if not self.is_in_check('red'):
                    eval = self.minimax(depth - 1, alpha, beta, True)
                    min_eval = min(min_eval, eval)
                    beta = min(beta, eval)
                
                # Restore position
                self.board[from_pos[0]][from_pos[1]] = moving_piece
                self.board[to_pos[0]][to_pos[1]] = captured_piece
                
                if beta <= alpha:
                    break
            return min_eval if min_eval != float('inf') else self.evaluate_position_simple()

    def evaluate_piece_safety(self, row, col, piece, color):
        """Evaluate how safe a piece is in its current position"""
        safety_score = 0
        piece_values = {
            '將': 0, '帥': 0,
            '車': 900,
            '馬': 400,
            '炮': 500,
            '象': 200, '相': 200,
            '士': 200, '仕': 200,
            '卒': 100, '兵': 100
        }
        
        # Check if the piece is under attack
        is_attacked = False
        defenders = 0
        attackers = 0
        
        # Count attackers and defenders
        for r in range(10):
            for c in range(9):
                checking_piece = self.board[r][c]
                if checking_piece:
                    if checking_piece[0] != color[0].upper():  # Enemy piece
                        # If enemy can capture this piece
                        if self.is_valid_move((r, c), (row, col)):
                            attackers += 1
                            is_attacked = True
                            # Penalty based on value difference
                            if piece_values[checking_piece[1]] < piece_values[piece[1]]:
                                safety_score -= 50  # Extra penalty if threatened by lesser piece
                    else:  # Friendly piece
                        if self.is_valid_move((r, c), (row, col)):
                            defenders += 1
                            safety_score += 20  # Bonus for each defender
        
        # Heavy penalty if attacked and not defended
        if is_attacked and defenders == 0:
            safety_score -= 200
        
        # Bonus for defended pieces
        if defenders > attackers:
            safety_score += 100
            
        return safety_score

    def make_ai_move(self):
        import time
        
        start_time = time.time()
        max_time = 5.0  # Reduced from 10.0 to make moves faster
                
        best_score = float('-inf')
        best_move = None
        best_moving_piece = None
        
        # Get all valid moves and sort them by preliminary evaluation
        moves = self.get_all_valid_moves('black')
        if not moves:
            return
        
        # Sort moves by preliminary evaluation
        moves.sort(key=self._move_sorting_score, reverse=True)
        
        # Check if opponent is in check
        is_check = self.is_in_check('red')
        max_depth = 6 if is_check else 4  # Search deeper when opponent is in check
        
        # Iterative deepening
        for search_depth in range(2, max_depth + 1):
            if time.time() - start_time > max_time:
                break
            
            alpha = float('-inf')
            beta = float('inf')
            
            for from_pos, to_pos in moves:
                if time.time() - start_time > max_time:
                    break
                
                moving_piece = self.board[from_pos[0]][from_pos[1]]
                captured_piece = self.board[to_pos[0]][to_pos[1]]
                
                # Make temporary move
                self.board[to_pos[0]][to_pos[1]] = moving_piece
                self.board[from_pos[0]][from_pos[1]] = None
                
                if not self.is_in_check('black'):
                    score = self.minimax(search_depth - 1, alpha, beta, False)
                    
                    if score > best_score:
                        best_score = score
                        best_move = (from_pos, to_pos)
                        best_moving_piece = moving_piece
                
                # Restore position
                self.board[from_pos[0]][from_pos[1]] = moving_piece
                self.board[to_pos[0]][to_pos[1]] = captured_piece
        
        # Make the best move found
        if best_move:
            from_pos, to_pos = best_move
            # Make the actual move
            self.board[to_pos[0]][to_pos[1]] = best_moving_piece
            self.board[from_pos[0]][from_pos[1]] = None
            
            # Play sound if available
            if hasattr(self, 'move_sound') and self.move_sound:
                self.move_sound.play()
            
            # Update game state
            self.highlighted_positions = [from_pos, to_pos]
            self.current_player = 'red'
                        
            # Add this line to record the AI move
            self.add_move_to_history(from_pos, to_pos, best_moving_piece)

            # Update display
            self.draw_board()
            
        # Check if the opponent is now in checkmate
        if self.is_checkmate(self.current_player):
            self.handle_game_end()

    def is_checkmate(self, color):
        """
        Check if the given color is in checkmate.
        Returns True if the player has no legal moves to escape check.
        """
        # If not in check, can't be checkmate
        if not self.is_in_check(color):
            return False
            
        # Try every possible move for every piece of the current player
        for row in range(10):
            for col in range(9):
                piece = self.board[row][col]
                if piece and piece[0] == color[0].upper():  # If it's current player's piece
                    # Try all possible destinations
                    for to_row in range(10):
                        for to_col in range(9):
                            if self.is_valid_move((row, col), (to_row, to_col)):
                                # Try the move
                                original_piece = self.board[to_row][to_col]
                                self.board[to_row][to_col] = piece
                                self.board[row][col] = None
                                
                                # Check if still in check
                                still_in_check = self.is_in_check(color)
                                
                                # Undo the move
                                self.board[row][col] = piece
                                self.board[to_row][to_col] = original_piece
                                
                                # If any move gets out of check, not checkmate
                                if not still_in_check:
                                    return False
        
        # If no legal moves found, it's checkmate
            
        self.game_over = True  # Add this line

        return True

    # YELLOW HIGHTLIGHT(2nd modification)

    def highlight_piece(self, row, col):
        """Draw a yellow highlight around the selected piece"""
        # Calculate position on intersections
        x = self.board_margin + col * self.cell_size
        y = self.board_margin + row * self.cell_size
        
        # Create a yellow square around the piece
        self.canvas.create_rectangle(
            x - self.piece_radius - 2,
            y - self.piece_radius - 2,
            x + self.piece_radius + 2,
            y + self.piece_radius + 2,
            outline='yellow',
            width=2,
            tags='highlight'
        )    

    def initialize_board(self):
        # Initialize empty board
        self.board = [[None for _ in range(9)] for _ in range(10)]
        
        # Set up initial piece positions
        self.setup_pieces()
        
    def setup_pieces(self):
        # Red pieces (bottom)
        red_pieces = {
            (9, 0): 'R車', (9, 1): 'R馬', (9, 2): 'R相',
            (9, 3): 'R仕', (9, 4): 'R帥', (9, 5): 'R仕',
            (9, 6): 'R相', (9, 7): 'R馬', (9, 8): 'R車',
            (7, 1): 'R炮', (7, 7): 'R炮',
            (6, 0): 'R兵', (6, 2): 'R兵', (6, 4): 'R兵',
            (6, 6): 'R兵', (6, 8): 'R兵'
        }
        
        # Black pieces (top)
        black_pieces = {
            (0, 0): 'B車', (0, 1): 'B馬', (0, 2): 'B象',
            (0, 3): 'B士', (0, 4): 'B將', (0, 5): 'B士',
            (0, 6): 'B象', (0, 7): 'B馬', (0, 8): 'B車',
            (2, 1): 'B炮', (2, 7): 'B炮',
            (3, 0): 'B卒', (3, 2): 'B卒', (3, 4): 'B卒',
            (3, 6): 'B卒', (3, 8): 'B卒'
        }
        
        # Place pieces on board
        for pos, piece in red_pieces.items():
            row, col = pos
            self.board[row][col] = piece
            
        for pos, piece in black_pieces.items():
            row, col = pos
            self.board[row][col] = piece

    def draw_board(self):
        # Clear canvas
        self.canvas.delete("all")
        
        # Draw the outer border
        self.canvas.create_rectangle(
            self.board_margin, self.board_margin,
            self.canvas_width - self.board_margin,
            self.canvas_height - self.board_margin,
            width=1
        )

        self.canvas.create_rectangle(
            self.board_margin - 5, self.board_margin - 5,
            self.canvas_width - self.board_margin + 6,
            self.canvas_height - self.board_margin + 6,
            width=2
        )

        # clear hightlight(3rd modification)
        self.canvas.delete('highlight')

        # add hightlight(4th modification)
        if self.selected_piece:
            row, col = self.selected_piece
            self.highlight_piece(row, col)

        # Draw grid lines
        for i in range(10):  # Horizontal lines
            y = self.board_margin + i * self.cell_size
            self.canvas.create_line(
                self.board_margin, y,
                self.canvas_width - self.board_margin, y
            )
            
        for i in range(9):  # Vertical lines
            x = self.board_margin + i * self.cell_size
            # Draw vertical lines with river gap
            self.canvas.create_line(
                x, self.board_margin,
                x, self.board_margin + 4 * self.cell_size
            )
            self.canvas.create_line(
                x, self.board_margin + 5 * self.cell_size,
                x, self.canvas_height - self.board_margin
            )

        # Draw palace diagonal lines
        # Top palace
        self.canvas.create_line(
            self.board_margin + 3 * self.cell_size, self.board_margin,
            self.board_margin + 5 * self.cell_size, self.board_margin + 2 * self.cell_size
        )
        self.canvas.create_line(
            self.board_margin + 5 * self.cell_size, self.board_margin,
            self.board_margin + 3 * self.cell_size, self.board_margin + 2 * self.cell_size
        )
        
        # Bottom palace
        self.canvas.create_line(
            self.board_margin + 3 * self.cell_size, self.canvas_height - self.board_margin - 2 * self.cell_size,
            self.board_margin + 5 * self.cell_size, self.canvas_height - self.board_margin
        )
        self.canvas.create_line(
            self.board_margin + 5 * self.cell_size, self.canvas_height - self.board_margin - 2 * self.cell_size,
            self.board_margin + 3 * self.cell_size, self.canvas_height - self.board_margin
        )

        # Draw river text
        river_y = self.board_margin + 4.5 * self.cell_size
        self.canvas.create_text(
            self.canvas_width / 2, river_y,
            text="楚   河        漢   界",
            font=('KaiTi', 23)
        )
        
        # Draw pieces on intersections
        for row in range(10):
            for col in range(9):
                if self.board[row][col]:
                    # Calculate position on intersections
                    x = self.board_margin + col * self.cell_size
                    y = self.board_margin + row * self.cell_size
                    
                    # Draw piece circle
                    color = 'red' if self.board[row][col][0] == 'R' else 'black'
                    self.canvas.create_oval(
                        x - self.piece_radius, y - self.piece_radius,
                        x + self.piece_radius, y + self.piece_radius,
                        fill='white',
                        outline=color,
                        width=2
                    )
                    
                    # Draw piece text
                    piece_text = self.board[row][col][1]
                    text_color = 'red' if self.board[row][col][0] == 'R' else 'black'
                    self.canvas.create_text(
                        x, y,
                        text=piece_text,
                        fill=text_color,
                        font=('KaiTi', 25, 'bold')
                    )
            
        # Modify the highlight section to show all highlighted positions
        self.canvas.delete('highlight')
        for pos in self.highlighted_positions:
            row, col = pos
            self.highlight_piece(row, col)

        # Draw column numbers at top and bottom
        # List of Chinese numbers for red side (bottom)
        red_numbers = ['九', '八', '七', '六', '五', '四', '三', '二', '一']
        # List of Arabic numbers for black side (top)
        black_numbers = ['1', '2', '3', '4', '5', '6', '7', '8', '9']

        # Draw top numbers (for black)
        for col, num in enumerate(black_numbers):
            x = self.board_margin + col * self.cell_size
            y = self.board_margin - 37  # Change from -15 to -25 to position numbers higher
            self.canvas.create_text(
                x, y,
                text=num,
                fill='black',
                font=('Arial', 12)
            )

        # Draw bottom numbers (for red)
        for col, num in enumerate(red_numbers):
            x = self.board_margin + col * self.cell_size
            y = self.canvas_height - self.board_margin + 37  # Change from +15 to +25 to position numbers lower
            self.canvas.create_text(
                x, y,
                text=num,
                fill='black',
                font=('Arial', 12)
            )

    def show_victory_message(self, winner):
        """Shows a victory message with special styling"""
        # Wait for any pending events to be processed
        self.window.update_idletasks()
        
        # Create victory window
        victory_window = tk.Toplevel()
        victory_window.title("胜利")
        victory_window.geometry('400x150')  # Larger size for victory message
        
        # Configure the victory window
        victory_window.transient(self.window)
        victory_window.grab_set()
        
        # Add message with larger font and decorative style
        message_frame = tk.Frame(victory_window)
        message_frame.pack(expand=True, fill='both')
        
        tk.Label(
            message_frame,
            text=f"🎊 恭喜 🎊\n{winner}赢了！",
            font=('Arial', 16, 'bold'),
            pady=20
        ).pack()
        
        # Add OK button with special styling
        tk.Button(
            message_frame,
            text="开始新游戏",
            command=victory_window.destroy,
            width=15,
            height=2,
            relief=tk.RAISED,
            bg='#f0f0f0'
        ).pack(pady=10)
        
        # Center the window on the board
        victory_window.update_idletasks()
        window_x = self.window.winfo_x()
        window_y = self.window.winfo_y()
        board_x = window_x + self.board_frame.winfo_x() + self.canvas.winfo_x()
        board_y = window_y + self.board_frame.winfo_y() + self.canvas.winfo_y()
        board_width = self.canvas.winfo_width()
        board_height = self.canvas.winfo_height()
        
        x = board_x + (board_width - victory_window.winfo_width()) // 2
        y = board_y + (board_height - victory_window.winfo_height()) // 2
        
        victory_window.geometry(f"+{x}+{y}")
        victory_window.focus_set()
        victory_window.wait_window()

    def restart_game(self):
        # Store the current game's move history if it exists
        if self.move_history:
            self.game_history.append(self.move_history)
        self.move_history = []
        
        # Reset game state
        self.selected_piece = None
        self.highlighted_positions = []
        self.current_player = 'red'
        self.replay_mode = False
        self.current_replay_index = 0            
        self.game_over = False  # Add this line
                    
        # Set button states for normal gameplay
        self.set_button_states_for_gameplay()
                
        # Reinitialize the board
        self.initialize_board()
        self.draw_board()

    # Add piece movement validation(8 functions)

    def is_valid_move(self, from_pos, to_pos):
        from_row, from_col = from_pos
        to_row, to_col = to_pos
        piece = self.board[from_row][from_col]
        
        # Basic validation
        if not (0 <= to_row < 10 and 0 <= to_col < 9):
            return False
            
        # Can't capture own pieces
        if self.board[to_row][to_col] and self.board[to_row][to_col][0] == piece[0]:
            return False
        
        # Get piece type (second character of the piece string)
        piece_type = piece[1]
        
        # Check specific piece movement rules
        if piece_type == '帥' or piece_type == '將':  # General/King
            return self.is_valid_general_move(from_pos, to_pos)
        elif piece_type == '仕' or piece_type == '士':  # Advisor
            return self.is_valid_advisor_move(from_pos, to_pos)
        elif piece_type == '相' or piece_type == '象':  # Elephant
            return self.is_valid_elephant_move(from_pos, to_pos)
        elif piece_type == '馬':  # Horse
            return self.is_valid_horse_move(from_pos, to_pos)
        elif piece_type == '車':  # Chariot
            return self.is_valid_chariot_move(from_pos, to_pos)
        elif piece_type == '炮':  # Cannon
            return self.is_valid_cannon_move(from_pos, to_pos)
        elif piece_type == '兵' or piece_type == '卒':  # Pawn
            return self.is_valid_pawn_move(from_pos, to_pos)
        
        return False

    def is_valid_general_move(self, from_pos, to_pos):
        from_row, from_col = from_pos
        to_row, to_col = to_pos
        piece = self.board[from_row][from_col]
        
        # Check if move is within palace (3x3 grid)
        if piece[0] == 'R':  # Red general
            if not (7 <= to_row <= 9 and 3 <= to_col <= 5):
                return False
        else:  # Black general
            if not (0 <= to_row <= 2 and 3 <= to_col <= 5):
                return False
        
        # Can only move one step horizontally or vertically
        if abs(to_row - from_row) + abs(to_col - from_col) != 1:
            return False
            
        return True

    def is_valid_advisor_move(self, from_pos, to_pos):
        from_row, from_col = from_pos
        to_row, to_col = to_pos
        piece = self.board[from_row][from_col]
        
        # Check if move is within palace
        if piece[0] == 'R':  # Red advisor
            if not (7 <= to_row <= 9 and 3 <= to_col <= 5):
                return False
        else:  # Black advisor
            if not (0 <= to_row <= 2 and 3 <= to_col <= 5):
                return False
        
        # Must move exactly one step diagonally
        if abs(to_row - from_row) != 1 or abs(to_col - from_col) != 1:
            return False
            
        return True

    def is_valid_elephant_move(self, from_pos, to_pos):
        from_row, from_col = from_pos
        to_row, to_col = to_pos
        piece = self.board[from_row][from_col]
        
        # Cannot cross river
        if piece[0] == 'R':  # Red elephant
            if to_row < 5:  # Cannot cross river
                return False
        else:  # Black elephant
            if to_row > 4:  # Cannot cross river
                return False
        
        # Must move exactly two steps diagonally
        if abs(to_row - from_row) != 2 or abs(to_col - from_col) != 2:
            return False
        
        # Check if there's a piece blocking the elephant's path
        blocking_row = (from_row + to_row) // 2
        blocking_col = (from_col + to_col) // 2
        if self.board[blocking_row][blocking_col]:
            return False
            
        return True

    def is_valid_horse_move(self, from_pos, to_pos):
        from_row, from_col = from_pos
        to_row, to_col = to_pos
        
        # Must move in an L-shape (2 steps in one direction, 1 step in perpendicular direction)
        row_diff = abs(to_row - from_row)
        col_diff = abs(to_col - from_col)
        if not ((row_diff == 2 and col_diff == 1) or (row_diff == 1 and col_diff == 2)):
            return False
        
        # Check for blocking piece
        if row_diff == 2:
            blocking_row = from_row + (1 if to_row > from_row else -1)
            if self.board[blocking_row][from_col]:
                return False
        else:
            blocking_col = from_col + (1 if to_col > from_col else -1)
            if self.board[from_row][blocking_col]:
                return False
                
        return True

    def is_valid_chariot_move(self, from_pos, to_pos):
        from_row, from_col = from_pos
        to_row, to_col = to_pos
        
        # Must move horizontally or vertically
        if from_row != to_row and from_col != to_col:
            return False
        
        # Check if path is clear
        if from_row == to_row:  # Horizontal move
            start_col = min(from_col, to_col) + 1
            end_col = max(from_col, to_col)
            for col in range(start_col, end_col):
                if self.board[from_row][col]:
                    return False
        else:  # Vertical move
            start_row = min(from_row, to_row) + 1
            end_row = max(from_row, to_row)
            for row in range(start_row, end_row):
                if self.board[row][from_col]:
                    return False
                    
        return True

    def is_valid_cannon_move(self, from_pos, to_pos):
        from_row, from_col = from_pos
        to_row, to_col = to_pos
        
        # Must move horizontally or vertically
        if from_row != to_row and from_col != to_col:
            return False
        
        # Count pieces between from and to positions
        pieces_between = 0
        if from_row == to_row:  # Horizontal move
            start_col = min(from_col, to_col) + 1
            end_col = max(from_col, to_col)
            for col in range(start_col, end_col):
                if self.board[from_row][col]:
                    pieces_between += 1
        else:  # Vertical move
            start_row = min(from_row, to_row) + 1
            end_row = max(from_row, to_row)
            for row in range(start_row, end_row):
                if self.board[row][from_col]:
                    pieces_between += 1
        
        # If capturing, need exactly one piece between
        if self.board[to_row][to_col]:
            return pieces_between == 1
        # If not capturing, path must be clear
        return pieces_between == 0

    def is_valid_pawn_move(self, from_pos, to_pos):
        from_row, from_col = from_pos
        to_row, to_col = to_pos
        piece = self.board[from_row][from_col]
        
        if piece[0] == 'R':  # Red pawn
            # Before crossing river
            if from_row > 4:
                # Can only move forward (up)
                return to_col == from_col and to_row == from_row - 1
            # After crossing river
            else:
                # Can move forward or sideways
                return (to_col == from_col and to_row == from_row - 1) or \
                       (to_row == from_row and abs(to_col - from_col) == 1)
        else:  # Black pawn
            # Before crossing river
            if from_row < 5:
                # Can only move forward (down)
                return to_col == from_col and to_row == from_row + 1
            # After crossing river
            else:
                # Can move forward or sideways
                return (to_col == from_col and to_row == from_row + 1) or \
                       (to_row == from_row and abs(to_col - from_col) == 1)

    # the following 3 functions (conbined with on_click function) is to add the CHECK feature
    def find_kings(self):
        """Find positions of both kings/generals"""
        red_king_pos = black_king_pos = None
        for row in range(10):
            for col in range(9):
                piece = self.board[row][col]
                if piece:
                    if piece[1] == '帥':
                        red_king_pos = (row, col)
                    elif piece[1] == '將':
                        black_king_pos = (row, col)
        return red_king_pos, black_king_pos

    def is_position_under_attack(self, pos, attacking_color):
        """Check if a position is under attack by pieces of the given color"""
        target_row, target_col = pos
        
        # Check from all positions on the board
        for row in range(10):
            for col in range(9):
                piece = self.board[row][col]
                if piece and piece[0] == attacking_color[0].upper():
                    # Check if this piece can move to the target position
                    if self.is_valid_move((row, col), pos):
                        return True
        return False  

    def is_generals_facing(self):
        """Check if the two generals are facing each other directly"""
        red_king_pos, black_king_pos = self.find_kings()
        
        # If either king is missing, return False
        if not red_king_pos or not black_king_pos:
            return False
            
        red_row, red_col = red_king_pos
        black_row, black_col = black_king_pos
        
        # Check if generals are in the same column
        if red_col != black_col:
            return False
            
        # Check if there are any pieces between the generals
        start_row = min(red_row, black_row) + 1
        end_row = max(red_row, black_row)
        
        for row in range(start_row, end_row):
            if self.board[row][red_col]:  # If there's any piece between
                return False
                
        # If we get here, the generals are facing each other
        return True

    def is_in_check(self, color):
        """Check if the king of the given color is in check"""
        red_king_pos, black_king_pos = self.find_kings()
        
        if not red_king_pos or not black_king_pos:
            return False
        
        # First check the special case of facing generals
        if self.is_generals_facing():
            return True  # Both kings are in check in this case
        
        # Then check the normal cases of being under attack
        if color == 'red':
            return self.is_position_under_attack(red_king_pos, 'black')
        else:
            return self.is_position_under_attack(black_king_pos, 'red')

    def run(self):
        self.window.mainloop()

# Create and run the game
if __name__ == "__main__":
    game = ChineseChess()
    game.run()