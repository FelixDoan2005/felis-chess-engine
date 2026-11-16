from modes.human import human_turn


def play(game, renderer, click, right_click):
    # two people take turns clicking on the same board
    human_turn(game, click)
    renderer.draw(game.board.grid, game.highlights, game.last_move)
