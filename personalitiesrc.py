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
    'epsilon5': r'epsilon5',
    'wavejumper3': r'wavejumper3',
    'clevor': r'clevor',
    'tinyhacker': r'tiny_hacker',
    'timmy': r'timmyturner',
    'caesar': r'caesar(?![0-9][0-9])',
    'fghsgh': r'fghsgh',
    'womp': r'mr womp womp',
    'beck': r'beck$|beckadam',
    'roccolox': r'roccolox',
    'nomkid': r'nomkid',
    'rogerwilco': r'rogerwilc',
    'jeffitus': r'jeffitus',
    'kryptonic': r'kryptonic',
    'iambian': r'iambian',
    'logical': r'logical$|logicaljoe',
    'commandblockguy': r'commandblockguy|commandz|cmdtwo',
    'jwinslow23': r'jwinslow',
    'barf': r'barf',
    'lax18': r'lax18',
    'sm84ce': r'sm84ce',
    'adriweb': r'adriweb',
    'jcgter777': r'jcgter',
    'thegeekyscientist': r'thegeekyscientist',
    'hooloovoo': r'hooloovoo',
    'botboy3000': r'botboy3000',
    'mateoc': r'mateoc',
    'calebj': r'caleb_j',
    'thelastmillennial': r'thelastmillennial',
    'theprogrammingcube': r'theprogrammingcube',
    'oldmud0': r'oldmud0',
    'little': r'little',
    'jacobkuschel': r'jacob_kuschel',
    'iphoenix': r'_iphoenix_|iphoenix',
    'michael23b': r'michaelb|michael2_3b',
    'pieman': r'pieman',
    'battlesquid': r'squid|battlesquid',
    'calcmeister': r'cmeister|calcmeister',
    'nik': r'chessy|nik$|thenik$',
    'pt': r'p_t|pt_',
    'seegreatness': r'seegreatness',
    'eightx84': r'eightx84|someone26',
    'solarsoftware': r'solarsoftware',
    'richardnixon': r'richardnixon',
    'jonbush': r'jonbush',
    'ivoah': r'ivoah',
    'kinfinity': r'kinfinity|kinginfinity',
    'eeems': r'eeems',
    'tari': r'tari',
    'geekboy': r'geekboy|geek$',
    'ephraimb': r'ephraim|ephraim b|harryp|lazygeek',
    'redstone': r'redstone|asian|imbanned|redstonepizza',
    'sircmpwn': r'sircmpwn',
    'ashbad': r'ashbad|obongo|aalewis',
    'jonimus': r'jonimus|thestorm|thestorm|jonimusprime',
    'joeyoung': r'jy$|joeyoung|mtgrss111|joeyoung',
    'comic': r'comic|comicidiot',
    'juju': r'juju',
    'debrouxl': r'debrouxl|ldebrouxl|lionel debroux',
    'bb010g': r'bb010g',
    'cvsoft': r'cv|notipa|cvsoft',
    'calebh': r'calebh|parse34|cheleron|calebhansberry',
    'netham45': r'netham45|netbot45|ham\\',
    'kevino': r'.*?kevin_o|dj.?omni|dj.o|djowalrii|`-`$|celtic3|xlibman|nom$|ragol666',
    'brandonw': r'brandonw',
    'tev': r'tev|travis|travis e',
    'merth': r'merth|merthsoft|shaun',
    'randomist': r'randomist|korinidos|.*arch|metalrand|randeimos|dama|dam\\|damvista|devoidofw|psychodro',
    'sirlewk': r'sir_lewk|sirlewk',
    'chronomex': r'chronomex|chronome1|.*?slythe|xmc|cmx|exmic|astrid|astrinaut',
    'michaelv': r'michael_v|michaelv',
    'ej': r'e-j|e-jl|el-j',
    'cricketb': r'cricket_b|cricketb|chirp_b|truepika',
    'glk': r'glk',
    'kerm': r'kerm(?!ut2ks)|kermmartian',
    'nikky': r'((nikky|allyn)(?!(?:bot|test))|allynfolksjr)',
}

personality_config = {
    'nik': {'order': 3},
    'iphoenix': {'order': 3},
    'jwinslow23': {'order': 2},
    'logical': {'order': 3},
}

personalities = {
    # Aliases...:
    'nikkybot': 'nikky',
    'astrinaut': 'chronomex',
    'astrid': 'chronomex',
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
    'jcgter': 'jcgter777',
    'jwinslow': 'jwinslow23',
    'jwin': 'jwinslow23',
    'tlm': 'thelastmillennial',
    'rogerwilc': 'rogerwilco',
    'commandz': 'commandblockguy',
    'mateo': 'mateoc',
    'beckadam': 'beck',
    'thenik': 'nik',
    'logicaljoe': 'logical',
    'timmyturner': 'timmy',
    'timmyturner62': 'timmy',
}

# Fill in primary personas...
for p in personality_regexes:
    personalities[p] = None

def get_personality_list_text():
    """Return a human-readable string of available personalities, or a
    location to find them
    """
    return 'Personality list: https://github.com/ticalc-travis/nikkybot/wiki/Personality-list  Talk to tev on EFNet (or PM Travis on Cemetech forum) to request a new personality.'


def get_personality_list():
    """Return a sequence of available personality names"""
    return personality_regexes.keys()
