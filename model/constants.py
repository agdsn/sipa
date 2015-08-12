from collections import namedtuple

# every property displayable in the usersuite table is presented here
FULL_FEATURE_LIST = {
    'user_id', 'name', 'state', 'room', 'ip',
    'mac', 'mac_change',
    'mail', 'mail_change'
    'userdb', 'userdb_change'
}


def PropertyBase(description, supported, value, is_good, actions):
    return {
        'description': description,
        'is_supported': supported,
        'value': value,
        'is_good': is_good,     # bool or None
        'actions': actions
    }


# noinspection PyPep8Naming
def Property(value, is_good=None, actions=None):
    if is_good is None:
        is_good = False
    if actions is None:
        actions = []
    return PropertyBase('', True, value, is_good, actions)


# noinspection PyPep8Naming
def UnsupportedProperty(description=None):
    if description is None:
        description = ""
    return PropertyBase(description, False, None, None, None)
