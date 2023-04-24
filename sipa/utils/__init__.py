"""
General utilities
"""

import dataclasses
import http.client
import json
import logging
import typing
from datetime import date, datetime, timedelta
from functools import wraps
from itertools import chain
from operator import itemgetter
from zoneinfo import ZoneInfo

import icalendar
import markdown
import recurring_ical_events
import requests
from cachetools import TTLCache, cached
from dateutil.relativedelta import relativedelta
from flask import flash, redirect, request, session, url_for
from flask_login import current_user
from icalendar import Calendar
from werkzeug.http import parse_date as parse_datetime

from flask.globals import current_app

logger = logging.getLogger(__name__)


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
    UTC = ZoneInfo("UTC")
    [avail, time] = session.get(
        'PBX_available',
        [False, datetime.fromtimestamp(0).replace(tzinfo=UTC)]
    )
    now = datetime.utcnow().replace(tzinfo=ZoneInfo("UTC"))

    assert (now.tzinfo is None) == (time.tzinfo is None)
    if now - time > timedelta(minutes=2):
        # refresh availability from pbx
        try:
            r = requests.get(current_app.config['PBX_URI'], timeout=0.5)
            r.raise_for_status()
            avail = r.text
            session['PBX_available'] = [avail, now]
        except requests.exceptions.RequestException:
            avail = False

    if avail == 'AVAILABLE':
        return True
    else:
        return False


@cached(cache=TTLCache(maxsize=1, ttl=300))
def try_fetch_calendar(url: str) -> Calendar | None:
    """Fetch an ICAL calendar from a given URL."""
    try:
        response = requests.get(url, timeout=1)
    except requests.exceptions.RequestException:
        logger.exception("Error when fetching calendar at %s", url)
        return
    if response.status_code != 200:
        logger.error("Got unknown status code %s", response.status_code)
        return

    try:
        return icalendar.Calendar.from_ical(response.text)
    except ValueError:
        logger.exception("Could not parse calendar response %s", response.text)
        return


Event = typing.TypedDict(
    "Event",
    {
        "CREATED": icalendar.prop.vDDDTypes,
        "LAST-MODIFIED": icalendar.prop.vDDDTypes,
        "DTSTAMP": icalendar.prop.vDDDTypes,
        "SUMMARY": icalendar.prop.vText,
        "PRIORITY": int,
        "RELATED-TO": icalendar.prop.vText,
        "X-MOZ-LASTACK": icalendar.prop.vText,
        "DTSTART": icalendar.prop.vDDDTypes,
        "DTEND": icalendar.prop.vDDDTypes,
        "CLASS": icalendar.prop.vText,
        "LOCATION": icalendar.prop.vText,
        "SEQUENCE": int,
        "TRANSP": icalendar.prop.vText,
        "X-APPLE-TRAVEL-ADVISORY-BEHAVIOR": icalendar.prop.vText,
        "X-MICROSOFT-CDO-BUSYSTATUS": icalendar.prop.vText,
        "X-MOZ-GENERATION": icalendar.prop.vText,
    }
)


def events_from_calendar(calendar: icalendar.Calendar) -> list[Event]:
    """Given a calendar, extract the events up until one month in the future."""
    return recurring_ical_events.of(calendar).between(
        datetime.now(), datetime.now() + relativedelta(months=1)
    )


def meetingcal():
    """Returns the calendar events got form the url in the config"""
    if not (calendar := try_fetch_calendar(current_app.config['MEETINGS_ICAL_URL'])):
        return []

    events = events_from_calendar(calendar)
    next_meetings = [
        {
            "title": event["SUMMARY"],
            "datetime": event["DTSTART"].dt,
            "location": event["LOCATION"] if "LOCATION" in event else "-",
            "location_link": markdown.markdown(event["LOCATION"])
            if "LOCATION" in event
            else "-",
        }
        for event in events
    ]
    next_meetings = sorted(next_meetings, key=itemgetter("datetime"))
    return next_meetings


def subscribe_to_status_page(url: str, token: str, request_timeout: int, email: str) -> bool | None:
    """Send subscription request to status page API endpoint

    Returns:
        bool or None: Result whether subscribing to the status page worked
    """
    try:
        response = requests.post(
            url,
            timeout=request_timeout,
            headers={
                "Authorization": "Token " + token
            },
            json={"email": email}
        )
    except requests.exceptions.RequestException:
        logger.exception("Error when sending request to %s", url)
        return None
    if response.status_code == 400:
        # bad request usually means that the person has already subscribed to the status page
        return False
    if response.status_code == 201:
        # Subscribing to the status page worked
        return True

    # unexpected response from the status page
    logger.exception("Unexpected response when sending request to %s: %s", url, response.reason)
    return None


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


def compare_all_attributes(one: object, other: object, attr_list: typing.Iterable[str]) -> bool:
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
