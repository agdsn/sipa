import logging
import logging.config
import os
import os.path
import typing as t
from contextlib import contextmanager
from datetime import datetime, UTC

import sentry_sdk
from jinja2 import Environment
from flask import Flask
from flask_babel import Babel, get_locale
from flask_login import current_user
from werkzeug.middleware.proxy_fix import ProxyFix
from flask_qrcode import QRcode
from sentry_sdk.integrations.flask import FlaskIntegration

from sipa.babel import (
    possible_locales,
    select_locale,
    setup_request_locale_context,
)
from sipa.backends import Backends
from sipa.base import IntegerConverter, login_manager
from sipa.blueprints.usersuite import get_attribute_endpoint
from sipa.defaults import DEFAULT_CONFIG
from sipa.flatpages import CategorizedFlatPages
from sipa.model import AVAILABLE_DATASOURCES
from sipa.model.misc import should_display_traffic_data
from sipa.model.pycroft import datasource
from sipa.session import SeparateLocaleCookieSessionInterface
from sipa.utils import url_self
from sipa.utils.babel_utils import get_weekday
from sipa.utils.git_utils import init_repo, update_repo

logger = logging.getLogger(__name__)
logger.addHandler(logging.StreamHandler())  # for before logging is configured


def create_app(config: dict[str, t.Any] | None = None) -> Flask:
    return init_app(Flask("sipa"), config)


def init_app(app: Flask, config: dict[str, t.Any] | None = None) -> Flask:
    """Initialize the Flask app located in the module sipa.

    This initializes the Flask app by:

    * calling the internal init_app() procedures of each module
    * registering the Blueprints
    * registering the Jinja global variables
    """
    # this is horribly confusing: if an app is given, we completely ignore the `app`s config,
    # and overwrite it with the `default` one.
    load_config_file(app, config=config)
    app.wsgi_app = ProxyFix(app.wsgi_app, x_for=app.config['NUM_PROXIES'])
    init_logging(app)
    init_env_and_config(app)
    logger.debug('Initializing app')
    login_manager.init_app(app, add_context_processor=False)
    babel = Babel()
    babel.init_app(app, locale_selector=select_locale)
    app.before_request(setup_request_locale_context)
    app.after_request(ensure_csp)
    app.session_interface = SeparateLocaleCookieSessionInterface()
    cf_pages = CategorizedFlatPages()
    cf_pages.init_app(app)
    backends = Backends(available_datasources=AVAILABLE_DATASOURCES)
    backends.init_app(app)
    QRcode(app)

    app.url_map.converters['int'] = IntegerConverter

    from sipa.blueprints import bp_features, bp_usersuite, \
        bp_pages, bp_documents, bp_news, bp_generic, bp_hooks, bp_register

    logger.debug('Registering blueprints')
    app.register_blueprint(bp_generic)
    app.register_blueprint(bp_features)
    app.register_blueprint(bp_usersuite)
    app.register_blueprint(bp_pages)
    app.register_blueprint(bp_documents)
    app.register_blueprint(bp_news)
    app.register_blueprint(bp_hooks)
    app.register_blueprint(bp_register)

    logger.debug('Registering Jinja globals')
    app.jinja_env.globals.update(
        current_user=current_user,
        get_locale=get_locale,
        get_weekday=get_weekday,
        # traffic_chart=provide_render_function(generate_traffic_chart),
    )
    init_jinja_env(app.jinja_env, cf_pages, backends)

    logger.debug("Jinja globals have been set",
                 extra={'data': {'jinja_globals': app.jinja_env.globals}})
    return app


def init_jinja_env(env: Environment, cf_pages: CategorizedFlatPages, backends: Backends):
    form_label_width = 4
    form_input_width = 8
    env.globals.update(
        possible_locales=possible_locales,
        cf_pages=cf_pages,
        # needs current_user
        get_attribute_endpoint=get_attribute_endpoint,
        # needs current_user, request
        should_display_traffic_data=should_display_traffic_data,
        current_datasource=datasource,
        form_label_width_class=f"col-sm-{form_label_width}",
        form_input_width_class=f"col-sm-{form_input_width}",
        form_input_offset_class=f"offset-sm-{form_label_width}",
        url_self=url_self,
        now=datetime.now(UTC),
    )


