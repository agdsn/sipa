import logging
import logging.config
import os
import os.path
from datetime import datetime

import sentry_sdk
from flask_babel import Babel, get_locale
from werkzeug.middleware.proxy_fix import ProxyFix
from flask_qrcode import QRcode
from sentry_sdk.integrations.flask import FlaskIntegration

from sipa.babel import possible_locales, save_user_locale_setting, select_locale
from sipa.base import IntegerConverter, login_manager
from sipa.blueprints.usersuite import get_attribute_endpoint
from sipa.defaults import DEFAULT_CONFIG
from sipa.flatpages import CategorizedFlatPages
from sipa.forms import render_links
from sipa.model import build_backends_ext
from sipa.model.misc import should_display_traffic_data
from sipa.session import SeparateLocaleCookieSessionInterface
from sipa.utils import url_self, support_hotline_available, meetingcal
from sipa.utils.babel_utils import get_weekday
from sipa.utils.git_utils import init_repo, update_repo
from sipa.utils.graph_utils import generate_traffic_chart, provide_render_function

logger = logging.getLogger(__name__)
logger.addHandler(logging.StreamHandler())  # for before logging is configured


def init_app(app, **kwargs):
    """Initialize the Flask app located in the module sipa.
    This initializes the Flask app by:

    * calling the internal init_app() procedures of each module
    * registering the Blueprints
    * registering the Jinja global variables
    """
    # this is horribly confusing: if an app is given, we completely ignore the `app`s config,
    # and overwrite it with the `default` one.
    load_config_file(app, config=kwargs.pop('config', None))
    app.wsgi_app = ProxyFix(app.wsgi_app, x_for=app.config['NUM_PROXIES'])
    init_logging(app)
    init_env_and_config(app)
    logger.debug('Initializing app')
    login_manager.init_app(app)
    babel = Babel()
    babel.init_app(app)
    babel.localeselector(select_locale)
    app.before_request(save_user_locale_setting)
    app.session_interface = SeparateLocaleCookieSessionInterface()
    cf_pages = CategorizedFlatPages()
    cf_pages.init_app(app)
    backends = build_backends_ext()
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
    form_label_width = 3
    form_input_width = 7
    app.jinja_env.globals.update(
        cf_pages=cf_pages,
        get_locale=get_locale,
        get_weekday=get_weekday,
        possible_locales=possible_locales,
        get_attribute_endpoint=get_attribute_endpoint,
        should_display_traffic_data=should_display_traffic_data,
        traffic_chart=provide_render_function(generate_traffic_chart),
        current_datasource=backends.current_datasource,
        form_label_width_class=f"col-sm-{form_label_width}",
        form_input_width_class=f"col-sm-{form_input_width}",
        form_input_offset_class=f"col-sm-offset-{form_label_width}",
        url_self=url_self,
        now=datetime.utcnow()
    )
    # the functions could also directly be added as globals,
    # however to minimize the diff things have been kept this way.
    app.context_processor(inject_hotline_status)
    app.context_processor(inject_meetingcal)

    app.add_template_filter(render_links)
    logger.debug("Jinja globals have been set",
                 extra={'data': {'jinja_globals': app.jinja_env.globals}})

    backends.init_backends()


def inject_hotline_status():
    """Adds :func:`support_hotline_available <sipa.utils.support_hotline_available>`
    to the :class:`jinja context <jinja2.runtime.Context>`"""
    return dict(support_hotline_available=support_hotline_available())


def inject_meetingcal():
    """Adds :func:`meetingcal <sipa.utils.meetingcal>`
    to the :class:`jinja context <jinja2.runtime.Context>`"""
    return dict(meetingcal=meetingcal())


def load_config_file(app, config=None):
    """Just load the config file, do nothing else"""
    # default configuration
    from .config import default

    app.config.from_pyfile(default.__file__)

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


def init_env_and_config(app):
    if not app.config['FLATPAGES_ROOT']:
        app.config['FLATPAGES_ROOT'] = os.path.join(
            os.path.dirname(__file__),
            '../content')
    if app.config['CONTENT_URL']:
        init_repo(app.config["FLATPAGES_ROOT"], app.config['CONTENT_URL'])
    else:
        if not os.path.isdir(app.config['FLATPAGES_ROOT']):
            try:
                os.mkdir(app.config['FLATPAGES_ROOT'])
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
            traces_sample_rate = 1.0,
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
