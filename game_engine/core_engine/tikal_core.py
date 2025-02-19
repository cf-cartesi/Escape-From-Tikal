from logging import getLogger, DEBUG
import random

from .aux import MOCKED_WORD_MOVES, check_word_similarity,print_gameboard_stats, print_gameboard, calculate_score, check_valid_tile_coord, query_ai_for_closest_word_group
from .const import EASY_ID_THRESHOLD, REASONING, INDEX, TYPE, WORD, BEGINNING, END, EMPTY, WATER, AMULET, TRAP, CURSE, TREASURE,EXIT, ONGOING, DEFEAT, VICTORY, TILES
from .confs import EASY_N_INITIAL_OBJECTS, MAP_0, MAP_1, GENESIS_WORDS, MAP_1_INITIAL_WORD_POSITIONS, INITIAL_WATER_SUPPLY, INITIAL_CURSES_COUNT, INITIAL_AMULET_COUNT, MAP_BOUNDARIES, HARD_N_INITIAL_OBJECTS

LOGGER = getLogger(__name__)

class GameMap:

    def __init__(self, tiles_definition=MAP_1, game_id=-1, random_positions=False):
        self.tiles = tiles_definition

        if game_id > -1:
            self.tiles = self.generate_tiles_from_game_id(game_id, random_positions)

    def generate_tiles_from_game_id(self, game_id, random_positions=False):
        # set difficulty (initial object numbers) based on id range
        n_initial_objects = EASY_N_INITIAL_OBJECTS \
            if game_id < EASY_ID_THRESHOLD else HARD_N_INITIAL_OBJECTS

        #Getting 3 random genesis words, deterministically given the game_id
        random.seed(game_id)
        word_list = []

        LOGGER.info(f"Drawing {n_initial_objects[WORD]} words for game id {game_id}")
        while (len(word_list) < n_initial_objects[WORD]):
            word_index = random.randint(0, len(GENESIS_WORDS) -1)
            if (not GENESIS_WORDS[word_index] in word_list):
                word_list.append(GENESIS_WORDS[word_index])
        LOGGER.info(f"Drawn words are {word_list}")

        #Setting  map with random positions
        if random_positions:
            return get_random_tiles(clone_map(MAP_0), word_list, n_initial_objects, random.choice)

        #Setting up tiles with initial configuration
        tiles = clone_map(MAP_1)

        #Placing selected words on initil positions
        for word_position in MAP_1_INITIAL_WORD_POSITIONS:
            line, column = word_position
            tiles[line][column] = {
                TYPE: WORD,
                WORD: word_list.pop()
            }
        return tiles

def clone_map(tiles):
    new_tiles = {}
    for line in tiles.keys():
        new_tiles[line] = {}
        for column in tiles[line].keys():
            new_tiles[line][column] = tiles[line][column]
    return new_tiles

def get_random_tiles(tiles, word_list, n_initial_objects, rnd_choice):
    possible_positions = [(k1,k2) for k1 in tiles for k2 in tiles[k1]]

    # Set words
    words_adjacent_tiles = []
    words_tiles = []
    words_set = 0
    while words_set < n_initial_objects[WORD]:
        word_possible_position = possible_positions \
            if len(words_adjacent_tiles) == 0 else words_adjacent_tiles
        chosen_position = rnd_choice(word_possible_position)
        words_tiles.append(chosen_position)
        possible_positions.remove(chosen_position)
        if chosen_position in words_adjacent_tiles:
            words_adjacent_tiles.remove(chosen_position)
        line, column = chosen_position
        tiles[line][column] = {
            TYPE: WORD,
            WORD: word_list[words_set]
        }
        words_adjacent_tiles.extend(get_adjacent_tiles(line, column))
        words_adjacent_tiles = list(set(words_adjacent_tiles) - set(words_tiles))
        words_set += 1

    # set exits
    exits_set = 0
    while exits_set < n_initial_objects[EXIT]:
        chosen_position = rnd_choice(list(set(possible_positions) - set(words_adjacent_tiles)))
        if chosen_position not in words_adjacent_tiles:
            possible_positions.remove(chosen_position)
            line, column = chosen_position
            tiles[line][column] = {
                TYPE: EXIT
            }
            exits_set += 1

    # set traps
    traps_set = 0
    while traps_set < n_initial_objects[TRAP]:
        chosen_position = rnd_choice(possible_positions)
        possible_positions.remove(chosen_position)
        line, column = chosen_position
        tiles[line][column] = {
            TYPE: TRAP
        }
        traps_set += 1

    # set curses
    curses_set = 0
    while curses_set < n_initial_objects[CURSE]:
        chosen_position = rnd_choice(possible_positions)
        possible_positions.remove(chosen_position)
        line, column = chosen_position
        tiles[line][column] = {
            TYPE: CURSE
        }
        curses_set += 1

    # set treasures
    treasures_set = 0
    while treasures_set < n_initial_objects[TREASURE]:
        chosen_position = rnd_choice(possible_positions)
        possible_positions.remove(chosen_position)
        line, column = chosen_position
        tiles[line][column] = {
            TYPE: TREASURE
        }
        treasures_set += 1

    # set amulets
    amulets_set = 0
    while amulets_set < n_initial_objects[AMULET]:
        chosen_position = rnd_choice(possible_positions)
        possible_positions.remove(chosen_position)
        line, column = chosen_position
        tiles[line][column] = {
            TYPE: AMULET
        }
        amulets_set += 1

    # set water
    water_set = 0
    while water_set < n_initial_objects[WATER]:
        chosen_position = rnd_choice(possible_positions)
        possible_positions.remove(chosen_position)
        line, column = chosen_position
        tiles[line][column] = {
            TYPE: WATER
        }
        water_set += 1

    return tiles

