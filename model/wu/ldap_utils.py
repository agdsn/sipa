# -*- coding: utf-8 -*-
from flask.ext.login import current_user
from flask.globals import current_app
import ldap3
from werkzeug.local import LocalProxy

from sipa.utils.exceptions import UserNotFound, PasswordInvalid, \
    LDAPConnectionError

import logging
logger = logging.getLogger(__name__)


def init_ldap(app):
    app.extensions['ldap'] = {
        'host': app.config['WU_LDAP_HOST'],
        'port': int(app.config['WU_LDAP_PORT']),
        'user': app.config['WU_LDAP_SEARCH_USER'],
        'password': app.config['WU_LDAP_SEARCH_PASSWORD'],
        'search_user_base': app.config['WU_LDAP_SEARCH_USER_BASE'],
        'search_group_base': app.config['WU_LDAP_SEARCH_GROUP_BASE']
    }


CONF = LocalProxy(lambda: current_app.extensions['ldap'])


class LdapConnector(ldap3.Connection):
    """This class is a wrapper for all LDAP connections.

    * If you pass it a username only, it will use an anonymous bind.
    * If you pass it a username and password, it will try to bind to LDAP with
        the users credentials.
    """

    def __init__(self, username, password=None):
        self.username = username
        self.password = password

        if not password:
            # anonymous or system-user bind
            bind_user = CONF['user']
            bind_password = CONF['password']
        else:
            # bind with user
            bind_user = "uid={},{}".format(self.username,
                                           CONF['search_user_base'])
            bind_password = self.password

        self.server = ldap3.Server(host=CONF['host'],
                                   port=CONF['port'],
                                   get_info=ldap3.SCHEMA,
                                   tls=None,  # accept any certificate
                                   connect_timeout=5)
        try:
            super().__init__(server=self.server,
                             user=bind_user,
                             password=bind_password,
                             check_names=True,
                             raise_exceptions=True,
                             auto_bind=ldap3.AUTO_BIND_TLS_BEFORE_BIND)
        except ldap3.LDAPInvalidCredentialsResult:
            raise PasswordInvalid
        except ldap3.LDAPUnwillingToPerformResult:
            # Empty password, treat as invalid
            raise PasswordInvalid
        except ldap3.LDAPInsufficientAccessRightsResult:
            raise LDAPConnectionError

    @staticmethod
    def fetch_user(username):
        """Fetch a user by his username from LDAP.
        This method does not check the authenticity of the requested user!

        Returns a formatted dict with the LDAP dn, username and real name.
        If the username was not found, returns None.
        """
        with LdapConnector(None) as l:
            l.search(search_base=CONF['search_user_base'],
                     search_scope=ldap3.SUBTREE,
                     search_filter="(uid={})".format(username),
                     attributes=['uid', 'gecos', 'mail'])

        if l.response:
            user = l.response.pop()
            attributes = user['attributes']
            userdict = {
                'dn': user['dn'],
                'uid': attributes['uid'].pop(),
                'name': attributes['gecos'],
                'mail': None
            }

            # If the user has mail set, put it in the dict
            if 'mail' in attributes:
                userdict['mail'] = attributes['mail'].pop()

            return userdict
        return None

    def get_dn(self):
        """who_am_i returns a string of the form 'dn:<full dn>',
        but we are only interested in the <full dn> part.
        """
        return self.extend.standard.who_am_i()[3:]


def search_in_group(username, group):
    """Searches for the given user in the given LDAP group memberuid list.
    This replaces the previous usage of hostflags.
    """
    with LdapConnector(username) as l:
        l.search(search_base=CONF['search_group_base'],
                 search_scope=ldap3.SUBTREE,
                 search_filter=("(&(objectClass=groupOfNames)"
                                "(cn={})"
                                "(memberuid={}))").format(group, username))

        return bool(l.response)


def change_email(username, password, email):
    """Change a user's email

    Uses ldap3.MODIFY_REPLACE in any case, it should add the
    attribute, if it is not yet set up (replace removes all
    attributes of the given kind and puts the new one in place)
    """
    try:
        with LdapConnector(username, password) as l:
            l.modify(dn=l.get_dn(),
                     changes={'mail': [(ldap3.MODIFY_REPLACE, [email])]})
    except ldap3.LDAPNoSuchObjectResult as e:
        logger.error('LDAP user not found when attempting '
                     'change of mail address',
                     extra={'data': {'exception_args': e.args},
                            'stack': True})
        raise UserNotFound from e
    except PasswordInvalid:
        logger.info('Wrong password provided when attempting '
                    'change of mail address')
        raise
    except ldap3.LDAPInsufficientAccessRightsResult:
        logger.error('Not sufficient rights to change the mail address')
        raise LDAPConnectionError
    else:
        logger.info('Mail address successfully changed to "%s"', email)


def change_password(username, old, new):
    with LdapConnector(username, old) as l:
        l.extend.standard.modify_password(user=l.get_dn(),
                                          old_password=old,
                                          new_password=new)


def get_current_uid():
    if not current_user.is_authenticated:
        raise AttributeError("current user not authenticated")
    return current_user.uid
