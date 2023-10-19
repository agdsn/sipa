from __future__ import annotations

import logging
import typing as t

from babel import Locale, UnknownLocaleError, negotiate_locale
from flask import request, session, Request, g
from werkzeug.exceptions import BadRequest

logger = logging.getLogger(__name__)


def possible_locales() -> list[Locale]:
    """Return the locales usable for sipa."""
    return [Locale('de'), Locale('en')]


def get_user_locale_setting() -> Locale | None:
    """Get a user's explicit locale setting, if available."""
    if (locale_identifier := session.get("locale")) is None:
        return None

    logger.debug(
        "get_user_locale(): saving explicitly requested locale %r to session",
        locale_identifier,
    )
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


def _save_user_locale_setting():
    """
    Persist the locale request argument in the session state.
    """
    logger.debug("save_user_locale_setting")
    locale_identifier = request.args.get('locale')
    if locale_identifier is None:
        logger.debug("  ...nothing to save.")
        return
    try:
        locale = Locale.parse(locale_identifier, sep='-')
    except (UnknownLocaleError, ValueError):
        raise BadRequest(f"Unknown locale {locale_identifier!r}") from None
    if locale not in possible_locales():
        raise BadRequest(f"Locale {locale_identifier!r} not available")
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


def _iter_preferred_locales(request: Request) -> t.Iterator[str]:
    if (user_locale := str(get_user_locale_setting())) is not None:
        yield user_locale
    yield from request.accept_languages.values()


def preferred_locales() -> list[str]:
    return g.preferred_locales


def _cache_preferred_locales(**extra):
    """Store the preferred locales on the `g` object."""
    logger.debug("cache_preferred_locales; %r", request)

    pl = list(_iter_preferred_locales(request))
    logger.debug(f"cache update: {pl=}")
    g.preferred_locales = pl


def setup_request_locale_context():
    """Saves locale information in session and caches preferred locales.

    this function should be registered as a ``before_request`` handler.
    """
    _save_user_locale_setting()
    _cache_preferred_locales()
