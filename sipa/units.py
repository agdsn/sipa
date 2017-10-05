# -*- coding: utf-8; -*-
from functools import wraps
from math import log, floor


#: 0 divisions mean the unit stays being `KiB`.
#: **Usage**: unit = UNIT_LIST[divisions]
UNIT_LIST = ["KiB", "MiB", "GiB"]
#: The format string for traffic values.  Rounds to two digits and
#: appends the unit.
TRAFFIC_FORMAT_STRING = "{0:.2f} {1}"
#: The format string for monetary values.  Round to two digits with a
#: sign and append €.  Mind the no-break space!
MONEY_FORMAT_STRING = "{:+.2f} €"


def max_divisions(number, base=1024, unit_list=None):
    """Find the maximum number of divisions to get 0 ≤ ``number`` ≤
    ``base``

    Return the maximum number of divisions we can make in the context
    of ``unit_list``.  If you give three units, no more than three
    divisions will be determined.

    :param int number: The number to test
    :param int base: The base to consider
    :param list unit_list: The list of units available

    :returns: The determined number of divisions

    :rtype: int
    """
    if unit_list is None:
        unit_list = UNIT_LIST

    # Determine largest whole logarithm of absolute value
    if number == 0:
        return 0
    divisions = floor(log(abs(number), base))
    if divisions <= 0:
        return 0

    # Make sure we have enough units available
    if divisions < len(unit_list):
        return divisions
    else:
        return len(unit_list) - 1


def reduce_by_base(number, divisions, base=1024):
    """Divide ``number`` by ``divisions`` potences of ``base``"""
    return number / base**divisions


def format_as_traffic(number, divisions, divide=True):
    """Format ``number`` as traffic value

    If ``divide`` is True, reduce ``value`` ``divisions`` times.
    ``divide=False`` effectively just appends the according unit.

    :param number: The number to format and perhaps divide
    :param divisions: Which unit to choose from :py:obj:`UNIT_LIST`
    :param divide: Whether ``number`` has to be divided.  If
        ``False``, leave as is.

    :returns: The formatted value

    :rtype: str
    """
    if divide:
        number = reduce_by_base(number, divisions)
    return TRAFFIC_FORMAT_STRING.format(number, UNIT_LIST[divisions])


def dynamic_unit(number):
    """Format a traffic value with a unit according to its size.

    :param float number: The traffic in units of the first element of
        :py:obj:`UNIT_LIST`

    :returns: The formatted value in a nice unit.  See
              :py:obj:`TRAFFIC_FORMAT_STRING`

    :rtype: str
    """
    divisions = max_divisions(number)
    return format_as_traffic(number, divisions=divisions, divide=True)


def money(func):
    """A decorator turning a float number into a stylized money string

    The given float is returned as e.g. ``±98792.09€``, the style is a
    bootstrap-style context class without the prefix (e.g.
    ``success``).

    :param function func: The function to be decorated

    :returns: Value as string and style

    :rtype: A dict in the form of ``{'value': <string>, 'style':
            <string>}``
    """
    @wraps(func)
    def _wrapped_func(*args, **kwargs):
        amount = func(*args, **kwargs)

        return {'value': format_money(amount),
                'raw_value': amount,
                'style': money_style(amount)}

    return _wrapped_func


def money_style(amount: float) -> str:
    """Return a corresponding bootstrap style to an amount of money

    :param float amount: The amount of money

    :returns: The bootstrap style
    """
    return 'success' if amount >= 0 else 'danger'


def format_money(amount: float) -> str:
    """Nicely format a monetary value

    :param float amount: The amount of euros

    :returns: The formatted value
    """
    return MONEY_FORMAT_STRING.format(amount)
