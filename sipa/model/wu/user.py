# -*- coding: utf-8 -*-
import logging
from contextlib import contextmanager
from datetime import datetime, timedelta
from ipaddress import IPv4Address, AddressValueError

from flask import current_app
from flask_babel import gettext
from flask_login import AnonymousUserMixin
from sqlalchemy import func
from sqlalchemy.exc import OperationalError
from sqlalchemy.orm.exc import NoResultFound

from sipa.model.user import BaseUser, BaseUserDB
from sipa.model.fancy_property import active_prop, connection_dependent
from sipa.model.finance import BaseFinanceInformation
from sipa.model.wu.database_utils import STATUS, ACTIVE_STATUS
from sipa.model.wu.ldap_utils import LdapConnector, change_email, \
    change_password, search_in_group
from sipa.model.wu.schema import db
from sipa.units import money
from sipa.utils import argstr, timetag_today
from sipa.utils.exceptions import PasswordInvalid, UserNotFound
from .schema import Computer, Credit, Nutzer, Traffic, Buchung


logger = logging.getLogger(__name__)


class User(BaseUser):
    """User object will be created from LDAP credentials,
    only stored in session.

    the terms 'uid' and 'username' refer to the same thing.
    """

    def __init__(self, uid, realname, mail):
        super().__init__(uid)
        self._realname = realname
        self.group = self.define_group()
        self._mail = mail
        self._userdb = UserDB(self)

    def __repr__(self):
        return "{}.{}({})".format(__name__, type(self).__name__, argstr(
            uid=self.uid,
            realname=self._realname,
            mail=self._mail,
        ))

    def __str__(self):
        return "User {} ({}), {}".format(self._realname, self.uid, self.group)

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
            sql_nutzer = (db.session.query(Nutzer)
                          .join(Computer)
                          .filter_by(c_ip=ip)
                          .filter(Nutzer.status.in_(ACTIVE_STATUS))
                          .one())
        except NoResultFound:
            return AnonymousUserMixin()

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

    @property
    def _nutzer(self):
        """Returns the corresponding Orm `Nutzer` object from netusers

        When firstly invoked, the ORM object is being cached in
        `self._cached_nutzer` to avoid multiple transactions for every
        property access.

        """
        if not getattr(self, '_cached_nutzer', None):
            sql_nutzer = None
            try:
                sql_nutzer = db.session.query(Nutzer).filter_by(
                    unix_account=self.uid
                ).one()
            except NoResultFound:
                logger.critical("User %s does not have a database entry",
                                self.uid)
            finally:
                self._cached_nutzer = sql_nutzer

        return self._cached_nutzer

    @property
    def traffic_history(self):
        traffic_history = []

        credit_entries = reversed(
            db.session.query(Credit)
            .filter_by(user_id=self._nutzer.nutzer_id)
            .order_by(Credit.timetag.desc())
            .limit(7).all()
        )

        accountable_ips = [c.c_ip for c in self._nutzer.computer]

        for credit_entry in credit_entries:
            traffic_entries = (db.session.query(Traffic)
                               .filter_by(timetag=credit_entry.timetag)
                               .filter(Traffic.ip.in_(accountable_ips))
                               .all()) if accountable_ips else []

            traffic_history.append({
                'day': (datetime.today() + timedelta(
                    days=credit_entry.timetag - timetag_today()
                )).weekday(),
                'input': sum(t.input for t in traffic_entries),
                'output': sum(t.output for t in traffic_entries),
                'throughput': sum(t.overall for t in traffic_entries),
                'credit': credit_entry.amount,
            })

        return traffic_history

    @property
    def credit(self):
        """Return the current credit that is left
        """
        latest_credit_entry = (
            db.session.query(Credit)
            .filter_by(user_id=self._nutzer.nutzer_id)
            .order_by(Credit.timetag.desc())
            .first()
        )

        credit = latest_credit_entry.amount
        today = latest_credit_entry.timetag

        accountable_ips = [c.c_ip for c in self._nutzer.computer]

        traffic_today = sum(
            t.overall for t
            in db.session.query(Traffic)
            .filter_by(timetag=today)
            .filter(Traffic.ip.in_(accountable_ips))
        ) if accountable_ips else 0

        return credit - traffic_today

    max_credit = 63 * 1024 * 1024
    daily_credit = 3 * 1024 * 1024

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
        return self._realname

    @active_prop
    @connection_dependent
    def mac(self):
        computer = self._nutzer.computer
        return {'value': ", ".join(c.c_etheraddr.upper() for c in computer),
                'tmp_readonly': len(computer) > 1}

    @mac.setter
    def mac(self, new_mac):
        # if this has been reached despite `tmp_readonly`, this is a bug.
        assert len(self._nutzer.computer) == 1 or not self.has_connection

        computer = self._nutzer.computer[0]
        computer.c_etheraddr = new_mac.lower()

        db.session.add(computer)
        db.session.commit()

    @active_prop
    def mail(self):
        return self._mail

    @mail.setter
    def mail(self, new_mail):
        change_email(self.uid, self.__password, new_mail)

    # See https://github.com/agdsn/sipa/issues/234
    # @mail.deleter
    # def mail(self):
    #     self._mail = ''

    @active_prop
    def address(self):
        return self._nutzer.address

    @active_prop
    @connection_dependent
    def ips(self):
        return ", ".join(c.c_ip for c in self._nutzer.computer)

    @active_prop
    def status(self):
        if self._nutzer.status in STATUS:
            status_tuple = STATUS[self._nutzer.status]
            return {'value': status_tuple[0], 'style': status_tuple[1]}

        return {'value': STATUS.get(self._nutzer.status, gettext("Unbekannt")),
                'empty': True}

    @property
    def has_connection(self):
        return self._nutzer.status in ACTIVE_STATUS

    @active_prop
    def id(self):
        return "{}-{}".format(
            self._nutzer.nutzer_id,
            sum(int(digit) for digit in str(self._nutzer.nutzer_id)) % 10,
        )

    @active_prop
    @connection_dependent
    def hostname(self):
        return ", ".join(c.c_hname for c in self._nutzer.computer)

    @active_prop
    @connection_dependent
    def hostalias(self):
        return ", ".join(c.c_alias for c in self._nutzer.computer
                         if c.c_alias)

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

    @property
    def finance_information(self):
        return FinanceInformation(transactions=self._nutzer.transactions)


