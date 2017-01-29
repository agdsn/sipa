import logging
from abc import ABCMeta, abstractmethod

import ldap3
from flask import current_app

from sipa.model.exceptions import InvalidCredentials, UserNotFound

logger = logging.getLogger(__name__)


def get_ldap_connection(user, password, use_ssl=True):
    """Test method to establish an ldap connection"""
    host = current_app.config['HSS_LDAP_HOST']
    port = current_app.config['HSS_LDAP_PORT']
    server = ldap3.Server(host, port, use_ssl=use_ssl,
                          get_info=ldap3.GET_ALL_INFO)
    userdn_format = current_app.config['HSS_LDAP_USERDN_FORMAT']

    user_dn = (user if "dc=wh12,dc=tu-dresden,dc=de" in user
               else userdn_format.format(user=user))

    return ldap3.Connection(server, auto_bind=True,
                            client_strategy=ldap3.STRATEGY_SYNC,
                            user=user_dn, password=password,
                            authentication=ldap3.AUTH_SIMPLE)


class BaseLdapConnector(ldap3.Connection, metaclass=ABCMeta):
    """This class is a wrapper for an ldap3 Connection."""

    def __init__(self, username=None, password=None,
                 server_args={}, connect_args={}):
        """Return an `ldap3.Connection` object.

        The bind uses what `type(self).config` provides as data.

        Can be used as ContextManager as well.

        :raises: ValueError if not password and not username
        :raises: InvalidCredentials if not password
        :raises: InvalidCredentials if bind sais so
        """
        self.username = username
        self.password = password

        if not password and not username:
            raise ValueError("Anonymous Bind not allowed!")
        elif not password and username:
            raise InvalidCredentials("Bind attempted with username without a password")
        elif not might_be_ldap_dn(username):
            # look username up only if `username` isn't remotely a dn
            bind_user, bind_password = self.get_bind_credentials(username, password)
        else:
            bind_user, bind_password = username, password

        self.server = ldap3.Server(
            host=self.config['host'],
            port=self.config['port'],
            use_ssl=self.config.get('use_ssl', False),
            **dict(self.DEFAULT_SERVER_ARGS, **server_args),
            # wu stuff:
            # get_info=ldap3.SCHEMA,
            # tls=None,  # accept any certificate
            # connect_timeout=5,
        )

        try:
            super().__init__(
                server=self.server,
                user=bind_user,
                password=bind_password,
                raise_exceptions=True,
                check_names=True,
                **dict(self.DEFAULT_CONNECT_ARGS, **connect_args),
                # wu stuff:
                # check_names=True,
                # raise_exceptions=True,
                # auto_bind=ldap3.AUTO_BIND_TLS_BEFORE_BIND,
            )
        except ldap3.LDAPInvalidCredentialsResult:
            raise InvalidCredentials()

    @classmethod
    def system_bind(cls):
        username, password = cls.get_system_bind_credentials()

        return cls(username, password)

    @classmethod
    def fetch_user(cls, username, connection=None):
        """Fetch `username` from LDAP, return a dict.

        :param: username the username to be used in cls.__init__()
        :returns: a dict {'uid': '', 'name': ''} containing the user data
        """
        def _search(conn):
            conn.search(
                search_base=cls.config['search_base'],
                search_filter='(uid={user})'.format(user=username),
                attributes=['uid', 'gecos', 'mail'],
            )

        if connection is not None:
            _search(connection)
            response = connection.response
        else:
            with cls.system_bind() as conn:
                _search(conn)
                response = conn.response

        if response:
            user = response.pop()
            attrs = user['attributes']
            return {
                'uid': attrs['uid'].pop(),
                'name': attrs['gecos'],
            }

        if response:
            logger.warning("Ldapsearch for uid=%s returned more than one result",
                           username)
        raise UserNotFound("User {uid} not found in ldap search"
                           .format(uid=username))

    @property
    def dn(self):
        """who_am_i returns a string of the form 'dn:<full dn>',
        but we are only interested in the <full dn> part.
        """
        return self.extend.standard.who_am_i().split(':', maxsplit=1)[1]

    @property
    @abstractmethod
    def config(self):
        raise NotImplementedError

    @classmethod
    @abstractmethod
    def get_bind_credentials(cls):
        raise NotImplementedError

    @classmethod
    @abstractmethod
    def get_system_bind_credentials(cls):
        raise NotImplementedError

    DEFAULT_CONNECT_ARGS = {}
    DEFAULT_SERVER_ARGS = {}


class HssConfigProxy:
    def __get__(self, obj, objtype):
        try:
            conf = current_app.config
        except RuntimeError:
            return {}
        return {
            'host': conf['HSS_LDAP_HOST'],
            'port': int(conf['HSS_LDAP_PORT']),
            'userdn_format': conf['HSS_LDAP_USERDN_FORMAT'],
            'system_bind': conf['HSS_LDAP_SYSTEM_BIND'],
            'system_password': conf['HSS_LDAP_SYSTEM_PASSWORD'],
            'search_base': conf['HSS_LDAP_SEARCH_BASE'],
            'use_ssl': conf.get('HSS_LDAP_USE_SSL', True),
        }


class HssLdapConnector(BaseLdapConnector):
    config = HssConfigProxy()

    DEFAULT_SERVER_ARGS = {
        'get_info': ldap3.GET_ALL_INFO,
    }
    DEFAULT_CONNECT_ARGS = {
        'auto_bind': True,
        'client_strategy': ldap3.STRATEGY_SYNC,
        'authentication': ldap3.AUTH_SIMPLE,
    }

    @classmethod
    def get_system_bind_credentials(cls):
        return cls.config['system_bind'], cls.config['system_password']

    @classmethod
    def get_bind_credentials(cls, username, password):
        """Return the according userdn of `username` and the given password"""
        return cls.config['userdn_format'].format(user=username), password


def search_in_group():
    """
    (with Conn(username) as l:)
    """
    raise NotImplementedError


def change_email():
    """
    (with Conn(username, pw) as l:)
    """
    raise NotImplementedError


def change_password(username, old, new, Connector=HssLdapConnector):
    with Connector(username, old) as l:
        l.extend.standard.modify_password(user=l.dn,
                                          old_password=old,
                                          new_password=new)


def might_be_ldap_dn(string):
    """Very rudimentary tester whether something looks like an LDAP dn.

    Basically, this assumes that the string is of the form "a=b,c=d,…"
    """
    return all(
        (len(node.split('=')) == 2 and
         all(atom for atom in node.split('=')))
        for node in string.split(',')
    )
