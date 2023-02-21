from itertools import permutations
from time import time

import pytest

from sipa.utils import dict_diff, timetag_today


def test_timetag_today():
    assert timetag_today() == time() // 86400


class TestDictDiff:
    @pytest.mark.parametrize(
        "d", ({}, {"foo": "bar"}, {"foo": "bar", "baz": {"boom": "sheesh"}})
    )
    def test_diffs_same_dicts(self, d):
        assert set(dict_diff(d, d)) == set()

    @pytest.mark.parametrize(
        "d1, d2",
        permutations(
            [
                {},
                {"foo": "one"},
                {"foo": "two"},
                {"bar": "three"},
                {"foo": "four", "bar": "five"},
            ],
            2,
        ),
    )
    def test_diffs_one_different(self, d1, d2):
        # the dicts in `dicts` *MUST NOT* have two dicts with keys
        # with the same value, because then the merge does not change
        # anything.
        merged = d1.copy()
        merged.update(d2)
        assert set(dict_diff(d1, merged)) == set(d2.keys())
