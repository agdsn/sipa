# -*- coding: utf-8; -*-

#: 0 divisions mean the unit stays being `KiB`
#: usage: unit = UNIT_LIST[divisions]
UNIT_LIST = ["KiB", "MiB", "GiB"]
TRAFFIC_FORMAT_STRING = "{0:.2f} {1}"


def reduce_unit(number, base=1024, unit_list=UNIT_LIST):
    """Find the maximum number of divisions to get 0 ≤ number ≤ base"""
    divisions = 0
    while number >= base and divisions < len(UNIT_LIST)-1:
        number /= base
        divisions += 1
    return divisions


def reduce_by_base(number, divisions, base=1024):
    """Divide `number` by `divisions` potences of `base`"""
    return number / base**divisions


def format_without_unit(number, divisions):
    return TRAFFIC_FORMAT_STRING.format(number, UNIT_LIST[divisions])


def format_with_unit(number, divisions):
    number = reduce_by_base(number, divisions)
    return TRAFFIC_FORMAT_STRING.format(number, UNIT_LIST[divisions])


def dynamic_unit(number, precision=2):
    """Display a KiB value in either KiB, MiB or GiB with unit according
    to size.
    """
    divisions = reduce_unit(number)
    return format_with_unit(number, divisions=divisions)
