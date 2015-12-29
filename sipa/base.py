# -*- coding: utf-8 -*-
from babel import Locale

from flask import request, session
from flask.ext.login import AnonymousUserMixin, LoginManager
from sipa.babel import possible_locales
from sipa.model import dormitory_from_name
from werkzeug.routing import IntegerConverter as BaseIntegerConverter

login_manager = LoginManager()


class IntegerConverter(BaseIntegerConverter):
    """Modification of the standard IntegerConverter which does not support
    negative values. See
    http://werkzeug.pocoo.org/docs/0.10/routing/#werkzeug.routing.IntegerConverter
    """
    regex = r'-?\d+'


@login_manager.user_loader
def load_user(username):
    """Loads a User object from/into the session at every request
    """
    if request.blueprint == "documents" or request.endpoint == "static":
        return AnonymousUserMixin()

    dormitory = dormitory_from_name(session.get('dormitory', None))
    if dormitory:
        return dormitory.datasource.user_class.get(username)
    else:
        return AnonymousUserMixin()


def babel_selector():
    """Tries to get the language setting from the current session cookie.
    If this fails (if it is not set) it first checks if a language was
    submitted as an argument ('/page?lang=de') and if not, the best matching
    language out of the header accept-language is chosen and set.
    """

    if 'locale' in request.args and Locale(
            request.args['locale']) in possible_locales():
        session['locale'] = request.args['locale']
    elif not session.get('locale'):
        langs = []
        for lang in possible_locales():
            langs.append(lang.language)
        session['locale'] = request.accept_languages.best_match(langs)

    return session.get('locale')
