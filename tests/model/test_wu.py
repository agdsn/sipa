from itertools import permutations
from unittest import TestCase
from unittest.mock import MagicMock, patch

from sipa.model.wu.user import User, UserDB


class UserTestCase(TestCase):
    ldap_search_mock = MagicMock(return_value=False)
    userdb_mock = MagicMock()

    def setUp(self):
        self.ldap_search_mock.reset_mock()
        self.userdb_mock.reset_mock()

    @patch('sipa.model.wu.user.search_in_group', ldap_search_mock)
    @patch('sipa.model.wu.user.UserDB', userdb_mock)
    def test_explicit_init(self):
        sample_user = {
            'uid': 'testnutzer',
            'name': "Test Nutzer",
            'mail': "test@nutzer.de",
        }

        user = User(
            uid=sample_user['uid'],
            name=sample_user['name'],
            mail=sample_user['mail'],
        )
        self.assertEqual(user.name, sample_user['name'])
        self.assertEqual(user.group, 'passive')
        self.assertEqual(user.mail.value, sample_user['mail'])
        assert self.userdb_mock.called

    @patch('sipa.model.wu.user.UserDB', userdb_mock)
    def test_define_group(self):
        sample_users = {
            # <uid>: <resulting_group>
            'uid1': 'passive',
            'uid2': 'active',
            'uid3': 'exactive',
        }

        def fake_search_in_group(uid, group_string):
            if group_string == "Aktiv":
                return sample_users[uid] == 'active'
            elif group_string == "Exaktiv":
                return sample_users[uid] == 'exactive'
            else:
                raise NotImplementedError

        for uid, group in sample_users.items():
            with patch('sipa.model.wu.user.search_in_group',
                       fake_search_in_group):
                user = User(uid=uid, name="", mail="")
                self.assertEqual(user.define_group(), group)
        return


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
