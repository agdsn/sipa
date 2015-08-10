# -*- coding: utf-8 -*-

from flask import request
from flask.ext.babel import gettext
from flask.ext.login import current_user, AnonymousUserMixin
from sqlalchemy.exc import OperationalError

from model.default import BaseUser
from model.wu.database_utils import init_db, ip_from_user_id, sql_query, \
    update_macaddress, query_userinfo, query_trafficdata, \
    query_current_credit
from model.wu.ldap_utils import init_ldap, search_in_group, LdapConnector, \
    get_dn, change_email
from sipa import logger
from sipa.utils.exceptions import PasswordInvalid, UserNotFound


def init_context(app):
    init_db(app)
    init_ldap(app)


# TODO split into `SQLUser` and `LDAPUser` or similar
# TODO split into AuthenticatedUserMixin and FlaskLoginUserMixin
class User(BaseUser):
    """User object will be created from LDAP credentials,
    only stored in session.

    the terms 'uid' and 'username' refer to the same thing.
    """

    def __init__(self, uid, name, mail, ip=None):
        super(User, self).__init__(uid)
        self.name = name
        # TODO include group in user information
        self.group = self.define_group()
        self.mail = mail
        self._ip = ip

    def _get_ip(self):
        self._ip = ip_from_user_id(self.uid)

    def __repr__(self):
        return "User<{},{}.{}>".format(self.uid, self.name, self.group)

    def __str__(self):
        return "User {} ({}), {}".format(self.name, self.uid, self.group)

    def define_group(self):
        """Define a user group from the LDAP group
        """
        if search_in_group(self.uid, 'Aktiv'):
            return 'active'
        elif search_in_group(self.uid, 'Exaktiv'):
            return 'exactive'
        return 'passive'


    @staticmethod
    def get(username, **kwargs):
        """Static method for flask-login user_loader,
        used before _every_ request.
        """
        user = LdapConnector.fetch_user(username)
        return User(user['uid'], user['name'], user['mail'], **kwargs)

    @staticmethod
    def authenticate(username, password):
        """This method checks the user and password combination against LDAP

        Returns the User object if successful.
        """
        try:
            with LdapConnector(username, password):
                return User.get(username)
        except PasswordInvalid:
            logger.info('Failed login attempt (Wrong %s)', 'password',
                        extra={'data': {'username': username}})
            raise
        except UserNotFound:
            logger.info('Failed login attempt (Wrong %s)', 'username',
                        extra={'data': {'username': username}})
            raise

    @staticmethod
    def from_ip(ip):
        result = sql_query("SELECT nutzer_id FROM computer WHERE c_ip = %s",
                            (ip,)).fetchone()
        if result is None:
            return AnonymousUserMixin

        return User.get(result['nutzer_id'], ip=ip)

    def change_password(self, old, new):
        """Change a user's password from old to new
        """
        try:
            with LdapConnector(self.uid, old) as l:
                l.passwd_s(get_dn(l),
                           old.encode('iso8859-1'),
                           new.encode('iso8859-1'))
        except PasswordInvalid:
            logger.info('Wrong password provided when attempting '
                        'change of password')
            raise
        else:
            logger.info('Password successfully changed')

    def get_information(self):
        return query_userinfo(self.uid)

    def get_traffic_data(self):
        return query_trafficdata(self.ip, self.uid)

    def get_current_credit(self):
        return query_current_credit(self.uid, self.ip)

    def change_mac_address(self, old_mac, new_mac):
        update_macaddress(self.ip, old_mac, new_mac)

    def change_mail(self, password, new_mail):
        change_email(self.uid, password, new_mail)


def query_gauge_data():
    credit = {}
    try:
        if current_user.is_authenticated():
            credit['data'] = current_user.get_current_credit()
        else:
            from model import User
            credit['data'] = User.from_ip(request.remote_addr).get_current_credit()
    except OperationalError:
        credit['error'] = gettext(u'Fehler bei der Abfrage der Daten')
    else:
        if not credit['data']:
            credit['error'] = gettext(u'Diese IP gehört nicht '
                                      u'zu unserem Netzwerk')
    return credit
