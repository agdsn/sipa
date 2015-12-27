# -*- coding: utf-8 -*-

from sqlalchemy import create_engine
from sqlalchemy.exc import OperationalError

from flask.ext.babel import lazy_gettext
from flask.globals import current_app
from werkzeug.local import LocalProxy

from .schema import db


import logging
logger = logging.getLogger(__name__)


def init_db(app):
    def get_atlantis_db_url(database):
        return ("mysql+pymysql://{user}:{pw}@{host}:3306/{db}"
                "?connect_timeout={timeout}"
                .format(
                    user=app.config['DB_ATLANTIS_USER'],
                    pw=app.config['DB_ATLANTIS_PASSWORD'],
                    host=app.config['DB_ATLANTIS_HOST'],
                    db=database,
                    timeout=app.config['SQL_TIMEOUT'],
                ))

    # set netusers as default binding
    app.config['SQLALCHEMY_DATABASE_URI'] = get_atlantis_db_url('netusers')
    app.config['SQLALCHEMY_BINDS'] = {
        'traffic': get_atlantis_db_url('traffic')
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

    app.extensions['db_helios'] = create_engine(
        'mysql+pymysql://{0}:{1}@{2}:{3}/'.format(
            app.config['DB_HELIOS_USER'],
            app.config['DB_HELIOS_PASSWORD'],
            app.config['DB_HELIOS_HOST'],
            int(app.config['DB_HELIOS_PORT'])),
        echo=False, connect_args={'connect_timeout': app.config['SQL_TIMEOUT']}
    )


db_helios = LocalProxy(lambda: current_app.extensions['db_helios'])

STATUS = {
    1: (lazy_gettext('ok'), 'success'),
    2: (lazy_gettext('Nicht bezahlt, Netzanschluss gesperrt'), 'warning'),
    7: (lazy_gettext('Verstoß gegen Netzordnung, Netzanschluss gesperrt'),
        'danger'),
    9: (lazy_gettext('Exaktiv'), 'muted'),
    12: (lazy_gettext('Trafficlimit überschritten, Netzanschluss gesperrt'),
         'danger')
}


def sql_query(query, args=(), database=db_helios):
    """Prepare and execute a raw sql query.
    'args' is a tuple needed for string replacement.
    """
    conn = database.connect()
    result = conn.execute(query, args)
    conn.close()
    return result
