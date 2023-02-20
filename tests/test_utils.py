from itertools import permutations
from time import time
from unittest import TestCase

from sipa.utils import dict_diff, timetag_today, meetingcal
from base import AppInitialized


class TimetagValidator(TestCase):
    def test_today_timetag(self):
        assert timetag_today() == time() // 86400


class TestDictDiff(TestCase):
    def test_diffs_same_dicts(self):
        dicts = [{}, {'foo': 'bar'}, {'foo': 'bar', 'baz': {'boom': 'sheesh'}}]
        for d in dicts:
            self.assertEqual(set(dict_diff(d, d)), set())

    def test_diffs_one_different(self):
        # the dicts in `dicts` *MUST NOT* have two dicts with keys
        # with the same value, because then the merge does not change
        # anything.
        dicts = [{}, {'foo': 'one'}, {'foo': 'two'}, {'bar': 'three'},
                 {'foo': 'four', 'bar': 'five'}]
        for d1, d2 in permutations(dicts, 2):
            merged = d1.copy()
            merged.update(d2)
            self.assertEqual(set(dict_diff(d1, merged)), set(d2.keys()))

    def test_meetingcal(self):
        with AppInitialized.create_app().app_context():
            self.assertNotEqual(meetingcal(), [])
