from itertools import permutations
from unittest import TestCase

from sipa.model.wu.user import UserDB


class UserDBTestCase(TestCase):
    def test_ipmask_validity_checker(self):
        valid_elements = ['1', '125', '255', '%']
        valid = permutations(valid_elements, 4)

        # probably not the most elegant choices, but that should do the trick
        invalid_elements = ['%%', '%%%', '1%1', '1%%1']
        invalid = []
        for p in valid:
            p = list(p)
            for inv in invalid_elements:
                invalid += [p[:i] + [inv] + p[i+1:] for i in range(4)]

        for ip_tuple in invalid:
            with self.assertRaises(ValueError):
                UserDB.test_ipmask_validity(".".join(ip_tuple))

        for ip_tuple in valid:
            with self.assertNotRaises(ValueError):
                UserDB.test_ipmask_validity(".".join(ip_tuple))
