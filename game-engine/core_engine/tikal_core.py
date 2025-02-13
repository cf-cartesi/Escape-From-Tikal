import core_engine.aux as aux
import core_engine.const as const
import core_engine.confs as confs


class GameMap:

    def __init__(self, tiles_definiton):
        self.tiles = tiles_definiton
        

class GameBoard:

    #Constructor to initialize an empty board
    def __init__(self):
        self.tiles = {}
        self.water_supply = confs.INITIAL_WATER_SUPPLY
        self.max_water_supply = confs.INITIAL_WATER_SUPPLY
        self.curse_count = confs.INITIAL_CURSES_COUNT
        self.amulet_count = confs.INITIAL_AMULET_COUNT
        self.words_on_board = {}
        self.game_status = const.ONGOING
        self.word_tile_coords_set = set()

        for line in confs.MAP_BOUNDARIES.keys():
            self.tiles[line] = {}

            for column in range(confs.MAP_BOUNDARIES[line][const.BEGINNING], confs.MAP_BOUNDARIES[line][const.END] + 1):
                self.tiles[line][column] = {const.TYPE: const.EMPTY}

    def load_initial_words(self, setup_words):
        #Validate words are valid and in correct amount
        word_count = 0
        for line in setup_words.keys():
            for column in setup_words[line].keys():
                if word_count >= 3:
                    raise ValueError(f"Provided more than 3 initial words")

                new_word = setup_words[line][column]
                similar_word = aux.check_word_similarity(new_word, self.words_on_board)
                if similar_word:
                    raise ValueError(f"Provided word ({new_word} is similar to an existing word ({similar_word}))")
                word_count += 1

        for line in setup_words.keys():
            for column in setup_words[line].keys():
                new_word = setup_words[line][column]
                self.tiles[line][column] = {const.TYPE: const.WORD, const.WORD: new_word}
                self.words_on_board[new_word] = (line, column)
                self.word_tile_coords_set.add((line, column))

class GameExecutor:

    def __init__(self, game_board, game_map):
        self.game_board = game_board
        self.game_map = game_map

    def execute_game(self, words):
        
        for word in words:
            #Generate word influence groups
            word_groups = generate_word_groups(self.game_board)

            #Ask AI to provide the closest related word group

            #Chose tile from tile group associated to chosen word group

            #Evaluate the move

            #Check if game ended

        #Return full state
        return self.game_board

#Goes through the board and generates all word groups that influence nearby tiles
def generate_word_groups(game_board):
    tiles = game_board.tiles
    aux.print_gameboard(tiles)

    #Set of word groups
    word_groups = set()

    #Set of tiles to visit
    pending_tiles = set()

    #word groups to tiles mapping
    wg_to_tiles = {}

    #Getting all valid tiles for next move
    for word in game_board.words_on_board.keys():
        line, column = game_board.words_on_board[word]
        
        print(f"\nTile to analyze next: {line},{column}")

        adjacent_tiles = [
            (line - 1, column),     #Tile above
            (line + 1, column),     #Tile bellow
            (line, column - 1),     #Tile top left
            (line + 1, column - 1), #Tile bottom left
            (line - 1, column + 1), #Tile top right
            (line, column + 1),     #Tile bottom right
        ]

        for adjacent_tile in adjacent_tiles:
            if aux.check_valid_tile_coord(adjacent_tile):
                if adjacent_tile not in pending_tiles:
                    if adjacent_tile not in game_board.word_tile_coords_set:
                        pending_tiles.add(adjacent_tile)

        print(f"\nPending tiles to visit: {sorted(pending_tiles, key=lambda tup: (tup[0],tup[1]) )}")

    #Getting all word groups for all tiles
    for pending_tile in pending_tiles:

        print(f"\nRetrieving word group for tile: {pending_tile}")
        line, column = pending_tile

        adjacent_tiles = [
            (line - 1, column),     #Tile above
            (line + 1, column),     #Tile bellow
            (line, column - 1),     #Tile top left
            (line + 1, column - 1), #Tile bottom left
            (line - 1, column + 1), #Tile top right
            (line, column + 1),     #Tile bottom right
        ]

        words = []

        for adjacent_tile in adjacent_tiles:
            if aux.check_valid_tile_coord(adjacent_tile):
                if adjacent_tile in game_board.word_tile_coords_set:
                    line, column = adjacent_tile
                    words.append(game_board.tiles[line][column][const.WORD])

        word_group = ",".join(sorted(words))
        print(f"\nWord group is {word_group}")
        if word_group not in wg_to_tiles.keys():
            wg_to_tiles[word_group] = []
        wg_to_tiles[word_group].append(pending_tile)
        print(f"\nMapping state is {wg_to_tiles}")

    #Sorting (just to ease debugging)
    for key in wg_to_tiles.keys():
        wg_to_tiles[key] = sorted(wg_to_tiles[key], key=lambda tup: (tup[0],tup[1])  )
    print(f"\nFinal mapping state is {wg_to_tiles}")
    return wg_to_tiles

WORD_MOVES_1 = {
    "Sandwich": [1, 5],
    "Ham": [1,6],
    "Breakfast": [2,6],
    "Bacon": [1,7],
    "Sea": [2,3],
    "Sand": [3,2],
    "Silicon": [4,2],
    "Carbon": [5,2],
    "Graphite": [6,2],
    "Grey": [5,3],
    "Graphene": [6,1],
    "Pencil": [6,3],
    "Tangerine": [3,6]
}