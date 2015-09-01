#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
all configuration options and dicts of external
information (dormitory mapping etc.)
Project-specific options should be included in the `config_local.py`,
which is a file not tracked in git containing IPs, user names, passwords, etc.
"""

import os

from flask.ext.babel import gettext

SECRET_KEY = os.getenv("SIPA_SECRET_KEY", "insecuresecretKey")

SENTRY_DSN = os.getenv('SIPA_SENTRY_DSN', '')

LOG_FILE = '/tmp/error.log'

CONTENT_URL = os.getenv("SIPA_CONTENT_URL")

FLATPAGES_ROOT = os.getenv("SIPA_FLATPAGES_ROOT", "")
FLATPAGES_EXTENSION = os.getenv("SIPA_FLATPAGES_EXTENSION", '.md')
sipa_flatpages_markdown_extensions = os.getenv(
    "SIPA_FLATPAGES_MARKDOWN_EXTENSIONS")
if sipa_flatpages_markdown_extensions is not None:
    sipa_flatpages_markdown_extensions = sipa_flatpages_markdown_extensions.split(
        ',')
else:
    sipa_flatpages_markdown_extensions = [
        'sane_lists',
        'sipa.utils.bootstraped_tables',
        'nl2br',
        'meta',
        'attr_list'
    ]
FLATPAGES_MARKDOWN_EXTENSIONS = sipa_flatpages_markdown_extensions

LOGGING_CONFIG_LOCATION = os.getenv("SIPA_LOGGING_CONFIG_LOCATION",
                                    "sipa/default_log_config")
GENERIC_LOGGING = True

# Mail configuration
MAILSERVER_HOST = os.getenv("SIPA_MAILSERVER_HOST", "127.0.0.1")
MAILSERVER_PORT = int(os.getenv("SIPA_MAILSERVER_PORT", '25'))

# LDAP configuration
LDAP_HOST = os.getenv("SIPA_LDAP_HOST", "127.0.0.1")
LDAP_PORT = int(os.getenv("SIPA_LDAP_PORT", '389'))
LDAP_SEARCH_BASE = os.getenv("SIPA_LDAP_SEARCH_BASE", "")

# MySQL configuration
DB_ATLANTIS_HOST = os.getenv("SIPA_DB_ATLANTIS_HOST", "127.0.0.1")
DB_ATLANTIS_USER = os.getenv("SIPA_DB_ATLANTIS_USER", "")
DB_ATLANTIS_PASSWORD = os.getenv("SIPA_DB_ATLANTIS_PASSWORD", "")

# MySQL Helios configuration
DB_HELIOS_HOST = os.getenv("SIPA_DB_HELIOS_HOST", "127.0.0.1")
DB_HELIOS_PORT = int(
    os.getenv("SIPA_DB_HELIOS_PORT", '3307'))  # alternative port for 2nd db
DB_HELIOS_USER = os.getenv("SIPA_DB_HELIOS_USER", "")
DB_HELIOS_PASSWORD = os.getenv("SIPA_DB_HELIOS_PASSWORD", "")

SQL_TIMEOUT = int(os.getenv("SIPA_SQL_TIMEOUT", '15'))

GEROK_ENDPOINT = os.getenv("SIPA_GEROK_ENDPOINT", "https://127.0.0.1/")
GEROK_API_TOKEN = os.getenv("SIPA_GEROK_API_TOKEN", "")

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
