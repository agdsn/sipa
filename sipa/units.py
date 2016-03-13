# -*- coding: utf-8; -*-

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
