# -*- coding: utf-8 -*-
import logging

from sipa.model.user import BaseUser
from sipa.model.finance import BaseFinanceInformation
from sipa.model.fancy_property import active_prop, connection_dependent, \
    unsupported_prop, ActiveProperty, UnsupportedProperty, Capabilities
from sipa.model.misc import PaymentDetails
from sipa.model.exceptions import UserNotFound, PasswordInvalid, \
    MacAlreadyExists, NetworkAccessAlreadyActive, TerminationNotPossible, UnknownError, \
    ContinuationNotPossible, SubnetFull
from .api import PycroftApi
from .exc import PycroftBackendError
from .schema import UserData, UserStatus
from .unserialize import UnserializationError
from .userdb import UserDB

from flask_login import AnonymousUserMixin
from flask.globals import current_app
from flask_babel import gettext
from werkzeug.local import LocalProxy
from werkzeug.http import parse_date

logger = logging.getLogger(__name__)

api: PycroftApi = LocalProxy(lambda: current_app.extensions['pycroft_api'])


class User(BaseUser):
    user_data: UserData

    def __init__(self, user_data: dict):
        try:
            self.user_data: UserData = UserData(user_data)
            self._userdb: UserDB = UserDB(self)
        except UnserializationError as e:
            raise PycroftBackendError("Error when parsing user lookup response") from e
        super().__init__(uid=str(self.user_data.id))

    @classmethod
    def get(cls, username):
        status, user_data = api.get_user(username)

        if status != 200:
            raise UserNotFound

        return cls(user_data)

    @classmethod
    def from_ip(cls, ip):
        status, user_data = api.get_user_from_ip(ip)

        if status != 200:
            return AnonymousUserMixin()

        return cls(user_data)

    def re_authenticate(self, password):
        self.authenticate(self.user_data.login, password)

    @classmethod
    def authenticate(cls, username, password):
        status, result = api.authenticate(username, password)

        if status != 200:
            raise PasswordInvalid

        return cls.get(result['id'])

    can_change_password = True

    def change_password(self, old, new):
        status, result = api.change_password(self.user_data.id, old, new)

        if status != 200:
            raise PasswordInvalid

    @property
    def traffic_history(self):
        return [{
            'day': parse_date(entry.timestamp).weekday(),
            'input': to_kib(entry.ingress),
            'output': to_kib(entry.egress),
            'throughput': to_kib(entry.ingress) + to_kib(entry.egress),
        } for entry in self.user_data.traffic_history]

    @active_prop
    def realname(self):
        return self.user_data.name

    @active_prop
    def birthdate(self):
        return self.user_data.birthdate

    @active_prop
    def login(self):
        return self.user_data.login

    @active_prop
    @connection_dependent
    def ips(self):
        ips = sorted(ip for i in self.user_data.interfaces for ip in i.ips)
        return ", ".join(ips)

    @active_prop
    @connection_dependent
    def mac(self):
        return {'value': ", ".join(i.mac for i in self.user_data.interfaces),
                'tmp_readonly': len(self.user_data.interfaces) > 1 or not self.has_property('network_access')}

    # Empty setter for "edit" capability
    @mac.setter
    def mac(self, new_mac):
        pass

    def change_mac_address(self, new_mac, host_name):
        # if this has been reached despite `tmp_readonly`, this is a bug.
        assert len(self.user_data.interfaces) == 1

        status, result = api.change_mac(self.user_data.id, self._tmp_password,
                                        self.user_data.interfaces[0].id,
                                        new_mac, host_name)

        if status == 401:
            raise PasswordInvalid
        elif status == 400:
            raise MacAlreadyExists

    @active_prop
    @connection_dependent
    def network_access_active(self):
        return {'value': len(self.user_data.interfaces) > 0,
                'tmp_readonly': len(self.user_data.interfaces) > 0
                                or not self.has_property('network_access')
                                or self.user_data.room is None}

    @network_access_active.setter
    def network_access_active(self, value):
        pass

    def activate_network_access(self, password, mac, birthdate, host_name):
        status, result = api.activate_network_access(self.user_data.id, password, mac,
                                                     birthdate, host_name)

        if status == 401:
            raise PasswordInvalid
        elif status == 400:
            raise MacAlreadyExists
        elif status == 412:
            raise NetworkAccessAlreadyActive
        elif status == 422:
            raise SubnetFull

    def terminate_membership(self, end_date):
        status, result = api.terminate_membership(self.user_data.id, end_date)

        if status == 400:
            raise TerminationNotPossible
        elif status != 200:
            raise UnknownError

    def estimate_balance(self, end_date):
        status, result = api.estimate_balance_at_end_of_membership(self.user_data.id, end_date)

        if status == 200:
            return result['estimated_balance']
        else:
            raise UnknownError

    def continue_membership(self):
        status, result = api.continue_membership(self.user_data.id)

        if status == 400:
            raise ContinuationNotPossible
        elif status != 200:
            raise UnknownError

    @active_prop
    def mail(self):
        return {'value': self.user_data.mail,
                'tmp_readonly': not self.has_property('mail')}

    @mail.setter
    def mail(self, new_mail):
        status, result = api.change_mail(self.user_data.id, self._tmp_password, new_mail,
                                         self.user_data.mail_forwarded)

        if status == 401:
            raise PasswordInvalid
        elif status == 404:
            raise UserNotFound

    @active_prop
    def mail_forwarded(self):
        value = self.user_data.mail_forwarded
        return {'raw_value': value,
                'value': gettext('Aktiviert') if value else gettext('Nicht aktiviert'),
                'tmp_readonly': not self.has_property('mail')}

    @mail_forwarded.setter
    def mail_forwarded(self, value):
        self.user_data.mail_forwarded = value

    @property
    def mail_confirmed(self):
        confirmed = self.user_data.mail_confirmed
        editable = self.has_property('mail') and self.user_data.mail and not confirmed
        return ActiveProperty(
                name='mail_confirmed',
                value=gettext('Bestätigt') if confirmed else gettext('Nicht bestätigt'),
                style='success' if confirmed else 'danger',
                capabilities=Capabilities(edit=editable, delete=False))

    def resend_confirm_mail(self) -> bool:
        return api.resend_confirm_email(self.user_data.id)

    @active_prop
    def address(self):
        return self.user_data.room

    @active_prop
    def status(self):
        value, style = self.evaluate_status(self.user_data.status)
        return {'value': value, 'style': style}

    @active_prop
    def id(self):
        return {'value': self.user_data.user_id}

    @unsupported_prop
    def hostname(self):
        raise NotImplementedError

    @unsupported_prop
    def hostalias(self):
        raise NotImplementedError

    @property
    def userdb_status(self):
        status = self.userdb.has_db

        capabilities = Capabilities(edit=True, delete=True)

        if not self.has_property("userdb"):
            return UnsupportedProperty("userdb_status")

        if status is None:
            return ActiveProperty(name="userdb_status",
                                  value=gettext("Datenbank nicht erreichbar"),
                                  style='danger',
                                  empty=True)

        if status:
            return ActiveProperty(name="userdb_status",
                                  value=gettext("Aktiviert"),
                                  style='success',
                                  capabilities=capabilities)

        return ActiveProperty(name="userdb_status",
                                  value=gettext("Nicht aktiviert"),
                                  empty=True,
                                  capabilities=capabilities)

    @property
    def userdb(self):
        return self._userdb

    @property
    def has_connection(self):
        return True

    @property
    def finance_information(self):
        return FinanceInformation(
            balance=self.user_data.finance_balance,
            transactions=((parse_date(t.valid_on), t.amount) for t in
                          self.user_data.finance_history),
            last_update=parse_date(self.user_data.last_finance_update)
        )

    def payment_details(self) -> PaymentDetails:
        return PaymentDetails(
            recipient="StuRa der TUD - AG DSN",
            bank="Ostsächsische Sparkasse Dresden",
            iban="DE61 8505 0300 3120 2195 40",
            bic="OSDD DE 81 XXX",
            purpose="{id}, {name}, {address}".format(
                id=self.user_data.user_id,
                name=self.user_data.name,
                address=self.user_data.room,
            ),
        )

    def has_property(self, property):
        return property in self.user_data.properties

    @active_prop
    def membership_end_date(self):
        """Implicitly used in :py:meth:`evaluate_status`"""
        return {'value': self.user_data.membership_end_date,
                'tmp_readonly': not self.is_member}

    # Empty setter for "edit" capability
    @membership_end_date.setter
    def membership_end_date(self, end_date):
        pass

    @property
    def is_member(self):
        return self.has_property('member')

    def evaluate_status(self, status: UserStatus):
        message = None
        style = None
        if status.violation:
            message, style = gettext('Verstoß gegen Netzordnung'), 'danger'
        elif not status.account_balanced:
            message, style = gettext('Nicht bezahlt'), 'warning'
        elif status.traffic_exceeded:
            message, style = gettext('Trafficlimit überschritten'), 'danger'
        elif not status.member and self.user_data.membership_begin_date is not None:
            message, style = "{} {}".format(gettext('Mitglied ab'),
                                            self.user_data.membership_begin_date.isoformat()), \
                             'warning'
        elif not status.member:
            message, style = gettext('Kein Mitglied'), 'muted'
        elif status.member and self.membership_end_date.raw_value is not None:
            message, style = "{} {}".format(gettext('Mitglied bis'),
                                            self.membership_end_date.value.isoformat()), \
                             'warning'
        elif status.member:
            message, style = gettext('Mitglied'), 'success'

        if status.member and not status.network_access:
            if message is not None:
                message += ', {}'.format(gettext('Netzzugang gesperrt'))
            else:
                message, style = gettext('Netzzugang gesperrt'), 'danger'

        if message is None:
            message, style = gettext('Ok'), 'success'

        return message, style

    @active_prop
    def wifi_password(self):
        return {'value': self.user_data.wifi_password,
                'style': 'password' if self.user_data.wifi_password is not None else None,
                'description_url': '../pages/service/wlan'}

    @wifi_password.setter
    def wifi_password(self, val):
        raise NotImplementedError

    def reset_wifi_password(self):
        status, result = api.reset_wifi_password(self.user_data.id)

        if status != 200:
            raise UnknownError

        return result


def to_kib(v: int) -> int:
    return (v // 1024) if v is not None else 0


class FinanceInformation(BaseFinanceInformation):
    has_to_pay = True

    def __init__(self, balance, transactions, last_update):
        self._balance = balance
        self._transactions = transactions
        self._last_update = last_update

    @property
    def raw_balance(self):
        return self._balance

    @property
    def last_update(self):
        return self._last_update

    @property
    def history(self):
        return self._transactions