class FinanceInformation(BaseFinanceInformation):
    has_to_pay = True

    def __init__(self, transactions):
        self._transactions = transactions

    @property
    def _balance(self):
        return sum(t.value for t in self._transactions)

    @property
    def last_update(self):
        """Return an educated guess for the last finance update.

        It is based on the highest date in the database.  The only
        possible case this date is wrong is if on the day of the
        import, nothing has actually been transacted.
        """
        return db.session.query(func.max(Buchung.datum)).one()[0]

    @property
    def history(self):
        return self._transactions


class UserDB(BaseUserDB):
    def __init__(self, user):
        super().__init__(user)

        mask = current_app.config.get('DB_HELIOS_IP_MASK')
        self.test_ipmask_validity(mask)
        self.ip_mask = mask

    @staticmethod
    def test_ipmask_validity(mask):
        """Test whether a valid ip mask (at max one consecutive '%') was given

        This is being done by replacing '%' with the maximum possible
        value ('255').  Thus, everything surrounding the '%' except
        for dots causes an invalid IPv4Address and thus a
        `ValueError`.
        """
        try:
            IPv4Address(mask.replace("%", "255"))
        except AddressValueError:
            raise ValueError("Mask {} is not a valid IP address or contains "
                             "more than one consecutive '%' sign".format(mask))

    @staticmethod
    def sql_query(query, args=()):
        """Prepare and execute a raw sql query.
        'args' is a tuple needed for string replacement.
        """
        database = current_app.extensions['db_helios']
        conn = database.connect()
        result = conn.execute(query, args)
        conn.close()
        return result

    @property
    def has_db(self):
        try:
            userdb = self.sql_query(
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
        self.sql_query(
            "CREATE DATABASE "
            "IF NOT EXISTS `%s`" % self.user.uid,
        )
        self.change_password(password)

    def drop(self):
        self.sql_query(
            "DROP DATABASE "
            "IF EXISTS `%s`" % self.user.uid,
        )

        self.sql_query(
            "DROP USER %s@%s",
            (self.user.uid, self.ip_mask),
        )

    def change_password(self, password):
        user = self.sql_query(
            "SELECT user "
            "FROM mysql.user "
            "WHERE user = %s",
            (self.user.uid,),
        ).fetchall()

        if not user:
            self.sql_query(
                "CREATE USER %s@%s "
                "IDENTIFIED BY %s",
                (self.user.uid, self.ip_mask, password,),
            )
        else:
            self.sql_query(
                "SET PASSWORD "
                "FOR %s@%s = PASSWORD(%s)",
                (self.user.uid, self.ip_mask, password,),
            )

        self.sql_query(
            "GRANT SELECT, INSERT, UPDATE, DELETE, "
            "ALTER, CREATE, DROP, INDEX, LOCK TABLES "
            "ON `{}`.* "
            "TO %s@%s".format(self.user.uid),
            (self.user.uid, self.ip_mask),
        )
