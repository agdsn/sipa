# -*- coding: utf-8 -*-

from flask.ext.babel import lazy_gettext


WEEKDAYS = (
    lazy_gettext('Montag'),
    lazy_gettext('Dienstag'),
    lazy_gettext('Mittwoch'),
    lazy_gettext('Donnerstag'),
    lazy_gettext('Freitag'),
    lazy_gettext('Samstag'),
    lazy_gettext('Sonntag'),
)
