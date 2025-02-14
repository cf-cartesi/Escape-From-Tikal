import core_engine.const as const

#Game configurations
INITIAL_WATER_SUPPLY = 7
INITIAL_CURSES_COUNT = 0
INITIAL_AMULET_COUNT = 0

#Structure that maps the limits of the lines and columns of the hexagonal-tiled hexagonal map
#Each side of the map is 4 hexagonal tiles wide
MAP_BOUNDARIES = { 
    1: {
        const.BEGINNING: 4,
        const.END: 7
    },
    2: {
        const.BEGINNING: 3,
        const.END: 7
    },
    3: {
        const.BEGINNING: 2,
        const.END: 7
    },
    4: {
        const.BEGINNING: 1,
        const.END: 7
    },
    5: {
        const.BEGINNING: 1,
        const.END: 6
    },
    6: {
        const.BEGINNING: 1,
        const.END: 5
    },
    7: {
        const.BEGINNING: 1,
        const.END: 4
    }
}

LLM_PROMPT_TEMPLATE_TEXT = """
I am going to provide you with a numbered list of word sets and with an 
isolated word and I need you to tell me the number of the word set that 
is more related to the given isolated word.
Only consider the meaning of the word. Do not accept multiple words, 
ignore radicals and suffix correlations, words that are not present 
on the english dictionary, in these cases answer 0.
Begin your answer with the isolated number followed by a period.
After the period you can add your reasoning for choosing that option.
The word is {given_word} and the word sets are:
{word_sets}
"""

LLM_TO_USE = const.MOCKED