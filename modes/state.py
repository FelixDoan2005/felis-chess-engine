from ui.chess_logic import pawn_moves, knight_moves, bishop_moves, rook_moves, queen_moves, king_moves


class Game:
    # everything about the game in progress, shared by the menus and the three modes
    def __init__(self):
        self.piece_moves = {
            "pawn": pawn_moves,
            "knight": knight_moves,
            "bishop": bishop_moves,
            "rook": rook_moves,
            "queen": queen_moves,
            "king": king_moves,
        }

        self.state = "menu"
        self.board = None
        self.highlights = []
        self.selected_square = None
        self.promotion_square = None
        self.promotion_colour = None
        self.game_result = None
        self.game_over_time = None
        self.mode = None
        self.player_colour = None
        self.depth = None
        self.time_limit = None
        self.engine = None             # the engine program, started for the first game against it
        self.stockfish = None          # Stockfish, started for the first Engine vs Stockfish game
        self.stockfish_elo = None      # its Elo cap, None = full strength
        self.caption = ""              # Engine vs Stockfish: who is playing who, under the board
        self.last_move_time = 0        # when the last engine move was played
        self.move_list = []            # every move this game, e.g. ["e2e4", "e7e5"], for the engine
        self.game_number = 0           # goes up each game against the engine
        self.promotion_move = None     # a promotion waiting for its piece, e.g. "e7e8"
        self.custom_text = ""          # the custom time per move being typed, e.g. "20"
        self.custom_error = ""         # shown when what was typed isn't a number
        self.last_move = None          # (from square, to square) of the last move, drawn glowing green
        self.engine_thread = None
        self.engine_result = None
        self.clock_minutes = None      # game clock in minutes each, None = no clock
        self.clocks = None             # seconds left, e.g. {"white": 300.0, "black": 300.0}
        self.clock_side = "white"      # whose clock is running
        self.clock_start = 0           # when it started running
        self.premoves = []
