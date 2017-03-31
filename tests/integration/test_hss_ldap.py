import os
from functools import partial
import unittest
from unittest.mock import patch, MagicMock

import ldap3
from ldap3.core.exceptions import LDAPPasswordIsMandatoryError, LDAPBindError

from sipa.model.hss.ldap import (get_ldap_connection, HssLdapConnector as Connector,
                                 might_be_ldap_dn, change_password)
from sipa.model.hss.user import User
from sipa.model.exceptions import InvalidCredentials, UserNotFound
from ..base import AppInitialized
from .test_hss_postgres import HSSOneAccountFixture, HssPgTestBase


class HssLdapAppInitialized(AppInitialized):
    # LDAP_HOST given by env
    LDAP_PORT = 389
    LDAP_ADMIN_UID = 'cn=admin,dc=wh12,dc=tu-dresden,dc=de'
    LDAP_USER_BASE = 'ou=users,dc=wh12,dc=tu-dresden,dc=de'
    # LDAP_ADMIN_PASSWORD given by env
    LDAP_USER_FORMAT_STRING = "uid={user},ou=users,dc=wh12,dc=tu-dresden,dc=de"

    def create_app(self, *a, **kw):
        try:
            self.LDAP_HOST = os.environ['SIPA_TEST_LDAP_HOST']
            self.LDAP_ADMIN_PASSWORD = os.environ['SIPA_TEST_LDAP_ADMIN_PASSWORD']
        except KeyError:
            self.skipTest("SIPA_TEST_LDAP_HOST and "
                          "SIPA_TEST_LDAP_ADMIN_PASSWORD must be set.")
        conf = {
            **kw.pop('additional_config', {}),
            'HSS_LDAP_HOST': self.LDAP_HOST,
            'HSS_LDAP_PORT': self.LDAP_PORT,
            'HSS_LDAP_USERDN_FORMAT': self.LDAP_USER_FORMAT_STRING,
            'HSS_LDAP_SYSTEM_BIND': self.LDAP_ADMIN_UID,
            'HSS_LDAP_SYSTEM_PASSWORD': self.LDAP_ADMIN_PASSWORD,
            'HSS_LDAP_SEARCH_BASE': self.LDAP_USER_BASE,
            'HSS_LDAP_USE_SSL': False,
        }
        return super().create_app(*a, additional_config=conf, **kw)


class OneLdapUserFixture:
    fixtures = {
        'sipatinator': {
            'userPassword': 'notafraidtokickyourballs',
            'cn': 'dontlookatthisattribute',
            'gecos': 'Kleines Gnoemlein',
            'uidNumber': 1000,
            'gidNumber': 100,
            'homeDirectory': '/home/sipatinator'
        },
    }


class LdapSetupMixin:
    def setUp(self):
        super().setUp()
        server = ldap3.Server(self.LDAP_HOST, self.LDAP_PORT, use_ssl=False,
                              get_info=ldap3.ALL)

        with ldap3.Connection(server, auto_bind=True,
                              client_strategy=ldap3.SYNC,
                              user=self.LDAP_ADMIN_UID,
                              password=self.LDAP_ADMIN_PASSWORD,
                              authentication=ldap3.SIMPLE) as conn:
            self.conn = conn

            self.delete_everything_below_base()

            result = conn.add(self.LDAP_USER_BASE, 'organizationalUnit')
            if not result:
                self.add_failed(self.LDAP_USER_BASE)

            for uid, data in self.fixtures.items():
                data = data.copy()
                self.create_user_from_fixture(uid)

    def delete_everything_below_base(self):
        """Delete the LDAP_USER_BASE dn and every entry below it."""
        self.conn.search(self.LDAP_USER_BASE, '(objectclass=*)')
        if self.conn.entries:
            for entry in self.conn.entries:
                self.conn.delete(entry.entry_dn)

        self.conn.delete(self.LDAP_USER_BASE)

    def create_user_from_fixture(self, uid):
        """Create a user with uid `uid` from the fixtures

        This sets the password from 'userPassword' after the add.
        """
        user_dn = self.LDAP_USER_FORMAT_STRING.format(user=uid)
        data = self.fixtures[uid].copy()

        password = data.pop('userPassword')
        result = self.conn.add(user_dn, ['account', 'posixAccount'], data)
        if not result:
            self.add_failed(user_dn, description=self.conn.result)

        result = self.conn.modify(
            user_dn,
            {'userPassword': (ldap3.MODIFY_REPLACE, [password])},
        )
        if not result:
            self.add_failed(user_dn, description=self.conn.result['message'])

    @staticmethod
    def add_failed(dn, description=None):
        raise RuntimeError("Couldn't add entry {dn} to LDAP"
                           " – „{desc}“!".format(dn=dn,
                                                 desc=description))


class SimpleLdapTestBase(LdapSetupMixin, OneLdapUserFixture, HssLdapAppInitialized):
    """A TestBase providing an initialized LDAP and an initialized App."""
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.username = next(iter(self.fixtures.keys()))
        self.password = self.fixtures[self.username]['userPassword']
        self.user_dict = self.fixtures[self.username]


