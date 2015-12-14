# -*- coding: utf-8 -*-

"""
all configuration options and dicts of external
information (dormitory mapping etc.)
Project-specific options should be included in the `config.py`,
which is a file not tracked in git containing IPs, user names, passwords, etc.
"""

from os import getenv

SECRET_KEY = getenv("SIPA_SECRET_KEY")

SENTRY_DSN = getenv('SIPA_SENTRY_DSN', '')

LOG_FILE = '/tmp/error.log'

CONTENT_URL = getenv("SIPA_CONTENT_URL")

FLATPAGES_ROOT = getenv("SIPA_FLATPAGES_ROOT", "")
FLATPAGES_EXTENSION = getenv("SIPA_FLATPAGES_EXTENSION", '.md')
sipa_markdown_extensions = getenv(
    "SIPA_FLATPAGES_MARKDOWN_EXTENSIONS")
if sipa_markdown_extensions is not None:
    sipa_markdown_extensions = sipa_markdown_extensions.split(
        ',')
else:
    sipa_markdown_extensions = [
        'sane_lists',
        'sipa.utils.bootstraped_tables',
        'meta',
        'attr_list'
    ]
FLATPAGES_MARKDOWN_EXTENSIONS = sipa_markdown_extensions

LOGGING_CONFIG_LOCATION = getenv("SIPA_LOGGING_CONFIG_LOCATION",
                                 "sipa/default_log_config")
GENERIC_LOGGING = True

# Mail configuration
MAILSERVER_HOST = getenv("SIPA_MAILSERVER_HOST", "127.0.0.1")
MAILSERVER_PORT = int(getenv("SIPA_MAILSERVER_PORT", '25'))

# LDAP configuration
WU_LDAP_HOST = getenv("SIPA_WU_LDAP_HOST", "127.0.0.1")
WU_LDAP_PORT = int(getenv("SIPA_WU_LDAP_PORT", '389'))
WU_LDAP_SEARCH_USER_BASE = getenv("SIPA_WU_LDAP_SEARCH_USER_BASE", "")
WU_LDAP_SEARCH_GROUP_BASE = getenv("SIPA_WU_LDAP_SEARCH_GROUP_BASE", "")
WU_LDAP_SEARCH_USER = getenv("SIPA_WU_LDAP_SEARCH_USER", None)
WU_LDAP_SEARCH_PASSWORD = getenv("SIPA_WU_LDAP_SEARCH_PASSWORD", None)

# MySQL configuration
DB_ATLANTIS_HOST = getenv("SIPA_DB_ATLANTIS_HOST", "127.0.0.1")
DB_ATLANTIS_USER = getenv("SIPA_DB_ATLANTIS_USER", "")
DB_ATLANTIS_PASSWORD = getenv("SIPA_DB_ATLANTIS_PASSWORD", "")

# MySQL Helios configuration
DB_HELIOS_HOST = getenv("SIPA_DB_HELIOS_HOST", "127.0.0.1")
DB_HELIOS_PORT = int(
    getenv("SIPA_DB_HELIOS_PORT", '3307'))  # alternative port for 2nd db
DB_HELIOS_USER = getenv("SIPA_DB_HELIOS_USER", "")
DB_HELIOS_PASSWORD = getenv("SIPA_DB_HELIOS_PASSWORD", "")

SQL_TIMEOUT = int(getenv("SIPA_SQL_TIMEOUT", '2'))

GEROK_ENDPOINT = getenv("SIPA_GEROK_ENDPOINT", "https://127.0.0.1/")
GEROK_API_TOKEN = getenv("SIPA_GEROK_API_TOKEN", "")

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
