# -*- coding: utf-8 -*-
from flask import request, session, current_app
from flask.ext.babel import gettext
from flask.ext.login import current_user
from ipaddress import IPv4Address

from werkzeug.local import LocalProxy
from sqlalchemy.exc import OperationalError

from . import sample, wu, gerok


registered_divisions = [sample.division, wu.division,
                        gerok.division]

registered_dormitories = sample.dormitories + wu.dormitories + \
                         gerok.dormitories

unsupported_dormitories = {
    'hss': (u"Hochschulstraße", "https://wh12.tu-dresden.de"),
    'zeu': (u"Zeunerstraße", "https://zeus.wh25.tu-dresden.de")
}

supported_dormitories = {dormitory.name for dormitory
                         in registered_dormitories}


def init_divisions_dormitories(app):
    app.extensions['divisions'] = [
        div for div in registered_divisions
        if not div.debug_only or app.debug
    ]

    app.extensions['dormitories'] = [
        dorm for dorm in registered_dormitories
        if not dorm.division.debug_only or app.debug
    ]


def list_all_dormitories(ip=None):
    """Generate a list of all available dormitories (active & external).
    If an ip is given, try to place the according dormitory first.
    """
    if not ip and request:
        ip = request.remote_addr

    preferred = dormitory_from_ip(ip) if ip else None

    if preferred:
        active = [(preferred.name, preferred.display_name)] + [
            (dormitory.name, dormitory.display_name)
            for dormitory in current_app.extensions['dormitories']
            if not dormitory == preferred
        ]
    else:
        active = [(dormitory.name, dormitory.display_name)
                 for dormitory in current_app.extensions['dormitories']]

    extern = [(key, val[0]) for key, val in unsupported_dormitories.iteritems()]

    return active + extern


def init_context(app):
    for division in app.extensions['divisions']:
        division.init_context(app)


def dormitory_from_name(name):
    for dormitory in current_app.extensions['dormitories']:
        if dormitory.name == name:
            return dormitory
    return None


def current_division():
    if current_dormitory():
        return current_dormitory().division
    else:
        return None


def current_dormitory():
    return dormitory_from_name(session['dormitory'])


def division_from_ip(ip):
    dormitory = dormitory_from_ip(ip)
    if dormitory:
        return dormitory.division
    return None


def dormitory_from_ip(ip):
    for dormitory in current_app.extensions['dormitories']:
        if IPv4Address(unicode(ip)) in dormitory.subnets:
            return dormitory
    return None


def user_from_ip(ip):
    division = division_from_ip(ip)
    if division is not None:
        return division.user_class.from_ip(ip)
    else:
        return None


def current_user_supported():
    return LocalProxy(
        lambda: current_division().user_class.supported()
    )


def query_gauge_data():
    credit = {'data': None, 'error': False, 'foreign_user': False}
    try:
        if current_user.is_authenticated():
            user = current_user
        else:
            user = user_from_ip(request.remote_addr)
        credit['data'] = user.get_current_credit()
    except OperationalError:
        credit['error'] = True
    except AttributeError:
        credit['foreign_user'] = True
    return credit
