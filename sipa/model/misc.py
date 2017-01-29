from collections import namedtuple

TransactionTuple = namedtuple('Transaction', ['datum', 'value'])


def compare_all_attributes(one, other, attr_list):
    """Safely compare whether two ojbect's attributes are equal.

    :param one: The first object
    :param other: The second object
    :param list attr_list: A list of attributes (strings).

    :returns: Whether the attributes are equal or false on
              `AttributeError`

    :rtype: bool
    """
    try:
        return all(getattr(one, attr) == getattr(other, attr)
                   for attr in attr_list)
    except AttributeError:
        return False


def xor_hashes(*elements):
    """Combine all element's hashes with xor
    """
    _hash = 0
    for element in elements:
        _hash ^= hash(element)

    return _hash
