# -*- coding: utf-8 -*-
# every property displayable in the usersuite table is presented here
from flask.ext.babel import gettext

DISPLAY_FEATURE_SET = {
    'user_id', 'name', 'state', 'room', 'ip', 'mac', 'mail', 'userdb'
}
MANIPULATE_FEATURE_SET = {
    'mac_change', 'mail_change', 'userdb_change', 'password_change'
}

FULL_FEATURE_SET = DISPLAY_FEATURE_SET | MANIPULATE_FEATURE_SET


def property_base(description, supported, value, status_color, actions):
    return {
        'description': description,
        'is_supported': supported,
        'value': value,
        'status_color': status_color,     # bool or None
        'actions': actions,
        'action_links': dict()  # added later by sipa.usersuite.usersuite()
    }


def info_property(value, status_color=None, actions=None):
    # has been prefixed `info` to avoid using a builtin name
    if actions is None:
        actions = {}
    return property_base('', True, value, status_color, actions)


def unsupported_property(description=None):
    if description is None:
        description = ""
    return property_base(description, False, None, None, None)


class ACTIONS:
    EDIT, DELETE = range(2)


class STATUS_COLORS:
    GOOD, BAD, WARNING, INFO = range(1, 5)  # 0 left for no status color


WEEKDAYS = {
    '0': gettext('Sonntag'),
    '1': gettext('Montag'),
    '2': gettext('Dienstag'),
    '3': gettext('Mittwoch'),
    '4': gettext('Donnerstag'),
    '5': gettext('Freitag'),
    '6': gettext('Samstag')
}