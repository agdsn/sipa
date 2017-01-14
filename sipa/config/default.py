# -*- coding: utf-8 -*-

"""
all configuration options and dicts of external
information (dormitory mapping etc.)
Project-specific options should be included in the `config.py`,
which is a file not tracked in git containing IPs, user names, passwords, etc.
"""

SENTRY_DSN = None

CONTENT_URL = None

BACKENDS = ['sample']

FLATPAGES_ROOT = None
FLATPAGES_EXTENSION = '.md'

FLATPAGES_MARKDOWN_EXTENSIONS = [
    'sane_lists',
    'sipa.utils.bootstraped_tables',
    'sipa.utils.link_patch',
    'meta',
    'attr_list'
]

# Mail configuration
MAILSERVER_HOST = ""
MAILSERVER_PORT = 25

# LDAP configuration
WU_LDAP_HOST = ""
WU_LDAP_PORT = 389
WU_LDAP_SEARCH_USER_BASE = None
WU_LDAP_SEARCH_GROUP_BASE = None
WU_LDAP_SEARCH_USER = None
WU_LDAP_SEARCH_PASSWORD = None

# Userman configuration
# DB_USERMAN_URI: not set
# DB_NETUSERS_URI: not set
# DB_TRAFFIC_URI: not set

# MySQL Helios configuration
# DB_HELIOS_HOST: not set
DB_HELIOS_PORT = 3306
DB_HELIOS_USER = None
DB_HELIOS_PASSWORD = None
DB_HELIOS_IP_MASK = None

SQL_TIMEOUT = 2

GEROK_ENDPOINT = ""
GEROK_API_TOKEN = None

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
