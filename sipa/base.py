# -*- coding: utf-8 -*-
"""
Basic utilities for the Flask app

These are basic utilities necessary for the Flask app which are
disjoint from any blueprint.
"""
from babel import Locale, negotiate_locale
from flask import request, session
from flask_login import AnonymousUserMixin, LoginManager
from werkzeug.routing import IntegerConverter as BaseIntegerConverter

from sipa.babel import possible_locales
from sipa.model import backends

login_manager = LoginManager()


class IntegerConverter(BaseIntegerConverter):
    """IntegerConverter supporting negative values

    This is a Modification of the standard IntegerConverter which does
    not support negative values.  See the corresponding `werkzeug
    documentation
    <http://werkzeug.pocoo.org/docs/0.10/routing/#werkzeug.routing.IntegerConverter>`_.
    """
    regex = r'-?\d+'


@login_manager.user_loader
def load_user(username):
    """Loads a User object from/into the session at every request
    """
    if request.blueprint == "documents" or request.endpoint == "static":
        return AnonymousUserMixin()

    dormitory = backends.get_dormitory(session.get('dormitory', None))
    if dormitory:
        return dormitory.datasource.user_class.get(username)
    else:
        return AnonymousUserMixin()


def babel_selector():
    """Select a suitable locale

    Try to pick a locale from the following ordered sources:

        1. The ``lang`` query argument, if available.

        2. The current ``session`` cookie

        3. The best match to the ``accept-language`` HTTP header

    In any case, the session will be updated to the determined value.

    :returns: The determined locale

    :rtype: str
    """
    if 'locale' in request.args and Locale(
            request.args['locale']) in possible_locales():
        session['locale'] = request.args['locale']
    elif not session.get('locale'):
        session['locale'] = negotiate_locale(
            request.accept_languages.values(),
            list(map(str, possible_locales())), sep='-')

    return session.get('locale')
