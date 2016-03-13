from functools import partial
from unittest import TestCase

from sipa.units import TRAFFIC_FORMAT_STRING, UNIT_LIST, dynamic_unit, \
    format_as_traffic, max_divisions, reduce_by_base


class TrafficFormatStringTestCase(TestCase):
    CORRECT_FORMAT_TUPLE = (35.037, "GiB")

    def test_contains_less_or_equal_two_format_fields(self):
        """Test that the format string expects ≤2 fields"""
        try:
            TRAFFIC_FORMAT_STRING.format(*self.CORRECT_FORMAT_TUPLE)
        except IndexError:
            self.fail("`TRAFFIC_FORMAT_STRING` has more than two fields'")

    def test_contains_more_than_one_format_field(self):
        """Test that the format string expects >1 field"""
        with self.assertRaises(IndexError):
            TRAFFIC_FORMAT_STRING.format(*self.CORRECT_FORMAT_TUPLE[:-1])


class ThingsWithBasesTestCase(TestCase):
    BASES = [100, 1000, 1024]

    def test_max_divisions(self):
        """Test `max_divisions()` for basic cases"""
        for base in self.BASES:
            with self.subTest(base=base):
                example = [(1, 0), (base / 2, 0), (base, 1), (2 * base, 1), (base**2, 2)]
                for num, expected_division in example:
                    with self.subTest(num=num):
                        self.assertEqual(max_divisions(num, base=base), expected_division)

    def test_number_reduced_correctly(self):
        """Test `reduce_by_base()` for basic cases"""
        for base in self.BASES:
            with self.subTest(base=base):
                # Some trivial examples should be enough
                examples = [(0, 0), (base, 1), (base**2, base)]
                for num, result in examples:
                    with self.subTest(num=num):
                        self.assertEqual(
                            reduce_by_base(number=num, base=base, divisions=1),
                            result,
                        )

    def test_unit_in_formatted_string(self):
        num, divisions = 1024, 1

        for func in [partial(format_as_traffic, divide=False), dynamic_unit]:
            with self.subTest(func=func):
                formatted = func(num, divisions)
                # Checking num was passed isn't really testable, since
                # it could've been formatted ANY possible way.
                # Calling the format string itself is a stupid test,
                # on the other hand, basically reprogramming the
                # method.  Therefore, it is only tested that the
                # correct unit is appended.
                self.assertIn(UNIT_LIST[divisions], formatted)
