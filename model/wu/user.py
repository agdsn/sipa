# -*- coding: utf-8 -*-
from contextlib import contextmanager

from datetime import datetime, timedelta

from flask.ext.babel import gettext
from flask.ext.login import AnonymousUserMixin
from sqlalchemy.exc import OperationalError

from model.property import active_prop

from model.default import BaseUser, BaseUserDB
from model.wu.database_utils import sql_query, \
    DORMITORIES, STATUS, \
    session_atlantis
from model.wu.ldap_utils import search_in_group, LdapConnector, \
    change_email, change_password
from .schema import Credit, Computer, Nutzer, Traffic

from sipa.utils import argstr, timetag_today
from sipa.utils.exceptions import PasswordInvalid, UserNotFound

from sqlalchemy import or_
from sqlalchemy.orm.exc import NoResultFound

import logging
logger = logging.getLogger(__name__)


class User(BaseUser):
    """User object will be created from LDAP credentials,
    only stored in session.

    the terms 'uid' and 'username' refer to the same thing.
    """

    datasource = 'wu'

    def __init__(self, uid, name, mail):
        super().__init__(uid)
        self.name = name
        self.group = self.define_group()
        self._mail = mail
        self.cache_information()
        self._userdb = UserDB(self)

    def __repr__(self):
        return "{}.{}({})".format(__name__, type(self).__name__, argstr(
            uid=self.uid,
            name=self.name,
            mail=self._mail,
        ))

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

    @classmethod
    def get(cls, username, **kwargs):
        """Static method for flask-login user_loader,
        used before _every_ request.
        """
        user = LdapConnector.fetch_user(username)
        if user:
            return cls(user['uid'], user['name'], user['mail'], **kwargs)
        return AnonymousUserMixin()

    @classmethod
    def authenticate(cls, username, password):
        """This method checks the user and password combination against LDAP

        Returns the User object if successful.
        """
        try:
            with LdapConnector(username, password):
                return cls.get(username)
        except PasswordInvalid:
            logger.info('Failed login attempt (Wrong %s)', 'password',
                        extra={'data': {'username': username}})
            raise
        except UserNotFound:
            logger.info('Failed login attempt (Wrong %s)', 'username',
                        extra={'data': {'username': username}})
            raise

    @classmethod
    def from_ip(cls, ip):
        try:
            sql_nutzer = (session_atlantis.query(Computer)
                          .filter_by(c_ip=ip)
                          .join(Nutzer)
                          .filter(Nutzer.status.in_([1, 2, 7, 12]))
                          .one())
        except NoResultFound:
            return AnonymousUserMixin

        username = sql_nutzer.unix_account

        user = cls.get(username)
        if not user:
            logger.warning("User %s could not be fetched from LDAP",
                           username, extra={'data': {
                               'username': username,
                               'user_id': sql_nutzer.nutzer_id,
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
        try:
            sql_nutzer = session_atlantis.query(Nutzer).filter_by(
                unix_account=self.uid
            ).one()
        except NoResultFound:
            logger.critical("User %s does not have a database entry", self.uid,
                            extra={'stack': True})
            self._nutzer = None
        else:
            self._nutzer = sql_nutzer

    @property
    def traffic_history(self):
        traffic_history = []

        credit_entries = reversed(
            session_atlantis.query(Credit)
            .filter_by(user_id=10564)
            .order_by(Credit.timetag.desc())
            .limit(7).all()
        )

        accountable_ips = [c.c_ip for c in self._nutzer.computer]

        for credit_entry in credit_entries:
            traffic_entries = (session_atlantis.query(Traffic)
                               .filter_by(timetag=credit_entry.timetag)
                               .filter(Traffic.ip.in_(accountable_ips))
                               .all())

            traffic_history.append({
                'day': (datetime.today() + timedelta(
                    days=credit_entry.timetag - timetag_today()
                )).weekday(),
                'input': sum(t.input for t in traffic_entries) / 1024,
                'output': sum(t.output for t in traffic_entries) / 1024,
                'throughput': sum(t.overall for t in traffic_entries) / 1024,
                'credit': credit_entry.amount / 1024,
            })

        return traffic_history

    @property
    def credit(self):
        """Return the current credit that is left
        """
        latest_credit_entry = (
            session_atlantis.query(Credit)
            .filter_by(user_id=self._nutzer.nutzer_id)
            .order_by(Credit.timetag.desc())
            .first()
        )

        credit = latest_credit_entry.amount
        today = latest_credit_entry.timetag

        accountable_ips = [c.c_ip for c in self._nutzer.computer]

        traffic_today = sum(
            t.overall for t
            in session_atlantis.query(Traffic)
            .filter_by(timetag=today)
            .filter(Traffic.ip.in_(accountable_ips))
        )

        return (credit - traffic_today) / 1024

    @contextmanager
    def tmp_authentication(self, password):
        """Check and temporarily store the given password.

        Returns a context manager.  The password is stored in
        `self.__password`.

        This is quite an ugly hack, only existing because sipa does
        not have an ldap bind for this datasource and needs the user's
        password.  THe need for the password breaks compatability with
        the usual `instance.property = value` – now, an AttributeError
        has to be catched and in that case this wrapper has to be used.

        I could not think of a better way to get around this.

        """
        self.re_authenticate(password)
        self.__password = password
        yield
        del self.__password

    @active_prop
    def login(self):
        return self.uid

    @active_prop
    def realname(self):
        return self.name

    @active_prop
    def mac(self):
        computer = self._nutzer.computer
        return {'value': ", ".join(c.c_etheraddr.upper() for c in computer),
                'tmp_readonly': len(computer) > 1}

    @mac.setter
    def mac(self, new_mac):
        # if this has been reached despite `tmp_readonly`, this is a bug.
        assert len(self._nutzer.computer) == 1

        computer = self._nutzer.computer[0]
        computer.c_etheraddr = new_mac

        session_atlantis.add(computer)
        session_atlantis.commit()

    @active_prop
    def mail(self):
        return self._mail

    @mail.setter
    def mail(self, new_mail):
        change_email(self.uid, self.__password, new_mail)

    @mail.deleter
    def mail(self):
        self.mail = ''

    @active_prop
    def address(self):
        return "{} / {} {}".format(
            DORMITORIES[self._nutzer.wheim_id - 1],
            self._nutzer.etage,
            self._nutzer.zimmernr,
        )

    @active_prop
    def ips(self):
        return ", ".join(c.c_ip for c in self._nutzer.computer)

    @active_prop
    def status(self):
        if self._nutzer.status in STATUS:
            status_tuple = STATUS[self._nutzer.status]
            return {'value': status_tuple[0], 'style': status_tuple[1]}

        return {'value': STATUS.get(self._nutzer.status, gettext("Unbekannt")),
                'empty': True}

    @active_prop
    def id(self):
        return "{}-{}".format(
            self._nutzer.nutzer_id,
            sum(int(digit) for digit in str(self._nutzer.nutzer_id)) % 10,
        )

    @active_prop
    def hostname(self):
        return ", ".join(c.c_hname for c in self._nutzer.computer)

    @active_prop
    def hostalias(self):
        return ", ".join(c.c_alias for c in self._nutzer.computer)

    @active_prop
    def userdb_status(self):
        try:
            status = self.userdb.has_db
        except OperationalError:
            return {'value': gettext("Datenbank nicht erreichbar"),
                    'style': 'danger', 'empty': True}

        if status:
            return {'value': gettext("Aktiviert"),
                    'style': 'success'}
        return {'value': gettext("Nicht aktiviert"),
                'empty': True}

    userdb_status = userdb_status.fake_setter()

    @property
    def userdb(self):
        return self._userdb


class UserDB(BaseUserDB):
    def __init__(self, user):
        super().__init__(user)

    @property
    def has_db(self):
        try:
            userdb = sql_query(
                "SELECT SCHEMA_NAME "
                "FROM INFORMATION_SCHEMA.SCHEMATA "
                "WHERE SCHEMA_NAME = %s",
                (self.user.uid,),
            ).fetchone()

            return userdb is not None
        except OperationalError:
            logger.critical("User db of user %s unreachable", self.user.uid)
            raise

    def create(self, password):
        sql_query(
            "CREATE DATABASE "
            "IF NOT EXISTS `%s`" % self.user.uid,
        )
        self.change_password(password)

    def drop(self):
        sql_query(
            "DROP DATABASE "
            "IF EXISTS `%s`" % self.user.uid,
        )

        sql_query(
            "DROP USER %s@'10.1.7.%%'",
            (self.user.uid,),
        )

    def change_password(self, password):
        user = sql_query(
            "SELECT user "
            "FROM mysql.user "
            "WHERE user = %s",
            (self.user.uid,),
        ).fetchall()

        if not user:
            sql_query(
                "CREATE USER %s@'10.1.7.%%' "
                "IDENTIFIED BY %s",
                (self.user.uid, password),
            )
        else:
            sql_query(
                "SET PASSWORD "
                "FOR %s@'10.1.7.%%' = PASSWORD(%s)",
                (self.user.uid, password),
            )

        sql_query(
            "GRANT SELECT, INSERT, UPDATE, DELETE, "
            "ALTER, CREATE, DROP, INDEX, LOCK TABLES "
            "ON `%s`.* "
            "TO %%s@'10.1.7.%%%%'" % self.user.uid,
            (self.user.uid,),
        )