class GameBoard:

    #Constructor to initialize an empty board
    def __init__(self):
        self.tiles = {}
        self.water_supply = INITIAL_WATER_SUPPLY
        self.max_water_supply = INITIAL_WATER_SUPPLY
        self.curse_count = INITIAL_CURSES_COUNT
        self.amulet_count = INITIAL_AMULET_COUNT
        self.max_amulet_count = 0
        self.treasure_count = 0
        self.move_count = 0
        self.last_visited_tile_type = EMPTY
        self.last_visited_tile = (0, 0)
        self.last_move_reasoning = ""
        self.score = 0
        self.defeat_reason = EMPTY
        self.game_status = ONGOING
        self.words_on_board = {}
        self.word_tile_coords_set = set()

        for line in MAP_BOUNDARIES.keys():
            self.tiles[line] = {}

            for column in range(MAP_BOUNDARIES[line][BEGINNING], MAP_BOUNDARIES[line][END] + 1):
                self.tiles[line][column] = {TYPE: EMPTY}

    def load_initial_words(self, setup_words):
        #Validate words are valid and in correct amount
        word_count = 0
        for line in setup_words.keys():
            for column in setup_words[line].keys():
                if word_count >= 3:
                    raise ValueError("Provided more than 3 initial words")

                new_word = setup_words[line][column]
                similar_word = check_word_similarity(new_word, self.words_on_board)
                if similar_word:
                    raise ValueError(f"Provided word ({new_word} is similar to an existing word ({similar_word}))")
                word_count += 1

        for line in setup_words.keys():
            for column in setup_words[line].keys():
                new_word = setup_words[line][column]
                self.tiles[line][column] = {TYPE: WORD, WORD: new_word}
                self.words_on_board[new_word] = (line, column)
                self.word_tile_coords_set.add((line, column))

    def load_parameter_based_on_map(self, game_map):

        for line in game_map.tiles.keys():
            for column in game_map.tiles[line].keys():
                tile_type = game_map.tiles[line][column][TYPE]
                #Increase the total number of amulets available on map
                if tile_type == AMULET:
                    self.max_amulet_count += 1

    def setup_initial_words_based_on_map(self, game_map):

        for line in game_map.tiles.keys():
            for column in game_map.tiles[line].keys():
                tile_type = game_map.tiles[line][column][TYPE]
                #Increase the total number of amulets available on map
                if tile_type == WORD:
                    word = game_map.tiles[line][column][WORD]
                    self.tiles[line][column] = {TYPE: WORD, WORD: word}
                    self.words_on_board[word] = (line, column)
                    self.word_tile_coords_set.add((line, column))

    def rebuild_indexing_data_structures(self):
        #Creating new indexing data structures
        self.words_on_board = {}
        self.word_tile_coords_set = set()

        #Go through board tiles to index data
        for line in self.tiles.keys():
            for column in self.tiles[line].keys():
                tile = self.tiles[line][column]

                if tile[TYPE] == WORD:
                    #Indexing
                    word = self.tiles[line][column][WORD]
                    self.words_on_board[word] = (line, column)
                    self.word_tile_coords_set.add((line, column))

