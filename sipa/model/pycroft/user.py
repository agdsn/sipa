# -*- coding: utf-8 -*-
import logging

from sipa.model.user import BaseUser
from sipa.model.finance import BaseFinanceInformation
from sipa.model.fancy_property import active_prop, connection_dependent, \
    unsupported_prop
from sipa.model.misc import PaymentDetails
from sipa.model.exceptions import UserNotFound, PasswordInvalid, \
    MacAlreadyExists, NetworkAccessAlreadyActive
from .api import PycroftApi
from .exc import PycroftBackendError
from .schema import UserData, UserStatus
from .unserialize import UnserializationError

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
            'throughput': to_kib(entry.ingress + entry.egress),
            'credit': to_kib(entry.balance),
        } for entry in self.user_data.traffic_history]

    @property
    def credit(self):
        return to_kib(self.user_data.traffic_balance)

    max_credit = 210 * 1024 * 1024
    daily_credit = 5 * 1024 * 1024

    @active_prop
    def realname(self):
        return self.user_data.realname

    @active_prop
    def login(self):
        return self.user_data.login

    @active_prop
    @connection_dependent
    def ips(self):
        return ", ".join(ip for i in self.user_data.interfaces for ip in i.ips)

    @active_prop
    @connection_dependent
    def mac(self):
        return {'value': ", ".join(i['mac'] for i in self.user_data.interfaces),
                'tmp_readonly': len(self.user_data.interfaces) != 1}

    @active_prop
    @connection_dependent
    def network_access_active(self):
        return {'value': (gettext("Aktiviert") if len(self.user_data.interfaces) > 0
                          else gettext("Nicht aktiviert")),
                'tmp_readonly': len(self.user_data.interfaces) > 0}

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
    def mail(self):
        return self.user_data.mail

    @mail.setter
    def mail(self, new_mail):
        status, result = api.change_mail(self.user_data.id, self._tmp_password, new_mail)

        if status == 401:
            raise PasswordInvalid
        elif status == 404:
            raise UserNotFound

    @mail.deleter
    def mail(self):
        status, result = api.change_mail(self.user_data.id, self._tmp_password, new_mail=None)
        if status == 401:
            raise PasswordInvalid
        elif status == 404:
            raise UserNotFound

    @active_prop
    def address(self):
        return self.user_data.room

    @active_prop
    def status(self):
        value, style = evaluate_status(self.user_data.status)
        return {'value': value, 'style': style}

    @active_prop
    def id(self):
        return self.user_data.user_id

    @active_prop
    def use_cache(self):
        if self.user_data.cache:
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
        api.change_cache_usage(self.user_data.id, new_use_cache)

    @unsupported_prop
    def hostname(self):
        raise NotImplementedError

    @unsupported_prop
    def hostalias(self):
        raise NotImplementedError

    @unsupported_prop
    def userdb_status(self):
        raise NotImplementedError

    @unsupported_prop
    def userdb(self):
        raise NotImplementedError

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
            recipient="Studentenrat TUD - AG DSN",
            bank="Ostsächsische Sparkasse Dresden",
            iban="DE61 8505 0300 3120 2195 40",
            bic="OSDD DE 81 XXX",
            purpose="{id}, {name}, {address}".format(
                id=self.user_data.user_id,
                name=self.user_data.realname,
                address=self.user_data.room,
            ),
        )


def to_kib(v: int) -> int:
    return (v // 1024) if v is not None else 0


def evaluate_status(status: UserStatus):
    message = None
    style = None
    if status.violation:
        message, style = gettext('Verstoß gegen Netzordnung'), 'danger'
    elif not status.account_balanced:
        message, style = gettext('Nicht bezahlt'), 'warning'
    elif status.traffic_exceeded:
        message, style = gettext('Trafficlimit überschritten'), 'danger'
    elif not status.member:
        message, style = gettext('Kein Mitglied'), 'muted'

    if status.member and not status.network_access:
        if message is not None:
            message += ', {}'.format(gettext('Netzzugang gesperrt'))
        else:
            message, style = gettext('Netzzugang gesperrt'), 'danger'

    if message is None:
        message, style = gettext('ok'), 'success'

    return (message, style)


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
