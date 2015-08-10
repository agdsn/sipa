# -*- coding: utf-8 -*-
from flask.ext.babel import get_locale


def lang():
    return str(get_locale())
