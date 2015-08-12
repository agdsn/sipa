from collections import namedtuple

# every property displayable in the usersuite table is presented here
FULL_FEATURE_LIST = {
    'user_id', 'name', 'state', 'room', 'ip',
    'mac', 'mac_change',
    'mail', 'mail_change'
    'userdb', 'userdb_change'
}


def property_base(description, supported, value, is_good, actions):
    return {
        'description': description,
        'is_supported': supported,
        'value': value,
        'is_good': is_good,     # bool or None
        'actions': actions
    }


def info_property(value, is_good=None, actions=None):
    # has been prefixed `info` to avoid using a builtin name
    if is_good is None:
        is_good = False
    if actions is None:
        actions = {}
    return property_base('', True, value, is_good, actions)


def unsupported_property(description=None):
    if description is None:
        description = ""
    return property_base(description, False, None, None, None)


class ACTIONS:
    EDIT, DELETE = range(2)
