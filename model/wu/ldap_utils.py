from flask.ext.login import current_user
from flask.globals import current_app
import ldap
from ldap.ldapobject import SimpleLDAPObject
from werkzeug.local import LocalProxy
from sipa import logger
from sipa.utils.exceptions import UserNotFound, PasswordInvalid, \
    LDAPConnectionError


def init_ldap(app):
    app.extensions['ldap'] = {
        'host': app.config['LDAP_HOST'],
        'port': app.config['LDAP_PORT'],
        'search_base': app.config['LDAP_SEARCH_BASE']
    }

CONF = LocalProxy(lambda: current_app.extensions['ldap'])


class LdapConnector(object):
    """This class is a wrapper for all LDAP connections.

    * If you pass it a username only, it will use an anonymous bind.
    * If you pass it a username and password, it will try to bind to LDAP with
        the users credentials.
    """

    def __init__(self, username, password=None):
        self.username = username
        self.password = password
        self.l = None

    def __enter__(self):
        try:
            user = self.fetch_user(self.username)
            if not user:
                raise UserNotFound
            self.l = ldap.initialize("ldap://{}:{}".format(CONF['host'],
                                                           CONF['port']))
            self.l.protocol_version = ldap.VERSION3

            if self.password:
                self.l.simple_bind_s(user['dn'],
                                     self.password.encode('iso8859-1'))

            return self.l
        except ldap.INVALID_CREDENTIALS:
            raise PasswordInvalid
        except ldap.UNWILLING_TO_PERFORM:
            # Empty password
            raise PasswordInvalid
        except ldap.INSUFFICIENT_ACCESS:
            raise LDAPConnectionError

    def __exit__(self, exc_type, exc_val, exc_tb):
        if isinstance(self.l, SimpleLDAPObject):
            self.l.unbind_s()

    @staticmethod
    def fetch_user(username):
        """Fetch a user by his username from LDAP.
        This method does not check the authenticity of the requested user!

        Returns a formatted dict with the LDAP dn, username and real name.
        If the username was not found, returns None.
        """
        l = ldap.initialize("ldap://{}:{}".format(CONF['host'], CONF['port']))
        user = l.search_s(CONF['search_base'],
                          ldap.SCOPE_SUBTREE,
                          "(uid=%s)" % username,
                          ['uid', 'gecos', 'mail'])
        l.unbind_s()

        if user:
            user = user.pop()
            userdict = {
                'dn': user[0],
                'uid': user[1]['uid'].pop(),
                'name': user[1]['gecos'].pop(),
                'mail': None
            }

            # If the user has mail set, put it in the dict
            if 'mail' in user[1]:
                userdict['mail'] = user[1]['mail'].pop()

            return userdict
        return None


def get_dn(l):
    """l.whoami_s returns a string 'dn:<full dn>',
    but we need the <full dn> part only.
    """
    return l.whoami_s()[3:]


def search_in_group(username, group):
    """Searches for the given user in the given LDAP group memberuid list.
    This replaces the previous usage of hostflags.
    """
    with LdapConnector(username) as l:
        group_object = l.search_s(
            'cn=' + group + ',ou=Gruppen,ou=Sektion Wundtstrasse,o=AG DSN,c=de',
            ldap.SCOPE_SUBTREE, '(memberuid=%s)' % username)

        if group_object:
            return True
        return False


def change_email(username, password, email):
    """Change a user's email

    Uses ldap.MOD_REPLACE in any case, it should add the
    attribute, if it is not yet set up (replace removes all
    attributes of the given kind and puts the new one in place)
    """
    try:
        with LdapConnector(username, password) as l:
            # The attribute to modify. 'email' is casted to a string, because
            # passing a unicode object will raise a TypeError
            attr = [(ldap.MOD_REPLACE, 'mail', str(email))]
            l.modify_s(get_dn(l), attr)
    except UserNotFound as e:
        logger.error('LDAP-User not found  when attempting '
                     'change of mail address',
                     extra={'data': {'exception_args': e.args},
                            'stack': True})
        raise
    except PasswordInvalid:
        logger.info('Wrong password provided when attempting '
                    'change of mail address')
        raise
    except LDAPConnectionError:
        logger.error('Not sufficient rights to change the mail address')
        raise
    else:
        logger.info('Mail address successfully changed to "%s"', email)


def get_current_uid():
    if not current_user.is_authenticated:
        raise AttributeError("current user not authenticated")
    return current_user.uid