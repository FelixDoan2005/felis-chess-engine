from ui.chess_logic import pixel_to_square, select_piece
from engine.uci import square_name
from modes.common import make_move_and_check_promotion, switch_clock, end_if_over

PROMOTION_LETTERS = {"queen": "q", "rook": "r", "bishop": "b", "knight": "n"}


def human_turn(game, click):
    # a person clicks a piece, then a square to move it to (Player vs Player, and your turn against Felis)
    if not click:
        return
    square = pixel_to_square(*click)
    if square:
        piece = game.board.get_piece(*square)

        if piece is not None and piece.startswith(game.board.turn):
            game.selected_square, game.highlights = select_piece(square, piece, game.board, game.piece_moves)
        else:
            if square in game.highlights:
                uci = square_name(game.selected_square) + square_name(square)
                game.last_move = (game.selected_square, square)
                promo_colour = make_move_and_check_promotion(game.board, game.selected_square, square)

                if promo_colour is not None:
                    # added to move_list once the piece is picked
                    game.promotion_move = uci
                    game.promotion_square = square
                    game.promotion_colour = promo_colour
                    game.state = "promotion"
                else:
                    game.move_list.append(uci)
                    switch_clock(game)
                    end_if_over(game)

                game.selected_square = None
                game.highlights = []
            else:
                if piece is not None and piece.startswith(game.board.turn):
                    game.selected_square, game.highlights = select_piece(square, piece, game.board, game.piece_moves)
                else:
                    game.selected_square = None
                    game.highlights = []


def promotion_screen(game, renderer, click):
    # the piece picker shown when your pawn reaches the last row
    renderer.draw(game.board.grid, [], game.last_move)
    renderer.draw_promotion_picker(game.promotion_colour)

    if click:
        for kind, rect in renderer.promotion_rects.items():
            if rect.collidepoint(click):
                row, col = game.promotion_square
                game.board.grid[row][col] = f"{game.promotion_colour}_{kind}"
                game.move_list.append(game.promotion_move + PROMOTION_LETTERS[kind])
                switch_clock(game)
                game.promotion_move = None
                game.promotion_square = None
                game.promotion_colour = None

                if not end_if_over(game):
                    game.state = "playing"
                break
