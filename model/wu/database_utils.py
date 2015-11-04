# -*- coding: utf-8 -*-

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from flask.ext.babel import lazy_gettext
from flask.globals import current_app
from werkzeug.local import LocalProxy

from .ldap_utils import get_current_uid
from .netusers import Traffic


import logging
logger = logging.getLogger(__name__)


def init_db(app):
    # TODO: refactor these things
    # e.g.: db_atlantis is not needed directly anymore
    app.extensions['db_atlantis'] = create_engine(
        'mysql+pymysql://{0}:{1}@{2}:3306/netusers'.format(
            app.config['DB_ATLANTIS_USER'],
            app.config['DB_ATLANTIS_PASSWORD'],
            app.config['DB_ATLANTIS_HOST']),
        echo=False, connect_args={'connect_timeout': app.config['SQL_TIMEOUT']}
    )
    app.extensions['db_helios'] = create_engine(
        'mysql+pymysql://{0}:{1}@{2}:{3}/'.format(
            app.config['DB_HELIOS_USER'],
            app.config['DB_HELIOS_PASSWORD'],
            app.config['DB_HELIOS_HOST'],
            int(app.config['DB_HELIOS_PORT'])),
        echo=False, connect_args={'connect_timeout': app.config['SQL_TIMEOUT']}
    )
    Session = sessionmaker(bind=db_atlantis, binds={Traffic: create_engine(
        'mysql+pymysql://{0}:{1}@{2}:3306/traffic'.format(
            app.config['DB_ATLANTIS_USER'],
            app.config['DB_ATLANTIS_PASSWORD'],
            app.config['DB_ATLANTIS_HOST']),
        echo=False, connect_args={'connect_timeout': app.config['SQL_TIMEOUT']}
    )})
    app.extensions['wu_session_atlantis'] = Session()


db_atlantis = LocalProxy(lambda: current_app.extensions['db_atlantis'])
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


def calculate_userid_checksum(user_id):
    """Calculate checksum for a userid.
    (Modulo 10 on the sum of all digits)

    :param user_id: The id of the mysql user tuple
    """
    return sum(map(int, str(user_id))) % 10
