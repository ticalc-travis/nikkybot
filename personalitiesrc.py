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
    'kg583': r'kg583',
    'lifeemu': r'lifeemu',
    'nato': r'nato',
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
    'iambian': r'iambian',
    'logical': r'logical$|logicaljoe',
    'commandblockguy': r'commandblockguy|commandz|cmdtwo',
    'barf': r'barf',
    'lax18': r'lax18',
    'adriweb': r'adriweb',
    'mateoc': r'mateoc',
    'thelastmillennial': r'thelastmillennial',
    'iphoenix': r'_iphoenix_|iphoenix',
    'michael23b': r'michaelb|michael2_3b',
    'pieman': r'pieman',
    'eeems': r'eeems',
    'tari': r'tari',
    'ephraimb': r'ephraim|ephraim b|harryp|lazygeek',
    'comic': r'comic|comicidiot',
    'cvsoft': r'cv|notipa|cvsoft',
    'calebh': r'calebh|parse34|cheleron|calebhansberry',
    'netham45': r'netham45|netbot45|ham\\',
    'kevino': r'.*?kevin_o|dj.?omni|dj.o|djowalrii|`-`$|celtic3|xlibman|nom$|ragol666',
    'brandonw': r'brandonw',
    'tev': r'tev|travis|travis e',
    'merth': r'merth|merthsoft|shaun',
    'chronomex': r'chronomex|chronome1|.*?slythe|xmc|cmx|exmic|astrid|astrinaut',
    'ej': r'e-j|e-jl|el-j',
    'glk': r'glk',
    'kerm': r'kerm(?!ut2ks)|kermmartian',
    'nikky': r'((nikky|allyn)(?!(?:bot|test))|allynfolksjr)',
}

personality_config = {
    'iphoenix': {'order': 3},
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
    'kermphd': 'kerm',
    'mateoconlechuga': 'mateoc',
    'tlm': 'thelastmillennial',
    'commandz': 'commandblockguy',
    'mateo': 'mateoc',
    'beckadam': 'beck',
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
