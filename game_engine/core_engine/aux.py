import re
from logging import getLogger

from .const import BEGINNING, DEFEAT, END, INDEX, REASONING, TYPE, VICTORY,WORD,TRAP_EMOJI, EXIT_EMOJI,CURSE_EMOJI,EMPTY_EMOJI,WATER_EMOJI,AMULET_EMOJI,NOTHING_EMOJI,TREASURE_EMOJI,EMPTY,TRAP,WATER,AMULET,TREASURE,EXIT,CURSE
from .confs import INITIAL_WATER_SUPPLY, LLM_PROMPT_TEMPLATE_TEXT, MAP_BOUNDARIES

LOGGER = getLogger(__name__)

TYPE = TYPE
WORD = WORD

TRAP_EMOJI = TRAP_EMOJI
WATER_EMOJI = WATER_EMOJI
CURSE_EMOJI = CURSE_EMOJI
AMULET_EMOJI = AMULET_EMOJI
EXIT_EMOJI = EXIT_EMOJI
TREASURE_EMOJI = TREASURE_EMOJI
NOTHING_EMOJI = NOTHING_EMOJI
EMPTY_EMOJI = EMPTY_EMOJI

MOCKED_MAP_SETUP_WORDS = {
    1: {
        4: "Salt"
    },
    2: {
        4: "Fish",
        5: "Bread"
    }
}

MOCKED_LLM_RESPONSE_DICT = {
    "Sandwich": 2,
    "Ham": 5,
    "Breakfast": 5,
    "Bacon": 4,
    "Sea": 3,
    "Sand": 5,
    "Silicon": 3,
    "Carbon": 3,
    "Graphite": 1,
    "Grey": 5,
    "Graphene": 6,
    "Pencil": 10,
    "Tangerine": 11
}

MOCKED_WORD_MOVES = {
    "Sandwich": (1, 5),
    "Ham": (1,6),
    "Breakfast": (2,6),
    "Bacon": (1,7),
    "Sea": (2,3),
    "Sand": (3,2),
    "Silicon": (4,2),
    "Carbon": (5,2),
    "Graphite": (6,2),
    "Grey": (5,3),
    "Graphene": (6,1),
    "Pencil": (6,3),
    "Tangerine": (3,6)
}

#Prints tiles map on terminal
def print_gameboard(gameboard):
    #print(gameboard)
    print_layout = {}
    for line in range (1,14):
        print_layout[line] = {}
        for column in range (1,14):
            print_layout[line][column] = NOTHING_EMOJI

    word_index = []
    for line in gameboard.keys():
        for column in gameboard[line].keys():
            tile_content = gameboard[line][column]
            new_symbol = NOTHING_EMOJI
            if tile_content[TYPE] == WORD:
                new_symbol = gameboard[line][column][WORD]
                #Checking if above 2 characters lenght, if so, changing content for an index
                if len(new_symbol) > 2:
                    next_index = len(word_index)
                    word_index.append(f"{new_symbol}")
                    new_symbol = f"{next_index}"
                #Checking if equal to one, adding padding in case it is to match emoji visual lenght
                if len(new_symbol) == 1:
                    new_symbol = f".{new_symbol}"
            elif tile_content[TYPE] == EMPTY:
                new_symbol = EMPTY_EMOJI
            elif tile_content[TYPE] == WATER:
                new_symbol = WATER_EMOJI
            elif tile_content[TYPE] == TRAP:
                new_symbol = TRAP_EMOJI
            elif tile_content[TYPE] == CURSE:
                new_symbol = CURSE_EMOJI
            elif tile_content[TYPE] == AMULET:
                new_symbol = AMULET_EMOJI
            elif tile_content[TYPE] == EXIT:
                new_symbol = EXIT_EMOJI
            elif tile_content[TYPE] == TREASURE:
                new_symbol = TREASURE_EMOJI

            x = 2*line + column - 5
            y = 2*column - 1
            print_layout[x][y] = new_symbol

    map_str = ""
    for line in print_layout.keys():
        map_str += "\n"
        for column in print_layout[line].keys():
            map_str += print_layout[line][column]

    print(map_str)
    #Printing word index
    word_index_str = ""
    for idx, word in enumerate(word_index):
        word_index_str += f"{idx} - {word}"
        if ((idx > 0) and (idx % 4 == 0)):
            word_index_str += "\n"
        else:
            word_index_str += " "
    print("Word index:\n" + word_index_str)
    return (map_str)

