#!/usr/bin/env python
# -*- coding: utf-8 -*-

import datetime
from flask.globals import request
from sqlalchemy import create_engine
from sqlalchemy.exc import OperationalError

from sipa import app
from sipa.utils import timestamp_from_timetag, timetag_from_timestamp
from .exceptions import DBQueryEmpty, ForeignIPAccessError


db_atlantis = create_engine('mysql+mysqldb://{0}:{1}@{2}:3306/netusers'.format(
    app.config['DB_ATLANTIS_USER'],
    app.config['DB_ATLANTIS_PASSWORD'],
    app.config['DB_ATLANTIS_HOST'] ),
    echo=False, connect_args={'connect_timeout': app.config['SQL_TIMEOUT']})

db_helios = create_engine(
    'mysql+mysqldb://{0}:{1}@{2}:{3}/'.format(
        app.config['DB_HELIOS_USER'],
        app.config['DB_HELIOS_PASSWORD'],
        app.config['DB_HELIOS_HOST'],
        app.config['DB_HELIOS_PORT']),
    echo=False, connect_args={'connect_timeout': app.config['SQL_TIMEOUT'] })


def sql_query(query, args=(), database=db_atlantis):
    """Prepare and execute a raw sql query.
    'args' is a tuple needed for string replacement.
    """
    conn = database.connect()
    result = conn.execute(query, args)
    conn.close()
    return result


def query_userinfo(username):
    """Executes select query for the username and returns a prepared dict.

    * Dormitory IDs in Mysql are from 1-11, so we map to 0-10 with "x-1".

    Returns "-1" if a query result was empty (None), else
    returns the prepared dict.
    """
    user = sql_query(
        "SELECT nutzer_id, wheim_id, etage, zimmernr, status "
        "FROM nutzer "
        "WHERE unix_account = %s",
        (username,)
    ).fetchone()

    if not user:
        raise DBQueryEmpty

    computer = sql_query(
        "SELECT c_etheraddr, c_ip, c_hname, c_alias "
        "FROM computer "
        "WHERE nutzer_id = %s",
        (user['nutzer_id'])
    ).fetchone()

    if not computer:
        raise DBQueryEmpty

    try:
        has_mysql_db = user_has_mysql_db(username)
    except OperationalError:
        # todo display error (helios unreachable)
        # was a workaround to not abort due to this error
        has_mysql_db = False

    user = {
        'id': user['nutzer_id'],
        'address': u"{0} / {1} {2}".format(
            app.config['DORMITORIES'][user['wheim_id'] - 1],
            user['etage'],
            user['zimmernr']
        ),
        'status': app.config['STATUS'][user['status']],
        'status_is_good': user['status'] == 1,
        'ip': computer['c_ip'],
        'mac': computer['c_etheraddr'].upper(),
        'hostname': computer['c_hname'],
        'hostalias': computer['c_alias'],
        'heliosdb': has_mysql_db
    }

    return user


def user_id_from_ip(ip=None):
    if ip is None:
        raise ValueError

    result = sql_query("SELECT nutzer_id FROM computer WHERE c_ip = %s",
                       (ip,)).fetchone()
    if result is None:
        raise ForeignIPAccessError()

    return result['nutzer_id']


