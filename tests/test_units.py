from unittest import TestCase

from sipa.units import TRAFFIC_FORMAT_STRING, UNIT_LIST, dynamic_unit, \
    format_as_traffic, max_divisions, reduce_by_base, money, format_money, money_style


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
                example = [(1, 0), (base / 2, 0), (base, 1), (2 * base, 1), (base**2, 2),
                           (0, 0), (base**-2, 0), (-(base**-2), 0),
                           (-base / 2, 0), (-base, 1), (-2 * base, 1), (-(base**2), 2)]
                for num, expected_division in example:
                    with self.subTest(num=num):
                        self.assertEqual(max_divisions(num, base=base), expected_division)

    def test_number_reduced_correctly(self):
        """Test `reduce_by_base()` for basic cases"""
        for base in self.BASES:
            with self.subTest(base=base):
                # Some trivial examples should be enough
                examples = [(0, 0), (base, 1), (base**2, base),
                            (-base, -1), (-(base**2), -base)]
                for num, result in examples:
                    with self.subTest(num=num):
                        self.assertEqual(
                            reduce_by_base(number=num, base=base, divisions=1),
                            result,
                        )

    def test_unit_in_formatted_string(self):
        num, divisions = 1024, 1

        formatted = format_as_traffic(num, divisions, divide=False)
        # Checking num was passed isn't really testable, since
        # it could've been formatted ANY possible way.
        # Calling the format string itself is a stupid test,
        # on the other hand, basically reprogramming the
        # method.  Therefore, it is only tested that the
        # correct unit is appended.
        self.assertIn(UNIT_LIST[divisions], formatted)

    def test_dynamic_unit_contains_unit(self):
        self.assertIn(UNIT_LIST[1], dynamic_unit(1024))


class MoneyStyleMixin:
    STYLE_POS = 'success'
    STYLE_NEG = 'danger'


class MoneyStylePositiveTestCase(MoneyStyleMixin, TestCase):
    def setUp(self):
        super().setUp()
        self.nums = [3, 5, 1.6, 7.4, 0]

    def test_positive_style_returned(self):
        for num in self.nums:
            with self.subTest(num=num):
                self.assertEqual(money_style(num), self.STYLE_POS)


class MoneyStyleNegativeTestCase(MoneyStyleMixin, TestCase):
    def setUp(self):
        super().setUp()
        self.nums = [-3, -5, -1.6, -7.4, -0.5]

    def test_positive_style_returned(self):
        for num in self.nums:
            with self.subTest(num=num):
                self.assertEqual(money_style(num), self.STYLE_NEG)


class MoneyDecoratorTestCase(MoneyStyleMixin, TestCase):
    @money
    def dummy_func(self, value):
        return value

    def prepare_dict(self, d):
        value = d.pop('value')
        style = d.pop('style')
        raw_value = d.pop('raw_value')
        self.assertEqual(d, {})
        return value, style, raw_value

    def test_positive_float(self):
        value, style, raw_value = self.prepare_dict(self.dummy_func(3.5))

        self.assertEqual(raw_value, +3.5)
        self.assertTrue(value.startswith('+3.50'))
        self.assertTrue(value.endswith("€"))

        self.assertEqual(style, self.STYLE_POS)

    def test_negative_float(self):
        value, style, raw_value = self.prepare_dict(self.dummy_func(-3.5))

        self.assertEqual(raw_value, -3.5)
        self.assertTrue(value.startswith('-3.50'))
        self.assertTrue(value.endswith("€"))

        self.assertEqual(style, self.STYLE_NEG)

    def test_zero_is_positive(self):
        value, style, raw_value = self.prepare_dict(self.dummy_func(0))

        self.assertEqual(raw_value, 0)
        self.assertTrue(value.startswith('+0.00'))
        self.assertTrue(style, self.STYLE_POS)

    def test_whole_number_has_cent_digits(self):
        self.assertIn("3.00", self.dummy_func(3)['value'])


class MoneyTestCase(TestCase):
    def test_positive_float(self):
        value = format_money(+3.5)

        self.assertTrue(value.startswith('+3.50'))
        self.assertTrue(value.endswith("€"))

    def test_negative_float(self):
        value = format_money(-3.5)
        self.assertTrue(value.startswith('-3.50'))
        self.assertTrue(value.endswith("€"))

    def test_zero_is_positive(self):
        value = format_money(0)
        self.assertTrue(value.startswith('+0.00'))
