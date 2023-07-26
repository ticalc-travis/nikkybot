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
    'adriweb': r'adriweb',
    'beck': r'beck$|beckadam',
    'brandonw': r'brandonw',
    'caesar': r'caesar(?![0-9][0-9])',
    'calebh': r'calebh|parse34|cheleron|calebhansberry',
    'chronomex': r'chronomex|chronome1|.*?slythe|xmc|cmx|exmic|astrid|astrinaut',
    'clevor': r'clevor',
    'comic': r'comic|comicidiot',
    'commandblockguy': r'commandblockguy|commandz|cmdtwo',
    'cvsoft': r'cv|notipa|cvsoft',
    'eeems': r'eeems',
    'ej': r'e-j|e-jl|el-j',
    'ephraimb': r'ephraim|ephraim b|harryp|lazygeek',
    'epsilon5': r'epsilon5',
    'fghsgh': r'fghsgh',
    'glk': r'glk',
    'iambian': r'iambian',
    'iphoenix': r'_iphoenix_|iphoenix',
    'kerm': r'kerm(?!ut2ks)|kermmartian',
    'kevino': r'.*?kevin_o|dj.?omni|dj.o|djowalrii|`-`$|celtic3|xlibman|nom$|ragol666',
    'kg583': r'kg583',
    'lax18': r'lax18',
    'lifeemu': r'lifeemu',
    'logical': r'logical$|logicaljoe',
    'mateoc': r'mateoc',
    'merth': r'merth|merthsoft|shaun',
    'michael23b': r'michaelb|michael2_3b',
    'nato': r'nato',
    'netham45': r'netham45|netbot45|ham\\',
    'nikky': r'((nikky|allyn)(?!(?:bot|test))|allynfolksjr)',
    'nomkid': r'nomkid',
    'pieman': r'pieman',
    'roccolox': r'roccolox',
    'tari': r'tari',
    'tev': r'tev|travis|travis e',
    'thelastmillennial': r'thelastmillennial',
    'timmy': r'timmyturner',
    'tinyhacker': r'tiny_hacker',
    'wavejumper3': r'wavejumper3',
    'womp': r'mr womp womp',
}

personality_config = {
    'iphoenix': {'order': 3},
    'logical': {'order': 3},
}

personalities = {
    # Aliases...:
    'nikkybot': 'nikky',
    'beckadam': 'beck',
    'astrid': 'chronomex',
    'astrinaut': 'chronomex',
    'cmx': 'chronomex',
    'duncans': 'chronomex',
    'exmic': 'chronomex',
    'xmc': 'chronomex',
    'imclevor': 'clevor',
    'comicidiot': 'comic',
    'comicsans': 'comic',
    'commandz': 'commandblockguy',
    'cvsoftd': 'cvsoft',
    'cvsoftl': 'cvsoft',
    'ephraim': 'ephraimb',
    'kermm': 'kerm',
    'kermmartian': 'kerm',
    'kermphd': 'kerm',
    'djo': 'kevino',
    'djomni': 'kevino',
    'djomnimaga': 'kevino',
    'xlibman': 'kevino',
    'logicaljoe': 'logical',
    'mateo': 'mateoc',
    'mateoconlechuga': 'mateoc',
    'merthsoft': 'merth',
    'shaun': 'merth',
    'netham': 'netham45',
    'tlm': 'thelastmillennial',
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
    return list(personality_regexes.keys())
