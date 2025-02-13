import pytest
import core_engine.tikal_core as tkl_core
import core_engine.const as const
from core_engine.aux import print_gameboard

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


TEST_MAP_1 = {
    1: {
        4: {
            TYPE: WORD,
            WORD: ".S" 
        },
        5: {
            TYPE: const.EMPTY
        },
        6: {
            TYPE: const.TREASURE
        },
        7: {
            TYPE: const.TRAP
        }
    },
    2: {
        3: {
            TYPE: const.EMPTY
        },
        4: {
            TYPE: WORD,
            WORD: ".F" 
        },
        5: {
            TYPE: WORD,
            WORD: ".B" 
        },
        6: {
            TYPE: const.EMPTY
        },
        7: {
            TYPE: const.EMPTY
        }
    },
    3: {
        2: {
            TYPE: const.WATER
        },
        3: {
            TYPE: const.TRAP
        },
        4: {
            TYPE: const.EMPTY
        },
        5: {
            TYPE: const.EMPTY
        },
        6: {
            TYPE: const.EXIT
        },
        7: {
            TYPE: const.EMPTY
        }
    },
    4: {
        1:{
            TYPE: const.EMPTY
        },
        2: {
            TYPE: const.EMPTY
        },
        3: {
            TYPE: const.EMPTY
        },
        4: {
            TYPE: const.CURSE
        },
        5: {
            TYPE: const.TRAP
        },
        6: {
            TYPE: const.TREASURE
        },
        7: {
            TYPE: const.EMPTY
        }
    },
    5: {
        1:{
            TYPE: const.EMPTY
        },
        2: {
            TYPE: const.CURSE
        },
        3: {
            TYPE: const.TRAP
        },
        4: {
            TYPE: const.EMPTY
        },
        5: {
            TYPE: const.EMPTY
        },
        6: {
            TYPE: const.EMPTY
        }
    },
    6: {
        1:{
            TYPE: const.TREASURE
        },
        2: {
            TYPE: const.WATER
        },
        3: {
            TYPE: const.AMULET
        },
        4: {
            TYPE: const.CURSE
        },
        5: {
            TYPE: const.EMPTY
        }        
    },
    7: {
        1:{
            TYPE: const.WATER
        },
        2: {
            TYPE: const.EMPTY
        },
        3: {
            TYPE: const.EMPTY
        },
        4: {
            TYPE: const.EMPTY
        }
    }
}

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

MATCH_LOG_1 = {
    MAP : TEST_MAP_1,
    SETUP_WORDS : SETUP_WORDS_MAP_1,
    WORD_LIST : TEST_WORD_LIST_1
}

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
⚫⚫⚫⚫⚫⚫.S⚫⚫⚫⚫⚫⚫
⚫⚫⚫⚫⚪⚫⚫⚫⚪⚫⚫⚫⚫
⚫⚫💧⚫⚫⚫.F⚫⚫⚫🪙⚫⚫
⚪⚫⚫⚫🪤⚫⚫⚫.B⚫⚫⚫🪤
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
    return TEST_MAP_1

@pytest.fixture
def match_log():
    return MATCH_LOG_1

def test_create_gameboard(test_map):

    empty_gameboard = tkl_core.GameBoard()

    output_gameboard = print_gameboard(empty_gameboard.tiles)

    assert(output_gameboard.strip() == EMPTY_MAP_TEXT.strip())
    print("\n\n\n")

    output_gameboard = print_gameboard(test_map)

    assert(output_gameboard.strip() == TEST_MAP_1_TEXT.strip())

def test_batch_match(match_log):

    #Create gamemap
    gamemap = tkl_core.GameMap(match_log[MAP])
    print_gameboard(gamemap.tiles)

    #Create gameboard
    gameboard = tkl_core.GameBoard()

    #Load initial word tiles
    gameboard.load_initial_words(match_log[SETUP_WORDS])
    print_gameboard(gameboard.tiles)

    #Create game executor and load map and board
    game_executor = tkl_core.GameExecutor(gameboard, gamemap)

    #Execute game
    gameboard_output = game_executor.execute_game(match_log[WORD_LIST])
    print_gameboard(gameboard_output.tiles) 

    