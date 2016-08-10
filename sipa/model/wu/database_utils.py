# -*- coding: utf-8 -*-
import logging

from flask_babel import lazy_gettext
from sqlalchemy import create_engine
from sqlalchemy.exc import OperationalError

from .schema import db
from sipa.utils.exceptions import InvalidConfiguration

logger = logging.getLogger(__name__)


def init_atlantis(app, static_connection_string=None):
    try:
        url_userman = app.config['DB_USERMAN_CONNECTION_STRING']
    except KeyError as exc:
        raise InvalidConfiguration(*exc.args)

    app.config['SQLALCHEMY_BINDS'] = {'userman': url_userman}

    if static_connection_string:
        app.config['SQLALCHEMY_BINDS'].update(traffic=static_connection_string,
                                              netusers=static_connection_string)

        return

    try:
        url_base = (
            "mysql+pymysql://{user}:{pw}@{host}:3306/{{}}"
            "?connect_timeout={timeout}"
            .format(
                user=app.config['DB_ATLANTIS_USER'],
                pw=app.config['DB_ATLANTIS_PASSWORD'],
                host=app.config['DB_ATLANTIS_HOST'],
                timeout=app.config['SQL_TIMEOUT'],
            )
        )

    except KeyError as exc:
        raise InvalidConfiguration(*exc.args)

    app.config['SQLALCHEMY_BINDS'].update(traffic=url_base.format('traffic'),
                                          netusers=url_base.format('netusers'))

    for bind in ['netusers', 'traffic']:
        engine = db.get_engine(app, bind=bind)
        try:
            conn = engine.connect()
        except OperationalError:
            logger.error(
                # the password in the engine repr is replaced by '***'
                "Connect to engine %s failed", engine,
                extra={'data': {
                    'engine': engine,
                    'bind': bind,
                }},
            )
        else:
            # If an exception got cought, `conn` does not exist
            # thus it cannot be closed in a `finally` clause
            conn.execute("SET lock_wait_timeout=%s", (2,))
            conn.close()


def init_userdb(app):
    try:
        app.extensions['db_helios'] = create_engine(
            'mysql+pymysql://{0}:{1}@{2}:{3}/'.format(
                app.config['DB_HELIOS_USER'],
                app.config['DB_HELIOS_PASSWORD'],
                app.config['DB_HELIOS_HOST'],
                int(app.config['DB_HELIOS_PORT'])),
            echo=False, connect_args={'connect_timeout': app.config['SQL_TIMEOUT']}
        )
    except KeyError as exc:
        raise InvalidConfiguration(*exc.args)


def init_db(app):
    """Register atlantis and userdb extensions onto the app object

    For testing reasons, the initialization of userdb will be skipped
    on invalid configuration.  Configuring atlantis however is
    obligatiory.  See `init_atlantis`.
    """
    init_atlantis(
        app,
        # No condition necessary: if not set, it will be None and ignored.
        static_connection_string=app.config.get('WU_CONNECTION_STRING'),
    )

    try:
        init_userdb(app)
    except InvalidConfiguration as exception:
        logger.info("Incomplete Configuration for userdb (%s)."
                    " Skipping `init_init_userdb()`.",
                    exception.args[0])

STATUS = {
    1: (lazy_gettext('ok'), 'success'),
    2: (lazy_gettext('Nicht bezahlt, Netzanschluss gesperrt'), 'warning'),
    7: (lazy_gettext('Verstoß gegen Netzordnung, Netzanschluss gesperrt'),
        'danger'),
    9: (lazy_gettext('Exaktiv'), 'muted'),
    12: (lazy_gettext('Trafficlimit überschritten, Netzanschluss gesperrt'),
         'danger')
}

ACTIVE_STATUS = [
    1,  # ok
    2,  # not paid
    7,  # abuse
    12,  # traffic
]
