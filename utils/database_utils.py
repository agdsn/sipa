#!/usr/bin/env python
# -*- coding: utf-8 -*-

import datetime
from sqlalchemy import create_engine

from exceptions import DBQueryEmpty
from config import *
from utils import timestamp_from_timetag


def sql_query(query, database, args=None):
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
        db,
        (username,)
    ).fetchone()

    if not user:
        raise DBQueryEmpty

    computer = sql_query(
        "SELECT c_etheraddr, c_ip, c_hname, c_alias "
        "FROM computer "
        "WHERE nutzer_id = %s",
        db,
        (user['nutzer_id'])
    ).fetchone()

    if not computer:
        raise DBQueryEmpty

    user = {
        'id': user['nutzer_id'],
        'address': u"{0} / {1} {2}".format(
            dormitories[user['wheim_id']-1],
            user['etage'],
            user['zimmernr']
        ),
        'status': status[user['status']],
        'ip': computer['c_ip'],
        'mac': computer['c_etheraddr'].upper(),
        'hostname': computer['c_hname'],
        'hostalias': computer['c_alias']
    }

    return user


def query_trafficdata(ip):
    """Query traffic input/output for IP
    """
    trafficdata = sql_query(
        "SELECT timetag, input, output "
        "FROM traffic.tuext "
        "WHERE ip = %s "
        "ORDER BY timetag DESC "
        "LIMIT 0, 7",
        db,
        (ip,)
    ).fetchall()

    if not trafficdata:
        raise DBQueryEmpty

    traffic = {
        'history': [
            [],
            [],
            []
        ],
        'total': 0,
        'percent': 0.0
    }

    for i in reversed(trafficdata):
        day = datetime.date.fromtimestamp(
            timestamp_from_timetag(i['timetag'])
        ).strftime('%w')

        input = round(i['input'] / 1024.0, 2)
        output = round(i['output'] / 1024.0, 2)

        traffic['history'][0].append(weekdays[day])
        traffic['history'][1].append(input)
        traffic['history'][2].append(output)

        traffic['total'] += input + output

    traffic['percent'] = round(traffic['total'] / (14 * 1024) * 100, 2)

    return traffic


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
        db,
        (newmac.lower(), ip, oldmac)
    )


def user_has_mysql_db(username):
    """Returns true if a database with the given name exists on helios-userdatabase,
    otherwise false.
    """
    userdb = sql_query(
        "SELECT SCHEMA_NAME FROM INFORMATION_SCHEMA.SCHEMATA WHERE SCHEMA_NAME = '{0}'".format(username),
        db_helios,
        ()
    ).fetchone()

    print(userdb)

    if userdb is not None:
        return True
    else:
        return False


def create_mysql_userdatabase(username, password):
    """A user specific database on helios is going to be created.
    """
    sql_query(
        "CREATE DATABASE IF NOT EXISTS {0}".format(username),
        db_helios,
        ()
    )
    change_mysql_userdatabase_password(username, password)


def change_mysql_userdatabase_password(username, password):
    """This changes a user password for the helios MySQL-database.
    """
    str = "GRANT USAGE ON {0}.* TO {0}@'10.1.7.%%' IDENTIFIED BY '{1}' WITH MAX_QUERIES_PER_HOUR 0 MAX_CONNECTIONS_PER_HOUR 0 MAX_UPDATES_PER_HOUR 0".format(username, password)
    erg = sql_query(
        str,
        db_helios,
        ()
    )


def drop_mysql_userdatabase(username):
    """This removes a userdatabase on helios.
    """
    sql_query(
        "DROP DATABASE IF EXISTS {0}".format(username),
        db_helios,
        ()
    )

db = create_engine('mysql+mysqldb://{0}:{1}@127.0.0.1:3306/netusers'.format(DB_USER, DB_PASSWORD), echo=False)
db_helios = create_engine('mysql+mysqldb://{0}:{1}@{2}:3306/'.format(
    DB_HELIOS_USER, DB_HELIOS_PASSWORD, DB_HELIOS_HOST), echo=False)
