# -*- coding: utf-8 -*-
import logging.config
import os
import os.path

from flask import Flask

from raven import setup_logging
from raven.contrib.flask import Sentry
from raven.handlers.logging import SentryHandler

from flask.ext.babel import get_locale

from model import init_context, init_datasources_dormitories, \
    current_datasource
from model.constants import ACTIONS, STATUS_COLORS

from sipa import logger
from sipa.base import login_manager, babel_selector, IntegerConverter
from sipa.babel import babel, possible_locales
from sipa.flatpages import cf_pages
from sipa.utils.graph_utils import render_traffic_chart
from sipa.utils.git_utils import init_repo, update_repo


def create_app(name=None):
    app = Flask(name if name else __name__)
    init_app(app)
    return app


def init_app(app):
    """Initialize the Flask app located in the module sipa.
    This initializes the Flask app by:
    * calling the internal init_app() procedures of each module
    * registering the Blueprints
    * configuring the rotatingFileHandler for loggin
    * registering the Jinja global variables
    :return: None
    """
    app.wsgi_app = ReverseProxied(app.wsgi_app)
    init_env_and_config(app)
    logger.debug('Initializing app')
    login_manager.init_app(app)
    babel.init_app(app)
    babel.localeselector(babel_selector)
    cf_pages.init_app(app)

    app.url_map.converters['int'] = IntegerConverter

    from sipa.blueprints import bp_features, bp_usersuite, \
        bp_pages, bp_documents, bp_news, bp_generic

    logger.debug('Registering blueprints')
    app.register_blueprint(bp_generic)
    app.register_blueprint(bp_features)
    app.register_blueprint(bp_usersuite)
    app.register_blueprint(bp_pages)
    app.register_blueprint(bp_documents)
    app.register_blueprint(bp_news)

    if not app.debug:
        app.config.setdefault('LOG_MAX_BYTES', 1024 ** 2)
        app.config.setdefault('LOG_BACKUP_COUNT', 10)
        import logging
        from logging.handlers import RotatingFileHandler
        file_handler = RotatingFileHandler(
            app.config['LOG_FILE'],
            maxBytes=app.config['LOG_MAX_BYTES'],
            backupCount=app.config['LOG_BACKUP_COUNT'])
        file_handler.setLevel(logging.WARNING)
        app.logger.addHandler(file_handler)

    from model import query_gauge_data
    logger.debug('Registering Jinja globals')
    app.jinja_env.globals.update(
        cf_pages=cf_pages,
        gauge_data=query_gauge_data,
        get_locale=get_locale,
        possible_locales=possible_locales,
        chart=render_traffic_chart,
        current_datasource=current_datasource,
        ACTIONS=ACTIONS,
        STATUS_COLORS=STATUS_COLORS
    )

    init_logging(app)
    init_datasources_dormitories(app)
    init_context(app)


def init_env_and_config(app):
    # default configuration
    app.config.from_pyfile(os.path.realpath("sipa/default_config.py"))
    # if local config file exists, load everything into local space.
    if 'SIPA_CONFIG_FILE' not in os.environ:
        os.environ['SIPA_CONFIG_FILE'] = os.path.realpath("config.py")
    try:
        app.config.from_envvar('SIPA_CONFIG_FILE', silent=True)
    except IOError:
        print("No Config found")

    app.config.update({
        name[len("SIPA_"):]: value for name, value in os.environ.items()
        if name.startswith("SIPA_")
    })
    if app.config['FLATPAGES_ROOT'] == "":
        app.config['FLATPAGES_ROOT'] = os.path.join(
            os.path.dirname(os.path.abspath(__file__)),
            '../content')
    if app.config['CONTENT_URL']:
        init_repo(app.config["FLATPAGES_ROOT"], app.config['CONTENT_URL'])
    else:
        if not os.path.isdir(app.config['FLATPAGES_ROOT']):
            os.mkdir(app.config['FLATPAGES_ROOT'])

    if os.getenv("SIPA_UWSGI", "False") == 'True':
        import uwsgi

        def update_uwsgi(signum):
            hasToReload = update_repo(app.config["FLATPAGES_ROOT"])
            if hasToReload:
                uwsgi.reload

        uwsgi.register_signal(20, "", update_uwsgi)
        uwsgi.add_timer(20, 300)

    if not app.config['SECRET_KEY']:
        raise ValueError("SECRET_KEY must not be empty")


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


class ReverseProxied(object):
    """Wrap the application in this middleware and configure the
    front-end server to add these headers, to let you quietly bind
    this to a URL other than / and to an HTTP scheme that is
    different than what is used locally.

    In nginx:
    location /myprefix {
        proxy_pass http://192.168.0.1:5001;
        proxy_set_header Host $host;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Scheme $scheme;
        proxy_set_header X-Script-Name /myprefix;
        }

    :param app: the WSGI application
    """
    def __init__(self, flask_app):
        self.app = flask_app

    def __call__(self, environ, start_response):
        script_name = environ.get('HTTP_X_SCRIPT_NAME', '')
        if script_name:
            environ['SCRIPT_NAME'] = script_name
            path_info = environ['PATH_INFO']
            if path_info.startswith(script_name):
                environ['PATH_INFO'] = path_info[len(script_name):]

        scheme = environ.get('HTTP_X_SCHEME', '')
        if scheme:
            environ['wsgi.url_scheme'] = scheme

        server = environ.get('HTTP_X_FORWARDED_SERVER', '')
        if server:
            environ['HTTP_HOST'] = server
        return self.app(environ, start_response)
