from itertools import permutations
from unittest import TestCase
from unittest.mock import MagicMock, patch

from flask_login import AnonymousUserMixin

from sipa.model.wu.user import User, UserDB
from sipa.model.wu.ldap_utils import UserNotFound, PasswordInvalid


class UserNoDBTestCase(TestCase):
    userdb_mock = MagicMock()

    def setUp(self):
        self.userdb_mock.reset_mock()

    def assert_userdata_passed(self, user, user_dict):
        self.assertEqual(user.group, user_dict.get('group', 'passive'))
        self.assertEqual(user.mail, user_dict['mail'])

    @staticmethod
    def patch_user_group(user_dict):
        return patch(
            'sipa.model.wu.user.User.define_group',
            MagicMock(return_value=user_dict.get('group', 'passive'))
        )

    @patch('sipa.model.wu.user.UserDB', userdb_mock)
    def test_explicit_init(self):
        sample_user = {
            'uid': 'testnutzer',
            'mail': "test@nutzer.de",
            'group': 'passive',
        }

        with self.patch_user_group(sample_user):
            user = User(
                uid=sample_user['uid'],
                mail=sample_user['mail'],
            )

        self.assert_userdata_passed(user, sample_user)
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
                user = User(uid=uid, mail="")
                with self.subTest(user=user):
                    self.assertEqual(user.define_group(), group)
        return

    @patch('sipa.model.wu.user.UserDB', userdb_mock)
    def test_get_constructor(self):
        test_users = [
            {'uid': "uid1", 'mail': "test@foo.bar"},
            {'uid': "uid2", 'mail': "test@foo.baz"},
            {'uid': "uid3", 'mail': "shizzle@damn.onion"},
        ]

        for test_user in test_users:
            with self.subTest(user=test_user):

                with self.patch_user_group(test_user), \
                     patch('sipa.model.wu.user.LdapConnector') as LdapConnectorMock:
                    LdapConnectorMock.fetch_user.return_value = test_user

                    user = User.get(test_user['uid'])
                    assert LdapConnectorMock.fetch_user.called

                self.assertIsInstance(user, User)
                self.assert_userdata_passed(user, test_user)

    def test_get_constructor_returns_anonymous(self):
        with patch('sipa.model.wu.user.LdapConnector') as LdapConnectorMock:
            LdapConnectorMock.fetch_user.return_value = None
            user = User.authenticate("foo", "bar")
        self.assertIsInstance(user, AnonymousUserMixin)

    def test_authentication_passing(self):
        """Test correct instanciation behaviour of `User.authenticate`.

        It is checked whether the ldap is called correctly and
        instanciation is done using `User.get`.
        """
        sample_users = [
            ("uid", "pass"),
            ("foo", "bar"),
            ("baz", None),
        ]
        for uid, password in sample_users:
            with patch('sipa.model.wu.user.LdapConnector') as ldap_mock, \
                 patch('sipa.model.wu.user.User.get') as get_mock, \
                 self.subTest(uid=uid, password=password):

                User.authenticate(uid, password)

                self.assertEqual(ldap_mock.call_args[0], (uid, password))
                self.assertEqual(get_mock.call_args[0], (uid,))

    def test_authentication_reraise_unknown_user(self):
        """Test that certain exceptions are re-raised by `User.authenticate`.

        Objects of interest are `UserNotFound`, `PasswordInvalid`.
        """
        for exception_class in [UserNotFound, PasswordInvalid]:
            def raise_exception(): raise exception_class()
            with patch('sipa.model.wu.user.LdapConnector') as ldap_mock, \
                    self.subTest(exception_class=exception_class):

                ldap_mock().__enter__.side_effect = raise_exception
                with self.assertRaises(exception_class):
                    User.authenticate(username=None, password=None)


class IPMaskValidityChecker(TestCase):
    """Tests concerning the validation of ip masks passed to the
    `UserDB`
    """

    def setUp(self):
        valid_elements = ['1', '125', '255', '%']
        self.valid = list(permutations(valid_elements, 4))

        # probably not the most elegant choices, but that should do the trick
        invalid_elements = ['%%', '%%%', '1%1', '1%%1']
        self.invalid = []
        for p in self.valid:
            p = list(p)
            for inv in invalid_elements:
                self.invalid += [p[:i] + [inv] + p[i+1:] for i in range(4)]

    def test_invalid_ips_raise(self):
        """Test that passing invalid ip masks raises a `ValueError`"""
        for ip_tuple in self.invalid:
            with self.subTest(ip_tuple=ip_tuple):
                with self.assertRaises(ValueError):
                    UserDB.test_ipmask_validity(".".join(ip_tuple))

    def test_valid_ips_pass(self):
        """Test that passing valid ip masks works"""
        for ip_tuple in self.valid:
            with self.subTest(ip_tuple=ip_tuple):
                try:
                    UserDB.test_ipmask_validity(".".join(ip_tuple))
                except ValueError:
                    self.fail("`test_ipmask_validity` raised ValueError "
                              "on correct ip '{}'".format(".".join(ip_tuple)))
