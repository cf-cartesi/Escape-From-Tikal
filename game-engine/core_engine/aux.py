import core_engine.const as const
import core_engine.confs as confs

TYPE = const.TYPE
WORD = const.WORD

TRAP_EMOJI = const.TRAP_EMOJI
WATER_EMOJI = const.WATER_EMOJI
CURSE_EMOJI = const.CURSE_EMOJI
AMULET_EMOJI = const.AMULET_EMOJI
EXIT_EMOJI = const.EXIT_EMOJI
TREASURE_EMOJI = const.TREASURE_EMOJI
NOTHING_EMOJI = const.NOTHING_EMOJI
EMPTY_EMOJI = const.EMPTY_EMOJI

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
            elif tile_content[TYPE] == const.EMPTY:
                new_symbol = EMPTY_EMOJI
            elif tile_content[TYPE] == const.WATER:
                new_symbol = WATER_EMOJI
            elif tile_content[TYPE] == const.TRAP:
                new_symbol = TRAP_EMOJI
            elif tile_content[TYPE] == const.CURSE:
                new_symbol = CURSE_EMOJI
            elif tile_content[TYPE] == const.AMULET:
                new_symbol = AMULET_EMOJI
            elif tile_content[TYPE] == const.EXIT:
                new_symbol = EXIT_EMOJI
            elif tile_content[TYPE] == const.TREASURE:
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

#Checks if provided tile coordinates are within the map boundaries
def check_valid_tile_coord(tile_coord):
    line, column = tile_coord

    if line in confs.MAP_BOUNDARIES.keys():
        if ((column >= confs.MAP_BOUNDARIES[line][const.BEGINNING]) and (column <= confs.MAP_BOUNDARIES[line][const.END])):
            return True
    return False

#Checks if the new provided word violates the previous words similarity rule
def check_word_similarity(new_word, previous_words):
    #TODO: check if new word is too similar to previous words, thus violating the rules of the game
    return False