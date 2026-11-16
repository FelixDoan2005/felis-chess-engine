import threading

import chess
import chess.engine
import pygame
from ui.chess_logic import in_check, get_all_legal_moves, draw_reason
from engine.uci import square_from_name, play_uci_move

GAME_OVER_DISPLAY_MS = 5000


def check_game_end(board, piece_moves):
    # Returns (title, reason) for the game-over popup, or None if play continues.
    if not get_all_legal_moves(board, piece_moves):
        if board.turn == "white":
            king_pos = board.white_king
            winner = "Black"
        else:
            king_pos = board.black_king
            winner = "White"
        if in_check(board.grid, board.turn, king_pos):
            return f"{winner} wins!", "by checkmate"
        return "Draw", "by stalemate"

    reason = draw_reason(board)
    if reason:
        return "Draw", f"by {reason}"
    return None

def end_if_over(game):
    # shows the game-over popup if the game has ended, returns True if it has
    result = check_game_end(game.board, game.piece_moves)
    if result:
        game.game_result = result
        game.game_over_time = pygame.time.get_ticks()
        game.state = "game_over"
        return True
    return False

def make_move_and_check_promotion(board, from_sq, to_sq):
    board.move_piece(from_sq, to_sq)
    moved_piece = board.get_piece(*to_sq)
    row = to_sq[0]
    if moved_piece is not None and moved_piece.endswith("pawn") and row in (0, 7):
        return moved_piece.split("_")[0]
    return None

def timeout_result(move_list, flagged):
    # running out of time loses, unless the other side can't possibly checkmate
    # (e.g. a lone king), then it's a draw
    chess_board = chess.Board()
    for uci in move_list:
        chess_board.push_uci(uci)
    if flagged == "white":
        other = chess.BLACK
        winner = "Black"
    else:
        other = chess.WHITE
        winner = "White"
    if chess_board.has_insufficient_material(other):
        return "Draw", "by timeout vs insufficient material"
    return f"{winner} wins!", "on time"

def press_clock(clocks, side, clock_start, move_list):
    # takes the time used off the side that just moved, returns when the next clock starts
    # white's first move is free: the clocks only start after it
    now = pygame.time.get_ticks()
    if len(move_list) > 1:
        clocks[side] -= (now - clock_start) / 1000
    return now

def switch_clock(game):
    # after a move: stop the mover's clock and start the other side's
    if game.clocks is not None:
        game.clock_start = press_clock(game.clocks, game.clock_side, game.clock_start, game.move_list)
        game.clock_side = game.board.turn

def run_engine_search(engine, move_list, limit, game_number, result):
    # the engine runs as its own program (engine/uci.py, or Stockfish): send it
    # the game so far and wait for its move, e.g. "e7e5"
    chess_board = chess.Board()
    for uci in move_list:
        chess_board.push_uci(uci)
    try:
        # a new game_number tells the engine a new game started ("ucinewgame"),
        # so it empties the table it keeps between moves
        played = engine.play(chess_board, limit, game=game_number)
        result["move"] = played.move.uci()
    except chess.engine.EngineError:
        result["move"] = None
    except chess.engine.EngineTerminatedError:
        result["move"] = None

def start_search(game, thinker, search_depth):
    # asks an engine program for a move, on its own thread so the window doesn't freeze
    if game.clocks is None:
        limit = chess.engine.Limit(depth=search_depth, time=game.time_limit)
    else:
        # the engine gets both clocks and decides its own time
        limit = chess.engine.Limit(depth=search_depth, white_clock=game.clocks["white"], black_clock=game.clocks["black"])
    game.engine_result = {}
    game.engine_thread = threading.Thread(
        target=run_engine_search,
        args=(thinker, list(game.move_list), limit, game.game_number, game.engine_result),
        daemon=True,
    )
    game.engine_thread.start()

def take_engine_move(game):
    # plays the move the engine thread found; returns True if the game goes on
    move = game.engine_result.get("move")
    game.engine_thread = None
    if move is None:
        # the engine program stopped answering
        game.game_result = ("Engine error", "the engine stopped responding")
        game.game_over_time = pygame.time.get_ticks()
        game.state = "game_over"
        return False

    play_uci_move(game.board, move)
    game.last_move = (square_from_name(move[0:2]), square_from_name(move[2:4]))
    game.move_list.append(move)
    game.last_move_time = pygame.time.get_ticks()
    switch_clock(game)
    game.selected_square = None
    game.highlights = []
    return not end_if_over(game)
