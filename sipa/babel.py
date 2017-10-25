# -*- coding: utf-8 -*-

from babel import Locale, UnknownLocaleError, negotiate_locale
from flask import request, session


def possible_locales():
    """Return the locales usable for sipa.

    :returns: Said Locales

    :rtype: List of :py:obj:`Locale` s
    """
    return [Locale('de'), Locale('en')]


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
