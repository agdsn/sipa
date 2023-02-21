import pytest

from sipa.utils import compare_all_attributes, xor_hashes


class TestCompareAllAttributes:
    class A:
        a = 'foo'
        b = 'bar'
        c = 'baz'

    class B:
        a = 'foo'
        b = 'bar'
        c = 'shizzle'

    class C:
        a = 'foo'
        b = 'shizzle'
        c = 'baz'

    @pytest.mark.parametrize(
        "a, b, args",
        [
            (A, B, ["a", "b"]),
            (A, C, ["a", "c"]),
        ],
    )
    def test_true_comparisons(self, a, b, args):
        assert compare_all_attributes(a, b, args)

    @pytest.mark.parametrize(
        "a, b, args",
        [
            (A, B, ["a", "c"]),
            (A, C, ["a", "b"]),
            (A, B, ["a", "b", "c"]),
            (A, C, ["a", "b", "c"]),
        ],
    )
    def test_false_comparisons(self, a, b, args):
        assert not compare_all_attributes(a, b, args)

    def test_attributes_missing_false(self):
        """Comparing to an object without these attrs should be `False`"""
        try:
            assert not compare_all_attributes(self.A, "", ["a"])
        except AttributeError:
            pytest.fail("AttributeError raised instead of returning `False`")


def test_xor_hashes_correct():
    a = "foo"
    b = "bar"
    c = "baz"
    d = 19
    e = True
    f = None
    expected = hash(a) ^ hash(b) ^ hash(c) ^ hash(d) ^ hash(e) ^ hash(f)
    assert xor_hashes(a, b, c, d, e, f) == expected
