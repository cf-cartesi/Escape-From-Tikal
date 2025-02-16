import jsonpickle
import pprint
import pytest
import core_engine.tikal_core as tkl_core
import core_engine.const as const
import core_engine.confs as confs
from core_engine.aux import print_gameboard, print_gameboard_stats
from copy import deepcopy

pp = pprint.PrettyPrinter(indent=4)

TYPE = const.TYPE
WORD = const.WORD
WORD_LIST = const.WORD_LIST
SETUP_WORDS = const.SETUP_WORDS
MAP = const.MAP


TRAP_EMOJI = "\N{MOUSE TRAP}"
WATER_EMOJI = "\N{DROPLET}"
CURSE_EMOJI = "\N{SKULL}"
AMULET_EMOJI = "\N{GEM STONE}"
EXIT_EMOJI = "\N{DOOR}"
TREASURE_EMOJI = "\N{COIN}"
NOTHING_EMOJI = "\N{MEDIUM BLACK CIRCLE}"
EMPTY_EMOJI = "\N{MEDIUM WHITE CIRCLE}"

SETUP_WORDS_MAP_1 = { 
    1: {
        4: "Salt"
    },
    2: {
        4: "Fish",
        5: "Bread"
    }
}

TEST_WORD_LIST_1 = [
    "Sandwich",
    "Ham",
    "Breakfast",
    "Bacon",
    "Sea",
    "Sand",
    "Silicon",
    "Carbon",
    "Graphite",
    "Grey",
    "Graphene",
    "Pencil",
    "Tangerine"
]

EMPTY_MAP_TEXT = """
⚫⚫⚫⚫⚫⚫⚪⚫⚫⚫⚫⚫⚫
⚫⚫⚫⚫⚪⚫⚫⚫⚪⚫⚫⚫⚫
⚫⚫⚪⚫⚫⚫⚪⚫⚫⚫⚪⚫⚫
⚪⚫⚫⚫⚪⚫⚫⚫⚪⚫⚫⚫⚪
⚫⚫⚪⚫⚫⚫⚪⚫⚫⚫⚪⚫⚫
⚪⚫⚫⚫⚪⚫⚫⚫⚪⚫⚫⚫⚪
⚫⚫⚪⚫⚫⚫⚪⚫⚫⚫⚪⚫⚫
⚪⚫⚫⚫⚪⚫⚫⚫⚪⚫⚫⚫⚪
⚫⚫⚪⚫⚫⚫⚪⚫⚫⚫⚪⚫⚫
⚪⚫⚫⚫⚪⚫⚫⚫⚪⚫⚫⚫⚪
⚫⚫⚪⚫⚫⚫⚪⚫⚫⚫⚪⚫⚫
⚫⚫⚫⚫⚪⚫⚫⚫⚪⚫⚫⚫⚫
⚫⚫⚫⚫⚫⚫⚪⚫⚫⚫⚫⚫⚫
"""

TEST_MAP_1_TEXT = """
⚫⚫⚫⚫⚫⚫.0⚫⚫⚫⚫⚫⚫
⚫⚫⚫⚫⚪⚫⚫⚫⚪⚫⚫⚫⚫
⚫⚫💧⚫⚫⚫.1⚫⚫⚫🪙⚫⚫
⚪⚫⚫⚫🪤⚫⚫⚫.2⚫⚫⚫🪤
⚫⚫⚪⚫⚫⚫⚪⚫⚫⚫⚪⚫⚫
⚪⚫⚫⚫⚪⚫⚫⚫⚪⚫⚫⚫⚪
⚫⚫💀⚫⚫⚫💀⚫⚫⚫🚪⚫⚫
🪙⚫⚫⚫🪤⚫⚫⚫🪤⚫⚫⚫⚪
⚫⚫💧⚫⚫⚫⚪⚫⚫⚫🪙⚫⚫
💧⚫⚫⚫💎⚫⚫⚫⚪⚫⚫⚫⚪
⚫⚫⚪⚫⚫⚫💀⚫⚫⚫⚪⚫⚫
⚫⚫⚫⚫⚪⚫⚫⚫⚪⚫⚫⚫⚫
⚫⚫⚫⚫⚫⚫⚪⚫⚫⚫⚫⚫⚫
"""

