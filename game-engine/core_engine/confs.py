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