# -*- coding: utf-8 -*-
from flask_babel import get_locale


def lang():
    return str(get_locale())


def get_weekday(day):
    return get_locale().days['format']['wide'][day]
