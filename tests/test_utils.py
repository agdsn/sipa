from time import time
from unittest import TestCase

from sipa.utils import timetag_today


class TimetagValidator(TestCase):
    def test_today_timetag(self):
        assert timetag_today() == time() // 86400