#Print the statistics of the gameboard
def print_gameboard_stats(gameboard):

    status_str = "\nCurrent board conditions:\n\n"
    status_str += f"Current {WATER_EMOJI}: {gameboard.water_supply}\n"
    status_str += f"Max {WATER_EMOJI}: {gameboard.max_water_supply}\n"
    status_str += f"Current {CURSE_EMOJI}: {gameboard.curse_count}\n"
    status_str += f"Current {AMULET_EMOJI}: {gameboard.amulet_count}\n"
    status_str += f"Max {AMULET_EMOJI}: {gameboard.max_amulet_count}\n"
    status_str += f"Current {TREASURE_EMOJI}: {gameboard.treasure_count}\n"
    status_str += f"Move count: {gameboard.move_count}\n"
    status_str += f"Last move type: {gameboard.last_visited_tile_type}\n"
    status_str += f"Last move tile: {gameboard.last_visited_tile}\n"
    status_str += f"Last move reasoning: {gameboard.last_move_reasoning}\n"
    status_str += f"Game status: {gameboard.game_status}\n"
    status_str += f"Score: {gameboard.score}\n"

    if gameboard.game_status == DEFEAT:
        status_str += f"Defeat reason: {gameboard.defeat_reason}"

    print(status_str + "\n")

#Checks if provided tile coordinates are within the map boundaries
def check_valid_tile_coord(tile_coord):
    line, column = tile_coord

    if line in MAP_BOUNDARIES.keys():
        if ((column >= MAP_BOUNDARIES[line][BEGINNING]) and (column <= MAP_BOUNDARIES[line][END])):
            return True
    return False


def calculate_score(game_board):
    # score = 3000 + victory*1000 + treasures*500 - trap*100 - curse*300 + amulets*300 - moves*30
    score = 3000

    if (game_board.game_status == VICTORY):
        score += 2000
    score += 500 * game_board.treasure_count

    traps = INITIAL_WATER_SUPPLY - game_board.max_water_supply
    score -= 100 * traps

    score -= 300 * game_board.curse_count

    score += 300 * game_board.amulet_count

    score -= 30 * game_board.move_count

    return score

#Checks if the new provided word violates the previous words similarity rule
def check_word_similarity(new_word, previous_words):
    #TODO: check if new word is too similar to previous words, thus violating the rules of the game
    return check_duplicate_word(new_word, previous_words)

def check_duplicate_word(new_word, previous_words):
    #Getting all valid tiles for next move
    return new_word in previous_words

#Returns the word group index closest to the given word
def query_ai_for_closest_word_group(word, word_groups_tile_mapping, handler=None):

    groups_list_str = ""
    #Creating a list with the word groups
    for key in word_groups_tile_mapping.keys():
        groups_list_str += f"\n{word_groups_tile_mapping[key][INDEX]} - {key}"
    LOGGER.debug(groups_list_str)

    #Formatting prompt for the LLM
    llm_prompt = LLM_PROMPT_TEMPLATE_TEXT.format(given_word=word, word_sets=groups_list_str)
    LOGGER.debug(llm_prompt)

    #Calling the LLM
    llm_response_str = query_llm(llm_prompt, handler)

    #Splitting the selection and the reasoning
    llm_response_match = re.match(r'[^\d]*(\d+)\.?([\s\S]*)',llm_response_str)
    if llm_response_match is None or len(llm_response_match.group(1)) == 0:
        raise RuntimeError(f"Couldn't extract index from LLM response\nPrompt:\n{llm_prompt}\nResponse:\n{llm_response_str}")

    chosen_group_index = llm_response_match.group(1)
    reasoning = llm_response_match.group(2).strip()

    try:
        #Convert to int
        chosen_group_index = int(chosen_group_index)
    except Exception:
        raise RuntimeError(f"Couldn't extract index from LLM response\nPrompt:\n{llm_prompt}\nResponse:\n{llm_response_str}")

    LOGGER.debug(f"Chosen group was number {chosen_group_index}.\nReasoning:\n{reasoning}")
    return {INDEX: chosen_group_index, REASONING: reasoning}

def query_llm(llm_prompt, handler=None):

    #The handler is initialized with the mocked one but might be changed to a new one
    if handler:
        llm_handler=handler

    llm_response = llm_handler(llm_prompt)

    return llm_response

def mocked_llm(llm_prompt):

    word = llm_prompt.split("The word is ")[1].split(" and the word sets")[0]
    word_sets = llm_prompt.split("and the word sets are:")[1]
    LOGGER.debug(f"Mocked llm given word is {word}")
    LOGGER.debug(f"Provided word sets are:\n{word_sets}")

    index = 1
    if word in MOCKED_LLM_RESPONSE_DICT.keys():
        index = MOCKED_LLM_RESPONSE_DICT[word]

    llm_response = f"{index}. I like turtles"
    return llm_response

#Initializing the llm handler with the mocked one
llm_handler = mocked_llm