@pytest.fixture
def test_map():
    return confs.MAP_1

@pytest.fixture
def test_game_state():
    game_map = tkl_core.GameMap()
    game_board = tkl_core.GameBoard()
    game_board.load_initial_words(SETUP_WORDS_MAP_1)
    game_board.load_parameter_based_on_map(game_map)
    game_state = tkl_core.GameState(game_map=game_map, game_board=game_board, words=TEST_WORD_LIST_1, new_game=False)
    return game_state

def test_create_gameboard(test_map):

    empty_gameboard = tkl_core.GameBoard()

    output_gameboard = print_gameboard(empty_gameboard.tiles)

    assert(output_gameboard.strip() == EMPTY_MAP_TEXT.strip())
    print("\n\n\n")

    output_gameboard = print_gameboard(test_map)

    assert(output_gameboard.strip() == TEST_MAP_1_TEXT.strip())

def test_batch_match(test_game_state):

    #Printing initial state
    print("\n\nStarting batch match test\n\nMap:\n")
    print_gameboard(test_game_state.game_map.tiles)
    print("\nBoard:\n")
    print_gameboard(test_game_state.game_board.tiles)
    print_gameboard_stats(test_game_state.game_board)
    print("\n\nSerialized game state:\n\n")
    game_state_copy = deepcopy(test_game_state)
    del game_state_copy.game_board.words_on_board
    del game_state_copy.game_board.word_tile_coords_set
    json_game_state_copy = jsonpickle.encode(game_state_copy, indent=4)
    print(json_game_state_copy)
    print("\n\nExecuting game\n\n")

    #Create game executor and load map and board
    game_executor = tkl_core.GameExecutor(test_game_state.game_board, test_game_state.game_map)

    #Execute game
    gameboard_output = game_executor.execute_game(test_game_state.words)

    #Building output game state
    output_game_state = deepcopy(test_game_state)
    output_game_state.game_board = deepcopy(gameboard_output)
    del output_game_state.game_board.words_on_board
    del output_game_state.game_board.word_tile_coords_set

    #Serializing
    json_output_game_state = jsonpickle.encode(output_game_state, indent=4)
    print("\n\nFinal game state JSON\n\n")
    print(json_output_game_state)
    print("\n\nFinal game board\n\n")
    print_gameboard(gameboard_output.tiles)
    print_gameboard_stats(gameboard_output)

def test_execution_multiple_steps(test_game_state):
    #Load initial state
    current_state = test_game_state

    #Storing words copy for splitting execution
    all_words = deepcopy(current_state.words)
    next_word = all_words.pop(0)
    current_state.words = []
    current_state.words.append(next_word)

    #Remove indexes
    del current_state.game_board.words_on_board
    del current_state.game_board.word_tile_coords_set

    #Serialize and then deserealize and load 
    serialized_current_state = jsonpickle.encode(current_state, indent=4)
    print("\n\nInitial state JSON\n\n")
    print(serialized_current_state)

    iterations = len(all_words) + 1
    for i in range(0, iterations):
        deserialized_state = jsonpickle.decode(serialized_current_state)
        current_state = tkl_core.GameState(game_map=deserialized_state.game_map, 
            game_board=deserialized_state.game_board, words=deserialized_state.words,
            game_id=deserialized_state.game_id, new_game=False)

        #Create game executor and load map and board
        game_executor = tkl_core.GameExecutor(current_state.game_board, current_state.game_map)

        #Execute game
        gameboard_output = game_executor.execute_game(current_state.words)
    
        #Remove indexes
        del gameboard_output.words_on_board
        del gameboard_output.word_tile_coords_set
        
        current_state.game_board = gameboard_output

        serialized_output_state = jsonpickle.encode(current_state, indent=4)
        print("\n\nOutput state JSON\n\n")
        print(serialized_output_state)

        #Prepare next state
        if (len(all_words) > 0):
            next_word = all_words.pop(0)
            current_state.words = []
            current_state.words.append(next_word)
            serialized_current_state = jsonpickle.encode(current_state, indent=4)
            print("\n\nNext state JSON\n\n")
            print(serialized_current_state)
        else:
            break

