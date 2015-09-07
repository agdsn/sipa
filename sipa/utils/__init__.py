#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
General utilities
"""

import http.client
import socket
import time
from flask import request, url_for

from flask.ext.login import current_user


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
        r = conn.getresponse()
    except socket.error:
        return None

    r_data = r.read()

    data = []
    entry_count = 0

    for i in r_data[2:-2].split('],['):
        if entry_count == count:
            break
        entry_count += 1

        tmpdata = i[1:-1].split('","')
        try:
            try:
                data.append(
                    [tmpdata[0], tmpdata[1].decode('utf8'), int(tmpdata[2])])
            except ValueError:
                data.append([tmpdata[0], tmpdata[1].decode('utf8'), 0])
        except IndexError:
            return None

    return data


def current_user_name():
    if current_user.is_authenticated():
        return current_user.uid
    elif current_user.is_anonymous():
        return 'anonymous'
    else:
        return ''


def redirect_url(default='index'):
    return request.args.get('next') or request.referrer or url_for(default)
