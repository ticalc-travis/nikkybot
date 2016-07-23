# Markov chain nick configuration
#
# personalities = {
#       'alias': 'primary_persona_name',
#       ...
#       'alias': None,   # 'alias' is the primary persona name
# }
#
# personality_regexes = {
# 'Personality name':
#       ('IRC nick regex',
#        'Cemetech forum username regex' or None,
#        'Omnimaga forum username regex' or None,
#        'CodeWalrus forum username regex' or None),
# ...etc....
# }

personality_regexes = {
    'avgn':
        (r'AVGN',
         None,
         None,
         None),
    'eightx84':
        (r'eightx84|someone26',
         'eightx84',
         'eightx84',
         'eightx84'),
    'solarsoftware':
        (None,
         'solarsoftware',
         None,
         None),
    'richardnixon':
        (r'RichardNixon',
         None,
         None,
         None),
    'jonbush':
        (r'jonbush',
         None,
         None,
         None),
    'ivoah':
        (r'ivoah',
         r'ivoah',
         r'ivoah',
         r'ivoah'),
    'kinfinity':
        (r'kinfinity',
         r'kinginfinity',
         None,
         None),
    'eeems':
        (r'eeems',
         r'eeems',
         r'eeems',
         r'eeems'),
    'tari':
        (r'tari',
         r'tari',
         r'tari',
         r'tari'),
    'geekboy':
        (r'geek',
         r'geekboy',
         r'geekboy',
         r'geekboy'),
    'ephraimb':
        (r'ephraim|harryp|lazygeek',
         r'ephraim b',
         r'ephraim',
         r'ephraim'),
    'redstone':
        (r'redstone|asian|imbanned',
         r'redstonepizza',
         None,
         None),
    'sircmpwn':
        (r'sircmpwn',
         r'sircmpwn',
         r'sircmpwn',
         r'sircmpwn'),
    'ashbad':
        (r'ashbad|obongo|aalewis',
         r'ashbad',
         r'ashbad',
         None),
    'jonimus':
        (r'jonimus|thestorm',
         r'TheStorm',
         r'TheStorm|JonimusPrime',
         None),
    'joeyoung':
        (r'jy|joeyoung|mtgrss111',
         r'JoeYoung',
         None,
         None),
    'comic':
        (r'comic',
         r'comicIDIOT',
         None,
         None),
    'juju':
        (r'juju',
         r'juju',
         r'juju',
         r'juju'),
    'debrouxl':
        (r'debrouxl|ldebrouxl',
         r'Lionel Debroux',
         r'Lionel Debroux',
         r'Lionel Debroux'),
    'bb010g':
        (r'bb010g',
         r'bb010g',
         r'bb010g',
         r'bb010g'),
    'cvsoft':
        (r'cv|notipa',
         r'CVSoft',
         None,
         None),
    'calebh':
        (r'calebh|parse34|cheleron',
         r'CalebHansberry',
         None,
         None),
    'netham45':
        (r'netham45|netbot45|ham\\',
         r'netham45',
         r'netham45',
         r'netham45'),
    'kevino':
        (r'.*?kevin_o|dj_omni|dj_o|djowalrii|`-`$|celtic3|xlibman|nom$|ragol666',
         r'dj.?omni|dj.o',
         r'dj.?omni|dj.o',
         r'dj.?omni|dj.o'),
    'brandonw':
        (r'brandonw',
         r'brandonw',
         r'brandonw',
         r'brandonw'),
    'tev':
        (r'tev',
         r'travis',
         r'travise|travis e|travis e\.',
         r'travis'),
    'merth':
        (r'merth|merthsoft|shaun',
         r'merth|merthsoft|shaun',
         r'merth|merthsoft|shaun',
         r'merth|merthsoft|shaun'),
    'randomist':
        (r'randomist|korinidos|.*arch|metalrand|randeimos|dama|dam\\|damvista|devoidofw|psychodro',
         None,
         None,
         None),
    'sirlewk':
        (r'sir_lewk|sirlewk',
         None,
         None,
         None),
    'chronomex':
        (r'chronomex|chronome1|.*?slythe|xmc|cmx|exmic',
         r'chronomex',
         r'chronomex',
         None),
    'michaelv':
        (r'michael_v|michaelv',
         None,
         None,
         None),
    'ej':
        (r'e-j|e-jl|el-j',
         None,
         None,
         None),
    'cricketb':
        (r'cricket_b|cricketb|chirp_b|truepika',
         None,
         None,
         None),
    'glk':
        (r'glk',
         None,
         None,
         None),
    'kerm':
        (r'kerm',
         r'KermMartian',
         r'KermMartian',
         None),
    'nikky':
        (r'(nikky|allyn)(?!(?:bot|test))',
         r'allynfolksjr',
         None,
         None),
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
    'nixon': 'richardnixon'
}

# Fill in primary personas...
for p in personality_regexes:
    personalities[p] = None

