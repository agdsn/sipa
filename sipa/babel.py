from __future__ import absolute_import

from itertools import imap
from babel.core import UnknownLocaleError
from flask import request
from flask_babel import Babel, Locale, get_locale

babel = Babel()


def locale_preferences():
    main_locale = get_locale()
    locales = [main_locale]

    def to_locale(language):
        try:
            return Locale(language)
        except UnknownLocaleError:
            return main_locale

    locales.extend(imap(to_locale, request.accept_languages.itervalues()))
    return locales


def possible_locales():
    """
    (TODO) write a GOOD function which gives us all possible Languages
    """
    return [Locale('de'), Locale('en')]
