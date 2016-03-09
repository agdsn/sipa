# -*- coding: utf-8 -*-
import logging

from flask.ext.babel import lazy_gettext
from sqlalchemy import create_engine
from sqlalchemy.exc import OperationalError

from .schema import db

logger = logging.getLogger(__name__)


def init_atlantis(app, static_connection_string=None):
    if static_connection_string:
        app.config['SQLALCHEMY_DATABASE_URI'] = static_connection_string
        app.config['SQLALCHEMY_BINDS'] = {
            'traffic': static_connection_string
        }
        db.init_app(app)
        return

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

    # set netusers as default binding
    app.config['SQLALCHEMY_DATABASE_URI'] = url_base.format('netusers')
    app.config['SQLALCHEMY_BINDS'] = {
        'traffic': url_base.format('traffic')
    }

    db.init_app(app)
    for bind in [None, 'traffic']:
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
    app.extensions['db_helios'] = create_engine(
        'mysql+pymysql://{0}:{1}@{2}:{3}/'.format(
            app.config['DB_HELIOS_USER'],
            app.config['DB_HELIOS_PASSWORD'],
            app.config['DB_HELIOS_HOST'],
            int(app.config['DB_HELIOS_PORT'])),
        echo=False, connect_args={'connect_timeout': app.config['SQL_TIMEOUT']}
    )


def init_db(app):
    """Register atlantis and userdb extensions onto the app object"""
    if app.config.get('DB_ATLANTIS_HOST'):
        init_atlantis(app)
    elif app.config.get('WU_CONNECTION_STRING'):
        init_atlantis(app, static_connection_string=app.config['WU_CONNECTION_STRING'])
    elif not app.debug:
        logger.info("DB_ATLANTIS_HOST not set. Skipping `init_atlantis()`.")

    if app.config.get('DB_HELIOS_HOST'):
        init_userdb(app)
    elif not app.debug:
        logger.info("DB_HELIOS_HOST not set. Skipping `init_userdb()`.")

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
