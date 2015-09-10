# -*- coding: utf-8 -*-
from flask.ext.babel import gettext
from flask.ext.login import AnonymousUserMixin
from sqlalchemy.exc import OperationalError

from model.constants import info_property, STATUS_COLORS, ACTIONS, \
    FULL_FEATURE_SET
from model.default import BaseUser
from model.wu.database_utils import ip_from_user_id, sql_query, \
    update_macaddress, query_trafficdata, \
    query_current_credit, create_mysql_userdatabase, drop_mysql_userdatabase, \
    change_mysql_userdatabase_password, user_has_mysql_db, \
    calculate_userid_checksum, DORMITORIES, status_string_from_id, \
    user_id_from_uid
from model.wu.ldap_utils import search_in_group, LdapConnector, \
    get_dn, change_email
from sipa import logger
from sipa.utils.exceptions import PasswordInvalid, UserNotFound, DBQueryEmpty


class User(BaseUser):
    """User object will be created from LDAP credentials,
    only stored in session.

    the terms 'uid' and 'username' refer to the same thing.
    """

    def __init__(self, uid, name, mail, ip=None):
        super(User, self).__init__(uid)
        self.name = name
        self.group = self.define_group()
        self.mail = mail
        self._ip = ip

    def _get_ip(self):
        self._ip = ip_from_user_id(user_id_from_uid(self.uid))

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
            return AnonymousUserMixin()

        username = sql_query("SELECT unix_account FROM nutzer "
                             "WHERE nutzer_id = %s",
                             (result['nutzer_id'],)).fetchone()['unix_account']

        return User.get(username, ip=ip)

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

    _supported_features = FULL_FEATURE_SET

    def get_information(self):
        """Executes select query for the username and returns a prepared dict.

        * Dormitory IDs in Mysql are from 1-11, so we map to 0-10 with "x-1".

        Returns "-1" if a query result was empty (None), else
        returns the prepared dict.
        """
        userinfo = {}
        user = sql_query(
            "SELECT nutzer_id, wheim_id, etage, zimmernr, status "
            "FROM nutzer "
            "WHERE unix_account = %s",
            (self.uid,)
        ).fetchone()

        if not user:
            raise DBQueryEmpty

        mysql_id = user['nutzer_id']
        userinfo.update(
            id=info_property(
                "{}-{}".format(mysql_id, calculate_userid_checksum(mysql_id))),
            address=info_property(u"{0} / {1} {2}".format(
                DORMITORIES[user['wheim_id'] - 1],
                user['etage'],
                user['zimmernr']
            )),
            # todo use more colors (yellow for finances etc.)
            status=info_property(status_string_from_id(user['status']),
                                 status_color=(STATUS_COLORS.GOOD
                                               if user['status'] is 1
                                               else None)),
        )

        computer = sql_query(
            "SELECT c_etheraddr, c_ip, c_hname, c_alias "
            "FROM computer "
            "WHERE nutzer_id = %s",
            (user['nutzer_id'])
        ).fetchone()

        if not computer:
            raise DBQueryEmpty

        userinfo.update(
            ip=info_property(computer['c_ip']),
            mail=info_property(self.mail, actions={ACTIONS.EDIT,
                                                   ACTIONS.DELETE}),
            mac=info_property(computer['c_etheraddr'].upper(),
                              actions={ACTIONS.EDIT}),
            # todo figure out where that's being used
            hostname=info_property(computer['c_hname']),
            hostalias=info_property(computer['c_alias'])
        )

        try:
            if user_has_mysql_db(self.uid):
                user_db_prop = info_property(
                    gettext("Aktiviert"),
                    status_color=STATUS_COLORS.GOOD,
                    actions={ACTIONS.EDIT}
                )
            else:
                user_db_prop = info_property(
                    gettext("Nicht aktiviert"),
                    status_color=STATUS_COLORS.INFO,
                    actions={ACTIONS.EDIT}
                )
        except OperationalError:
            logger.critical("User db unreachable")
            user_db_prop = info_property(gettext(u"Datenbank nicht erreichbar"))
        finally:
            userinfo.update(userdb=user_db_prop)

        return userinfo

    def get_traffic_data(self):
        return query_trafficdata(self.ip, user_id_from_uid(self.uid))

    def get_current_credit(self):
        return query_current_credit(self.uid, self.ip)

    def change_mac_address(self, old_mac, new_mac):
        update_macaddress(self.ip, old_mac, new_mac)

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