class GetLdapConnectionTestCase(SimpleLdapTestBase):
    """Tests for the `get_ldap_connecton` function.

    May be deleted, just as said function.
    """
    ldap_connect = partial(get_ldap_connection, use_ssl=False)

    def test_ldap_password_required(self):
        with self.assertRaises(LDAPPasswordIsMandatoryError):
            self.ldap_connect(self.username, '')

    def test_ldap_wrong_password(self):
        with self.assertRaises(LDAPBindError):
            self.ldap_connect(self.username, self.password + 'wrong')

    def test_ldap_wrong_username(self):
        with self.assertRaises(LDAPBindError):
            self.ldap_connect(self.username + 'wrong', self.password)

    def test_ldap_successful_bind(self):
        try:
            self.ldap_connect(self.username, self.password)
        except LDAPBindError:
            self.fail("LDAPBindError thrown instead of successful bind!")


class HssLdapConnectorTestCase(SimpleLdapTestBase):
    def test_connector_works(self):
        with Connector(self.username, self.password):
            pass

    def test_wrong_password_raises(self):
        with self.assertRaises(InvalidCredentials), \
             Connector(self.username, self.password + 'wrong'):
            pass

    def test_wrong_username_raises(self):
        with self.assertRaises(InvalidCredentials), \
             Connector(self.username + 'wrong', self.password):
            pass

    def test_anonymous_bind_raises(self):
        """Test connecting without username and password raises a ValueError"""
        with self.assertRaises(ValueError), Connector():
            pass

    def test_system_bind_successful(self):
        try:
            with Connector.system_bind():
                pass
        except LDAPBindError:
            self.fail("LDAPBindError thrown instead of successful bind!")

    def test_empty_password_bind_raises(self):
        with self.assertRaises(InvalidCredentials), \
             Connector(self.username, ''):
            pass


class HssFetchUserTestCase(SimpleLdapTestBase):
    def test_fetch_user(self):
        expected_user_dict = {
            'uid': self.username,
            'name': self.user_dict['gecos'],
        }
        self.assertEqual(Connector.fetch_user(self.username),
                         expected_user_dict)

    def test_fetch_invalid_user_raises(self):
        with self.assertRaises(UserNotFound):
            Connector.fetch_user(self.username + 'wrong')

    def test_fetch_user_already_bound(self):
        class MockedConnector(Connector):
            """A connector mock listing how often `system_bind` gets
            """
            _call_args = []

            def search(self, *a, **kw):
                self._call_args.append((a, kw))
                return super().search(*a, **kw)

        with patch('sipa.model.hss.ldap.HssLdapConnector') as class_mock, \
                MockedConnector.system_bind() as conn:
            previous_searches = len(MockedConnector._call_args)
            Connector.fetch_user(self.username, connection=conn)
            # We expect a search to have been performed exactly once
            self.assertEqual(len(MockedConnector._call_args), previous_searches + 1)

        # The original class (class_mock) shouldn't have been used
        self.assertFalse(class_mock.fetch_user.called)
        self.assertFalse(class_mock.search.called)
        self.assertFalse(class_mock.system_bind.called)


class MightBeLdapDNTestCase(unittest.TestCase):
    def test_ldap_dn_checker_samples(self):
        samples = [
            ('cn=admin,dc=wh12,dc=tu-dresden,dc=de', True),
            ('ou=users,dc=wh12,dc=tu-dresden,dc=de', True),
            ("uid={user},ou=users,dc=wh12,dc=tu-dresden,dc=de", True),
            ('password', False),
            ('dn=foo,cn=', False),
        ]
        for sample, value in samples:
            with self.subTest(sample=sample):
                if value:
                    self.assertTrue(might_be_ldap_dn(sample))
                else:
                    self.assertFalse(might_be_ldap_dn(sample))


class SimpleLdapUserTestBase(SimpleLdapTestBase):
    def assert_user_data_passed(self, user, login, name):
        # Everything in here is irrelevant, since handled by sql.
        # This method stays in here though to maintain the class
        # structure, since it is planned to use this for the wu LDAP
        # as well.
        pass


class AuthenticateTestCase(SimpleLdapUserTestBase):
    def test_invalid_password_raises(self):
        with self.assertRaises(InvalidCredentials):
            User.authenticate(self.username, self.password + 'wrong')

    def test_invalid_username_raises(self):
        with self.assertRaises(InvalidCredentials):
            User.authenticate(self.username + 'wrong', self.password)


class SimpleHssPgTestBase(HSSOneAccountFixture, HssPgTestBase):
    pass


class HssLdapPasswordChangeableTestCase(SimpleLdapUserTestBase):
    def setUp(self):
        super().setUp()

    def test_password_changeable(self):
        try:
            change_password(self.username, self.password, 'test')
        except NotImplementedError:
            self.fail("Not Implemented!")


@patch.object(User, 'get', new=MagicMock())
class HssLdapPasswordChangeTestCase(SimpleLdapUserTestBase):
    def setUp(self):
        super().setUp()
        self.new_password = self.password + 'new'
        change_password(self.username, self.password, self.new_password)

    def test_auth_fail_with_old_password(self):
        with self.assertRaises(InvalidCredentials):
            User.authenticate(self.username, self.password)

    def test_auth_succeeds_with_new_password(self):
        try:
            User.authenticate(self.username, self.new_password)
        except InvalidCredentials:
            self.fail("Authentication failed with new password")
