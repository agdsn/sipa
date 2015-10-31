from unittest import TestCase
from sipa.utils import timetag_today
from time import time


class TimetagValidator(TestCase):
    def test_today_timetag(self):
        assert timetag_today() == time() // 86400
