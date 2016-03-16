# -*- coding: utf-8 -*-
"""config.example

    This is an example configuration file for SIPA, suggesting
    defaults for deployment.

    Every value not commented with "Must be set" has been given the
    default value which is assigned in the comment.
"""

# The Secret key. It should ALWAYS be set and kept secret!
# SECRET_KEY = "{random_string}"

# The Sentry DSN.
# SENTRY_DSN = "http://{public}:{secret}@{host}:{port}/{int}"

# The url to the git repository containing the `/content`
# CONTENT_URL = "https://{url_to_git_repo}"

# The root for the flatpages
# FLATPAGES_ROOT = None

# The extension the flatpages have
# FLATPAGES_EXTENSION = '.md'

# The markdown extensioins you want to use.
# FLATPAGES_MARKDOWN_EXTENSIONS = [
#     'sane_lists',
#     'sipa.utils.bootstraped_tables',
#     'sipa.utils.link_patch',
#     'meta',
#     'attr_list'
# ]

# Mail configuration
# MAILSERVER_HOST = "atlantis.agdsn"
# MAILSERVER_PORT = 25

# LDAP configuration
# WU_LDAP_HOST = "atlantis.agdsn"  # Must be set
# WU_LDAP_PORT = 389
# WU_LDAP_SEARCH_USER_BASE = None
# WU_LDAP_SEARCH_GROUP_BASE = None
# WU_LDAP_SEARCH_USER = None
# WU_LDAP_SEARCH_PASSWORD = None

# MySQL configuration
# DB_ATLANTIS_HOST = "atlantis.agdsn"  # Must be set
# DB_ATLANTIS_USER = None
# DB_ATLANTIS_PASSWORD = None

# MySQL Helios configuration
# DB_HELIOS_HOST = "helios.agdsn"  # Must be set
# DB_HELIOS_PORT = 3306
# DB_HELIOS_USER = None
# DB_HELIOS_PASSWORD = None
# DB_HELIOS_IP_MASK = None

# The SQL_TIMEOUT in seconds.
# SQL_TIMEOUT = 2

# The data for the gerok api.

# GEROK_ENDPOINT = "https://gerok.agdsn:3000/api"
# GEROK_API_TOKEN = ""

# The Token for the git update hook.
# It is disabled if nothing provided
# GIT_UPDATE_HOOK_TOKEN = ""

# The languages babel provides.  It does not make much sense to chagne
# anything here.

# LANGUAGES = {
#     'de': 'Deutsch',
#     'en': 'English'
# }

# If you want to change the Busstops used in the VVO-API query, modify
# this list.

# BUSSTOPS = [
#     "Zellescher Weg",
#     "Strehlener Platz",
#     "Weberplatz"
# ]
