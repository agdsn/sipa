"""
all configuration options and dicts of external
information (dormitory mapping etc.)
Project-specific options should be included in the `config.py`,
which is a file not tracked in git containing IPs, user names, passwords, etc.
"""

SENTRY_DSN = None

CONTENT_URL = None

LOCALE_COOKIE_NAME = 'locale'
LOCALE_COOKIE_MAX_AGE = 86400 * 31

# Maximum number of reverse proxies
NUM_PROXIES = 1

BACKENDS = ['pycroft']

FLATPAGES_ROOT = None
FLATPAGES_EXTENSION = '.md'

FLATPAGES_MARKDOWN_EXTENSIONS = [
    'sane_lists',
    'sipa.utils.bootstraped_tables',
    'sipa.utils.link_patch',
    'meta',
    'attr_list'
]
FLATPAGES_EXTENSION_CONFIGS = {
    'sane_lists': {},
    'sipa.utils.bootstraped_tables': {},
    'sipa.utils.link_patch': {},
    'meta': {},
    'attr_list': {},
}

# Mail configuration
MAILSERVER_HOST = ""
MAILSERVER_PORT = 25
MAILSERVER_SSL = None
MAILSERVER_SSL_VERIFY = False
MAILSERVER_SSL_CA_DATA = None
MAILSERVER_SSL_CA_FILE = None
MAILSERVER_USER = None
MAILSERVER_PASSWORD = None
# CONTACT_SENDER_MAIL  # Must be set

# MySQL Helios configuration
# DB_HELIOS_URI = None  # Must be set
DB_HELIOS_IP_MASK = None

SQL_TIMEOUT = 2
SQL_CONNECTION_RECYCLE = 3600

# PYCROFT_ENDPOINT  # Must be set
# PYCROFT_API_KEY  # Must be set

# Whether to use the timer
UWSGI_TIMER_ENABLED = False

# The Token for the git update hook.
# It is disabled if nothing provided
GIT_UPDATE_HOOK_TOKEN = ""

# Languages
LANGUAGES = {
    'de': 'Deutsch',
    'en': 'English'
}

# Bus & tram stops
BUSSTOPS = [
    "Zellescher Weg",
    "Strehlener Platz",
    "Weberplatz"
]

# Membership contribution
# Amount of membership contribution in cents
MEMBERSHIP_CONTRIBUTION = 500

# Pycroft backend
PYCROFT_ENDPOINT = "http://pycroft_dev-app_1:5000/api/v0/"
PYCROFT_API_KEY = "secret"

DB_HELIOS_URI = "mysql+pymysql://verwaltung:{}@userdb.agdsn.network:3306/".format("secret")
DB_HELIOS_IP_MASK = "10.0.7.%"

# PBX Endpoint
PBX_URI = "http://voip.agdsn.de:8000"

# Contact addresses
CONTACT_ADDRESSES = [
    {
        'name': "Wundtstraße 5",
        'doorbell': '0100',
        'floor': 0,
        'city': '01217 Dresden',
    },
    {
        'name': "Hochschulstraße 50",
        'doorbell': '0103',
        'floor': 0,
        'city': '01069 Dresden',
    },
    {
        'name': "Borsbergstraße 34",
        'floor': 7,
        'city': '01309 Dresden',
        'only_residents': True,
    },
]

# link to clandar
MEETINGS_ICAL_URL = "https://agdsn.de/cloud/remote.php/dav/public-calendars/bgiQmBstmfzRdMeH?export"
