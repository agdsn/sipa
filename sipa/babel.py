# -*- coding: utf-8 -*-
from babel.core import Locale

from flask import request
from flask_babel import Babel


def possible_locales():
    """Return the locales usable for sipa.

    :returns: Said Locales

    :rtype: List of :py:obj:`Locale` s
    """
    return [Locale('de'), Locale('en')]
