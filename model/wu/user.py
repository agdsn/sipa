# -*- coding: utf-8 -*-
from flask.ext.babel import gettext
from flask.ext.login import AnonymousUserMixin
from sqlalchemy.exc import OperationalError

from model.property import active_prop

from model.default import BaseUser
from model.wu.database_utils import ip_from_user_id, sql_query, \
    update_macaddress, query_trafficdata, \
    query_current_credit, create_mysql_userdatabase, drop_mysql_userdatabase, \
    change_mysql_userdatabase_password, user_has_mysql_db, \
    calculate_userid_checksum, DORMITORIES, status_string_from_id, \
    user_id_from_uid
from model.wu.ldap_utils import search_in_group, LdapConnector, \
    change_email, change_password

from sipa.utils.exceptions import PasswordInvalid, UserNotFound, DBQueryEmpty

import logging
logger = logging.getLogger(__name__)


class User(BaseUser):
    """User object will be created from LDAP credentials,
    only stored in session.

    the terms 'uid' and 'username' refer to the same thing.
    """

    def __init__(self, uid, name, mail, ip=None):
        super(User, self).__init__(uid)
        self.name = name
        self.group = self.define_group()
        self._mail = mail
        self._ip = ip
        self.cache_information()

    def _get_ip(self):
        self._ip = ip_from_user_id(user_id_from_uid(self.uid))

    def __repr__(self):
        return "User<{},{}.{}>".format(self.uid, self.name, self.group)

    def __str__(self):
        return "User {} ({}), {}".format(self.name, self.uid, self.group)

    can_change_password = True

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
        if user:
            return User(user['uid'], user['name'], user['mail'], **kwargs)
        return AnonymousUserMixin()

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
        result = sql_query("SELECT c.nutzer_id FROM computer as c "
                           "LEFT JOIN nutzer as n "
                           "ON c.nutzer_id = n.nutzer_id "
                           "WHERE c_ip = %s "
                           "AND (n.status < 8 OR n.status > 10) "
                           "ORDER BY c.nutzer_id DESC",
                           (ip,)).fetchone()
        if result is None:
            return AnonymousUserMixin()

        username = sql_query("SELECT unix_account FROM nutzer "
                             "WHERE nutzer_id = %s",
                             (result['nutzer_id'],)).fetchone()['unix_account']

        user = User.get(username, ip=ip)
        if not user:
            logger.warning("User %s could not be fetched from LDAP",
                           username, extra={'data': {
                               'username': username,
                               'user_id': result['nutzer_id'],
                           }})
            return AnonymousUserMixin()

        return user

    def change_password(self, old, new):
        """Change a user's password from old to new
        """
        try:
            change_password(self.uid, old, new)
        except PasswordInvalid:
            logger.info('Wrong password provided when attempting '
                        'change of password')
            raise
        else:
            logger.info('Password successfully changed')

    def cache_information(self):
        user = sql_query(
            "SELECT nutzer_id, wheim_id, etage, zimmernr, status "
            "FROM nutzer "
            "WHERE unix_account = %s",
            (self.uid,)
        ).fetchone()

        if not user:
            # TODO: more information on this very specific issue.
            raise DBQueryEmpty

        mysql_id = user['nutzer_id']
        self._id = "{}-{}".format(mysql_id,
                                  calculate_userid_checksum(mysql_id))
        self._address = "{0} / {1} {2}".format(
            # MySQL Dormitory IDs in are from 1-11, so we map to 0-10 with x-1
            DORMITORIES[user['wheim_id'] - 1],
            user['etage'],
            user['zimmernr']
        )
        # todo use more colors (yellow for finances etc.)
        self._status = status_string_from_id(user['status'])

        computer = sql_query(
            "SELECT c_etheraddr, c_ip, c_hname, c_alias "
            "FROM computer "
            "WHERE nutzer_id = %s",
            (user['nutzer_id'])
        ).fetchone()

        if not computer:
            raise DBQueryEmpty

        self._ip = computer['c_ip']
        self._mac = computer['c_etheraddr'].upper()
        # todo figure out where that's being used
        self._hostname = computer['c_hname']
        self._hostalias = computer['c_alias']

        # TODO: figure out where the formatting should be handled
        try:
            if user_has_mysql_db(self.uid):
                self._user_db = gettext("Aktiviert")
            else:
                self._user_db = gettext("Nicht aktiviert")
        except OperationalError:
            logger.critical("User db unreachable")
            self._user_db = gettext("Datenbank nicht erreichbar")

    def get_traffic_data(self):
        # TODO: this throws DBQueryEmpty
        print("self._ip: {}".format(self._ip))
        return query_trafficdata(self._ip, user_id_from_uid(self.uid))

    def get_current_credit(self):
        return query_current_credit(self.uid, self._ip)

    def change_mac_address(self, old_mac, new_mac):
        update_macaddress(self._ip, old_mac, new_mac)

    def change_mail(self, password, new_mail):
        change_email(self.uid, password, new_mail)

    def has_user_db(self):
        return user_has_mysql_db(self.uid)

    def user_db_create(self, password):
        return create_mysql_userdatabase(self.uid, password)

    def user_db_drop(self):
        return drop_mysql_userdatabase(self.uid)

    def user_db_password_change(self, password):
        return change_mysql_userdatabase_password(self.uid, password)

    @active_prop
    def login(self):
        return self.uid

    @active_prop
    def mac(self):
        return self._mac

    @mac.setter
    def mac(self, value):
        raise NotImplementedError("TODO!")

    @active_prop
    def mail(self):
        return self._mail

    @mail.setter
    def mail(self, value):
        raise NotImplementedError("TODO!")

    @mail.deleter
    def mail(self):
        raise NotImplementedError("TODO!")

    @active_prop
    def user_id(self):
        return self._user

    @active_prop
    def address(self):
        return self._address

    @active_prop
    def ip(self):
        return self._ip

    @active_prop
    def status(self):
        return self._status

    @active_prop
    def id(self):
        return self._id

    @active_prop
    def hostname(self):
        return self._hostname

    @active_prop
    def hostalias(self):
        return self._hostalias

    @active_prop
    def userdb(self):
        # TODO: format accordingly if error
        return self._user_db

    @userdb.setter
    def userdb(self):
        # TODO: find a better way which does not set `__get__`
        # (but only the capability)
        assert False, "This function should never be reached"
