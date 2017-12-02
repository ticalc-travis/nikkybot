# Markov chain nick configuration
#
# personalities = {
#       'alias': 'primary_persona_name',
#       ...
#       'alias': None,   # 'alias' is the primary persona name
# }
#
# personality_regexes = {
#     'Personality name': 'Nick regexp'
#     ...
# }

personality_regexes = {
    'thegeekyscientist': 'thegeekyscientist',
    'hooloovoo': 'hooloovoo',
    'botboy3000': 'botboy3000',
    'mateoc': 'mateoc',
    'calebj': 'caleb_j',
    'thelastmillennial': 'thelastmillennial',
    'theprogrammingcube': 'theprogrammingcube',
    'oldmud0': 'oldmud0',
    'little': 'little',
    'jacobkuschel': 'jacob_kuschel',
    'iphoenix': '_iphoenix_',
    'michael23b': 'michaelb|michael2_3b',
    'pieman': 'pieman',
    'battlesquid': 'squid|battlesquid',
    'calcmeister': 'cmeister|calcmeister',
    'nik': 'chessy|nik$',
    'pt': 'p_t|pt_',
    'seegreatness': 'seegreatness',
    'avgn': 'avgn',
    'eightx84': 'eightx84|someone26',
    'solarsoftware': 'solarsoftware',
    'richardnixon': 'richardnixon',
    'jonbush': 'jonbush',
    'ivoah': 'ivoah',
    'kinfinity': 'kinfinity|kinginfinity',
    'eeems': 'eeems',
    'tari': 'tari',
    'geekboy': 'geekboy|geek$',
    'ephraimb': 'ephraim|ephraim b|harryp|lazygeek',
    'redstone': 'redstone|asian|imbanned|redstonepizza',
    'sircmpwn': 'sircmpwn',
    'ashbad': 'ashbad|obongo|aalewis',
    'jonimus': 'jonimus|thestorm|thestorm|jonimusprime',
    'joeyoung': 'jy$|joeyoung|mtgrss111|joeyoung',
    'comic': 'comic|comicidiot',
    'juju': 'juju',
    'debrouxl': 'debrouxl|ldebrouxl|lionel debroux',
    'bb010g': 'bb010g',
    'cvsoft': 'cv|notipa|cvsoft',
    'calebh': 'calebh|parse34|cheleron|calebhansberry',
    'netham45': 'netham45|netbot45|ham\\',
    'kevino': '.*?kevin_o|dj.?omni|dj.o|djowalrii|`-`$|celtic3|xlibman|nom$|ragol666',
    'brandonw': 'brandonw',
    'tev': 'tev|travis|travis e',
    'merth': 'merth|merthsoft|shaun',
    'randomist': 'randomist|korinidos|.*arch|metalrand|randeimos|dama|dam\\|damvista|devoidofw|psychodro',
    'sirlewk': 'sir_lewk|sirlewk',
    'chronomex': 'chronomex|chronome1|.*?slythe|xmc|cmx|exmic',
    'michaelv': 'michael_v|michaelv',
    'ej': 'e-j|e-jl|el-j',
    'cricketb': 'cricket_b|cricketb|chirp_b|truepika',
    'glk': 'glk',
    'kerm': 'kerm|kermmartian',
    'nikky': '((nikky|allyn)(?!(?:bot|test))|allynfolksjr)',
}

personality_config = {
    'avgn': {'order': 3},
    'nik': {'order': 3},
    'iphoenix': {'order': 3},
}

personalities = {
    # Aliases...:
    'nikkybot': 'nikky',
    'exmic': 'chronomex',
    'cmx': 'chronomex',
    'xmc': 'chronomex',
    'duncans': 'chronomex',
    'comicidiot': 'comic',
    'comicsans': 'comic',
    'cvsoftd': 'cvsoft',
    'cvsoftl': 'cvsoft',
    'jonimusp': 'jonimus',
    'thestorm': 'jonimus',
    'djo': 'kevino',
    'djomni': 'kevino',
    'djomnimaga': 'kevino',
    'xlibman': 'kevino',
    'kermm': 'kerm',
    'kermmartian': 'kerm',
    'merthsoft': 'merth',
    'shaun': 'merth',
    'netham': 'netham45',
    'ephraim': 'ephraimb',
    'kinginfinity': 'kinfinity',
    'nixon': 'richardnixon',
    'squid': 'battlesquid',
    'chessy': 'nik',
    'kermphd': 'kerm',
    'mateoconlechuga': 'mateoc',
}

# Fill in primary personas...
for p in personality_regexes:
    personalities[p] = None

def get_personality_list_text():
    """Return a human-readable string of available personalities, or a
    location to find them
    """
    return 'Personality list: https://github.com/ticalc-travis/nikkybot/wiki/Personality-list'

def get_personality_list():
    """Return a sequence of available personality names"""
    return personality_regexes.keys()
