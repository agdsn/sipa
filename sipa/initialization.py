# -*- coding: utf-8 -*-
import logging.config
import os.path

from raven import setup_logging
from raven.contrib.flask import Sentry
from raven.handlers.logging import SentryHandler

from sipa import logger
from sipa.utils.git_utils import init_repo, update_repo


def init_env_and_config(app):
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
            '../content')
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


def init_logging(app):
    location_log_config = app.config['LOGGING_CONFIG_LOCATION']
    if os.path.isfile(location_log_config):
        logging.config.fileConfig(location_log_config,
                                  disable_existing_loggers=True)
        logger.info('Loaded logging configuration file "%s"',
                    location_log_config)
    else:
        logger.warning('Error loading configuration file "%s"',
                       location_log_config)
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