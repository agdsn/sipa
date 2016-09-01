from unittest import TestCase

from sipa.model.misc import compare_all_attributes, xor_hashes


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
            self.assertTrue(compare_all_attributes(*args))

    def test_false_comparisons(self):
        arglist = [
            (self.A, self.B, ['a', 'c']),
            (self.A, self.C, ['a', 'b']),
            (self.A, self.B, ['a', 'b', 'c']),
            (self.A, self.C, ['a', 'b', 'c']),
        ]
        for args in arglist:
            self.assertFalse(compare_all_attributes(*args))


class XorHashesTestCase(TestCase):
    def test_xor_hashes_correct(self):
        a = "foo"
        b = "bar"
        c = "baz"
        d = 19
        e = True
        f = None
        expected = hash(a) ^ hash(b) ^ hash(c) ^ hash(d) ^ hash(e) ^ hash(f)
        self.assertEqual(xor_hashes(a, b, c, d, e, f), expected)
