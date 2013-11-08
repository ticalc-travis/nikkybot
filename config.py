# -*- coding: utf-8 -*-

SERVERS = (
    # (Name, port)
    ('irc.choopa.net', 6667),
    ('efnet.port80.se', 6667),
    ('irc.eversible.net', 6667),
    ('irc.shoutcast.com', 6667),
    ('irc.teksavvy.ca', 6667),
    ('irc.paraphysics.net', 6667),
)
REAL_NAME = 'NikkyBot'
NICKS = ('nikkybot', 'nikkybot2', 'nikkybot_')
CHANNELS = ('#flood', '#markov', '#cemetech')
CLIENT_VERSION = \
    "nikkybot (twisted IRC bot)--contact 'tev' or travisgevans@gmail.com"
ADMIN_HOSTMASKS = ('*!ijel@ip68-102-86-156.ks.ok.cox.net',
                   '*!travise@nvm2u.com',
                   '*!travise@64.13.172.47')
RECONNECT_WAIT = 30    # seconds
MAX_LINE_LENGTH = 256    # characters
MIN_SEND_TIME = 1   # seconds
NICK_RETRY_WAIT = 300    # seconds
INITIAL_REPLY_DELAY = 2    # seconds
SIMULATED_TYPING_SPEED = .1    # seconds/character
STATE_FILE = '/home/nikkybot/bot/nikkybot.state'    # Place to save AI state (None to disable)