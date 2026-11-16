from ui.chess_logic import pixel_to_square, select_piece
from engine.uci import square_name
from modes.common import make_move_and_check_promotion, switch_clock, end_if_over, start_search, take_engine_move
from modes.human import human_turn


def premove_position(grid, premoves):
    position = []
    for row in grid:
        position.append(row[:])
    for from_sq, to_sq in premoves:
        fr, fc = from_sq
        tr, tc = to_sq
        piece = position[fr][fc]
        if piece is None:
            continue
        position[fr][fc] = None
        colour, kind = piece.split("_")
        if kind == "pawn" and (tr == 0 or tr == 7):
            position[tr][tc] = f"{colour}_queen"
        else:
            position[tr][tc] = piece
        if kind == "king" and fc == 4 and tc == 6:
            position[tr][5] = position[tr][7]
            position[tr][7] = None
        if kind == "king" and fc == 4 and tc == 2:
            position[tr][3] = position[tr][0]
            position[tr][0] = None
    return position

def premove_targets(square, piece):
    row, col = square
    colour, kind = piece.split("_")
    targets = []

    def add(r, c):
        if 0 <= r < 8 and 0 <= c < 8:
            targets.append((r, c))

    if kind == "pawn":
        if colour == "white":
            forward = -1
            start_row = 6
        else:
            forward = 1
            start_row = 1
        add(row + forward, col)
        if row == start_row:
            add(row + 2 * forward, col)
        add(row + forward, col - 1)
        add(row + forward, col + 1)
    elif kind == "knight":
        for dr, dc in [(1, 2), (2, 1), (2, -1), (1, -2), (-1, -2), (-2, -1), (-2, 1), (-1, 2)]:
            add(row + dr, col + dc)
    elif kind == "king":
        for dr in [-1, 0, 1]:
            for dc in [-1, 0, 1]:
                if dr != 0 or dc != 0:
                    add(row + dr, col + dc)
        if colour == "white":
            home_row = 7
        else:
            home_row = 0
        if row == home_row and col == 4:
            add(row, 6)
            add(row, 2)
    else:
        directions = []
        if kind == "bishop" or kind == "queen":
            directions.extend([(1, 1), (1, -1), (-1, 1), (-1, -1)])
        if kind == "rook" or kind == "queen":
            directions.extend([(1, 0), (-1, 0), (0, 1), (0, -1)])
        for dr, dc in directions:
            r = row + dr
            c = col + dc
            while 0 <= r < 8 and 0 <= c < 8:
                add(r, c)
                r += dr
                c += dc
    return targets


def play_premove(game):
    # after Felis moves, plays the first premove you lined up if it's legal, otherwise drops them all
    from_sq, to_sq = game.premoves.pop(0)
    piece = game.board.get_piece(*from_sq)
    legal = []
    if piece is not None and piece.startswith(game.board.turn):
        _, legal = select_piece(from_sq, piece, game.board, game.piece_moves)
    if to_sq in legal:
        uci = square_name(from_sq) + square_name(to_sq)
        game.last_move = (from_sq, to_sq)
        promo_colour = make_move_and_check_promotion(game.board, from_sq, to_sq)
        if promo_colour is not None:
            game.board.grid[to_sq[0]][to_sq[1]] = f"{promo_colour}_queen"
            uci += "q"
        game.move_list.append(uci)
        switch_clock(game)
        end_if_over(game)
    else:
        game.premoves = []


def queue_premove(game, click):
    # while Felis is thinking: click a piece, then a square, to line up a premove
    square = pixel_to_square(*click)
    if square:
        position = premove_position(game.board.grid, game.premoves)
        piece = position[square[0]][square[1]]
        if game.selected_square is not None and square in game.highlights:
            game.premoves.append((game.selected_square, square))
            game.selected_square = None
            game.highlights = []
        elif piece is not None and piece.startswith(game.player_colour):
            game.selected_square = square
            game.highlights = premove_targets(square, piece)
        else:
            game.selected_square = None
            game.highlights = []


def felis_turn(game, click, right_click):
    if game.engine_thread is None:
        start_search(game, game.engine, game.depth)
    elif not game.engine_thread.is_alive():
        if take_engine_move(game) and len(game.premoves) > 0:
            play_premove(game)

    if right_click:
        game.premoves = []
        game.selected_square = None
        game.highlights = []
    elif click and game.state == "playing" and game.engine_thread is not None:
        queue_premove(game, click)


def play(game, renderer, click, right_click):
    # you play one colour and Felis plays the other
    if game.board.turn != game.player_colour:
        felis_turn(game, click, right_click)
    else:
        human_turn(game, click)

    renderer.draw(premove_position(game.board.grid, game.premoves), game.highlights, game.last_move, game.premoves)
    if game.engine_thread is not None:
        renderer.draw_thinking()
