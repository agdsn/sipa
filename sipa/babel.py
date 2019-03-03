# -*- coding: utf-8 -*-
import logging
from typing import List, Optional

from babel import Locale, UnknownLocaleError, negotiate_locale
from flask import request, session
from werkzeug.exceptions import BadRequest


logger = logging.getLogger(__name__)


def possible_locales() -> List[Locale]:
    """Return the locales usable for sipa."""
    return [Locale('de'), Locale('en')]


def get_user_locale_setting() -> Optional[Locale]:
    """Get a user's explicit locale setting, if available."""
    locale_identifier = session.get('locale')
    if locale_identifier is None:
        return None

    try:
        locale = Locale.parse(locale_identifier)
    except (UnknownLocaleError, ValueError):
        logger.warning("Illegal locale {!r} stored in user session."
                       .format(locale_identifier))
        session.pop('locale')
        return None

    if locale not in possible_locales():
        logger.warning("Unavailable locale {} stored in user session."
                       .format(locale))
        session.pop('locale', None)
        return None

    return locale


def save_user_locale_setting():
    """
    Persist the locale request argument in the session state.

    This function should be installed as before_request handler.
    """
    locale_identifier = request.args.get('locale')
    if locale_identifier is None:
        return
    try:
        locale = Locale.parse(locale_identifier, sep='-')
    except (UnknownLocaleError, ValueError):
        raise BadRequest("Unknown locale {!r}".format(locale_identifier))
    if locale not in possible_locales():
        raise BadRequest("Locale {!r} not available".format(locale_identifier))
    session['locale'] = str(locale)


def select_locale() -> str:
    """Select a suitable locale

    Try to pick a locale from the following ordered sources:

        1. The user's explicit locale setting

        2. The best match according to the ``Accept-Language`` request header

    :returns: The locale string
    """
    locale = get_user_locale_setting()
    if locale is not None:
        return str(locale)
    return negotiate_locale(
        request.accept_languages.values(),
        list(map(str, possible_locales())), sep='-')
