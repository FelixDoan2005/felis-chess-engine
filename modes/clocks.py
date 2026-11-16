import pygame
from modes.common import timeout_result


def update_clocks(game, renderer):
    # game clock: the side to move loses when theirs runs out
    # it starts after white's first move, and in Engine vs Stockfish
    # it waits during the pause between moves
    clock_ticking = False
    if game.clocks is not None and (game.state == "playing" or game.state == "promotion") and len(game.move_list) > 0:
        if game.mode != "evs" or game.engine_thread is not None:
            clock_ticking = True

    if clock_ticking:
        time_left = game.clocks[game.clock_side] - (pygame.time.get_ticks() - game.clock_start) / 1000
        if time_left <= 0:
            game.clocks[game.clock_side] = 0
            game.game_result = timeout_result(game.move_list, game.clock_side)
            game.game_over_time = pygame.time.get_ticks()
            game.state = "game_over"

    if game.clocks is not None and (game.state == "playing" or game.state == "promotion" or game.state == "game_over"):
        white_left = game.clocks["white"]
        black_left = game.clocks["black"]
        running_clock = None
        if game.state != "game_over" and len(game.move_list) > 0:
            running_clock = game.clock_side
        if clock_ticking:
            elapsed = (pygame.time.get_ticks() - game.clock_start) / 1000
            if game.clock_side == "white":
                white_left -= elapsed
            else:
                black_left -= elapsed
        renderer.draw_clocks(white_left, black_left, running_clock)
