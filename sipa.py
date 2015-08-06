# -*- coding: utf-8 -*-
"""
    sipa.py
    ~~~~~~~~~~~~~~

    This file shall be used to start the Flask app. Specific things are handled
    in the `sipa` package.

"""

import os.path
import logging.config

from sipa.utils.git_utils import update_repo, init_repo
from raven import setup_logging
from raven.contrib.flask import Sentry
from raven.handlers.logging import SentryHandler
from sipa import app, logger

# todo don't init by accessing app globally. rather make_app() with params.

### STEP ONE: CONFIG + DEFAULT VALUE EVALUATION

# default configuration
app.config.from_pyfile('default_config.py')

# if local config file exists, load everything into local space.
config_dir = os.getenv('SIPA_CONFIG_DIR', '..')
try:
    app.config.from_pyfile('{}/config.py'.format(config_dir))
except IOError:
    print("No Config found")
if app.config['FLATPAGES_ROOT'] == "":
    app.config['FLATPAGES_ROOT'] = os.path.join(
        os.path.dirname(os.path.abspath(__file__)),
        'content')

if app.config['CONTENT_URL']:
    init_repo(app.config["FLATPAGES_ROOT"], app.config['CONTENT_URL'])

if os.getenv("SIPA_UWSGI", "False") == 'True':
    import uwsgi

    def update_uwsgi(signum):
        hasToReload = update_repo(app.config["FLATPAGES_ROOT"])
        if hasToReload:
            uwsgi.reload

    uwsgi.register_signal(20, "", update_uwsgi)
    uwsgi.add_cron(20, -5, -1, -1, -1, -1)

### STEP TWO: INIT_APP

from sipa.base import init_app
init_app()

### STEP THREE: LOGGING

location_log_config = app.config['LOGGING_CONFIG_LOCATION']

if os.path.isfile(location_log_config):
    logging.config.fileConfig(location_log_config,
                              disable_existing_loggers=True)
    logger.info('Loaded logging configuration file "%s"', location_log_config)
else:
    logger.warning('Error loading configuration file "%s"', location_log_config)

if app.config['SENTRY_DSN']:
    sentry = Sentry()
    sentry.init_app(app)

    handler = SentryHandler(app.config['SENTRY_DSN'])
    handler.level = logging.NOTSET

    setup_logging(handler)

    # suppress INFO logging messages occurring every request
    logging.getLogger('werkzeug').setLevel(logging.WARNING)
    logger.debug("Sentry DSN: {}".format(app.config['SENTRY_DSN']))
else:
    logger.debug("No sentry DSN specified")

### STEP FOUR: APP.RUN

if __name__ == "__main__":
    # from sipa import make_app
    # app = make_app(*args, **kwargs)
    logger.info('Starting sipa...')
    logger.warning('Running in Debug mode')
    app.run(debug=True, host="0.0.0.0")
