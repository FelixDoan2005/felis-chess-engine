import json
import chess
import chess.pgn
import re

with open("all-games-data.json", encoding="utf-8-sig") as f:
    games = json.load(f)

pgn_games = []
errors = []

for index, data in enumerate(games, 1):
    try:
        player = str(data.get("name") or "Unknown")
        colour = data.get("player_colour", "w")
        rating = str(data.get("rating") or "?")
        result = str(data.get("result") or "*")

        if result not in ("1-0", "0-1", "1/2-1/2", "*"):
            result = "*"

        game = chess.pgn.Game()

        game.headers["Event"] = "Felis Game"
        game.headers["White"] = player if colour == "w" else "Felis"
        game.headers["Black"] = "Felis" if colour == "w" else player
        game.headers["Result"] = result

        if rating != "?":
            if colour == "w":
                game.headers["WhiteElo"] = rating
            else:
                game.headers["BlackElo"] = rating

        filename = data.get("source_file", "")
        date = re.search(r"(\d{4})-(\d{2})-(\d{2})", filename)

        if date:
            game.headers["Date"] = ".".join(date.groups())

        reason = data.get("reason")
        if reason:
            game.headers["Termination"] = str(reason)

        if data.get("clock_minutes") is not None:
            game.headers["FelisClockMinutes"] = str(data["clock_minutes"])

        if data.get("seconds") is not None:
            game.headers["FelisSecondsPerMove"] = str(data["seconds"])

        board = game.board()
        node = game

        for uci in data.get("moves", []):
            move = chess.Move.from_uci(uci)
            if move not in board.legal_moves:
                raise ValueError(f"Illegal move: {uci}")

            node = node.add_variation(move)
            board.push(move)

        game.headers["PlyCount"] = str(len(data.get("moves", [])))

        exporter = chess.pgn.StringExporter(
            headers=True,
            variations=False,
            comments=False
        )

        pgn_games.append(game.accept(exporter))

        print(f"Converted game {index}/{len(games)}: {player}")

    except Exception as e:
        errors.append(f"Game {index} ({data.get('name', 'Unknown')}): {e}")

with open("all-games.pgn", "w", encoding="utf-8") as f:
    f.write("\n\n".join(pgn_games))

print(f"\nSuccessfully converted: {len(pgn_games)}/{len(games)} games")
print("Created all-games.pgn")

if errors:
    print("\nGames with conversion errors:")
    for error in errors:
        print(error)
