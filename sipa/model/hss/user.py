import logging
from datetime import datetime, timedelta

from flask_babel import gettext
from flask_login import AnonymousUserMixin
from sqlalchemy import func
from sqlalchemy.orm.exc import NoResultFound

from sipa.model.user import BaseUser
from sipa.model.fancy_property import active_prop, unsupported_prop
from sipa.model.finance import BaseFinanceInformation
from sipa.model.misc import PaymentDetails
from sipa.model.sqlalchemy import db
from sipa.model.hss.ldap import HssLdapConnector, change_password
from sipa.model.hss.schema import Account, IP, AccountStatementLog, TrafficQuota
from sipa.utils import argstr, compare_all_attributes
from sipa.model.exceptions import InvalidCredentials
logger = logging.getLogger(__name__)


class User(BaseUser):
    LdapConnector = HssLdapConnector

    def __init__(self, uid):
        """Initialize the User object.

        Note that init itself is not called directly, but mainly by the
        static methods.

        This method should be called by any subclass.  Therefore,
        prepend `super().__init__(uid)`.  After this, other
        variables like `mail`, `group` or `name` can be initialized
        similiarly.

        :param uid: A unique unicode identifier for the User
        :param name: The real name gotten from the LDAP
        """
        self.uid = uid

    def __eq__(self, other):
        return compare_all_attributes(self, other, ['uid', 'datasource'])

    def __repr__(self):
        return "{}.{}({})".format(__name__, type(self).__name__, argstr(
            uid=self.uid,
            name=self.realname,
        ))

    @classmethod
    def get(cls, username):
        """Used by user_loader. Return a User Instance.

        Returns a valid User instance if a psql user with the given
        username exists, else AnonymousUserMixin().
        """
        bare_user = cls(uid=username)

        return bare_user if bare_user._pg_account else AnonymousUserMixin()

    @classmethod
    def from_ip(cls, ip):
        """Return a user based on an ip.

        If there is no user associated with this ip, return AnonymousUserMixin.
        """
        account_name = db.session.query(IP).filter_by(ip=ip).one().account
        if not account_name:
            return AnonymousUserMixin()

        return cls.get(account_name)

    def re_authenticate(self, password):
        self.authenticate(self.uid, password)

    @classmethod
    def authenticate(cls, username, password):
        """Return a User instance or raise PasswordInvalid"""
        try:
            with HssLdapConnector(username, password):
                pass
        except InvalidCredentials:  # Covers `UserNotFound`, `PasswordInvalid`
            raise
        else:
            return cls.get(username)

    @property
    def _pg_account(self):
        """Return the corresponding ORM Account"""
        try:
            return db.session.query(Account).filter_by(
                account=self.uid
            ).one()
        except NoResultFound:
            return
        except RuntimeError:
            logger.warning("RuntimeError caught when accessing _pg_account",
                           extra={'data': {'user': self}})
            return

    can_change_password = True

    @property
    def _pg_trafficquota(self):
        """Return the corresponding ORM TrafficQuota for an Account"""
        try:
            return db.session.query(TrafficQuota).filter_by(
                id=self._pg_account.traffic_quota_id
            ).one()
        except NoResultFound:
            logger.warning("No traffic quota object found for account %s",
                           self._pg_account.account)
            raise

    def change_password(self, old, new):
        """Change the user's password from old to new.

        Although the password has been checked using
        re_authenticate(), some data sources like those which have to
        perform an LDAP bind need it anyways.
        """
        change_password(self.uid, old, new)

    @property
    def traffic_history(self):
        """Return the current credit and the traffic history as a dict.

        The history should cover one week. The assumed unit is KiB.

        The dict syntax is as follows:

        return {'credit': 0,
                'history': [(day, <in>, <out>, <credit>)
                            for day in range(7)]}

        """
        history = []

        for date_delta in range(-6, 1):
            expected_date = (datetime.today() + timedelta(date_delta)).date()
            expected_log = [l for l in self._pg_account.traffic_log
                            if l.date == expected_date]
            try:
                log = expected_log.pop()
            except IndexError:
                history.append({
                    'day': expected_date.weekday(),
                    'input': 0,
                    'output': 0,
                    'throughput': 0,
                    'credit': 0,
                })
            else:
                history.append({
                    'day': expected_date.weekday(),
                    'input': log.bytes_in / 1024,
                    'output': log.bytes_out / 1024,
                    'throughput': (log.bytes_in + log.bytes_out) / 1024,
                    'credit': 0,
                })
                # get the history from the expected_date

        return self.reconstruct_credit(history, self.credit)

    def reconstruct_credit(self, old_history, last_credit):
        history = old_history.copy()
        history[-1]['credit'] = last_credit - history[-1]['throughput']

        for i, entry in enumerate(reversed(history)):
            try:
                # previous means *chronologically* previous (we
                # iterate over `reversed`) ⇒ use [i+1]
                previous_entry = list(reversed(history))[i+1]
            except IndexError:
                pass
            else:
                # Throughput: gets *subtracted* after the day → `+` for before
                # Credit: gets *added* after the day → `-` for before
                previous_entry['credit'] = (
                    entry['credit'] + previous_entry['throughput'] - self.daily_credit
                    # 3 → 3 KiB
                    # 3 * 1024 → 3 MiB
                    # 3 * 1024**2 → 3 GiB
                )

        return history

    @property
    def credit(self):
        """Return the current credit in KiB"""
        return self._pg_account.traffic_balance / 1024

    @property
    def max_credit(self):
        """Return the current credit in KiB"""
        try:
            return self._pg_trafficquota.max_credit / 1024
        except NoResultFound:
            return 210 * 1024 ** 2

    @property
    def daily_credit(self):
        """Return the current credit in KiB"""
        try:
            return self._pg_trafficquota.daily_credit / 1024
        except NoResultFound:
            return 10 * 1024 ** 2

    @active_prop
    def ips(self):
        return ", ".join(ip.ip for ip in self._pg_account.ips)

    @property
    def name(self):
        return self.uid

    @active_prop
    def realname(self):
        return self._pg_account.name

    @active_prop
    def login(self):
        return self._pg_account.account

    @active_prop
    def mac(self):
        return {'value': ", ".join(mac.mac.lower() for mac in self._pg_account.macs),
                'tmp_readonly': len(self._pg_account.macs) > 1}

    @mac.setter
    def mac(self, new_mac):
        # if this has been reached despite `tmp_readonly`, this is a bug.
        assert len(self._pg_account.macs) == 1 or not self.has_connection

        mac = self._pg_account.macs[0]
        mac.mac = new_mac

        db.session.add(mac)
        db.session.commit()

    @active_prop
    def mail(self):
        return "{}@agdsn.me".format(self._pg_account.account)

    @active_prop
    def address(self):
        acc = self._pg_account.access
        return "{building} {floor}-{flat}{room}".format(
            floor=acc.floor,
            flat=acc.flat,
            room=acc.room,
            building=acc.building,
        )

    @active_prop
    def status(self):
        if self._pg_account.properties.active:
            return gettext("Aktiv")
        return gettext("Passiv")

    @unsupported_prop
    def id(self):
        raise NotImplementedError

    @unsupported_prop
    def use_cache(self):
        raise NotImplementedError

    @unsupported_prop
    def hostname(self):
        raise NotImplementedError

    @unsupported_prop
    def hostalias(self):
        raise NotImplementedError

    @unsupported_prop
    def userdb_status(self):
        raise NotImplementedError

    @property
    def userdb(self):
        raise NotImplementedError

    @property
    def has_connection(self):
        return True

    @property
    def finance_information(self):
        return FinanceInformation.from_pg_account(self._pg_account)

    def payment_details(self):
        return PaymentDetails(
            recipient="Studentenrat TUD - AG DSN",
            bank="Ostsächsische Sparkasse Dresden",
            iban="DE40 8505 0300 3120 2419 37",
            bic="OSDD DE 81 XXX",
            purpose="{uid}, {name}, {address}".format(
                uid=self.name,
                name=self.realname.value,
                address=self.address.value,
            ),
        )

    @active_prop
    def use_cache(self):
        if self._pg_account.use_cache:
            return {'value': gettext("Aktiviert"),
                    'raw_value': True,
                    'style': 'success',
                    'empty': False,
                    }
        return {'value': gettext("Nicht aktiviert"),
                'raw_value': False,
                'empty': True}

    @use_cache.setter
    def use_cache(self, new_use_cache):
        account = self._pg_account
        account.use_cache = new_use_cache

        db.session.add(account)
        db.session.commit()


class FinanceInformation(BaseFinanceInformation):
    has_to_pay = True

    def __init__(self, balance, history):
        self._raw_balance = balance
        self._history = history

    @classmethod
    def from_pg_account(cls, pg_account):
        return cls(
            balance=pg_account.finance_balance,
            history=pg_account.combined_transactions,
        )

    @property
    def raw_balance(self):
        return self._raw_balance

    @property
    def last_update(self):
        return db.session.query(func.max(AccountStatementLog.timestamp)).one()[0]

    @property
    def history(self):
        return self._history
