from unittest import TestCase

import pytest

from sipa.units import TRAFFIC_FORMAT_STRING, UNIT_LIST, dynamic_unit, \
    format_as_traffic, max_divisions, reduce_by_base, money, format_money, money_style


class TestTrafficFormatString:
    CORRECT_FORMAT_TUPLE = (35.037, "GiB")

    def test_contains_less_or_equal_two_format_fields(self):
        """Test that the format string expects ≤2 fields"""
        try:
            TRAFFIC_FORMAT_STRING.format(*self.CORRECT_FORMAT_TUPLE)
        except IndexError:
            pytest.fail("`TRAFFIC_FORMAT_STRING` has more than two fields'")

    def test_contains_more_than_one_format_field(self):
        """Test that the format string expects >1 field"""
        with pytest.raises(IndexError):
            TRAFFIC_FORMAT_STRING.format(*self.CORRECT_FORMAT_TUPLE[:-1])


class TestThingsWithBases:
    BASES = [100, 1000, 1024]

    @pytest.mark.parametrize(
        "base, num, expected_division",
        [
            (b, num, e)
            for b in BASES
            for num, e in [
                (1, 0),
                (b / 2, 0),
                (b, 1),
                (2 * b, 1),
                (b**2, 2),
                (0, 0),
                (b**-2, 0),
                (-(b**-2), 0),
                (-b / 2, 0),
                (-b, 1),
                (-2 * b, 1),
                (-(b**2), 2),
            ]
        ],
    )
    def test_max_divisions(self, base, num, expected_division):
        """Test `max_divisions()` for basic cases"""
        assert max_divisions(num, base=base) == expected_division

    @pytest.mark.parametrize(
        "base, num, result",
        [
            (b, num, res)
            for b in BASES
            for num, res in [(0, 0), (b, 1), (b**2, b), (-b, -1), (-(b**2), -b)]
        ],
    )
    def test_number_reduced_correctly(self, base, num, result):
        """Test `reduce_by_base()` for basic cases"""
        assert reduce_by_base(number=num, base=base, divisions=1) == result

    def test_unit_in_formatted_string(self):
        num, divisions = 1024, 1

        formatted = format_as_traffic(num, divisions, divide=False)
        # Checking num was passed isn't really testable, since
        # it could've been formatted ANY possible way.
        # Calling the format string itself is a stupid test,
        # on the other hand, basically reprogramming the
        # method.  Therefore, it is only tested that the
        # correct unit is appended.
        assert UNIT_LIST[divisions] in formatted

    def test_dynamic_unit_contains_unit(self):
        assert UNIT_LIST[1] in dynamic_unit(1024)


STYLE_POS = "success"
STYLE_NEG = "danger"


@pytest.mark.parametrize("num", (3, 5, 1.6, 7.4, 0))
def test_positive_style_returned(num):
    assert money_style(num) == STYLE_POS


@pytest.mark.parametrize("num", (-3, -5, -1.6, -7.4, -0.5))
def test_negative_style_returned(num):
    assert money_style(num) == STYLE_NEG


def parse_money_dict(d):
    value = d.pop("value")
    style = d.pop("style")
    raw_value = d.pop("raw_value")
    assert d == {}
    return value, style, raw_value


class TestMoneyDecorator:
    @pytest.fixture(scope="class")
    def decorated_function(self):
        @money
        def id_(value):
            return value

        return id_

    def test_positive_float(self, decorated_function):
        value, style, raw_value = parse_money_dict(decorated_function(3.5))

        assert raw_value == +3.5
        assert value.startswith("+3.50")
        assert value.endswith("€")

        assert style == STYLE_POS

    def test_negative_float(self, decorated_function):
        value, style, raw_value = parse_money_dict(decorated_function(-3.5))

        assert raw_value == -3.5
        assert value.startswith("-3.50")
        assert value.endswith("€")
        assert style == STYLE_NEG

    def test_zero_is_positive(self, decorated_function):
        value, style, raw_value = parse_money_dict(decorated_function(0))

        assert raw_value == 0
        assert value.startswith("+0.00")
        assert style, STYLE_POS

    def test_whole_number_has_cent_digits(self, decorated_function):
        assert "3.00" in decorated_function(3)["value"]


class MoneyTestCase(TestCase):
    def test_positive_float(self):
        value = format_money(+3.5)

        assert value.startswith("+3.50")
        assert value.endswith("€")

    def test_negative_float(self):
        value = format_money(-3.5)
        assert value.startswith("-3.50")
        assert value.endswith("€")

    def test_zero_is_positive(self):
        value = format_money(0)
        assert value.startswith("+0.00")
