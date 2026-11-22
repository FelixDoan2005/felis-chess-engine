import pygame
from ui.window import create_window
from ui.renderer import Renderer
from ui.input_handler import InputHandler
from ui.constants import FPS
from modes.state import Game
from modes.clocks import update_clocks
from modes.human import promotion_screen
from modes import menus, pvp, pve, evs


def main() -> None:
    screen = create_window()
    clock = pygame.time.Clock()
    renderer = Renderer(screen)
    handler = InputHandler()
    game = Game()

    running = True
    while running:
        events = pygame.event.get()
        running = handler.handle(events)
        click = handler.get_mouse_click(events)
        right_click = handler.get_right_click(events)

        if game.state != "menu" and game.state != "message" and click and renderer.menu_rect.collidepoint(click):
            menus.back_to_menu(game)
            click = None

        if game.state == "menu":
            menus.menu_screen(game, renderer, click)
        elif game.state == "message":
            menus.message_screen(game, renderer)
        elif game.state == "colour_select":
            menus.colour_select_screen(game, renderer, click)
        elif game.state == "difficulty_select":
            menus.difficulty_select_screen(game, renderer, click)
        elif game.state == "stockfish_select":
            menus.stockfish_select_screen(game, renderer, click)
        elif game.state == "clock_select":
            menus.clock_select_screen(game, renderer, click)
        elif game.state == "time_select":
            menus.time_select_screen(game, renderer, click)
        elif game.state == "custom_time":
            menus.custom_time_screen(game, renderer, events)
        elif game.state == "start_game":
            menus.start_game(game)
        elif game.state == "playing":
            if game.mode == "pvp":
                pvp.play(game, renderer, click, right_click)
            elif game.mode == "pve":
                pve.play(game, renderer, click, right_click)
            elif game.mode == "evs":
                evs.play(game, renderer, click, right_click)
        elif game.state == "promotion":
            promotion_screen(game, renderer, click)
        elif game.state == "game_over":
            menus.game_over_screen(game, renderer)

        update_clocks(game, renderer)

        if game.state != "menu" and game.state != "message":
            renderer.draw_menu_button()

        pygame.display.flip()
        clock.tick(FPS)

    # stop the engine programs straight away, even if they're mid-search
    if game.engine is not None:
        game.engine.close()
    if game.stockfish is not None:
        game.stockfish.close()
    pygame.quit()

if __name__ == "__main__":
    main()
