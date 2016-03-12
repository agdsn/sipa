from unittest import TestCase

from sipa.units import reduce_unit


class UnitsTestCase(TestCase):
    bases = [100, 1000, 1024]

    def test_reduce_units(self):
        """Test `reduce_unit` with some sample data"""
        for base in self.bases:
            with self.subTest(base=base):
                example = [(1, 0), (base / 2, 0), (base, 1), (2 * base, 1), (base**2, 2)]
                for num, expected_division in example:
                    with self.subTest(num=num):
                        self.assertEqual(reduce_unit(num, base=base), expected_division)
