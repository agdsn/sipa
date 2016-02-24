# -*- coding: utf-8 -*-
import logging
import logging.config
import os
import os.path

from flask.ext.babel import get_locale
from raven import setup_logging
from raven.contrib.flask import Sentry
from raven.handlers.logging import SentryHandler
from sipa.babel import babel, possible_locales
from sipa.base import IntegerConverter, babel_selector, login_manager
from sipa.blueprints.usersuite import get_attribute_endpoint
from sipa.defaults import DEFAULT_CONFIG
from sipa.flatpages import cf_pages
from sipa.model import (current_datasource, init_context,
                        init_datasources_dormitories)
from sipa.utils import replace_empty_handler_callables
from sipa.utils.babel_utils import get_weekday
from sipa.utils.git_utils import init_repo, update_repo
from sipa.utils.graph_utils import (generate_credit_chart,
                                    generate_traffic_chart,
                                    provide_render_function)

logger = logging.getLogger(__name__)


def init_app(app):
    """Initialize the Flask app located in the module sipa.
    This initializes the Flask app by:
    * calling the internal init_app() procedures of each module
    * registering the Blueprints
    * registering the Jinja global variables
    :return: None
    """
    app.wsgi_app = ReverseProxied(app.wsgi_app)
    init_env_and_config(app)
    init_logging(app)
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

    from sipa.model import query_gauge_data
    logger.debug('Registering Jinja globals')
    form_label_width = 3
    form_input_width = 7
    app.jinja_env.globals.update(
        cf_pages=cf_pages,
        gauge_data=query_gauge_data,
        get_locale=get_locale,
        get_weekday=get_weekday,
        possible_locales=possible_locales,
        get_attribute_endpoint=get_attribute_endpoint,
        traffic_chart=provide_render_function(generate_traffic_chart),
        credit_chart=provide_render_function(generate_credit_chart),
        current_datasource=current_datasource,
        form_label_width_class="col-sm-{}".format(form_label_width),
        form_input_width_class="col-sm-{}".format(form_input_width),
        form_input_offset_class="col-sm-offset-{}".format(form_label_width)
    )
    logger.debug("Jinja globals have been set",
                 extra={'data': {'jinja_globals': app.jinja_env.globals}})

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
        logger.warning("SIPA_CONFIG_FILE not readable: %s",
                       os.environ['SIPA_CONFIG_FILE'])
    else:
        logger.info("Successfully read config file %s",
                    os.environ['SIPA_CONFIG_FILE'])

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

        logger.info("Registering repo update to uwsgi_signal")
        uwsgi.register_signal(20, "", update_uwsgi)
        uwsgi.add_timer(20, 300)

    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

    if not app.config['SECRET_KEY']:
        raise ValueError("SECRET_KEY must not be empty")


def init_logging(app):
    """Initialize the app's logging mechanisms

    - Configure the sentry client, if a DSN is given
    - Apply the default config dict (`defaults.DEFAULT_CONFIG`)
    - If given and existent, apply the additional config file
    """

    # Configure Sentry client (raven)
    if app.config['SENTRY_DSN']:
        logger.debug("Sentry DSN: {}".format(app.config['SENTRY_DSN']))
        sentry = Sentry()
        sentry.init_app(app, dsn=app.config['SENTRY_DSN'])

        def register_sentry_handler():
            handler = SentryHandler()

            handler.client = app.extensions['sentry'].client
            setup_logging(handler)

            return handler
    else:
        logger.debug("No sentry DSN specified")

        def register_sentry_handler():
            return logging.NullHandler()

    # Apply default config dict
    config = replace_empty_handler_callables(DEFAULT_CONFIG,
                                             register_sentry_handler)
    logging.config.dictConfig(config)
    logger.debug('Loaded default log config dict', extra={'data': {
        'DEFAULT_CONFIG': DEFAULT_CONFIG,
    }})

    if app.config.get('LOG_CONFIG') is not None:
        config = replace_empty_handler_callables(app.config['LOG_CONFIG'],
                                                 register_sentry_handler)
        logging.config.dictConfig(config)
        logger.debug('Loaded extra log config dict', extra={'data': {
            'CONFIG': app.config['LOG_CONFIG'],
        }})


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
