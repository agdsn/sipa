#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
Everything used for authentication in Sektionsweb (Usersuite..).
"""

import ldap
from ldap.ldapobject import SimpleLDAPObject

from config import LDAP_HOST, LDAP_PORT, LDAP_SEARCH_BASE


class User(object):
    """User object will be created from LDAP credentials,
    only stored in session.
    """
    def __init__(self, uid, name, hostflag, mail):
        self.uid = uid
        self.name = name
        self.group = self.define_group(hostflag)
        self.mail = mail

    def __repr__(self):
        return "User<%s,%s,%s>" % (self.uid, self.name, self.group)

    def is_active(self):
        """Needed for flask-login
        """
        return True

    def is_authenticated(self):
        """Needed for flask-login
        """
        return True

    def is_anonymous(self):
        """Needed for flask-login
        """
        return False

    def get_id(self):
        """Needed for flask-login
        """
        return self.uid

    def define_group(self, hostflag):
        """Define a simple user group from the host flag
        """
        if hostflag == 'atlantis':
            return 'active'
        elif hostflag == 'exorg':
            return 'exactive'
        else:
            return 'passive'

    @staticmethod
    def get(username):
        """Static method for flask-login user_loader,
        used before _every_ request.
        """
        user = LdapConnector.fetch_user(username)
        return User(user['uid'], user['name'], user['host'], user['mail'])


class LdapConnector(object):
    """This class is a wrapper for all LDAP connections.

    * If you pass it a username only, it will use an anonymous bind.
    * If you pass it a username and password, it will try to bind to LDAP with
        the users credentials.

    Return codes are
    * -1: User not found
    * -2: Wrong password
    * -3: Insufficient rights to perform LDAP operation
    """
    def __init__(self, username, password=None):
        self.username = username
        self.password = password
        self.l = None

    def __enter__(self):
        try:
            user = self.fetch_user(self.username)
            if not user:
                return -1
            self.l = ldap.initialize("ldap://%s:%s" % (LDAP_HOST, LDAP_PORT))
            self.l.protocol_version = ldap.VERSION3

            if self.password:
                self.l.simple_bind_s(user['dn'], self.password.encode('iso8859-1'))

            return self.l
        except ldap.INVALID_CREDENTIALS:
            return -2
        except ldap.UNWILLING_TO_PERFORM:
            # Empty password
            return -2
        except ldap.INSUFFICIENT_ACCESS:
            return -3

    def __exit__(self, exc_type, exc_val, exc_tb):
        if isinstance(self.l, SimpleLDAPObject):
            self.l.unbind_s()

    @staticmethod
    def fetch_user(username):
        """Fetch a user by his username from LDAP.
        This method does not check the authenticity of the requested user!

        Returns a formatted dict with the LDAP dn, username, real name and host.
        If the username was not found, returns None.
        """
        l = ldap.initialize("ldap://%s:%s" % (LDAP_HOST, LDAP_PORT))
        user = l.search_s(LDAP_SEARCH_BASE,
                          ldap.SCOPE_SUBTREE,
                          "(uid=%s)" % username,
                          ['uid', 'gecos', 'host', 'mail'])
        l.unbind_s()

        if user:
            user = user.pop()
            userdict = {
                'dn': user[0],
                'uid': user[1]['uid'].pop(),
                'name': user[1]['gecos'].pop(),
                'host': None,
                'mail': None
            }

            # If the user has a hostflag or mail set, put it in the dict
            if 'host' in user[1]:
                userdict['host'] = user[1]['host'].pop()
            if 'mail' in user[1]:
                userdict['mail'] = user[1]['mail'].pop()

            return userdict
        return None


def get_dn(l):
    """l.whoami_s returns a string 'dn:<full dn>',
    but we mostly need the <full dn> part only.
    """
    return l.whoami_s()[3:]


def authenticate(username, password):
    """This method checks the user and password combination against LDAP

    Returns the User object if successful, else
    returns -1 if the user was not found and
    -2 if the password was incorrect.
    """
    with LdapConnector(username, password) as l:
        if isinstance(l, int):
            return l
        return User.get(username)


def change_password(username, old, new):
    """Change a user's password from old to new
    """
    with LdapConnector(username, old) as l:
        if isinstance(l, int):
            return l
        l.passwd_s(get_dn(l), old.encode('iso8859-1'), new.encode('iso8859-1'))
        return 1


def change_email(username, password, email):
    """Change a user's email

    Uses ldap.MOD_REPLACE in any case, it should add the
    attribute, if it is not yet set up (replace removes all
    attributes of the given kind and puts the new one in place)
    """
    with LdapConnector(username, password) as l:
        if isinstance(l, int):
            return l

        # The attribute to modify. 'email' is casted to a string, because
        # passing a unicode object will raise a TypeError
        attr = [(ldap.MOD_REPLACE, 'mail', str(email))]
        l.modify_s(get_dn(l), attr)
        return 1
