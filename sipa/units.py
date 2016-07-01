# -*- coding: utf-8; -*-
from functools import wraps


#: 0 divisions mean the unit stays being `KiB`
#: usage: unit = UNIT_LIST[divisions]
UNIT_LIST = ["KiB", "MiB", "GiB"]
TRAFFIC_FORMAT_STRING = "{0:.2f} {1}"


def max_divisions(number, base=1024, unit_list=UNIT_LIST):
    """Find the maximum number of divisions to get 0 ≤ number ≤ base"""
    divisions = 0
    while number >= base and divisions < len(UNIT_LIST)-1:
        number /= base
        divisions += 1
    return divisions


def reduce_by_base(number, divisions, base=1024):
    """Divide `number` by `divisions` potences of `base`"""
    return number / base**divisions


def format_as_traffic(number, divisions, divide=True):
    """Format `number` as traffic value

    If `divide` is True, reduce `value` `divisions` times.
    `divide=False` effectively just appends the according unit.
    """
    if divide:
        number = reduce_by_base(number, divisions)
    return TRAFFIC_FORMAT_STRING.format(number, UNIT_LIST[divisions])


def dynamic_unit(number, precision=2):
    """Display a KiB value in either KiB, MiB or GiB with unit according
    to size.
    """
    divisions = max_divisions(number)
    return format_as_traffic(number, divisions=divisions, divide=True)


def money(func):
    """A decorator turning a float number into a stylized money string.

    The given float is returned as `±98792.09€`, the style is a
    bootstrap-style context class without the prefix (e.g. `success`).

    :return: Value as string and style
    :rtype: A dict in the form of {'value': <string>, 'style': <string>}
    """
    @wraps(func)
    def _wrapped_func(*args, **kwargs):
        amount = func(*args, **kwargs)
        style = 'success' if amount >= 0 else 'danger'

        return {'value': format_money(amount),
                'raw_value': amount,
                'style': style}

    return _wrapped_func


def format_money(amount):
    return "{:+.2f} €".format(amount)
