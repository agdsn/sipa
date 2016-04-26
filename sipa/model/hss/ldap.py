from abc import ABCMeta, abstractmethod

import ldap3

from flask import current_app


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

        The bind uses what `{type}.`

        Can be used as ContextManager as well.
        """.format(type=type(self))
        self.username = username
        self.password = password

        if not password and not username:
            # Attempt an anonymous bind, don't use the username
            bind_user, bind_password = self.get_anonymous_bind_credentials()
        elif not password and username:
            raise ValueError("Bind attempted with username without a password")
        else:
            bind_user, bind_password = self.get_bind_credentials(username, password)

        self.server = ldap3.Server(
            host=self.config['host'],
            port=self.config['port'],
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
                **dict(self.DEFAULT_CONNECT_ARGS, **connect_args),
                # wu stuff:
                # check_names=True,
                # raise_exceptions=True,
                # auto_bind=ldap3.AUTO_BIND_TLS_BEFORE_BIND,
            )
        except ldap3.LDAPBindError:
            raise NotImplementedError

    @staticmethod
    def fetch_user(self, username):
        raise NotImplementedError

    @property
    @abstractmethod
    def config(self):
        raise NotImplementedError

    @abstractmethod
    def get_bind_credentials(self):
        raise NotImplementedError

    @abstractmethod
    def get_anonymous_bind_credentials(self):
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
            # 'user': conf['WU_LDAP_SEARCH_USER'],
            'password': conf['WU_LDAP_SEARCH_PASSWORD'],
            # 'search_user_base': conf['HSS_SEARCH_USER_BASE'],
            # 'search_group_base': conf['WU_LDAP_SEARCH_GROUP_BASE'],
            'userdn_format': current_app.config['HSS_LDAP_USERDN_FORMAT'],
        }


class HssLdapConnector(BaseLdapConnector):
    config = HssConfigProxy()

    DEFAULT_SERVER_ARGS = {
        'use_ssl': True,
        'get_info': ldap3.GET_ALL_INFO,
    }
    DEFAULT_CONNECT_ARGS = {
        'auto_bind': True,
        'client_strategy': ldap3.STRATEGY_SYNC,
        'authentication': ldap3.AUTH_SIMPLE,
    }

    def get_anonymous_bind_credentials(self):
        raise ValueError("The Hss Connector doesn't support Anonymous Binding")

    def get_bind_credentials(self, username, password):
        """Return the according userdn of `username` and the given password"""
        return self.config['userdn_format'].format(user=username), password


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


def change_password():
    """
    (with Conn(username, pw) as l:)
    """
    raise NotImplementedError
