from collections import namedtuple

TransactionTuple = namedtuple('Transaction', ['datum', 'value'])


def compare_all_attributes(one, other, attr_list):
    return all(getattr(one, attr) == getattr(other, attr)
               for attr in attr_list)


def xor_hashes(*elements):
    """Combine all element's hashes with xor
    """
    _hash = 0
    for element in elements:
        _hash ^= hash(element)

    return _hash
