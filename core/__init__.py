import ssl

# Paths to local things
PROG_PATH = None
CONF_FILE = 'config.cfg'
LOG_DIR = 'logs'
PLUGIN_DIR = 'plugins'
DB_FILE = 'watcher.sqlite'
THEME = 'Default'

# Paths to internet things
GIT_URL = 'https://github.com/nosmokingbandit/watcher3'
GIT_REPO = 'https://github.com/nosmokingbandit/watcher3.git'
GIT_API = 'https://api.github.com/repos/nosmokingbandit/watcher3'

# Server settings
SERVER_ADDRESS = None
SERVER_PORT = None
URL_BASE = ''

# Update info
UPDATE_STATUS = None
UPDATE_LAST_CHECKED = None
UPDATING = False
CURRENT_HASH = None

# Dynamic info
NEXT_SEARCH = None
CONFIG = None
NOTIFICATIONS = []
NO_VERIFY = ssl.create_default_context()
NO_VERIFY.check_hostname = False
NO_VERIFY.verify_mode = ssl.CERT_NONE

# Rate limiting
TMDB_TOKENS = 35
TMDB_LAST_FILL = None

# Global Media Constants
RESOLUTIONS = ['BluRay-4K', 'BluRay-1080P', 'BluRay-720P',
               'WebDL-4K', 'WebDL-1080P', 'WebDL-720P',
               'WebRip-4K', 'WebRip-1080P', 'WebRip-720P',
               'DVD-SD',
               'Screener-1080P', 'Screener-720P',
               'Telesync-SD', 'CAM-SD']
