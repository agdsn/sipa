# -*- coding: utf-8 -*-

"""
General utilities
"""

import time
from functools import wraps
from itertools import chain

from flask import flash, redirect, request, url_for
from flask.ext.login import current_user

import http.client
import json
import socket


def timetag_today():
    """Return the timetag for today"""
    return int(time.time() // 86400)


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


def password_changeable(user):
    """A decorator used to disable functions (routes) if a certain feature
    is not provided by the User class.

    given_features has to be a callable to ensure runtime distinction
    between datasources.

    :param needed_feature: The feature needed
    :param given_features: A callable returning the set of supported features
    :return:
    """
    def feature_decorator(func):
        @wraps(func)
        def decorated_view(*args, **kwargs):
            if user.is_authenticated and user.can_change_password:
                return func(*args, **kwargs)
            else:
                def not_supported():
                    flash("Diese Funktion ist nicht verfügbar.", 'error')
                    return redirect(redirect_url())
                return not_supported()

        return decorated_view
    return feature_decorator


def get_user_name(user=current_user):
    if user.is_authenticated:
        return user.uid

    if user.is_anonymous:
        return 'anonymous'

    return ''


def redirect_url(default='generic.index'):
    return request.args.get('next') or request.referrer or url_for(default)


def argstr(*args, **kwargs):
    return ", ".join(chain(
        ("{}".format(arg) for arg in args),
        ("{}={!r}".format(key, val) for key, val in kwargs.items()),
    ))


def replace_empty_handler_callables(config, func):
    """Register func as specfic handler's callable in a dict logging config.

    This method looks at the elements of the 'handlers' section of the
    `config`.

    If an element has an unassigned handler callable, which is a dict line
    `'()': None`, `None` is replaced by func.

    This function is kind of a hack, but necessary, because else the
    choice of the handler callable is limited to some static,
    predefined method.

    The specific example that lead to this: Because the callable to
    create a SentryHandler can only be defined *after* the import of
    the default config dict, but *before* the knowledge whether a
    `SENTRY_DSN` is given, it has to be dynamically created.

    :param dict config: A dict as used for logging.dictConfig()
    :return: The new, modified dict
    """

    if 'handlers' not in config:
        return config

    ret = config.copy()
    ret['handlers'] = {
        h_name: {param: (func
                         if val is None and param == '()'
                         else val)
                 for param, val in h_conf.items()}
        for h_name, h_conf in ret['handlers'].items()
    }
    return ret


def dict_diff(d1, d2):
    """Return a list of keys that have changed."""
    for key in set(d1.keys()) | set(d2.keys()):
        if key not in d1 or key not in d2 or d1[key] != d2[key]:
            yield key
