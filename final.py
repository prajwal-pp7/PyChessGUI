import pygame
import chess
import chess.engine
import platform
import os
import sys
import json
import uuid

WIDTH, HEIGHT = 800, 800
BOARD_SIZE = 500
SQUARE_SIZE = BOARD_SIZE // 8
PIECE_SIZE = int(SQUARE_SIZE * 0.9)

THEMES = {
    'light': {
        'BACKGROUND_COLOR': (200, 200, 200),
        'TEXT_COLOR': (0, 0, 0),
        'BUTTON_COLOR': (220, 220, 220),
        'BOARD_LIGHT': (235, 235, 208),
        'BOARD_DARK': (119, 148, 85),
        'DIVIDER_COLOR': (0, 0, 0),
        'INPUT_BG': (255, 255, 255),
        'INPUT_TEXT': (0, 0, 0)
    },
    'dark': {
        'BACKGROUND_COLOR': (50, 50, 50),
        'TEXT_COLOR': (255, 255, 255),
        'BUTTON_COLOR': (80, 80, 80),
        'BOARD_LIGHT': (181, 136, 99),
        'BOARD_DARK': (99, 71, 50),
        'DIVIDER_COLOR': (255, 255, 255),
        'INPUT_BG': (100, 100, 100),
        'INPUT_TEXT': (255, 255, 255)
    }
}

current_theme = 'light'

def get_color(color_name):
    return THEMES[current_theme][color_name]

HIGHLIGHT_GREEN = (100, 255, 100, 150)
HIGHLIGHT_BLUE = (100, 150, 255, 150)
HIGHLIGHT_RED = (255, 100, 100, 150)
SELECTED_SQUARE_COLOR = (255, 255, 0, 150)
HINT_COLOR = (128, 0, 128, 150)
SELECTED_BUTTON_COLOR = (100, 150, 255)
FOCUSED_BUTTON_COLOR = (255, 165, 0)
STOP_BUTTON_COLOR = (255, 0, 0)
RESUME_BUTTON_COLOR = (0, 0, 255)
SPEED_BUTTON_COLOR = (0, 150, 0)
RESIGN_BUTTON_COLOR = (255, 0, 0)
SAVE_BUTTON_COLOR = (0, 150, 0)

LOGIN_SCREEN, MODE_SCREEN, COLOR_SCREEN, DIFFICULTY_SCREEN, TIME_SCREEN, GAME_SCREEN, EVALUATION_SCREEN = range(7)

PIECES_PATH = "pieces"
PIECE_IMAGE_MAP = {
    "K": "wK", "Q": "wQ", "R": "wR", "B": "wB", "N": "wN", "P": "wP",
    "k": "bK", "q": "bQ", "r": "bR", "b": "bB", "n": "bN", "p": "bP",
}
PIECE_IMAGES = {}

try:
    for piece_symbol, filename in PIECE_IMAGE_MAP.items():
        img_path = os.path.join(PIECES_PATH, f"{filename}.png")
        PIECE_IMAGES[piece_symbol] = pygame.transform.scale(pygame.image.load(img_path), (PIECE_SIZE, PIECE_SIZE))
except pygame.error as e:
    print(f"Error loading piece images: {e}")
    sys.exit()

SOUNDS_PATH = "sounds"
SOUNDS = {}

try:
    pygame.mixer.init()
    move_sound_path = os.path.join(SOUNDS_PATH, "move.wav")
    capture_sound_path = os.path.join(SOUNDS_PATH, "capture.wav")
    SOUNDS["move"] = pygame.mixer.Sound(move_sound_path)
    SOUNDS["capture"] = pygame.mixer.Sound(capture_sound_path)
except pygame.error as e:
    print(f"Error loading sounds: {e}")
    SOUNDS = None

def get_stockfish_path():
    system = platform.system()
    if system == 'Windows':
        return os.path.join(os.getcwd(), 'stockfish-windows-x86-64-avx2.exe')
    elif system == 'Darwin':
        return os.path.join(os.getcwd(), 'stockfish-macos-arm64')
    elif system == 'Linux':
        return os.path.join(os.getcwd(), 'stockfish-linux-x86-64-avx2')
    else:
        raise OSError("Unsupported operating system.")

try:
    STOCKFISH_PATH = get_stockfish_path()
    engine = chess.engine.SimpleEngine.popen_uci(STOCKFISH_PATH)
    print("✅ Stockfish engine initialized successfully.")
except FileNotFoundError:
    print("Error: Stockfish executable not found.")
    sys.exit()
except OSError as e:
    print(f"Error initializing the chess engine: {e}")
    sys.exit()

DIFFICULTY_LEVELS = {
    "Easy": {"depth": 5},
    "Medium": {"depth": 10},
    "Hard": {"depth": 15},
    "Extreme": {"depth": 20}
}

AI_SKILL = DIFFICULTY_LEVELS["Medium"]["depth"]

class LoginSystem:
    def __init__(self):
        self.current_user = None
        self.user_data_file = "user_data.json"
        self.user_data = self.load_user_data()

    def load_user_data(self):
        if os.path.exists(self.user_data_file):
            with open(self.user_data_file, 'r') as f:
                return json.load(f)
        return {}

    def save_user_data(self):
        with open(self.user_data_file, 'w') as f:
            json.dump(self.user_data, f, indent=4)

    def login(self, username, password):
        if username in self.user_data and self.user_data[username]["password"] == password:
            self.current_user = username
            print(f"✅ User '{username}' logged in successfully.")
            return True
        print(f"❌ Login failed for user: '{username}'. No such account exists or incorrect password.")
        return False

    def create_account(self, username, password):
        if username in self.user_data:
            print(f"❌ Account creation failed. Username '{username}' already exists.")
            return False
        self.user_data[username] = {
            "password": password,
            "stats": {"wins": 0, "losses": 0, "ties": 0},
            "saved_games": []
        }
        self.save_user_data()
        self.current_user = username
        print(f"✅ Account for '{username}' created successfully.")
        return True

    def guest_login(self):
        guest_id = str(uuid.uuid4())
        self.current_user = f"guest_{guest_id}"
        self.user_data[self.current_user] = {
            "password": None,
            "stats": {"wins": 0, "losses": 0, "ties": 0},
            "saved_games": []
        }
        print(f"👤 Guest user '{self.current_user}' has logged in.")

    def get_user_stats(self):
        if self.current_user:
            return self.user_data[self.current_user]["stats"]
        return {"wins": 0, "losses": 0, "ties": 0}

    def update_user_stats(self, result, human_color):
        if not self.current_user:
            return
        stats = self.user_data[self.current_user]["stats"]
        if result == "1-0":
            if human_color == chess.WHITE:
                stats["wins"] += 1
                print(f"🏆 Human player won as White. Updating stats for {self.current_user}.")
            else:
                stats["losses"] += 1
                print(f"💔 Human player lost as Black. Updating stats for {self.current_user}.")
        elif result == "0-1":
            if human_color == chess.BLACK:
                stats["wins"] += 1
                print(f"🏆 Human player won as Black. Updating stats for {self.current_user}.")
            else:
                stats["losses"] += 1
                print(f"💔 Human player lost as White. Updating stats for {self.current_user}.")
        elif result == "1/2-1/2":
            stats["ties"] += 1
            print(f"🤝 Game was a tie. Updating stats for {self.current_user}.")
        self.save_user_data()

    def get_saved_games(self):
        if self.current_user and "saved_games" in self.user_data[self.current_user]:
            return self.user_data[self.current_user]["saved_games"]
        return []

    def save_game(self, game_state):
        if not self.current_user:
            print("💾 Cannot save game. No user is logged in.")
            return
        saved_game = {
            "id": str(uuid.uuid4()),
            "fen": game_state.board.fen(),
            "history": [move.uci() for move in game_state.move_history],
            "hints_used": game_state.hints_used,
            "human_color": "white" if game_state.human_color == chess.WHITE else "black",
            "time_limit": game_state.time_limit,
            "difficulty": game_state.difficulty,
            "game_mode": game_state.game_mode
        }
        self.user_data[self.current_user]["saved_games"].append(saved_game)
        self.save_user_data()
        print(f"💾 Game saved for user: {self.current_user}.")

    def load_game(self, game_id):
        for game in self.user_data[self.current_user]["saved_games"]:
            if game["id"] == game_id:
                return game
        return None

