import logging
import logging.config
import os
import os.path
from datetime import datetime

import sentry_sdk
from flask import g
from flask_babel import Babel, get_locale
from flask_login import current_user
from werkzeug import Response
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
from sipa.forms import render_links
from sipa.model import AVAILABLE_DATASOURCES
from sipa.model.misc import should_display_traffic_data
from sipa.session import SeparateLocaleCookieSessionInterface
from sipa.utils import url_self
from sipa.utils.babel_utils import get_weekday
from sipa.utils.csp import ensure_items, NonceInfo
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
    form_label_width = 4
    form_input_width = 8
    app.jinja_env.globals.update(
        current_user=current_user,
        cf_pages=cf_pages,
        get_locale=get_locale,
        get_weekday=get_weekday,
        possible_locales=possible_locales,
        get_attribute_endpoint=get_attribute_endpoint,
        should_display_traffic_data=should_display_traffic_data,
        traffic_chart=provide_render_function(generate_traffic_chart),
        current_datasource=lambda: backends.datasource,
        form_label_width_class=f"col-sm-{form_label_width}",
        form_input_width_class=f"col-sm-{form_input_width}",
        form_input_offset_class=f"offset-sm-{form_label_width}",
        url_self=url_self,
        now=datetime.utcnow()
    )
    app.add_template_filter(render_links)

    def glyphicon_to_bi(glyphicon: str) -> str:
        MAP = {
            "glyphicon-briefcase": "bi-briefcase-fill",
            "glyphicon-bullhorn": "bi-megaphone-fill",
            "glyphicon-chevron-down": "bi-chevron-down",
            "glyphicon-cloud": "bi-cloud-fill",
            "glyphicon-comment": "bi-chat-left-fill",
            "glyphicon-dashboard": "bi-speedometer",
            "glyphicon-download-alt": "bi-download",
            "glyphicon-envelope": "bi-envelope-fill",
            "glyphicon-euro": "bi-currency-euro",
            "glyphicon-file": "bi-file-earmark-fill",
            "glyphicon-globe": "bi-globe-europe-africa",
            "glyphicon-headphones": "bi-headphones",
            "glyphicon-list-alt": "bi-card-list",
            "glyphicon-lock": "bi-lock-fill",
            "glyphicon-log-in": "bi-box-arrow-in-right",
            "glyphicon-question-sign": "bi-question-circle-fill",
            "glyphicon-retweet": "bi-arrow-repeat",
            "glyphicon-signal": "bi-router-fill",  # used for router page
            "glyphicon-star": "bi-star-fill",
            "glyphicon-tasks": "bi-box-arrow-up-right",
            "glyphicon-tint": "bi-droplet-fill",
            "glyphicon-transfer": "bi-arrow-left-right",
            "glyphicon-user": "bi-person-fill",
            "glyphicon-wrench": "bi-wrench-adjustable",
        }
        return MAP.get(glyphicon, glyphicon.replace("glyphicon-", "bi-"))

    app.add_template_filter(glyphicon_to_bi)
    logger.debug("Jinja globals have been set",
                 extra={'data': {'jinja_globals': app.jinja_env.globals}})


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


def ensure_csp(r: Response) -> Response:
    apply_nonces_to_csp(r)

    csp = r.content_security_policy
    SELF = ("'self'",)
    csp.default_src = ensure_items(csp.default_src, SELF)
    csp.connect_src = ensure_items(
        csp.connect_src,
        (
            "'self'",
            "https://status.agdsn.net",
            "https://*.tile.openstreetmap.de",
        ),
    )
    csp.form_action = ensure_items(csp.form_action, SELF)
    csp.frame_ancestors = ensure_items(csp.frame_ancestors, SELF)
    csp.img_src = ensure_items(
        csp.img_src,
        (
            "'self'",
            "data:",
            "https://*.tile.openstreetmap.de",
        ),
    )
    csp.script_src = ensure_items(
        csp.script_src,
        (
            "'self'",
            "https://status.agdsn.net",
        ),
    )
    csp.style_src = ensure_items(csp.style_src, SELF)
    csp.style_src_attr = ensure_items(csp.style_src_attr, ("'self'", "'unsafe-inline'"))
    csp.worker_src = ensure_items(csp.worker_src, ("'none'",))
    # there doesn't seem to be a good way to set `upgrade-insecure-requests`
    return r


def apply_nonces_to_csp(r: Response) -> None:
    if not hasattr(g, "nonce_info"):
        return

    nonce_info = g.nonce_info
    assert isinstance(nonce_info, NonceInfo)

    nonce_info.apply_to_csp(r.content_security_policy)
