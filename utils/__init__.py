#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
General utilities
"""

import time


def timetag_from_timestamp(timestamp=time.time()):
    """Convert a UNIX timestamp to a timetag.

    If timestamp is None, use the current time.
    COPIED FROM LEGACY
    """
    return int(timestamp // 86400)


def timestamp_from_timetag(timetag):
    """Convert a timetag to a UNIX timestamp.

    COPIED FROM LEGACY
    """
    return timetag * 86400