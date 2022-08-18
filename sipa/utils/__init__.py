"""
General utilities
"""

import dataclasses
import http.client
import json
import time
from collections.abc import Iterable
from datetime import datetime, timedelta, date
from functools import wraps
from itertools import chain

import requests
from flask import flash, redirect, request, url_for, session
from flask_login import current_user
from werkzeug.http import parse_date as parse_datetime

from sipa.config.default import PBX_URI


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
            f'/abfahrtsmonitor/Abfahrten.do?ort=Dresden&hst={stopname}'
        )
        response = conn.getresponse()
    except OSError:
        return None

    response_data = json.loads(response.read().decode())

    return ({
        'line': i[0],
        'dest': i[1],
        'minutes_left': int(i[2]) if i[2] else 0,
    } for i in response_data)
# TODO: check whether this is the correct format


def support_hotline_available():
    """Asks the PBX if there are agents logged in to anwser calls to our
    support hotline.

    :return: True if the hotline is available
    """
    [avail, time] = session.get('PBX_available', [False, datetime.fromtimestamp(0)])

    if datetime.now() - time > timedelta(minutes=2):
        # refresh availability from pbx
        try:
            r = requests.get(PBX_URI, timeout=0.5)
            r.raise_for_status()
            avail = r.text
            session['PBX_available'] = [avail, datetime.now()]
        except requests.exceptions.RequestException:
            avail = False

    if avail == 'AVAILABLE':
        return True
    else:
        return False


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


def url_self(**values):
    """Generate a URL to the request's current endpoint with the same view
    arguments.

    Additional arguments can be specified to override or extend the current view
    arguments.

    :param values: Additional variable arguments for the endpoint
    :return: A URL to the current endpoint
    """
    if request.endpoint is None:
        endpoint = 'generic.index'
    else:
        endpoint = request.endpoint
    # if no endpoint matches the given URL, `request.view_args` is
    # ``None``, not ``{}``
    kw = request.view_args.copy() if request.view_args is not None else {}
    kw.update(values)
    return url_for(endpoint, **kw)


def redirect_url(default='generic.index'):
    return request.args.get('next') or request.referrer or url_for(default)


def argstr(*args, **kwargs):
    return ", ".join(chain(
        (f"{arg}" for arg in args),
        (f"{key}={val!r}" for key, val in kwargs.items()),
    ))




def dict_diff(d1, d2):
    """Return a list of keys that have changed."""
    for key in set(d1.keys()) | set(d2.keys()):
        if key not in d1 or key not in d2 or d1[key] != d2[key]:
            yield key


def compare_all_attributes(one: object, other: object, attr_list: Iterable[str]) -> bool:
    """Safely compare whether two ojbect's attributes are equal.

    :param one: The first object
    :param other: The second object
    :param attr_list: A list of attribute names.

    :returns: Whether the attributes are equal or false on
              `AttributeError`
    """
    try:
        return all(getattr(one, attr) == getattr(other, attr)
                   for attr in attr_list)
    except AttributeError:
        return False


def xor_hashes(*elements: object) -> int:
    """Combine all element's hashes with xor
    """
    _hash = 0
    for element in elements:
        _hash ^= hash(element)

    return _hash


def parse_date(date: str | None) -> date | None:
    return parse_datetime(date).date() if date is not None else None


def dataclass_from_dict(cls, raw: dict):
    fields = {field.name for field in dataclasses.fields(cls)}
    kwargs = {key: value for key, value in raw.items() if key in fields}
    return cls(**kwargs)
