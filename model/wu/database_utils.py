# -*- coding: utf-8 -*-

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from flask.ext.babel import lazy_gettext
from flask.globals import current_app
from werkzeug.local import LocalProxy

from .schema import Traffic


import logging
logger = logging.getLogger(__name__)


def init_db(app):
    atlantis_connection_string = 'mysql+pymysql://{0}:{1}@{2}:3306'.format(
        app.config['DB_ATLANTIS_USER'],
        app.config['DB_ATLANTIS_PASSWORD'],
        app.config['DB_ATLANTIS_HOST']
    )

    db_atlantis_netusers = create_engine(
        "{}/netusers".format(atlantis_connection_string),
        echo=False, connect_args={'connect_timeout': app.config['SQL_TIMEOUT']}
    )
    db_atlantis_traffic = create_engine(
        "{}/traffic".format(atlantis_connection_string),
        echo=False, connect_args={'connect_timeout': app.config['SQL_TIMEOUT']}
    )
    Session = sessionmaker(bind=db_atlantis_netusers,
                           binds={Traffic: db_atlantis_traffic})
    app.extensions['wu_session_atlantis'] = Session()

    app.extensions['db_helios'] = create_engine(
        'mysql+pymysql://{0}:{1}@{2}:{3}/'.format(
            app.config['DB_HELIOS_USER'],
            app.config['DB_HELIOS_PASSWORD'],
            app.config['DB_HELIOS_HOST'],
            int(app.config['DB_HELIOS_PORT'])),
        echo=False, connect_args={'connect_timeout': app.config['SQL_TIMEOUT']}
    )


db_helios = LocalProxy(lambda: current_app.extensions['db_helios'])
session_atlantis = LocalProxy(
    lambda: current_app.extensions['wu_session_atlantis']
)

DORMITORIES = [
    'Wundstraße 5',
    'Wundstraße 7',
    'Wundstraße 9',
    'Wundstraße 11',
    'Wundstraße 1',
    'Wundstraße 3',
    'Zellescher Weg 41',
    'Zellescher Weg 41A',
    'Zellescher Weg 41B',
    'Zellescher Weg 41C',
    'Zellescher Weg 41D',
    'Borsbergstraße 34',
]

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
