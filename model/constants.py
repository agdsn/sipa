from collections import namedtuple

# every property displayable in the usersuite table is presented here
FULL_FEATURE_LIST = {
    'user_id', 'name', 'state', 'room', 'ip',
    'mac', 'mac_change',
    'mail', 'mail_change'
    'userdb', 'userdb_change'
}


def property_base(description, supported, value, status_color, actions):
    return {
        'description': description,
        'is_supported': supported,
        'value': value,
        'status_color': status_color,     # bool or None
        'actions': actions,
        'action_links': dict()  # to be added later by the sipa gui
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
