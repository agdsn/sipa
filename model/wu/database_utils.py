# -*- coding: utf-8 -*-

import datetime

from sqlalchemy import create_engine
from flask.ext.babel import gettext
from flask.globals import current_app

from werkzeug.local import LocalProxy

from model.constants import WEEKDAYS

from sipa.utils import timetag_from_timestamp, timestamp_from_timetag
from sipa.utils.exceptions import DBQueryEmpty
from .ldap_utils import get_current_uid

import logging
logger = logging.getLogger(__name__)


def init_db(app):
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


db_atlantis = LocalProxy(lambda: current_app.extensions['db_atlantis'])
db_helios = LocalProxy(lambda: current_app.extensions['db_helios'])

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
    1: (gettext('Bezahlt, verbunden'), 'success'),
    2: (gettext('Nicht bezahlt, Netzanschluss gesperrt'), 'warning'),
    7: (gettext('Verstoß gegen Netzordnung, Netzanschluss gesperrt'),
        'danger'),
    9: (gettext('Exaktiv'), 'muted'),
    12: (gettext('Trafficlimit überschritten, Netzanschluss gesperrt'),
         'danger')
}


def sql_query(query, args=(), database=db_atlantis):
    """Prepare and execute a raw sql query.
    'args' is a tuple needed for string replacement.
    """
    conn = database.connect()
    result = conn.execute(query, args)
    conn.close()
    return result


def user_id_from_uid(uid=None):
    """Fetch user.id (MySQL) from user.uid (LDAP)

    :param uid: The uid of the LDAP user object
    :return: The user id of the MySQL user
    """
    if uid is None:
        uid = get_current_uid()

    return sql_query("SELECT nutzer_id FROM nutzer WHERE unix_account = %s",
                     (uid,)).fetchone()['nutzer_id']


def update_macaddress(ip, oldmac, newmac):
    """Update a MAC address in computer table.

    Adding a `LIMIT 1` would be an “unsafe statement”, because using a
    `LIMIT` w/o an `ORDER BY` does not give control over which row
    actually would be affected, if the `WHERE` clauses would apply to
    more than one row.

    """
    sql_query(
        "UPDATE computer "
        "SET c_etheraddr = %s "
        "WHERE c_ip = %s "
        "AND c_etheraddr = %s ",
        (newmac.lower(), ip, oldmac)
    )


def calculate_userid_checksum(user_id):
    """Calculate checksum for a userid.
    (Modulo 10 on the sum of all digits)

    :param user_id: The id of the mysql user tuple
    """
    return sum(map(int, str(user_id))) % 10