class GameState:

    def __init__(self, game_id=-1, game_map=None, game_board=None, words=None, new_game=True, random_positions=False):
        if new_game:
            #New game
            self.game_board = GameBoard()
            self.game_map = GameMap(game_id=game_id, random_positions=random_positions)
            self.words = []
            self.game_id = game_id

            self.game_board.load_parameter_based_on_map(self.game_map)
            self.game_board.setup_initial_words_based_on_map(self.game_map)
            if LOGGER.isEnabledFor(DEBUG):
                print_gameboard(self.game_map.tiles)
                print_gameboard_stats(self.game_board)

        else:
            #Constructor to load an ongoing game
            self.game_board = game_board
            self.game_map = game_map
            self.words = words
            self.game_id = game_id

            #Fix numeric keys
            self.fix_numeric_keys()
            #Rebuild gameboard indexing structures
            self.game_board.rebuild_indexing_data_structures()


    def fix_numeric_keys(self):

        #Fix game map
        fixed_game_map = {}

        for line in self.game_map.tiles.keys():
            fixed_game_map[int(line)] = {}

            for column in self.game_map.tiles[line].keys():
                fixed_game_map[int(line)][int(column)] = self.game_map.tiles[line][column]

        self.game_map.tiles = fixed_game_map

        #Fix game board tiles

        fixed_tiles = {}
        for line in self.game_board.tiles.keys():
            fixed_tiles[int(line)] = {}

            for column in self.game_board.tiles[line].keys():
                fixed_tiles[int(line)][int(column)] = self.game_board.tiles[line][column]

        self.game_board.tiles = fixed_tiles

class GameExecutor:

    def __init__(self, game_board, game_map):
        self.game_board = game_board
        self.game_map = game_map

    def execute_game(self, words, handler=None):

        for word in words:
            word = word.strip().lower()
            if check_word_similarity(word,self.game_board.words_on_board.keys()):
                raise Exception("Duplicate word")

            #Generate word influence groups and tiles mapping
            word_groups_tile_mapping = generate_word_groups_per_tile(self.game_board)

            #Ask AI to provide the closest related word group index
            wg_index_dict = query_ai_for_closest_word_group(word, word_groups_tile_mapping, handler)

            #Storing movement reasoning
            self.game_board.last_move_reasoning = wg_index_dict[REASONING]

            #Choose tile from tile group associated to chosen word group
            tile = self.choose_tile_from_word_group(word, wg_index_dict[INDEX], word_groups_tile_mapping, handler)

            #Evaluate the move
            self.evaluate_move(tile, word)

            #Print game board state
            LOGGER.debug(f"Game board state after move {self.game_board.move_count}")
            if LOGGER.isEnabledFor(DEBUG):
                print_gameboard(self.game_board.tiles)
                print_gameboard_stats(self.game_board)

            #Check if game ended
            if (self.game_board.game_status != ONGOING):
                #Game ended, no need to evaluate other words
                break

        #Return full state
        return self.game_board

    def choose_tile_from_word_group(self, word, group_index, word_groups_tile_mapping, handler=None):

        tiles_from_word_group = []

        for key in word_groups_tile_mapping.keys():
            if (word_groups_tile_mapping[key][INDEX] == group_index):
                tiles_from_word_group = word_groups_tile_mapping[key][TILES]

        return_tile = tiles_from_word_group[0]

        #Checking if there is more than one tile adjacent to the same words
        if (len(tiles_from_word_group) > 1):

            if not handler:
                return_tile = MOCKED_WORD_MOVES[word]
                LOGGER.debug("Using mocked data")
            else:
                #Creating a deterministic seed based on all the words on the map sorted
                sorted_words_on_board_str = ", ".join(sorted(self.game_board.words_on_board.keys()))
                random.seed(sorted_words_on_board_str)

                #Chosing a random option based on the seed
                rand_index = random.randint(0, len(tiles_from_word_group) - 1)
                return_tile = tiles_from_word_group[rand_index]

        LOGGER.debug(f"Chose tile {return_tile} for {word} from group {tiles_from_word_group}")

        return return_tile

    def evaluate_move(self, tile, word):

        line, column = tile

        #Checking the game board tile is empty
        if self.game_board.tiles[line][column][TYPE] != EMPTY:
            #It's not, there is a bug and something went VERY WRONG
            print_gameboard(self.game_board.tiles)
            raise RuntimeError(f"CRITICAL ERROR! Tried moving to tile {tile} with word {word} but it was already occupied")

        #Recover map tile
        map_tile = self.game_map.tiles[line][column]

        #Write word on GameBoard tile and update indexing structures
        self.game_board.tiles[line][column] = {
            TYPE: WORD,
            WORD: word
        }
        self.game_board.words_on_board[word] = (line, column)
        self.game_board.word_tile_coords_set.add((line, column))

        #Consume water
        self.game_board.water_supply -= 1

        #Increase move count
        self.game_board.move_count += 1

        #Updating last visited tile data
        self.game_board.last_visited_tile_type = map_tile[TYPE]
        self.game_board.last_visited_tile = tile

        #Apply efect of map tile on GameBoard
        if (map_tile[TYPE] == CURSE):
            #It's a curse, increasing curse count and lose if above limit
            self.game_board.curse_count += 1
            if self.game_board.curse_count > self.game_board.max_amulet_count:
                #No way to remove all curses, lost the game
                self.game_board.game_status = DEFEAT
                self.game_board.defeat_reason = CURSE
                self.game_board.score = calculate_score(self.game_board)

        elif (map_tile[TYPE] == WATER):
            #It's a water fountain, refill the water supply
            self.game_board.water_supply = self.game_board.max_water_supply

        elif (map_tile[TYPE] == TREASURE):
            #It's a treasure chest, increase treasure count
            self.game_board.treasure_count += 1

        elif (map_tile[TYPE] == TRAP):
            #It's a trap! (lol, starwars). Decrease max water supply
            self.game_board.max_water_supply -= 1
            if (self.game_board.max_water_supply < 1):
                #No way to move any longer, lost the game
                self.game_board.game_status = DEFEAT
                self.game_board.defeat_reason = TRAP
                self.game_board.score = calculate_score(self.game_board)

        elif (map_tile[TYPE] == AMULET):
            #It's an amulet, increase amulet count
            self.game_board.amulet_count += 1

        elif (map_tile[TYPE] == EXIT):
            #It's the exit, check if not cursed
            if (self.game_board.amulet_count >= self.game_board.curse_count):
                if self.game_board.treasure_count == 0:
                    #Left the maze cursed :( Lost the game
                    self.game_board.game_status = DEFEAT
                    self.game_board.defeat_reason = TREASURE
                    self.game_board.score = calculate_score(self.game_board)
                    return
                #Safe! Won the game
                self.game_board.game_status = VICTORY
                self.game_board.score = calculate_score(self.game_board)
                return
            else:
                #Left the maze cursed :( Lost the game
                self.game_board.game_status = DEFEAT
                self.game_board.defeat_reason = CURSE
                self.game_board.score = calculate_score(self.game_board)
                return

        #Check if there is no more water
        if self.game_board.water_supply <= 0:
            #There isn't, lost the game
            self.game_board.game_status = DEFEAT
            self.game_board.defeat_reason = WATER
            self.game_board.score = calculate_score(self.game_board)

