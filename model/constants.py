# -*- coding: utf-8 -*-

from flask.ext.babel import gettext


class STATUS_COLORS:
    GOOD, BAD, WARNING, INFO = list(range(1, 5))  # 0 left for no status color


WEEKDAYS = {
    '0': gettext('Sonntag'),
    '1': gettext('Montag'),
    '2': gettext('Dienstag'),
    '3': gettext('Mittwoch'),
    '4': gettext('Donnerstag'),
    '5': gettext('Freitag'),
    '6': gettext('Samstag')
}
