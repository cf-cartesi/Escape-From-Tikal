import core_engine.aux as aux
import core_engine.const as const
import core_engine.confs as confs

import random

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
        self.max_amulet_count = 0
        self.treasure_count = 0
        self.move_count = 0
        self.last_visited_tile_type = const.EMPTY
        self.last_visited_tile = (0, 0)
        self.defeat_reason = const.EMPTY
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

    def load_parameter_based_on_map(self, game_map):

        for line in game_map.tiles.keys():
            for column in game_map.tiles[line].keys():
                tile_type = game_map.tiles[line][column][const.TYPE]
                #Increase the total number of amulets available on map
                if tile_type == const.AMULET:
                    self.max_amulet_count += 1

class GameExecutor:

    def __init__(self, game_board, game_map):
        self.game_board = game_board
        self.game_map = game_map

    def execute_game(self, words):
        
        for word in words:
            #Generate word influence groups and tiles mapping
            word_groups_tile_mapping = generate_word_groups_per_tile(self.game_board)

            #Ask AI to provide the closest related word group index
            wg_index_dict = aux.query_ai_for_closest_word_group(word, word_groups_tile_mapping)

            #Choose tile from tile group associated to chosen word group
            tile = self.choose_tile_from_word_group(word, wg_index_dict[const.INDEX], word_groups_tile_mapping)

            #Evaluate the move
            self.evaluate_move(tile, word)

            #Print game board state
            print(f"Game board state after move {self.game_board.move_count}")
            aux.print_gameboard(self.game_board.tiles)
            aux.print_gameboard_stats(self.game_board)

            #Check if game ended
            if (self.game_board.game_status != const.ONGOING):
                #Game ended, no need to evaluate other words
                break

        #Return full state
        return self.game_board

    def choose_tile_from_word_group(self, word, group_index, word_groups_tile_mapping):

        tiles_from_word_group = []

        for key in word_groups_tile_mapping.keys():
            if (word_groups_tile_mapping[key][const.INDEX] == group_index):
                tiles_from_word_group = word_groups_tile_mapping[key][const.TILES]

        print(f"Possible tiles are {tiles_from_word_group}")
        return_tile = tiles_from_word_group[0]

        #Checking if there is more than one tile adjacent to the same words
        if (len(tiles_from_word_group) > 1):

            if confs.LLM_TO_USE == const.MOCKED:
                return_tile = aux.MOCKED_WORD_MOVES[word]
                print("Using mocked data")
            else:
                #Creating a deterministic seed based on all the words on the map sorted
                sorted_words_on_board_str = ", ".join(sorted(self.game_board.words_on_board.keys()))
                random.seed(sorted_words_on_board_str)

                #Chosing a random option based on the seed
                rand_index = random.randint(0, len(tiles_from_word_group) - 1)
                return_tile = tiles_from_word_group[rand_index]

        print(f"Chose tile {return_tile} for {word}")

        return return_tile

    def evaluate_move(self, tile, word):
        
        line, column = tile

        #Checking the game board tile is empty
        if self.game_board.tiles[line][column][const.TYPE] != const.EMPTY:
            #It's not, there is a bug and something went VERY WRONG
            aux.print_gameboard(self.game_board.tiles)
            raise RuntimeError(f"CRITICAL ERROR! Tried moving to tile {tile} with word {word} but it was already occupied")

        #Recover map tile
        map_tile = self.game_map.tiles[line][column]

        #Write word on GameBoard tile and update indexing structures
        self.game_board.tiles[line][column] = {
            const.TYPE: const.WORD,
            const.WORD: word
        }
        self.game_board.words_on_board[word] = (line, column)
        self.game_board.word_tile_coords_set.add((line, column))

        #Consume water
        self.game_board.water_supply -= 1

        #Increase move count
        self.game_board.move_count += 1

        #Updating last visited tile data
        self.game_board.last_visited_tile_type = map_tile[const.TYPE]
        self.game_board.last_visited_tile = tile

        #Apply efect of map tile on GameBoard
        if (map_tile[const.TYPE] == const.CURSE):
            #It's a curse, increasing curse count and lose if above limit
            self.game_board.curse_count += 1
            if self.game_board.curse_count > self.game_board.max_amulet_count:
                #No way to remove all curses, lost the game
                self.game_board.game_status = const.DEFEAT 
                self.game_board.defeat_reason = const.CURSE

        elif (map_tile[const.TYPE] == const.WATER):
            #It's a water fountain, refill the water supply
            self.game_board.water_supply = self.game_board.max_water_supply

        elif (map_tile[const.TYPE] == const.TREASURE):
            #It's a treasure chest, increase treasure count
            self.game_board.treasure_count += 1

        elif (map_tile[const.TYPE] == const.TRAP):
            #It's a trap! (lol, starwars). Decrease max water supply
            self.game_board.max_water_supply -= 1
            if (self.game_board.max_water_supply < 1):
                #No way to move any longer, lost the game
                self.game_board.game_status = const.DEFEAT
                self.game_board.defeat_reason = const.TRAP

        elif (map_tile[const.TYPE] == const.AMULET):
            #It's an amulet, increase amulet count
            self.game_board.amulet_count += 1
        
        elif (map_tile[const.TYPE] == const.EXIT):
            #It's the exit, check if not cursed
            if (self.game_board.amulet_count >= self.game_board.curse_count):
                #Safe! Won the game
                self.game_board.game_status = const.VICTORY
                return
            else:
                #Left the maze cursed :( Lost the game
                self.game_board.game_status = const.DEFEAT
                self.game_board.defeat_reason = const.CURSE
                return

        #Check if there is no more water
        if self.game_board.water_supply <= 0:
            #There isn't, lost the game
            self.game_board.game_status = const.DEFEAT
            self.game_board.defeat_reason = const.WATER

#Goes through the board and generates all word groups that influence nearby tiles
def generate_word_groups_per_tile(game_board):
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

        #Sorting words so we don't create new groups for different tiles in which the
        # adjacents were visited in a different order
        word_group = ",".join(sorted(words))
        print(f"\nWord group is {word_group}")

        if word_group not in wg_to_tiles.keys():
            wg_to_tiles[word_group] = []
        wg_to_tiles[word_group].append(pending_tile)
        print(f"\nMapping state is {wg_to_tiles}")

    #Sorting (just to ease debugging) and adding an index to each word group
    #Index starts on 1 as we ask the LLM to use 0 as an error code for invalid options
    idx = 1
    for key in wg_to_tiles.keys():
        wg_to_tiles[key] = {
            const.INDEX: idx,
            const.TILES: sorted(wg_to_tiles[key], key=lambda tup: (tup[0],tup[1])  )
        }
        idx +=1    
    print(f"\nFinal mapping state is {wg_to_tiles}")
    return wg_to_tiles
