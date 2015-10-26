# -*- coding: utf-8 -*-

"""
General utilities
"""

import http.client
import json
import socket
import time
from flask import request, url_for
from flask.ext.login import current_user
from itertools import chain


def timetag_from_timestamp(timestamp=None):
    """Convert a UNIX timestamp to a timetag.

    If timestamp is None, use the current time.
    COPIED FROM LEGACY
    """
    return int((time.time() if timestamp is None else timestamp) // 86400)


def timestamp_from_timetag(timetag):
    """Convert a timetag to a UNIX timestamp.

    COPIED FROM LEGACY
    """
    return timetag * 86400


def get_bustimes(stopname, count=10):
    """Parses the VVO-Online API return string.
    API returns in format [["line", "to", "minutes"],[__],[__]], where "__" are
    up to nine more Elements.

    :param stopname: Requested stop.
    :param count: Limit the entries for the stop.
    """
    conn = http.client.HTTPConnection('widgets.vvo-online.de', timeout=1)

    stopname = stopname.replace(' ', '%20')
    try:
        conn.request(
            'GET',
            '/abfahrtsmonitor/Abfahrten.do?ort=Dresden&hst={}'.format(stopname)
        )
        response = conn.getresponse()
    except socket.error:
        return None

    response_data = json.loads(response.read().decode())

    return ({
        'line': i[0],
        'dest': i[1],
        'minutes_left': int(i[2]) if i[2] else 0,
    } for i in response_data)
# TODO: check whether this is the correct format


def current_user_name():
    if current_user.is_authenticated:
        return current_user.uid
    elif current_user.is_anonymous:
        return 'anonymous'
    else:
        return ''


def redirect_url(default='index'):
    return request.args.get('next') or request.referrer or url_for(default)


def argstr(*args, **kwargs):
    return ", ".join(chain(
        ("{}".format(arg) for arg in args),
        ("{}={!r}".format(key, val) for key, val in kwargs.items()),
    ))
