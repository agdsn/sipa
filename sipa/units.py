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


def max_divisions(number: float, base: int = 1024, unit_list: list = None) -> int:
    """Find the maximum number of divisions to get 0 ≤ ``number`` ≤
    ``base``

    Return the maximum number of divisions we can make in the context
    of ``unit_list``.  If you give three units, no more than three
    divisions will be determined.

    :param number: The number to test
    :param base: The base to consider
    :param unit_list: The list of units available

    :returns: The determined number of divisions
    """
    if unit_list is None:
        unit_list = UNIT_LIST

    # Determine largest whole logarithm of absolute value
    if number == 0:
        return 0

    return max(0, min(floor(log(abs(number), base)), len(unit_list) - 1))


def reduce_by_base(number: float, divisions: int, base: int = 1024) -> float:
    """Divide ``number`` by ``divisions`` potences of ``base``"""
    return number / base**divisions


def format_as_traffic(number: float, divisions: int, divide: bool = True) -> str:
    """Format ``number`` as traffic value

    If ``divide`` is True, reduce ``value`` ``divisions`` times.
    ``divide=False`` effectively just appends the according unit.

    :param number: The number to format and perhaps divide
    :param divisions: Which unit to choose from :py:obj:`UNIT_LIST`
    :param divide: Whether ``number`` has to be divided.  If
        ``False``, leave as is.

    :returns: The formatted value
    """
    if divide:
        number = reduce_by_base(number, divisions)
    return TRAFFIC_FORMAT_STRING.format(number, UNIT_LIST[divisions])


def dynamic_unit(number: float) -> str:
    """Format a traffic value with a unit according to its size.

    :param number: The traffic in units of the first element of
        :py:obj:`UNIT_LIST`

    :returns: The formatted value in a nice unit.  See
              :py:obj:`TRAFFIC_FORMAT_STRING`
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

    :param amount: The amount of money

    :returns: The bootstrap style
    """
    return 'success' if amount >= 0 else 'danger'


def format_money(amount: float) -> str:
    """Nicely format a monetary value

    :param amount: The amount of euros

    :returns: The formatted value
    """
    return MONEY_FORMAT_STRING.format(amount)
