from itertools import permutations
from time import time
from unittest import TestCase

from sipa.utils import dict_diff, replace_empty_handler_callables, \
    timetag_today


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


class TestHandlerReplacer(TestCase):
    @staticmethod
    def do_nothing():
        pass

    def assert_untouched(self, data):
        self.assertEqual(
            data,
            replace_empty_handler_callables(data, self.do_nothing)
        )

    def test_no_handlers_key(self):
        self.assert_untouched({})
        self.assert_untouched({'key': 'value', 'nested': {'foo': 'bar'}})

    def test_leave_other_handlers(self, ):
        self.assert_untouched({'handlers': {}})
        self.assert_untouched({'handlers': {
            'one': {'not_to_replace': None},
            'two': {'neither_to_replace': 'Also None'},
        }})

    def test_leave_callables_not_None(self, ):
        self.assert_untouched({'handlers': {
            'one': {'()': 'NOT None!'},
            'two': {'()': 42, 'param': 'val'},
            'three': {'()': str}
        }})

    def test_callable_replaced_correctly(self):
        original = {'handlers': {
            'one': {'()': None, 'param': 'Something_else'}
        }}
        result = replace_empty_handler_callables(original, self.do_nothing)
        self.assertEqual(
            list(dict_diff(result, original)),
            ['handlers'],
        )

        original = original['handlers']
        result = result['handlers']
        self.assertEqual(
            list(dict_diff(result, original)),
            ['one'],
        )

        original = original['one']
        result = result['one']
        self.assertEqual(
            list(dict_diff(result, original)),
            ['()'],
        )
        self.assertEqual(result['()'], self.do_nothing)