def load_config_file(app: Flask, config: dict[str, t.Any] | None = None):
    """Just load the config file, do nothing else"""
    # default configuration
    from .config import default

    app.config.from_pyfile(default.__file__)

    if app.config.from_prefixed_env(prefix="SIPA"):
        logger.warning("Env Variables with SIPA prefix set!")

    if config:
        app.config.update(config)

    # if local config file exists, load everything into local space.
    if 'SIPA_CONFIG_FILE' in os.environ:
        try:
            app.config.from_envvar('SIPA_CONFIG_FILE')
        except OSError:
            logger.warning("SIPA_CONFIG_FILE not readable: %s",
                           os.environ['SIPA_CONFIG_FILE'])
        else:
            logger.info("Successfully read config file %s",
                        os.environ['SIPA_CONFIG_FILE'])
    else:
        logger.info("No SIPA_CONFIG_FILE configured. Moving on.")


@contextmanager
def maybe_uwsgi_lock():
    try:
        import uwsgi
    except ImportError:
        yield
        return

    uwsgi.lock()
    yield
    uwsgi.unlock()


def init_env_and_config(app):
    if not app.config.get("FLATPAGES_ROOT"):
        app.config["FLATPAGES_ROOT"] = os.path.join(
            os.path.dirname(__file__),
            "../content",
        )

    content_root = app.config["FLATPAGES_ROOT"]

    if url := app.config["CONTENT_URL"]:
        with maybe_uwsgi_lock():
            init_repo(content_root, url)
    else:
        if not os.path.isdir(content_root):
            try:
                os.mkdir(content_root)
            except PermissionError as e:
                raise RuntimeError(
                    "The FLATPAGES_ROOT does not exist and cannot be created."
                    "\nIf you are runing from inside a container using mounts,"
                    " please create the directory at the given location"
                    "\n(default: `<project_root>/content`,"
                    " else: see what has been passed as configuration)."
                ) from e

    if app.config['UWSGI_TIMER_ENABLED']:
        try_register_uwsgi_timer(app=app)

    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

    if not app.config.get('SECRET_KEY'):
        if not app.debug:
            logger.warning('SECRET_KEY not set. Using default Key.')
        app.config['SECRET_KEY'] = "yIhswxbuDCvK8a6EDGihW6xjNognxtyO85SI"


def try_register_uwsgi_timer(app):
    """Register the uwsgi timer if uwsgi isavailable"""
    try:
        import uwsgi
        from uwsgidecorators import timer
    except ImportError:
        logger.info("uwsgi package not found, uwsgi_timer hasn't been set")
    else:
        @timer(300)
        def update_uwsgi(signum):
            flatpages_root = app.config["FLATPAGES_ROOT"]
            logger.debug("Updating git repository at %s", flatpages_root)
            hasToReload = update_repo(flatpages_root)
            if hasToReload:
                logger.debug("Reloading flatpages and uwsgi", extra={'data': {
                    'uwsgi.numproc': uwsgi.numproc,
                    'uwsgi.opt': uwsgi.opt,
                    'uwsgi.applications': uwsgi.applications,
                }})
                uwsgi.reload()

        logger.debug("Registered repo update to uwsgi signal")


def init_logging(app):
    """Initialize the app's logging mechanisms

    - Configure the sentry client, if a DSN is given
    - Apply the default config dict (`defaults.DEFAULT_CONFIG`)
    - If given and existent, apply the additional config file
    """

    if not (dsn := app.config['SENTRY_DSN']):
        logger.debug("No sentry DSN specified")
    # Configure Sentry SDK
    else:
        logger.debug("Sentry DSN: %s", dsn)
        sentry_sdk.init(
            dsn=dsn,
            integrations=[FlaskIntegration()],
            traces_sample_rate=1.0,
            # release="myapp@1.0.0",
        )

    # Apply default config dict
    logging.config.dictConfig(DEFAULT_CONFIG)

    if app.config.get('LOG_CONFIG') is not None:
        logging.config.dictConfig(app.config['LOG_CONFIG'])

    logger.debug('Initialized logging', extra={'data': {
        'DEFAULT_CONFIG': DEFAULT_CONFIG,
        'EXTRA_CONFIG': app.config.get('LOG_CONFIG')
    }})
