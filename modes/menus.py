import chess.engine
import pygame
from ui.chess_logic import Board
from engine.ai import DIFFICULTY_DEPTH
from engine.uci import engine_command, stockfish_path
from modes.common import GAME_OVER_DISPLAY_MS
from modes import evs


def back_to_menu(game):
    # the Menu button: stop the engine programs if they're mid-search
    if game.engine_thread is not None:
        if game.engine is not None:
            game.engine.close()
            game.engine = None
        if game.stockfish is not None:
            game.stockfish.close()
            game.stockfish = None
        game.engine_thread = None
    game.state = "menu"


def menu_screen(game, renderer, click):
    renderer.draw_menu()
    if click:
        if renderer.pvp_rect.collidepoint(click):
            game.mode = "pvp"
            game.player_colour = None
            game.state = "clock_select"
        elif renderer.pve_rect.collidepoint(click):
            game.mode = "pve"
            game.state = "colour_select"
        elif renderer.evs_rect.collidepoint(click):
            if stockfish_path() is None:
                game.game_result = ("Stockfish not found", "set STOCKFISH_PATH (see README)")
                game.game_over_time = pygame.time.get_ticks()
                game.state = "message"
            else:
                game.mode = "evs"
                game.state = "colour_select"


def message_screen(game, renderer):
    renderer.draw_menu()
    renderer.draw_game_over_popup(*game.game_result)
    if pygame.time.get_ticks() - game.game_over_time >= GAME_OVER_DISPLAY_MS:
        game.state = "menu"


def colour_select_screen(game, renderer, click):
    # Engine vs Stockfish: player_colour is the colour Felis plays
    if game.mode == "evs":
        renderer.draw_colour_select("Felis Plays", "White", "Black")
    else:
        renderer.draw_colour_select()
    if click:
        if renderer.white_rect.collidepoint(click):
            game.player_colour = "white"
            game.state = "difficulty_select"
        elif renderer.black_rect.collidepoint(click):
            game.player_colour = "black"
            game.state = "difficulty_select"


def difficulty_select_screen(game, renderer, click):
    renderer.draw_difficulty_select()
    if click:
        for level, rect in renderer.difficulty_rects.items():
            if rect.collidepoint(click):
                # "max": no depth limit, the engine searches as deep as the time allows
                if level == "max":
                    game.depth = None
                else:
                    game.depth = DIFFICULTY_DEPTH[level]
                if game.mode == "evs":
                    game.state = "stockfish_select"
                else:
                    game.state = "clock_select"
                break


def stockfish_select_screen(game, renderer, click):
    renderer.draw_stockfish_select()
    if click:
        for elo, rect in renderer.stockfish_rects.items():
            if rect.collidepoint(click):
                game.stockfish_elo = elo
                game.state = "clock_select"
                break


def clock_select_screen(game, renderer, click):
    # ratings were only tested at max difficulty
    show_ratings = False
    if game.mode != "pvp" and game.depth is None:
        show_ratings = True
    renderer.draw_clock_select(show_ratings=show_ratings)
    if click:
        for minutes, rect in renderer.clock_rects.items():
            if rect.collidepoint(click):
                game.clock_minutes = minutes
                # no clock against an engine: pick the seconds per move instead
                if minutes is None and game.mode != "pvp":
                    game.state = "time_select"
                else:
                    game.state = "start_game"
                break


def time_select_screen(game, renderer, click):
    # no "Unlimited" against Stockfish or on max difficulty: they'd think forever
    unlimited_allowed = True
    if game.mode == "evs" or game.depth is None:
        unlimited_allowed = False
    # ratings were only tested at max difficulty
    show_ratings = False
    if game.depth is None:
        show_ratings = True
    renderer.draw_time_select(include_unlimited=unlimited_allowed, show_ratings=show_ratings)
    if click:
        for limit, rect in renderer.time_rects.items():
            if limit is None and not unlimited_allowed:
                continue
            if rect.collidepoint(click):
                if limit == "custom":
                    game.custom_text = ""
                    game.custom_error = ""
                    game.state = "custom_time"
                else:
                    game.time_limit = limit
                    game.state = "start_game"
                break


def custom_time_screen(game, renderer, events):
    # type the seconds: Enter starts the game, Esc goes back
    renderer.draw_custom_time(game.custom_text, game.custom_error)
    for event in events:
        if event.type != pygame.KEYDOWN:
            continue
        if event.key == pygame.K_ESCAPE:
            game.state = "time_select"
        elif event.key == pygame.K_BACKSPACE:
            game.custom_text = game.custom_text[:-1]
        elif event.key == pygame.K_RETURN or event.key == pygame.K_KP_ENTER:
            try:
                seconds = float(game.custom_text)
            except ValueError:
                seconds = 0
            if seconds > 0:
                game.time_limit = seconds
                game.state = "start_game"
            else:
                game.custom_error = "Type a number of seconds, e.g. 20"
        elif event.unicode in "0123456789." and event.unicode != "" and len(game.custom_text) < 6:
            game.custom_text += event.unicode
            game.custom_error = ""


def start_game(game):
    # start the engine programs if needed, and a fresh board
    if game.engine is None and game.mode != "pvp":
        game.engine = chess.engine.SimpleEngine.popen_uci(engine_command())

    if game.clock_minutes is None:
        game.clocks = None
    else:
        game.clocks = {"white": game.clock_minutes * 60, "black": game.clock_minutes * 60}
        game.clock_side = "white"
        game.clock_start = pygame.time.get_ticks()

    if game.mode == "evs":
        evs.setup(game)

    game.game_number += 1
    game.board = Board()
    game.move_list = []
    game.last_move = None
    game.highlights = []
    game.selected_square = None
    game.promotion_square = None
    game.promotion_colour = None
    game.engine_thread = None
    game.engine_result = None
    game.premoves = []
    game.state = "playing"


def game_over_screen(game, renderer):
    renderer.draw(game.board.grid, [], game.last_move)
    renderer.draw_game_over_popup(*game.game_result)
    if pygame.time.get_ticks() - game.game_over_time >= GAME_OVER_DISPLAY_MS:
        game.state = "menu"
