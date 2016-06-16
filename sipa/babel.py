# -*- coding: utf-8 -*-
from babel.core import Locale, UnknownLocaleError

from flask import request
from flask_babel import Babel, get_locale

babel = Babel()


def locale_preferences():
    main_locale = get_locale()
    locales = [main_locale]

    def to_locale(language):
        try:
            return Locale(language)
        except UnknownLocaleError:
            return main_locale

    locales.extend(map(to_locale, iter(request.accept_languages.values())))
    return locales


def possible_locales():
    return [Locale('de'), Locale('en')]
