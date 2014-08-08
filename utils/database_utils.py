#!/usr/bin/env python
# -*- coding: utf-8 -*-

import datetime
from sqlalchemy import create_engine

from config import dormitories, status, weekdays, DB_USER, DB_PASSWORD
from exceptions import DBQueryEmpty
from utils import timestamp_from_timetag


def sql_query(query, args=None):
    """Prepare and execute a raw sql query.
    'args' is a tuple needed for string replacement.
    """
    conn = db.connect()
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
        (newmac.lower(), ip, oldmac)
    )


db = create_engine('mysql+mysqldb://{0}:{1}@127.0.0.1:3306/netusers'.format(DB_USER, DB_PASSWORD), echo=False)