from unittest import TestCase

from sipa.utils import compare_all_attributes, xor_hashes


class CompareAllAttributesTestCase(TestCase):
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

    def test_true_comparisons(self):
        arglist = [
            (self.A, self.B, ['a', 'b']),
            (self.A, self.C, ['a', 'c']),
        ]
        for args in arglist:
            assert compare_all_attributes(*args)

    def test_false_comparisons(self):
        arglist = [
            (self.A, self.B, ['a', 'c']),
            (self.A, self.C, ['a', 'b']),
            (self.A, self.B, ['a', 'b', 'c']),
            (self.A, self.C, ['a', 'b', 'c']),
        ]
        for args in arglist:
            assert not compare_all_attributes(*args)

    def test_attributes_missing_false(self):
        """Comparing to an object without these attrs should be `False`"""
        try:
            assert not compare_all_attributes(self.A, "", ["a"])
        except AttributeError:
            self.fail("AttributeError raised instead of returning `False`")


class XorHashesTestCase(TestCase):
    def test_xor_hashes_correct(self):
        a = "foo"
        b = "bar"
        c = "baz"
        d = 19
        e = True
        f = None
        expected = hash(a) ^ hash(b) ^ hash(c) ^ hash(d) ^ hash(e) ^ hash(f)
        assert xor_hashes(a, b, c, d, e, f) == expected