def get_adjacent_tiles(line, column):

    adjacent_tiles = [
        (line - 1, column),     #Tile above
        (line + 1, column),     #Tile bellow
        (line, column - 1),     #Tile top left
        (line + 1, column - 1), #Tile bottom left
        (line - 1, column + 1), #Tile top right
        (line, column + 1),     #Tile bottom right
    ]

    valid_adjacent_tiles = []
    for adjacent_tile in adjacent_tiles:
        if check_valid_tile_coord(adjacent_tile):
            valid_adjacent_tiles.append(adjacent_tile)

    return valid_adjacent_tiles

#Goes through the board and generates all word groups that influence nearby tiles
def generate_word_groups_per_tile(game_board):
    tiles = game_board.tiles
    if LOGGER.isEnabledFor(DEBUG):
        print_gameboard(tiles)

    #Set of tiles to visit
    pending_tiles = set()

    #word groups to tiles mapping
    wg_to_tiles = {}

    #Getting all valid tiles for next move
    for word in sorted(game_board.words_on_board.keys()):
        line, column = game_board.words_on_board[word]

        LOGGER.debug(f"\nTile to analyze next: {line},{column}")

        for adjacent_tile in get_adjacent_tiles(line, column):
            if adjacent_tile not in pending_tiles:
                if adjacent_tile not in game_board.word_tile_coords_set:
                    pending_tiles.add(adjacent_tile)

        LOGGER.debug(f"\nPending tiles to visit: {sorted(pending_tiles, key=lambda tup: (tup[0],tup[1]) )}")

    #Getting all word groups for all tiles
    for pending_tile in pending_tiles:

        LOGGER.debug(f"\nRetrieving word group for tile: {pending_tile}")
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
            if check_valid_tile_coord(adjacent_tile):
                if adjacent_tile in game_board.word_tile_coords_set:
                    line, column = adjacent_tile
                    words.append(game_board.tiles[line][column][WORD])

        #Sorting words so we don't create new groups for different tiles in which the
        # adjacents were visited in a different order
        word_group = ",".join(sorted(words))
        LOGGER.debug(f"\nWord group is {word_group}")

        if word_group not in wg_to_tiles.keys():
            wg_to_tiles[word_group] = []
        wg_to_tiles[word_group].append(pending_tile)
        LOGGER.debug(f"\nMapping state is {wg_to_tiles}")

    #Sorting (just to ease debugging) and adding an index to each word group
    #Index starts on 1 as we ask the LLM to use 0 as an error code for invalid options
    idx = 1
    for key in wg_to_tiles.keys():
        wg_to_tiles[key] = {
            INDEX: idx,
            TILES: sorted(wg_to_tiles[key], key=lambda tup: (tup[0],tup[1])  )
        }
        idx +=1
    LOGGER.debug(f"\nFinal mapping state is {wg_to_tiles}")
    return wg_to_tiles
