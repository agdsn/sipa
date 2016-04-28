from functools import partial
from unittest import TestCase

import ldap3
from ldap3.core.exceptions import LDAPPasswordIsMandatoryError, LDAPBindError

from sipa.model.hss.ldap import get_ldap_connection, HssLdapConnector, might_be_ldap_dn
from sipa.utils.exceptions import InvalidCredentials, UserNotFound
from tests.prepare import AppInitialized


class HssLdapAppInitialized(AppInitialized):
    LDAP_HOST = 'ldap_hss'
    LDAP_PORT = 389
    LDAP_ADMIN_UID = 'cn=admin,dc=wh12,dc=tu-dresden,dc=de'
    LDAP_USER_BASE = 'ou=users,dc=wh12,dc=tu-dresden,dc=de'
    LDAP_ADMIN_PASSWORD = 'password'
    LDAP_USER_FORMAT_STRING = "uid={user},ou=users,dc=wh12,dc=tu-dresden,dc=de"

    def create_app(self):
        return super().create_app(additional_config={
            'HSS_LDAP_HOST': self.LDAP_HOST,
            'HSS_LDAP_PORT': self.LDAP_PORT,
            'HSS_LDAP_USERDN_FORMAT': self.LDAP_USER_FORMAT_STRING,
            'HSS_LDAP_SYSTEM_BIND': self.LDAP_ADMIN_UID,
            'HSS_LDAP_SYSTEM_PASSWORD': self.LDAP_ADMIN_PASSWORD,
            'HSS_LDAP_SEARCH_BASE': self.LDAP_USER_BASE
        })


class OneLdapUserFixture:
    fixtures = {
        'testlogin': {
            'userPassword': 'notafraidtokickyourballs',
            'cn': 'dontlookatthisattribute',
            'gecos': 'Kleines Gnoemlein',
            'uidNumber': 1000,
            'gidNumber': 100,
            'homeDirectory': '/home/testlogin'
        },
    }


class LdapSetupMixin:
    def setUp(self):
        super().setUp()
        server = ldap3.Server(self.LDAP_HOST, self.LDAP_PORT, use_ssl=False,
                              get_info=ldap3.GET_ALL_INFO)

        with ldap3.Connection(server, auto_bind=True,
                              client_strategy=ldap3.STRATEGY_SYNC,
                              user=self.LDAP_ADMIN_UID,
                              password=self.LDAP_ADMIN_PASSWORD,
                              authentication=ldap3.AUTH_SIMPLE) as conn:
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
                self.conn.delete(entry.entry_get_dn())

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


class TestingHssLdapConnector(HssLdapConnector):
    def __init__(self, *a, **kw):
        old_args = kw.pop('server_args', {})
        server_args = {
            'use_ssl': False,
        }
        server_args.update(**old_args)

        super().__init__(*a, **kw, server_args=server_args)


class HssLdapConnectorTestCase(SimpleLdapTestBase):
    Connector = TestingHssLdapConnector

    def test_connector_works(self):
        with self.Connector(self.username, self.password):
            pass

    def test_wrong_password_raises(self):
        with self.assertRaises(InvalidCredentials), \
             self.Connector(self.username, self.password + 'wrong'):
            pass

    def test_wrong_username_raises(self):
        with self.assertRaises(InvalidCredentials), \
             self.Connector(self.username + 'wrong', self.password):
            pass

    def test_anonymous_bind_raises(self):
        """Test connecting without username and password raises a ValueError"""
        with self.assertRaises(ValueError), self.Connector():
            pass

    def test_system_bind_successful(self):
        try:
            with self.Connector.system_bind():
                pass
        except LDAPBindError:
            self.fail("LDAPBindError thrown instead of successful bind!")

    def test_empty_password_bind_raises(self):
        with self.assertRaises(InvalidCredentials), \
             self.Connector(self.username, ''):
            pass


class HssFetchUserTestCase(SimpleLdapTestBase):
    Connector = TestingHssLdapConnector

    def test_fetch_user(self):
        expected_user_dict = {
            'uid': self.username,
            'name': self.user_dict['gecos'],
        }
        self.assertEqual(self.Connector.fetch_user(self.username),
                         expected_user_dict)

    def test_fetch_invalid_user_raises(self):
        with self.assertRaises(UserNotFound):
            self.Connector.fetch_user(self.username + 'wrong')


class MightBeLdapDNTestCase(TestCase):
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
