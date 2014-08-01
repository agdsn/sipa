#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
Everything used for authentication in Sektionsweb (Usersuite..).
"""
import ldap


LDAP_HOST = "localhost"
LDAP_PORT = 1389
LDAP_SEARCH_BASE = "ou=buzz,o=AG DSN,c=de"


class User(object):
    """User object will be created from LDAP credentials,
    only stored in session.
    """
    def __init__(self, uid, name, hostflag):
        self.uid = uid
        self.name = name
        self.group = self.define_group(hostflag)

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
        """Static method for flask-login user_loader, used before _every_ request.
        """
        user = fetch_user(username)
        return User(user['uid'], user['name'], user['host'])


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
                      ['uid', 'gecos', 'host'])
    l.unbind_s()

    if user:
        user = user.pop()
        userdict = {
            'dn': user[0],
            'uid': user[1]['uid'].pop(),
            'name': user[1]['gecos'].pop(),
            'host': None
        }

        # If the user has a hostflag, put it in the dict
        if 'host' in user[1]:
            userdict['host'] = user[1]['host'].pop()
        return userdict
    return None


def authenticate(username, password):
    """This method checks the user and password combination against LDAP

    Returns the User object if successful, else
    returns -1 if the user was not found and
    -2 if the password was incorrect.
    """
    user = fetch_user(username)
    if not user:
        return -1

    try:
        l = ldap.initialize("ldap://%s:%s" % (LDAP_HOST, LDAP_PORT))
        l.simple_bind_s(user['dn'], password.encode('iso8859-1'))
        l.unbind_s()
        return User.get(username)
    except ldap.INVALID_CREDENTIALS:
        return -2
    except ldap.UNWILLING_TO_PERFORM:
        # Empty password
        return -2