# -*- coding: utf-8 -*-
import os

from flask import request, session
from flask.ext.babel import gettext
from flask.ext.login import current_user
from werkzeug.local import LocalProxy
from sqlalchemy.exc import OperationalError

from . import sample, wu, hss


registered_divisions = [sample.division, wu.division, hss.division]


def init_context(app):
    for division in registered_divisions:
        division.init_context(app)


def division_from_name(name):
    for division in registered_divisions:
        if division.name == name:
            return division
    return None


def current_division():
    return division_from_name(session['division'])


def division_from_ip(ip):
    # TODO: return correct division based on IP (dummy method)
    return sample.division


def user_from_ip(ip):
    return division_from_ip(ip).user_class.from_ip(ip)


def current_user_supported():
    return LocalProxy(
        lambda: current_division().user_class.supported()
    )


def query_gauge_data():
    credit = {}
    try:
        if current_user.is_authenticated():
            user = current_user
        else:
            user = user_from_ip(request.remote_addr)
        credit['data'] = user.get_current_credit()
    except OperationalError:
        credit['error'] = gettext(u'Fehler bei der Abfrage der Daten')
    except AttributeError:
        credit['error'] = gettext(u'Diese IP gehört nicht '
                                  u'zu unserem Netzwerk')
    return credit