class GameState:
    def __init__(self, game_mode, human_color=None, time_limit=None, difficulty="Medium", fen=None, history=None, hints=None):
        self.game_mode = game_mode
        self.board = chess.Board(fen) if fen else chess.Board()
        self.human_color = human_color
        self.selected_square = None
        self.valid_moves = []
        self.game_over = False
        self.result = None
        self.time_limit = time_limit
        self.start_time = pygame.time.get_ticks()
        self.remaining_time = {
            chess.WHITE: self.time_limit * 1000 if self.time_limit is not None else -1,
            chess.BLACK: self.time_limit * 1000 if self.time_limit is not None else -1,
        }
        self.is_timer_running = False
        self.hint_move = None
        self.move_history = [chess.Move.from_uci(m) for m in history] if history else []
        self.hints_used = hints if hints else []
        self.difficulty = difficulty
        self.ai_skill = DIFFICULTY_LEVELS.get(self.difficulty, {"depth": 10})["depth"]
        if self.game_mode == "AI vs AI":
            self.ai_skill = DIFFICULTY_LEVELS["Extreme"]["depth"]
        self.is_saved = False

    def handle_click(self, pos):
        board_top_left_x = (WIDTH - BOARD_SIZE) // 2
        board_top_left_y = (HEIGHT * 0.8 - BOARD_SIZE) / 2
        col = int((pos[0] - board_top_left_x) // SQUARE_SIZE)
        row = int((pos[1] - board_top_left_y) // SQUARE_SIZE)
        if 0 <= col < 8 and 0 <= row < 8:
            square = chess.square(col, 7 - row)
            if self.selected_square:
                move = chess.Move(self.selected_square, square)
                is_capture = self.board.piece_at(square) is not None
                if move in self.board.legal_moves:
                    self.board.push(move)
                    self.move_history.append(move)
                    self.reset_selection()
                    self.hint_move = None
                    self.is_timer_running = True
                    if self.time_limit is not None:
                        self.update_timer(self.board.turn)
                    if SOUNDS:
                        if is_capture:
                            SOUNDS["capture"].play()
                        else:
                            SOUNDS["move"].play()
                else:
                    self.reset_selection()
            else:
                piece = self.board.piece_at(square)
                if piece and (self.game_mode == "Human vs Human" or piece.color == self.human_color):
                    self.selected_square = square
                    self.valid_moves = [move.to_square for move in self.board.legal_moves if move.from_square == square]

    def reset_selection(self):
        self.selected_square = None
        self.valid_moves = []

    def get_hint(self):
        result = engine.play(self.board, chess.engine.Limit(time=0.1))
        self.hint_move = result.move
        self.hints_used.append(self.board.fullmove_number)
        print("💡 Hint requested and displayed.")

    def get_ai_move(self):
        self.is_timer_running = True
        result = engine.play(self.board, chess.engine.Limit(depth=self.ai_skill))
        if result.move:
            self.board.push(result.move)
            self.move_history.append(result.move)

    def check_game_over(self):
        if self.board.is_game_over():
            self.game_over = True
            self.result = self.board.result()
            print(f"🏁 Game over! Result: {self.result}")
            return True
        return False

    def update_timer(self, turn):
        if self.time_limit is not None:
            elapsed_time = pygame.time.get_ticks() - self.start_time
            self.remaining_time[turn] -= elapsed_time
            self.start_time = pygame.time.get_ticks()

    def check_time(self):
        if self.time_limit is not None and self.is_timer_running:
            self.remaining_time[self.board.turn] -= (pygame.time.get_ticks() - self.start_time)
            self.start_time = pygame.time.get_ticks()
            if self.remaining_time[self.board.turn] <= 0:
                self.game_over = True
                loser = 'White' if self.board.turn == chess.WHITE else 'Black'
                self.result = f"Time out for {loser}"
                print(f"⌛ Game over! Time out for {loser}.")

def draw_bottom_ui(screen):
    font_small = pygame.font.Font(None, 24)
    font_bold = pygame.font.Font(None, 28)
    font_bold.set_bold(True)
    text_210401 = font_small.render("210401", True, get_color('TEXT_COLOR'))
    text_210401_rect = text_210401.get_rect(center=(WIDTH // 2, HEIGHT - 65))
    screen.blit(text_210401, text_210401_rect)
    text_iitk = font_bold.render("IIT Kanpur", True, get_color('TEXT_COLOR'))
    text_iitk_rect = text_iitk.get_rect(center=(WIDTH // 2, HEIGHT - 35))
    screen.blit(text_iitk, text_iitk_rect)
    return pygame.Rect(0, 0, 0, 0), pygame.Rect(0, 0, 0, 0)

def draw_board(screen, game_state):
    board_top_left_x = (WIDTH - BOARD_SIZE) // 2
    board_top_left_y = (HEIGHT * 0.8 - BOARD_SIZE) / 2
    for row in range(8):
        for col in range(8):
            color = get_color('BOARD_LIGHT') if (row + col) % 2 == 0 else get_color('BOARD_DARK')
            pygame.draw.rect(screen, color, pygame.Rect(board_top_left_x + col * SQUARE_SIZE, board_top_left_y + row * SQUARE_SIZE, SQUARE_SIZE, SQUARE_SIZE), border_radius=5)
            if game_state.selected_square and chess.square(col, 7 - row) == game_state.selected_square:
                s = pygame.Surface((SQUARE_SIZE, SQUARE_SIZE), pygame.SRCALPHA)
                pygame.draw.rect(s, SELECTED_SQUARE_COLOR, s.get_rect(), border_radius=5)
                screen.blit(s, (board_top_left_x + col * SQUARE_SIZE, board_top_left_y + row * SQUARE_SIZE))
            if chess.square(col, 7 - row) in game_state.valid_moves:
                s = pygame.Surface((SQUARE_SIZE, SQUARE_SIZE), pygame.SRCALPHA)
                is_capture = game_state.board.piece_at(chess.square(col, 7 - row)) is not None
                color = HIGHLIGHT_RED if is_capture else HIGHLIGHT_GREEN
                pygame.draw.rect(s, color, s.get_rect(), border_radius=5)
                screen.blit(s, (board_top_left_x + col * SQUARE_SIZE, board_top_left_y + row * SQUARE_SIZE))

    for row in range(8):
        for col in range(8):
            square = chess.square(col, 7 - row)
            piece = game_state.board.piece_at(square)
            if piece:
                piece_img = PIECE_IMAGES[piece.symbol()]
                x_pos = board_top_left_x + col * SQUARE_SIZE + (SQUARE_SIZE - PIECE_SIZE) // 2
                y_pos = board_top_left_y + row * SQUARE_SIZE + (SQUARE_SIZE - PIECE_SIZE) // 2
                screen.blit(piece_img, (x_pos, y_pos))

    if game_state.hint_move:
        from_square = game_state.hint_move.from_square
        to_square = game_state.hint_move.to_square
        from_col = chess.square_file(from_square)
        from_row = 7 - chess.square_rank(from_square)
        to_col = chess.square_file(to_square)
        to_row = 7 - chess.square_rank(to_square)
        s = pygame.Surface((SQUARE_SIZE, SQUARE_SIZE), pygame.SRCALPHA)
        pygame.draw.rect(s, HINT_COLOR, s.get_rect(), border_radius=5)
        screen.blit(s, (board_top_left_x + from_col * SQUARE_SIZE, board_top_left_y + from_row * SQUARE_SIZE))
        screen.blit(s, (board_top_left_x + to_col * SQUARE_SIZE, board_top_left_y + to_row * SQUARE_SIZE))

def draw_buttons_and_info(screen, game_state, stats, user_selections):
    font = pygame.font.Font(None, 24)
    if game_state.time_limit is not None:
        white_time_ms = max(0, game_state.remaining_time[chess.WHITE])
        black_time_ms = max(0, game_state.remaining_time[chess.BLACK])
        white_minutes = int(white_time_ms / (60 * 1000))
        white_seconds = int((white_time_ms / 1000) % 60)
        black_minutes = int(black_time_ms / (60 * 1000))
        black_seconds = int((black_time_ms / 1000) % 60)
        white_timer_text = font.render(f"White: {white_minutes:02d}:{white_seconds:02d}", True, get_color('TEXT_COLOR'))
        black_timer_text = font.render(f"Black: {black_minutes:02d}:{black_seconds:02d}", True, get_color('TEXT_COLOR'))
        screen.blit(white_timer_text, (20, HEIGHT * 0.8 + 20))
        screen.blit(black_timer_text, (20, HEIGHT * 0.8 + 50))

    button_width = 120
    button_height = 50
    gap = 20
    buttons = []

    if user_selections["mode"] == "AI vs AI":
        resign_button_rect = pygame.Rect(WIDTH - 150, HEIGHT * 0.8 + 10, button_width, button_height)
        save_button_rect = pygame.Rect(WIDTH - 150 - (button_width + gap), HEIGHT * 0.8 + 10, button_width, button_height)
        buttons.append((resign_button_rect, "Resign", RESIGN_BUTTON_COLOR))
        buttons.append((save_button_rect, "Save", SAVE_BUTTON_COLOR if not game_state.is_saved else get_color('BUTTON_COLOR')))
        hint_button_rect = None
    else:
        resign_button_rect = pygame.Rect(WIDTH - 150, HEIGHT * 0.8 + 10, button_width, button_height)
        hint_button_rect = pygame.Rect(WIDTH - 150 - (button_width + gap), HEIGHT * 0.8 + 10, button_width, button_height)
        save_button_rect = pygame.Rect(WIDTH - 150 - 2*(button_width + gap), HEIGHT * 0.8 + 10, button_width, button_height)
        buttons.append((resign_button_rect, "Resign", RESIGN_BUTTON_COLOR))
        buttons.append((hint_button_rect, "Hint", SELECTED_BUTTON_COLOR))
        buttons.append((save_button_rect, "Save", SAVE_BUTTON_COLOR if not game_state.is_saved else get_color('BUTTON_COLOR')))

    for rect, text, color in buttons:
        pygame.draw.rect(screen, color, rect, border_radius=10)
        text_surface = font.render(text, True, get_color('TEXT_COLOR'))
        screen.blit(text_surface, text_surface.get_rect(center=rect.center))

    if user_selections["mode"] == "Human vs AI":
        return resign_button_rect, hint_button_rect, save_button_rect
    elif user_selections["mode"] == "Human vs Human":
        return resign_button_rect, hint_button_rect, save_button_rect
    else:
        return resign_button_rect, None, save_button_rect

def show_login_screen(screen, login_system):
    font = pygame.font.Font(None, 36)
    font_small = pygame.font.Font(None, 24)
    input_box_user = pygame.Rect(WIDTH // 2 - 150, HEIGHT // 2 - 150, 300, 50)
    input_box_pass = pygame.Rect(WIDTH // 2 - 150, HEIGHT // 2 - 50, 300, 50)
    login_button = pygame.Rect(WIDTH // 2 - 150, HEIGHT // 2 + 50, 140, 50)
    create_button = pygame.Rect(WIDTH // 2 + 10, HEIGHT // 2 + 50, 140, 50)
    next_button_rect = pygame.Rect(WIDTH - 130, 20, 100, 50)
    theme_button_rect = pygame.Rect(30, HEIGHT - 70, 100, 50)
    interactive_elements = [input_box_user, input_box_pass, login_button, create_button, next_button_rect, theme_button_rect]
    focus_index = 0
    next_enabled = False
    user_text = ''
    pass_text = ''
    active_box = None
    cursor_char = "|"
    cursor_on = True
    cursor_blink_rate = 500
    cursor_timer = pygame.time.get_ticks()

    while True:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                return "quit"

            if event.type == pygame.MOUSEBUTTONDOWN:
                for i, rect in enumerate(interactive_elements):
                    if rect.collidepoint(event.pos):
                        focus_index = i
                        active_box = rect if rect in [input_box_user, input_box_pass] else None
                        if rect == theme_button_rect:
                            global current_theme
                            current_theme = 'dark' if current_theme == 'light' else 'light'
                        elif rect == login_button:
                            if login_system.login(user_text, pass_text): return "next"
                        elif rect == create_button:
                            if login_system.create_account(user_text, pass_text): return "next"
                        elif rect == next_button_rect and next_enabled:
                            return "next"
                if not any(rect.collidepoint(event.pos) for rect in interactive_elements):
                    active_box = None

            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_TAB:
                    focus_index = (focus_index + 1) % len(interactive_elements)
                    active_box = interactive_elements[focus_index] if interactive_elements[focus_index] in [input_box_user, input_box_pass] else None
                elif event.key == pygame.K_RETURN or event.key == pygame.K_KP_ENTER:
                    focused_element = interactive_elements[focus_index]
                    if focused_element == theme_button_rect:
                        current_theme = 'dark' if current_theme == 'light' else 'light'
                    elif focused_element == login_button:
                        if login_system.login(user_text, pass_text): return "next"
                    elif focused_element == create_button:
                        if login_system.create_account(user_text, pass_text): return "next"
                    elif focused_element == next_button_rect and next_enabled:
                        return "next"
                elif active_box:
                    if event.key == pygame.K_BACKSPACE:
                        if active_box == input_box_user: user_text = user_text[:-1]
                        else: pass_text = pass_text[:-1]
                    else:
                        if active_box == input_box_user: user_text += event.unicode
                        else: pass_text += event.unicode

        if login_system.current_user:
            next_enabled = True

        screen.fill(get_color('BACKGROUND_COLOR'))
        pygame.draw.line(screen, get_color('DIVIDER_COLOR'), (0, HEIGHT * 0.9), (WIDTH, HEIGHT * 0.9), 2)
        user_label = font.render("Username:", True, get_color('TEXT_COLOR'))
        pass_label = font.render("Password:", True, get_color('TEXT_COLOR'))
        screen.blit(user_label, (input_box_user.x, input_box_user.y - 30))
        screen.blit(pass_label, (input_box_pass.x, input_box_pass.y - 30))
        pygame.draw.rect(screen, get_color('INPUT_BG'), input_box_user, border_radius=5)
        pygame.draw.rect(screen, get_color('INPUT_BG'), input_box_pass, border_radius=5)
        current_time = pygame.time.get_ticks()
        if current_time - cursor_timer > cursor_blink_rate:
            cursor_on = not cursor_on
            cursor_timer = current_time

        user_text_display = user_text + (cursor_char if active_box == input_box_user and cursor_on else "")
        pass_text_display = '*' * len(pass_text) + (cursor_char if active_box == input_box_pass and cursor_on else "")
        user_surface = font.render(user_text_display, True, get_color('INPUT_TEXT'))
        pass_surface = font.render(pass_text_display, True, get_color('INPUT_TEXT'))
        screen.blit(user_surface, user_surface.get_rect(midleft=(input_box_user.x + 5, input_box_user.centery)))
        screen.blit(pass_surface, pass_surface.get_rect(midleft=(input_box_pass.x + 5, input_box_pass.centery)))

        for rect in [login_button, create_button, next_button_rect, theme_button_rect]:
            color = SELECTED_BUTTON_COLOR if rect == next_button_rect and next_enabled else get_color('BUTTON_COLOR')
            pygame.draw.rect(screen, color, rect, border_radius=10)

        focused_rect = interactive_elements[focus_index]
        pygame.draw.rect(screen, FOCUSED_BUTTON_COLOR, focused_rect.inflate(6, 6), 3, border_radius=12)
        login_text = font_small.render("Login", True, get_color('TEXT_COLOR'))
        create_text = font_small.render("Create Account", True, get_color('TEXT_COLOR'))
        next_text = font.render("Next", True, get_color('TEXT_COLOR'))
        theme_text = font.render("Theme", True, get_color('TEXT_COLOR'))
        screen.blit(login_text, login_text.get_rect(center=login_button.center))
        screen.blit(create_text, create_text.get_rect(center=create_button.center))
        screen.blit(next_text, next_text.get_rect(center=next_button_rect.center))
        screen.blit(theme_text, theme_text.get_rect(center=theme_button_rect.center))
        draw_bottom_ui(screen)
        pygame.display.flip()

def show_mode_selection_screen(screen, selected_mode):
    font = pygame.font.Font(None, 40)
    modes = ["Human vs AI", "Human vs Human", "AI vs AI"]
    y_offset = HEIGHT // 2 - 100
    mode_buttons = [pygame.Rect(WIDTH // 2 - 150, y_offset + i * 80, 300, 60) for i in range(len(modes))]
    back_button_rect = pygame.Rect(30, 20, 100, 50)
    next_button_rect = pygame.Rect(WIDTH - 130, 20, 100, 50)
    theme_button_rect = pygame.Rect(30, HEIGHT - 70, 100, 50)
    interactive_elements = mode_buttons + [back_button_rect, next_button_rect, theme_button_rect]
    focus_index = 0

    while True:
        next_enabled = selected_mode is not None
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                return "quit", None

            if event.type == pygame.MOUSEBUTTONDOWN:
                for i, rect in enumerate(interactive_elements):
                    if rect.collidepoint(event.pos):
                        focus_index = i
                        if rect in mode_buttons:
                            selected_mode = modes[mode_buttons.index(rect)]
                        elif rect == back_button_rect: return "back", selected_mode
                        elif rect == next_button_rect and next_enabled: return "next", selected_mode
                        elif rect == theme_button_rect:
                            global current_theme
                            current_theme = 'dark' if current_theme == 'light' else 'light'

            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_TAB:
                    focus_index = (focus_index + 1) % len(interactive_elements)
                elif event.key == pygame.K_RETURN or event.key == pygame.K_KP_ENTER:
                    focused_element = interactive_elements[focus_index]
                    if focused_element in mode_buttons:
                        selected_mode = modes[mode_buttons.index(focused_element)]
                        focus_index = interactive_elements.index(next_button_rect)
                    elif focused_element == back_button_rect: return "back", selected_mode
                    elif focused_element == next_button_rect and next_enabled: return "next", selected_mode
                    elif focused_element == theme_button_rect:
                        current_theme = 'dark' if current_theme == 'light' else 'light'

        screen.fill(get_color('BACKGROUND_COLOR'))
        pygame.draw.line(screen, get_color('DIVIDER_COLOR'), (0, HEIGHT * 0.9), (WIDTH, HEIGHT * 0.9), 2)
        title = font.render("Select Game Mode", True, get_color('TEXT_COLOR'))
        screen.blit(title, title.get_rect(center=(WIDTH // 2, 50)))

        for i, rect in enumerate(interactive_elements):
            is_selected = (rect in mode_buttons and selected_mode == modes[mode_buttons.index(rect)]) or (rect == next_button_rect and next_enabled)
            color = SELECTED_BUTTON_COLOR if is_selected else get_color('BUTTON_COLOR')
            pygame.draw.rect(screen, color, rect, border_radius=10)

        if interactive_elements:
            focused_rect = interactive_elements[focus_index]
            pygame.draw.rect(screen, FOCUSED_BUTTON_COLOR, focused_rect.inflate(6, 6), 3, border_radius=12)

        for i, mode in enumerate(modes):
            text = font.render(mode, True, get_color('TEXT_COLOR'))
            screen.blit(text, text.get_rect(center=mode_buttons[i].center))

        back_text = font.render("Back", True, get_color('TEXT_COLOR'))
        screen.blit(back_text, back_text.get_rect(center=back_button_rect.center))
        next_text = font.render("Next", True, get_color('TEXT_COLOR'))
        screen.blit(next_text, next_text.get_rect(center=next_button_rect.center))
        theme_text = font.render("Theme", True, get_color('TEXT_COLOR'))
        screen.blit(theme_text, theme_text.get_rect(center=theme_button_rect.center))
        draw_bottom_ui(screen)
        pygame.display.flip()

def show_color_selection_screen(screen, selected_color):
    font = pygame.font.Font(None, 40)
    white_button_rect = pygame.Rect(WIDTH // 2 - 200, HEIGHT // 2 - 30, 150, 60)
    black_button_rect = pygame.Rect(WIDTH // 2 + 50, HEIGHT // 2 - 30, 150, 60)
    back_button_rect = pygame.Rect(30, 20, 100, 50)
    next_button_rect = pygame.Rect(WIDTH - 130, 20, 100, 50)
    theme_button_rect = pygame.Rect(30, HEIGHT - 70, 100, 50)
    interactive_elements = [white_button_rect, black_button_rect, back_button_rect, next_button_rect, theme_button_rect]
    focus_index = 0

    while True:
        next_enabled = selected_color is not None
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                return "quit", None

            if event.type == pygame.MOUSEBUTTONDOWN:
                for i, rect in enumerate(interactive_elements):
                    if rect.collidepoint(event.pos):
                        focus_index = i
                        if rect == white_button_rect: selected_color = chess.WHITE
                        elif rect == black_button_rect: selected_color = chess.BLACK
                        elif rect == back_button_rect: return "back", selected_color
                        elif rect == next_button_rect and next_enabled: return "next", selected_color
                        elif rect == theme_button_rect:
                            global current_theme
                            current_theme = 'dark' if current_theme == 'light' else 'light'

            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_TAB:
                    focus_index = (focus_index + 1) % len(interactive_elements)
                elif event.key == pygame.K_RETURN or event.key == pygame.K_KP_ENTER:
                    focused_element = interactive_elements[focus_index]
                    if focused_element in [white_button_rect, black_button_rect]:
                        selected_color = chess.WHITE if focused_element == white_button_rect else chess.BLACK
                        focus_index = interactive_elements.index(next_button_rect)
                    elif focused_element == back_button_rect: return "back", selected_color
                    elif focused_element == next_button_rect and next_enabled: return "next", selected_color
                    elif focused_element == theme_button_rect:
                        current_theme = 'dark' if current_theme == 'light' else 'light'

        screen.fill(get_color('BACKGROUND_COLOR'))
        pygame.draw.line(screen, get_color('DIVIDER_COLOR'), (0, HEIGHT * 0.9), (WIDTH, HEIGHT * 0.9), 2)
        title = font.render("Select Player Color", True, get_color('TEXT_COLOR'))
        screen.blit(title, title.get_rect(center=(WIDTH // 2, 50)))

        for i, rect in enumerate(interactive_elements):
            is_selected = (rect == white_button_rect and selected_color == chess.WHITE) or (rect == black_button_rect and selected_color == chess.BLACK) or (rect == next_button_rect and next_enabled)
            color = SELECTED_BUTTON_COLOR if is_selected else get_color('BUTTON_COLOR')
            pygame.draw.rect(screen, color, rect, border_radius=10)

        if interactive_elements:
            focused_rect = interactive_elements[focus_index]
            pygame.draw.rect(screen, FOCUSED_BUTTON_COLOR, focused_rect.inflate(6, 6), 3, border_radius=12)

        white_text = font.render("White", True, get_color('TEXT_COLOR'))
        black_text = font.render("Black", True, get_color('TEXT_COLOR'))
        screen.blit(white_text, white_text.get_rect(center=white_button_rect.center))
        screen.blit(black_text, black_text.get_rect(center=black_button_rect.center))
        back_text = font.render("Back", True, get_color('TEXT_COLOR'))
        screen.blit(back_text, back_text.get_rect(center=back_button_rect.center))
        next_text = font.render("Next", True, get_color('TEXT_COLOR'))
        screen.blit(next_text, next_text.get_rect(center=next_button_rect.center))
        theme_text = font.render("Theme", True, get_color('TEXT_COLOR'))
        screen.blit(theme_text, theme_text.get_rect(center=theme_button_rect.center))
        draw_bottom_ui(screen)
        pygame.display.flip()

def show_difficulty_selection_screen(screen, selected_difficulty):
    font = pygame.font.Font(None, 40)
    difficulties = ["Easy", "Medium", "Hard", "Extreme"]
    padding = 40
    max_text_width = max(font.render(d, True, (0,0,0)).get_width() for d in difficulties)
    button_width = max_text_width + padding
    gap = 20
    total_width_of_buttons = len(difficulties) * button_width + (len(difficulties) - 1) * gap
    start_x = (WIDTH - total_width_of_buttons) // 2
    difficulty_buttons = [pygame.Rect(start_x + i * (button_width + gap), HEIGHT // 2 - 30, button_width, 60) for i in range(len(difficulties))]
    back_button_rect = pygame.Rect(30, 20, 100, 50)
    next_button_rect = pygame.Rect(WIDTH - 130, 20, 100, 50)
    theme_button_rect = pygame.Rect(30, HEIGHT - 70, 100, 50)
    interactive_elements = difficulty_buttons + [back_button_rect, next_button_rect, theme_button_rect]
    focus_index = 0

    while True:
        next_enabled = selected_difficulty is not None
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                return "quit", None

            if event.type == pygame.MOUSEBUTTONDOWN:
                for i, rect in enumerate(interactive_elements):
                    if rect.collidepoint(event.pos):
                        focus_index = i
                        if rect in difficulty_buttons:
                            selected_difficulty = difficulties[difficulty_buttons.index(rect)]
                        elif rect == back_button_rect: return "back", selected_difficulty
                        elif rect == next_button_rect and next_enabled: return "next", selected_difficulty
                        elif rect == theme_button_rect:
                            global current_theme
                            current_theme = 'dark' if current_theme == 'light' else 'light'

            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_TAB:
                    focus_index = (focus_index + 1) % len(interactive_elements)
                elif event.key == pygame.K_RETURN or event.key == pygame.K_KP_ENTER:
                    focused_element = interactive_elements[focus_index]
                    if focused_element in difficulty_buttons:
                        selected_difficulty = difficulties[difficulty_buttons.index(focused_element)]
                        focus_index = interactive_elements.index(next_button_rect)
                    elif focused_element == back_button_rect: return "back", selected_difficulty
                    elif focused_element == next_button_rect and next_enabled: return "next", selected_difficulty
                    elif focused_element == theme_button_rect:
                        current_theme = 'dark' if current_theme == 'light' else 'light'

        screen.fill(get_color('BACKGROUND_COLOR'))
        pygame.draw.line(screen, get_color('DIVIDER_COLOR'), (0, HEIGHT * 0.9), (WIDTH, HEIGHT * 0.9), 2)
        title = font.render("Select Difficulty", True, get_color('TEXT_COLOR'))
        screen.blit(title, title.get_rect(center=(WIDTH // 2, 50)))

        for i, rect in enumerate(interactive_elements):
            is_selected = (rect in difficulty_buttons and selected_difficulty == difficulties[difficulty_buttons.index(rect)]) or (rect == next_button_rect and next_enabled)
            color = SELECTED_BUTTON_COLOR if is_selected else get_color('BUTTON_COLOR')
            pygame.draw.rect(screen, color, rect, border_radius=10)

        if interactive_elements:
            focused_rect = interactive_elements[focus_index]
            pygame.draw.rect(screen, FOCUSED_BUTTON_COLOR, focused_rect.inflate(6, 6), 3, border_radius=12)

        for i, difficulty in enumerate(difficulties):
            text = font.render(difficulty, True, get_color('TEXT_COLOR'))
            screen.blit(text, text.get_rect(center=difficulty_buttons[i].center))

        back_text = font.render("Back", True, get_color('TEXT_COLOR'))
        screen.blit(back_text, back_text.get_rect(center=back_button_rect.center))
        next_text = font.render("Next", True, get_color('TEXT_COLOR'))
        screen.blit(next_text, next_text.get_rect(center=next_button_rect.center))
        theme_text = font.render("Theme", True, get_color('TEXT_COLOR'))
        screen.blit(theme_text, theme_text.get_rect(center=theme_button_rect.center))
        draw_bottom_ui(screen)
        pygame.display.flip()

def show_time_selection_screen(screen, selected_time, no_time_selected):
    font = pygame.font.Font(None, 40)
    font_small = pygame.font.Font(None, 30)
    time_rects = {
        "hours": pygame.Rect(WIDTH // 2 - 200, HEIGHT // 2 - 100, 100, 50),
        "minutes": pygame.Rect(WIDTH // 2 - 50, HEIGHT // 2 - 100, 100, 50),
        "seconds": pygame.Rect(WIDTH // 2 + 100, HEIGHT // 2 - 100, 100, 50)
    }
    no_time_button_rect = pygame.Rect(WIDTH // 2 - 150, HEIGHT // 2 + 50, 300, 60)
    back_button_rect = pygame.Rect(30, 20, 100, 50)
    next_button_rect = pygame.Rect(WIDTH - 130, 20, 100, 50)
    theme_button_rect = pygame.Rect(30, HEIGHT - 70, 100, 50)
    interactive_elements = [time_rects["hours"], time_rects["minutes"], time_rects["seconds"], no_time_button_rect, back_button_rect, next_button_rect, theme_button_rect]
    focus_index = 0
    hours, minutes, seconds = 0, 0, 0
    if selected_time is not None:
        hours = selected_time // 3600
        minutes = (selected_time % 3600) // 60
        seconds = selected_time % 60

    seconds_options = [0, 10, 20, 30, 40, 50]
    minutes_options = [0, 5, 10, 15, 20, 25, 30, 35, 40, 45, 50, 55]
    hours_options = [0, 1, 2, 3, 4, 5, 6, 7, 8, 9, 10]

    def cycle_time(unit, value, direction):
        options = []
        if unit == 'h': options = hours_options
        elif unit == 'm': options = minutes_options
        elif unit == 's': options = seconds_options
        try:
            current_index = options.index(value)
            new_index = (current_index + direction) % len(options)
            return options[new_index]
        except ValueError:
            return options[0]

    while True:
        next_enabled = selected_time is not None or no_time_selected
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                return "quit", None, None

            if event.type == pygame.MOUSEBUTTONDOWN:
                for i, rect in enumerate(interactive_elements):
                    if rect.collidepoint(event.pos):
                        focus_index = i
                        if rect == time_rects["hours"]:
                            hours = cycle_time('h', hours, 1)
                            no_time_selected = False
                        elif rect == time_rects["minutes"]:
                            minutes = cycle_time('m', minutes, 1)
                            no_time_selected = False
                        elif rect == time_rects["seconds"]:
                            seconds = cycle_time('s', seconds, 1)
                            no_time_selected = False
                        elif rect == no_time_button_rect:
                            no_time_selected = True
                        elif rect == back_button_rect: return "back", selected_time, no_time_selected
                        elif rect == next_button_rect and next_enabled:
                            return "next", (hours * 3600 + minutes * 60 + seconds) if not no_time_selected else None, no_time_selected
                        elif rect == theme_button_rect:
                            global current_theme
                            current_theme = 'dark' if current_theme == 'light' else 'light'

            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_TAB:
                    focus_index = (focus_index + 1) % len(interactive_elements)
                elif event.key == pygame.K_RETURN or event.key == pygame.K_KP_ENTER:
                    focused_element = interactive_elements[focus_index]
                    if focused_element == time_rects["hours"]: hours = cycle_time('h', hours, 1); no_time_selected = False
                    elif focused_element == time_rects["minutes"]: minutes = cycle_time('m', minutes, 1); no_time_selected = False
                    elif focused_element == time_rects["seconds"]: seconds = cycle_time('s', seconds, 1); no_time_selected = False
                    elif focused_element == no_time_button_rect: no_time_selected = True
                    elif focused_element == back_button_rect: return "back", selected_time, no_time_selected
                    elif focused_element == next_button_rect and next_enabled:
                        return "next", (hours * 3600 + minutes * 60 + seconds) if not no_time_selected else None, no_time_selected
                    elif focused_element == theme_button_rect:
                        current_theme = 'dark' if current_theme == 'light' else 'light'
                elif event.key == pygame.K_DOWN:
                    focused_element = interactive_elements[focus_index]
                    if focused_element == time_rects["hours"]: hours = cycle_time('h', hours, 1); no_time_selected = False
                    elif focused_element == time_rects["minutes"]: minutes = cycle_time('m', minutes, 1); no_time_selected = False
                    elif focused_element == time_rects["seconds"]: seconds = cycle_time('s', seconds, 1); no_time_selected = False
                elif event.key == pygame.K_UP:
                    focused_element = interactive_elements[focus_index]
                    if focused_element == time_rects["hours"]: hours = cycle_time('h', hours, -1); no_time_selected = False
                    elif focused_element == time_rects["minutes"]: minutes = cycle_time('m', minutes, -1); no_time_selected = False
                    elif focused_element == time_rects["seconds"]: seconds = cycle_time('s', seconds, -1); no_time_selected = False

        if not no_time_selected:
            selected_time = hours * 3600 + minutes * 60 + seconds
        else:
            selected_time = None

        screen.fill(get_color('BACKGROUND_COLOR'))
        pygame.draw.line(screen, get_color('DIVIDER_COLOR'), (0, HEIGHT * 0.9), (WIDTH, HEIGHT * 0.9), 2)
        title = font.render("Set Time Limit", True, get_color('TEXT_COLOR'))
        screen.blit(title, title.get_rect(center=(WIDTH // 2, 50)))
        time_labels = ["Hours", "Minutes", "Seconds"]
        time_values = [hours, minutes, seconds]

        for i, key in enumerate(time_rects.keys()):
            rect = time_rects[key]
            label = font_small.render(time_labels[i], True, get_color('TEXT_COLOR'))
            screen.blit(label, (rect.x, rect.y - 30))
            pygame.draw.rect(screen, get_color('INPUT_BG'), rect, border_radius=5)
            text_surface = font_small.render(f"{time_values[i]:02d}", True, get_color('INPUT_TEXT'))
            screen.blit(text_surface, text_surface.get_rect(center=rect.center))

        for i, rect in enumerate(interactive_elements):
            if rect not in time_rects.values():
                is_selected = (rect == no_time_button_rect and no_time_selected) or (rect == next_button_rect and next_enabled)
                color = SELECTED_BUTTON_COLOR if is_selected else get_color('BUTTON_COLOR')
                pygame.draw.rect(screen, color, rect, border_radius=10)

        if interactive_elements:
            focused_rect = interactive_elements[focus_index]
            pygame.draw.rect(screen, FOCUSED_BUTTON_COLOR, focused_rect.inflate(6, 6), 3, border_radius=12)

        no_time_text = font.render("No Time Restriction", True, get_color('TEXT_COLOR'))
        screen.blit(no_time_text, no_time_text.get_rect(center=no_time_button_rect.center))
        back_text = font.render("Back", True, get_color('TEXT_COLOR'))
        screen.blit(back_text, back_text.get_rect(center=back_button_rect.center))
        next_text = font.render("Next", True, get_color('TEXT_COLOR'))
        screen.blit(next_text, next_text.get_rect(center=next_button_rect.center))
        theme_text = font.render("Theme", True, get_color('TEXT_COLOR'))
        screen.blit(theme_text, theme_text.get_rect(center=theme_button_rect.center))
        draw_bottom_ui(screen)
        pygame.display.flip()

def get_move_evaluation(board, move):
    info = engine.analyse(board, chess.engine.Limit(depth=15))
    score = info["score"].relative.score(mate_score=10000)
    if board.is_check():
        return "red"
    for legal_move in board.legal_moves:
        if legal_move == move:
            break
    else:
        return "red"
    try:
        best_move = info["pv"][0]
        if move == best_move:
            return "green"
        else:
            board.push(move)
            new_info = engine.analyse(board, chess.engine.Limit(depth=15))
            new_score = new_info["score"].relative.score(mate_score=10000)
            board.pop()
            score_diff = score - new_score
            if abs(score_diff) <= 100:
                return "blue"
            else:
                return "red"
    except (KeyError, IndexError):
        return "blue"

class EvaluationScreen:
    def __init__(self, game_state):
        self.game_state = game_state
        self.board = chess.Board()
        self.move_history = game_state.move_history
        self.evaluated_moves = []
        self.current_move_index = 0
        self.is_playing = True
        self.speed = 1.0
        self.last_move_time = pygame.time.get_ticks()
        self.speed_options = [0.25, 0.5, 0.75, 1.0, 1.25, 1.5, 1.75, 2.0]
        self.speed_index = 3
        self.focus_index = 0
        self.ui_elements = {}
        self.interactive_elements = []
        self.DIVIDER_Y = HEIGHT * 0.85
        font_bottom = pygame.font.Font(None, 26)
        width_bottom, height_bottom = 100, 40
        gap_bottom = 15
        total_width = 5 * width_bottom + 4 * gap_bottom
        start_x = (WIDTH - total_width) / 2
        y_pos = self.DIVIDER_Y + (HEIGHT - self.DIVIDER_Y - height_bottom) / 2
        self.ui_elements['go_to_start'] = {'rect': pygame.Rect(start_x, y_pos, width_bottom, height_bottom), 'text': 'Go to Start', 'font': font_bottom}
        self.ui_elements['play_pause'] = {'rect': pygame.Rect(start_x + (width_bottom + gap_bottom), y_pos, width_bottom, height_bottom), 'text': 'Pause', 'font': font_bottom}
        self.ui_elements['prev'] = {'rect': pygame.Rect(start_x + 2 * (width_bottom + gap_bottom), y_pos, width_bottom, height_bottom), 'text': 'Previous', 'font': font_bottom}
        self.ui_elements['next'] = {'rect': pygame.Rect(start_x + 3 * (width_bottom + gap_bottom), y_pos, width_bottom, height_bottom), 'text': 'Next', 'font': font_bottom}
        self.ui_elements['speed'] = {'rect': pygame.Rect(start_x + 4 * (width_bottom + gap_bottom), y_pos, width_bottom, height_bottom), 'text': f'{self.speed}x', 'font': font_bottom}
        board_area_width = WIDTH * 0.875
        board_left = (board_area_width - BOARD_SIZE) // 2
        upper_section_height = self.DIVIDER_Y
        board_top = (upper_section_height - BOARD_SIZE) // 2
        button_y_pos = board_top + BOARD_SIZE + 10
        font_top = pygame.font.Font(None, 28)

        if self.game_state.result == "Resignation":
            ng_w, ng_h = 120, 40
            cont_w, cont_h = 120, 40
            ng_x = board_left
            cont_x = board_left + BOARD_SIZE - cont_w
            self.ui_elements['new_game'] = {'rect': pygame.Rect(ng_x, button_y_pos, ng_w, ng_h), 'text': 'New Game', 'font': font_top}
            self.ui_elements['continue'] = {'rect': pygame.Rect(cont_x, button_y_pos, cont_w, cont_h), 'text': 'Continue', 'font': font_top}
            self.interactive_elements = ['new_game', 'continue', 'go_to_start', 'play_pause', 'prev', 'next', 'speed']
        else:
            ng_w, ng_h = 150, 40
            ng_x = board_left + (BOARD_SIZE - ng_w) / 2
            self.ui_elements['new_game'] = {'rect': pygame.Rect(ng_x, button_y_pos, ng_w, ng_h), 'text': 'New Game', 'font': font_top}
            self.interactive_elements = ['new_game', 'go_to_start', 'play_pause', 'prev', 'next', 'speed']
        self.evaluate_moves()

    def evaluate_moves(self):
        temp_board = chess.Board()
        for move in self.move_history:
            color = get_move_evaluation(temp_board, move)
            self.evaluated_moves.append({
                "move": temp_board.san(move),
                "color": color
            })
            temp_board.push(move)

    def handle_events(self, event):
        if event.type == pygame.MOUSEBUTTONDOWN:
            for key, element in self.ui_elements.items():
                if element['rect'].collidepoint(event.pos):
                    if key in self.interactive_elements:
                        self.focus_index = self.interactive_elements.index(key)
                    return self.trigger_action(key)

        if event.type == pygame.KEYDOWN:
            if event.key == pygame.K_TAB:
                self.focus_index = (self.focus_index + 1) % len(self.interactive_elements)
            elif event.key == pygame.K_RETURN or event.key == pygame.K_KP_ENTER:
                focused_key = self.interactive_elements[self.focus_index]
                return self.trigger_action(focused_key)
            elif event.key == pygame.K_UP:
                focused_key = self.interactive_elements[self.focus_index]
                if focused_key == 'speed':
                    self.speed_index = max(0, self.speed_index - 1)
                    self.speed = self.speed_options[self.speed_index]
            elif event.key == pygame.K_DOWN:
                focused_key = self.interactive_elements[self.focus_index]
                if focused_key == 'speed':
                    self.speed_index = min(len(self.speed_options) - 1, self.speed_index + 1)
                    self.speed = self.speed_options[self.speed_index]
        return None

    def trigger_action(self, key):
        if key == "new_game": return "start_new_game"
        if key == "continue": return "continue_game"
        if key == "go_to_start":
            self.is_playing = False; self.current_move_index = 0; self.update_board()
        elif key == "play_pause":
            if self.current_move_index < len(self.move_history): self.is_playing = not self.is_playing
        elif key == "prev":
            self.is_playing = False; self.current_move_index = max(0, self.current_move_index - 1); self.update_board()
        elif key == "next":
            self.is_playing = False; self.current_move_index = min(len(self.move_history), self.current_move_index + 1); self.update_board()
        elif key == "speed":
            self.speed_index = (self.speed_index + 1) % len(self.speed_options); self.speed = self.speed_options[self.speed_index]
        return None

    def update_board(self):
        self.board = chess.Board()
        for i in range(self.current_move_index):
            self.board.push(self.move_history[i])

    def draw(self, screen):
        screen.fill(get_color('BACKGROUND_COLOR'))
        font_main_heading = pygame.font.Font(None, 48); font_main_heading.set_bold(True)
        game_eval_surface = font_main_heading.render("Game Evaluation", True, get_color('TEXT_COLOR'))
        board_area_width = WIDTH * 0.875
        board_left = (board_area_width - BOARD_SIZE) // 2
        heading_rect = game_eval_surface.get_rect(center=(board_left + BOARD_SIZE / 2, 40))
        screen.blit(game_eval_surface, heading_rect)
        upper_section_height = self.DIVIDER_Y
        board_top = (upper_section_height - BOARD_SIZE) // 2
        temp_board = chess.Board()
        for i in range(self.current_move_index): temp_board.push(self.move_history[i])
        draw_board_evaluation(screen, temp_board, board_left, board_top)
        moves_panel_width = WIDTH * 0.125
        moves_panel_rect = pygame.Rect(WIDTH - moves_panel_width, 0, moves_panel_width, upper_section_height)
        pygame.draw.rect(screen, get_color('BUTTON_COLOR'), moves_panel_rect)
        font_moves_heading = pygame.font.Font(None, 30)
        moves_heading_text = font_moves_heading.render("Moves", True, get_color('TEXT_COLOR'))
        screen.blit(moves_heading_text, moves_heading_text.get_rect(center=(moves_panel_rect.centerx, 20)))
        font_moves = pygame.font.Font(None, 24)
        y = 40
        start_index = max(0, self.current_move_index - 25)

        for i in range(start_index, self.current_move_index):
            move_info = self.evaluated_moves[i]
            color_map = {"green": (0, 150, 0), "blue": (0, 0, 150), "red": (150, 0, 0)}
            text_color = color_map.get(move_info["color"], get_color('TEXT_COLOR'))
            text = font_moves.render(move_info["move"], True, text_color)
            screen.blit(text, (moves_panel_rect.x + 10, moves_panel_rect.y + y))
            y += 20

        pygame.draw.line(screen, get_color('DIVIDER_COLOR'), (0, self.DIVIDER_Y), (WIDTH, self.DIVIDER_Y), 2)
        self.ui_elements['play_pause']['text'] = "Pause" if self.is_playing else "Resume"
        self.ui_elements['speed']['text'] = f"{self.speed}x"

        for key, element in self.ui_elements.items():
            color = get_color('BUTTON_COLOR')
            if key in ['new_game', 'continue', 'go_to_start']: color = SELECTED_BUTTON_COLOR
            if key == 'play_pause' and self.current_move_index < len(self.move_history):
                color = STOP_BUTTON_COLOR if self.is_playing else RESUME_BUTTON_COLOR
            if key == 'prev' and not self.is_playing and self.current_move_index > 0: color = SELECTED_BUTTON_COLOR
            if key == 'next' and not self.is_playing and self.current_move_index < len(self.move_history): color = SELECTED_BUTTON_COLOR
            if key == 'speed': color = SPEED_BUTTON_COLOR
            pygame.draw.rect(screen, color, element['rect'], border_radius=10)
            text_surface = element['font'].render(element['text'], True, get_color('TEXT_COLOR'))
            screen.blit(text_surface, text_surface.get_rect(center=element['rect'].center))

        if self.interactive_elements:
            focused_key = self.interactive_elements[self.focus_index]
            focused_rect = self.ui_elements[focused_key]['rect']
            pygame.draw.rect(screen, FOCUSED_BUTTON_COLOR, focused_rect.inflate(6, 6), 3, border_radius=12)

        pygame.display.flip()

    def update_and_draw(self, screen):
        if self.is_playing:
            current_time = pygame.time.get_ticks()
            if current_time - self.last_move_time > 1000 / self.speed:
                if self.current_move_index < len(self.move_history):
                    self.current_move_index += 1
                    self.last_move_time = current_time
        self.draw(screen)

def draw_board_evaluation(screen, board, top_left_x, top_left_y):
    for row in range(8):
        for col in range(8):
            color = get_color('BOARD_LIGHT') if (row + col) % 2 == 0 else get_color('BOARD_DARK')
            pygame.draw.rect(screen, color, pygame.Rect(top_left_x + col * SQUARE_SIZE, top_left_y + row * SQUARE_SIZE, SQUARE_SIZE, SQUARE_SIZE), border_radius=5)

    for row in range(8):
        for col in range(8):
            square = chess.square(col, 7 - row)
            piece = board.piece_at(square)
            if piece:
                piece_img = PIECE_IMAGES[piece.symbol()]
                x_pos = top_left_x + col * SQUARE_SIZE + (SQUARE_SIZE - PIECE_SIZE) // 2
                y_pos = top_left_y + row * SQUARE_SIZE + (SQUARE_SIZE - PIECE_SIZE) // 2
                screen.blit(piece_img, (x_pos, y_pos))

def main():
    pygame.init()
    screen = pygame.display.set_mode((WIDTH, HEIGHT))
    pygame.display.set_caption("Chess with AI")
    login_system = LoginSystem()
    game_state = None
    evaluation_screen = None
    current_state = LOGIN_SCREEN
    user_selections = {
        "mode": None,
        "color": None,
        "difficulty": None,
        "time": None,
        "no_time": False
    }
    running = True

    while running:
        if current_state == LOGIN_SCREEN:
            action = show_login_screen(screen, login_system)
            if action == "quit": running = False
            elif action == "next": current_state = MODE_SCREEN
        elif current_state == MODE_SCREEN:
            action, mode = show_mode_selection_screen(screen, user_selections["mode"])
            user_selections["mode"] = mode
            if action == "quit": running = False
            elif action == "back": current_state = LOGIN_SCREEN
            elif action == "next":
                if mode == "Human vs AI": current_state = COLOR_SCREEN
                elif mode == "Human vs Human": current_state = TIME_SCREEN
                elif mode == "AI vs AI": current_state = GAME_SCREEN
        elif current_state == COLOR_SCREEN:
            action, color = show_color_selection_screen(screen, user_selections["color"])
            user_selections["color"] = color
            if action == "quit": running = False
            elif action == "back": current_state = MODE_SCREEN
            elif action == "next": current_state = DIFFICULTY_SCREEN
        elif current_state == DIFFICULTY_SCREEN:
            action, difficulty = show_difficulty_selection_screen(screen, user_selections["difficulty"])
            user_selections["difficulty"] = difficulty
            if action == "quit": running = False
            elif action == "back": current_state = COLOR_SCREEN
            elif action == "next": current_state = TIME_SCREEN
        elif current_state == TIME_SCREEN:
            action, time_limit, no_time = show_time_selection_screen(screen, user_selections["time"], user_selections["no_time"])
            user_selections["time"] = time_limit
            user_selections["no_time"] = no_time
            if action == "quit": running = False
            elif action == "back":
                if user_selections["mode"] == "Human vs Human": current_state = MODE_SCREEN
                else: current_state = DIFFICULTY_SCREEN
            elif action == "next":
                game_state = GameState(user_selections["mode"], user_selections["color"], user_selections["time"], user_selections["difficulty"])
                print("🚀 New game started.")
                print(f"   Mode: {game_state.game_mode}, Difficulty: {game_state.difficulty}, Time: {game_state.time_limit if game_state.time_limit else 'Unlimited'}")
                current_state = GAME_SCREEN
        elif current_state == GAME_SCREEN:
            if game_state:
                if game_state.game_over:
                    evaluation_screen = EvaluationScreen(game_state)
                    current_state = EVALUATION_SCREEN
                    print("📊 Entering evaluation screen.")
                else:
                    game_state.check_game_over()
                    if game_state.game_mode == "Human vs AI" and game_state.board.turn != game_state.human_color and not game_state.game_over:
                        game_state.get_ai_move()
                    elif game_state.game_mode == "AI vs AI" and not game_state.game_over:
                        game_state.get_ai_move()
                        pygame.time.wait(250)
                    game_state.check_time()
                    screen.fill(get_color('BACKGROUND_COLOR'))
                    pygame.draw.rect(screen, get_color('BACKGROUND_COLOR'), pygame.Rect(0, 0, WIDTH, HEIGHT * 0.8))
                    draw_board(screen, game_state)
                    line_y = HEIGHT * 0.8
                    pygame.draw.line(screen, get_color('DIVIDER_COLOR'), (0, line_y), (WIDTH, line_y), 2)
                    resign_rect, hint_rect, save_rect = draw_buttons_and_info(screen, game_state, login_system.get_user_stats(), user_selections)
                    draw_bottom_ui(screen)
                    pygame.display.flip()
                    for event in pygame.event.get():
                        if event.type == pygame.QUIT:
                            running = False
                        if event.type == pygame.MOUSEBUTTONDOWN:
                            game_state.handle_click(event.pos)
                            if resign_rect and resign_rect.collidepoint(event.pos):
                                game_state.game_over = True
                                game_state.result = "Resignation"
                                print("🏳️ Player has resigned the game.")
                            if hint_rect and hint_rect.collidepoint(event.pos):
                                if game_state.game_mode in ["Human vs AI", "Human vs Human"]:
                                    game_state.get_hint()
                            if save_rect and save_rect.collidepoint(event.pos) and not game_state.is_saved:
                                login_system.save_game(game_state)
                                game_state.is_saved = True
            else:
                game_state = GameState(user_selections["mode"], user_selections["color"], user_selections["time"], user_selections["difficulty"])
        elif current_state == EVALUATION_SCREEN:
            action = None
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    running = False
                action = evaluation_screen.handle_events(event)
                if action == "start_new_game":
                    print("\n🔄 Starting a new game from evaluation screen.")
                    current_state = MODE_SCREEN
                    game_state = None
                    break
                elif action == "continue_game":
                    game_state.game_over = False
                    current_state = GAME_SCREEN
                    print("▶️ Continuing resigned game.")
                    break
            if action in ["start_new_game", "continue_game"]: continue
            evaluation_screen.update_and_draw(screen)

    print("👋 Exiting chess application. Goodbye!")
    pygame.quit()
    engine.quit()
    sys.exit()

if __name__ == "__main__":
    main()
