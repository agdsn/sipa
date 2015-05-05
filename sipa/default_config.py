#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
all configuration options and dicts of external
information (dormitory mapping etc.)
Project-specific options should be included in the `config_local.py`,
which is a file not tracked in git containing IPs, user names, passwords, etc.
"""

from flask.ext.babel import gettext

SECRET_KEY = ""

LOG_FILE = 'error.log'

FLATPAGES_ROOT = ""
FLATPAGES_EXTENSION = '.md'
FLATPAGES_MARKDOWN_EXTENSIONS = [
    'sane_lists',
    'sipa.utils.bootstraped_tables',
    'nl2br',
    'meta',
    'attr_list'
]

LOGGING_CONFIG_LOCATION = "sipa/default_log_config"

# Mail configuration
MAILSERVER_HOST = "127.0.0.1"
MAILSERVER_PORT = 25

# LDAP configuration
LDAP_HOST = "127.0.0.1"
LDAP_PORT = 389
LDAP_SEARCH_BASE = ""

# MySQL configuration
DB_ATLANTIS_HOST = "127.0.0.1"
DB_ATLANTIS_USER = ""
DB_ATLANTIS_PASSWORD = ""

# MySQL Helios configuration
DB_HELIOS_HOST = "127.0.0.1"
DB_HELIOS_PORT = 3307   # alternative port for 2nd db
DB_HELIOS_USER = ""
DB_HELIOS_PASSWORD = ""

SQL_TIMEOUT = 15

# todo further modularization. id mappings are rather specific than generous.
# MySQL id mappings
DORMITORIES = [
    u'Wundstraße 5',
    u'Wundstraße 7',
    u'Wundstraße 9',
    u'Wundstraße 11',
    u'Wundstraße 1',
    u'Wundstraße 3',
    u'Zellescher Weg 41',
    u'Zellescher Weg 41A',
    u'Zellescher Weg 41B',
    u'Zellescher Weg 41C',
    u'Zellescher Weg 41D'
]

STATUS = {
    # todo vervollständigen oder mindestens fehlerresistent machen!
    # (Hat ein Nutzer einen unten nicht enthaltenen Status, gibts einen Fehler)
    1: gettext(u'Bezahlt, verbunden'),
    2: gettext(u'Nicht bezahlt, Netzanschluss gesperrt'),
    7: gettext(u'Verstoß gegen Netzordnung, Netzanschluss gesperrt'),
    9: gettext(u'Exaktiv'),
    12: gettext(u'Trafficlimit überschritten, Netzanschluss gesperrt')
}

WEEKDAYS = {
    '0': gettext('Sonntag'),
    '1': gettext('Montag'),
    '2': gettext('Dienstag'),
    '3': gettext('Mittwoch'),
    '4': gettext('Donnerstag'),
    '5': gettext('Freitag'),
    '6': gettext('Samstag')
}

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

