# -*- coding: utf-8 -*-
"""config.example

    This is an example configuration file for SIPA, suggesting
    defaults for deployment.

    Every value not commented with "Must be set" has been given the
    default value which is assigned in the comment.
"""

# The Secret key. It should ALWAYS be set and kept secret!
# SECRET_KEY = "{random_string}"

# The datasources to use.  Must be a list of strings being the name of
# an implemented datasource.  The list of available datasources is
# defined at the top of `model.__init__`.
# BACKENDS = ['hss', 'sample', 'pycroft', …]

# Datasource-specific config
# For each backend, you can set a config dict.
# Currently, only the backends `support_mail` can be customized.
# _conf = {'support_mail': 'foo@bar.baz'}
# BACKEND_CONFIG = {'hss': _conf}


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
# None, 'ssl' or 'starttls'
# MAILSERVER_SSL = None
# Verify certificate and host name of mail server
# MAILSERVER_SSL_VERIFY = False
# The cadata object, if present, is an ASCII string
# of one or more PEM-encoded certificates.
# MAILSERVER_SSL_CA_DATA = None
# The cafile string, if present, is the path to a file
# of concatenated CA certificates in PEM format.
# MAILSERVER_SSL_CA_FILE = None
# MAILSERVER_USER = None
# MAILSERVER_PASSWORD = None
# CONTACT_SENDER_MAIL = None  # Must be set

# Pycroft backend
# PYCROFT_ENDPOINT = "https://pycroft.agdsn.de/api/v0/"
# PYCROFT_API_KEY = secret.pycroft_api_key

# MySQL Helios configuration
# DB_HELIOS_URI = None  # Must be set
# DB_HELIOS_IP_MASK = None

# HSS_CONNECTION_STRING = "postgresql://user:pass@host:port/db"  # must be set

# The SQL_TIMEOUT in seconds.
# SQL_TIMEOUT = 2

# The Token for the git update hook.
# It is disabled if nothing provided
# GIT_UPDATE_HOOK_TOKEN = ""

# Whether to use the timer
# UWSGI_TIMER_ENABLED = False

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
