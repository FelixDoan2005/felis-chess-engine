import chess.engine
import pygame
from engine.uci import stockfish_path
from modes.common import start_search, take_engine_move

MOVE_DELAY_MS = 600   # a pause between moves, so you can follow the game


def setup(game):
    # starts Stockfish for the first game, sets its strength, and writes the caption under the board
    if game.stockfish is None:
        game.stockfish = chess.engine.SimpleEngine.popen_uci(stockfish_path())
    if game.stockfish_elo is None:
        game.stockfish.configure({"UCI_LimitStrength": False})
        stockfish_label = "full strength"
    else:
        game.stockfish.configure({"UCI_LimitStrength": True, "UCI_Elo": game.stockfish_elo})
        stockfish_label = f"{game.stockfish_elo}"
    if game.depth is None:
        engine_label = "max"
    else:
        engine_label = f"depth {game.depth}"
    if game.clock_minutes is None:
        time_label = f"{game.time_limit:g}s"
    else:
        time_label = f"{game.clock_minutes} min"
    game.caption = f"Felis ({engine_label}) vs Stockfish {stockfish_label}, {time_label}"
    game.last_move_time = pygame.time.get_ticks()


def play(game, renderer, click, right_click):
    # Felis and Stockfish take turns by themselves; player_colour is the colour Felis plays
    if game.engine_thread is None:
        # wait a moment after each move so you can follow
        if pygame.time.get_ticks() - game.last_move_time >= MOVE_DELAY_MS:
            if game.board.turn != game.player_colour:
                thinker = game.stockfish
                search_depth = None
            else:
                thinker = game.engine
                search_depth = game.depth
            # the pause between moves doesn't count on the clock
            if game.clocks is not None:
                game.clock_start = pygame.time.get_ticks()
            start_search(game, thinker, search_depth)
    elif not game.engine_thread.is_alive():
        take_engine_move(game)

    game.selected_square = None
    game.highlights = []

    renderer.draw(game.board.grid, game.highlights, game.last_move)
    renderer.draw_caption(game.caption)
    if game.engine_thread is not None:
        if game.board.turn != game.player_colour:
            renderer.draw_thinking("Stockfish is thinking...")
        else:
            renderer.draw_thinking("Felis is thinking...")