def query_trafficdata(ip=None, user_id=None):
    """Query traffic input/output for IP
    """
    if user_id is None:
        user_id = user_id_from_ip(ip)
    else:
        # ip gotten from db is preferred to the ip possibly given as parameter
        result = (sql_query(
            "SELECT c_ip FROM computer WHERE nutzer_id = %s",
            (user_id,)
        ).fetchone())
        if not result:
            raise DBQueryEmpty('Nutzer hat keine IP')
        ip = result['c_ip']

    trafficdata = sql_query(
        "SELECT t.timetag - %(today)s AS day, input, output, amount "
        "FROM traffic.tuext AS t "
        "LEFT OUTER JOIN credit AS c ON t.timetag = c.timetag "
        "WHERE ip = %(ip)s AND c.user_id = %(uid)s "
        "AND t.timetag BETWEEN %(weekago)s AND %(today)s "
        "ORDER BY 'day' DESC ",
        {'today': timetag_from_timestamp(),
         'weekago': timetag_from_timestamp() - 6,
         'ip': ip,
         'uid': user_id}
    ).fetchall()

    if not trafficdata:
        raise DBQueryEmpty

    traffic = {'history': [], 'credit': 0}
    returned_days = [int(i['day']) for i in trafficdata]

    # loop through expected days ([-6..0])
    for d in range(-6, 1):
        day = datetime.date.fromtimestamp(
            timestamp_from_timetag(timetag_from_timestamp() + d)
        ).strftime('%w')
        if d in returned_days:
            # pick the to `d` corresponding item of the mysql-result
            i = next((x for x in trafficdata if x['day'] == d), None)

            (input, output, credit) = (
                round(i[param] / 1024.0, 2)
                for param in ['input', 'output', 'amount']
            )
            traffic['history'].append((app.config['WEEKDAYS'][day], input, output, credit))
        else:
            traffic['history'].append(( app.config['WEEKDAYS'][day], 0.0, 0.0, 0.0))

    traffic['credit'] = (lambda x: x[3] - x[1] - x[2])(traffic['history'][-1])

    return traffic


def query_gauge_data():
    if request.remote_addr:
        try:
            return (lambda l: {
                "credit": l[3],
                "exhausted": l[1] + l[2]
            })(query_trafficdata(request.remote_addr)['history'][-1])
        except ForeignIPAccessError:
            # todo better method to tell that “error”?
            return {'error': 'foreign_ip'}
        except DBQueryEmpty:
            return {'error': True}
        except OperationalError:
            return {'error': True}
    else:
        return {'error': True}


def update_macaddress(ip, oldmac, newmac):
    """Update a MAC address in computer table.

    TODO: check, if 'LIMIT 1' causes problems (sqlalchemy says
    "Warning: Unsafe statement")
    """
    sql_query(
        "UPDATE computer "
        "SET c_etheraddr = %s "
        "WHERE c_ip = %s "
        "AND c_etheraddr = %s "
        "LIMIT 1",
        (newmac.lower(), ip, oldmac)
    )


def user_has_mysql_db(username):
    """Returns true if a database with the given name exists on
    helios-userdatabase, otherwise false.
    """
    userdb = sql_query(
        "SELECT SCHEMA_NAME "
        "FROM INFORMATION_SCHEMA.SCHEMATA "
        "WHERE SCHEMA_NAME = %s",
        (username,),
        database=db_helios
    ).fetchone()

    if userdb is not None:
        return True
    return False


def create_mysql_userdatabase(username, password):
    """A user specific database on helios is going to be created.
    """
    sql_query(
        "CREATE DATABASE "
        "IF NOT EXISTS `%s`" % username,
        database=db_helios
    )

    change_mysql_userdatabase_password(username, password)


def change_mysql_userdatabase_password(username, password):
    """This changes a user password for the helios MySQL-database.
    """
    user = sql_query(
        "SELECT user "
        "FROM mysql.user "
        "WHERE user = %s",
        (username,),
        database=db_helios
    ).fetchall()

    if not user:
        sql_query(
            "CREATE USER %s@'10.1.7.%%' "
            "IDENTIFIED BY %s",
            (username, password),
            database=db_helios
        )
    else:
        sql_query(
            "SET PASSWORD "
            "FOR %s@'10.1.7.%%' = PASSWORD(%s)",
            (username, password),
            database=db_helios
        )

    sql_query(
        "GRANT SELECT, INSERT, UPDATE, DELETE, ALTER, CREATE, DROP, INDEX, LOCK TABLES "
        "ON `%s`.* "
        "TO %%s@'10.1.7.%%%%'" % username,
        (username,),
        database=db_helios
    )


def drop_mysql_userdatabase(username):
    """This removes a userdatabase on helios.
    """
    sql_query(
        "DROP DATABASE "
        "IF EXISTS `%s`" % username,
        database=db_helios
    )

    sql_query(
        "DROP USER %s@'10.1.7.%%'",
        (username,),
        database=db_helios
    )
