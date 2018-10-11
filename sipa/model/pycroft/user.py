# -*- coding: utf-8 -*-
import logging

from sipa.model.user import BaseUser
from sipa.model.finance import BaseFinanceInformation
from sipa.model.fancy_property import active_prop, connection_dependent, \
    unsupported_prop
from sipa.model.misc import PaymentDetails
from sipa.model.exceptions import UserNotFound, PasswordInvalid, MacAlreadyExists, NetworkAccessAlreadyActive
from .api import PycroftApi

from flask_login import AnonymousUserMixin
from flask.globals import current_app
from flask_babel import gettext
from werkzeug.local import LocalProxy
from werkzeug.http import parse_date

logger = logging.getLogger(__name__)

api: PycroftApi = LocalProxy(lambda: current_app.extensions['pycroft_api'])


class User(BaseUser):
    def __init__(self, user_data):
        super().__init__(uid=str(user_data['id']))
        self.cache_user_data(user_data)

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
        self.authenticate(self._login, password)

    @classmethod
    def authenticate(cls, username, password):
        status, result = api.authenticate(username, password)

        if status != 200:
            raise PasswordInvalid

        return cls.get(result['id'])

    def cache_user_data(self, user_data):
        self._id = user_data['id']
        self._user_id = user_data['user_id']
        self._login = user_data['login']
        self._realname = user_data['name']
        self._status = user_data['status']
        self._address = user_data['room']
        self._mail = user_data['mail']
        self._use_cache = user_data['cache']
        self._credit = user_data['traffic_balance']
        self._traffic_history = user_data['traffic_history']
        self._interfaces = user_data['interfaces']
        self._finance_information = FinanceInformation(
            balance=user_data['finance_balance'],
            transactions=((parse_date(t['valid_on']), t['amount']) for t in
                          user_data['finance_history']),
            last_update=parse_date(user_data['last_finance_update'])
        )

    can_change_password = True

    def change_password(self, old, new):
        status, result = api.change_password(self._id, old, new)

        if status != 200:
            raise PasswordInvalid

    @property
    def traffic_history(self):
        return [{
            'day': parse_date(entry['timestamp']).weekday(),
            'input': to_kib(entry['ingress']),
            'output': to_kib(entry['egress']),
            'throughput': to_kib(entry['ingress']) + to_kib(entry['egress']),
            'credit': to_kib(entry['balance']),
        } for entry in self._traffic_history]

    @property
    def credit(self):
        return to_kib(self._credit)

    max_credit = 210 * 1024 * 1024
    daily_credit = 5 * 1024 * 1024

    @active_prop
    def realname(self):
        return self._realname

    @active_prop
    def login(self):
        return self._login

    @active_prop
    @connection_dependent
    def ips(self):
        return ", ".join(ip for i in self._interfaces for ip in i['ips'])

    @active_prop
    @connection_dependent
    def mac(self):
        return {'value': ", ".join(i['mac'] for i in self._interfaces),
                'tmp_readonly': len(self._interfaces) != 1}

    @active_prop
    @connection_dependent
    def network_access_active(self):
        return {'value': gettext("Aktiviert") if len(self._interfaces) > 0 else gettext("Nicht aktiviert"),
                'tmp_readonly': len(self._interfaces) > 0}

    @network_access_active.setter
    def network_access_active(self, value):
        pass

    def activate_network_access(self, password, mac, birthdate, host_name):
        status, result = api.activate_network_access(self._id, password, mac, birthdate, host_name)

        if status == 401:
            raise PasswordInvalid
        elif status == 400:
            raise MacAlreadyExists
        elif status == 412:
            raise NetworkAccessAlreadyActive

    @mac.setter
    def mac(self, new_mac):
        # if this has been reached despite `tmp_readonly`, this is a bug.
        assert len(self._interfaces) == 1

        status, result = api.change_mac(self._id, self._tmp_password,
                                        self._interfaces[0]['id'], new_mac)

        if status == 401:
            raise PasswordInvalid
        elif status == 400:
            raise MacAlreadyExists

    @active_prop
    def mail(self):
        return self._mail

    @mail.setter
    def mail(self, new_mail):
        status, result = api.change_mail(self._id, self._tmp_password, new_mail)

        if status == 401:
            raise PasswordInvalid
        elif status == 404:
            raise UserNotFound

    @mail.deleter
    def mail(self):
        status, result = api.change_mail(self._id, self._tmp_password, new_mail=None)
        if status == 401:
            raise PasswordInvalid
        elif status == 404:
            raise UserNotFound

    @active_prop
    def address(self):
        return self._address

    @active_prop
    def status(self):
        value, style = evaluate_status(self._status)
        return {'value': value, 'style': style}

    @active_prop
    def id(self):
        return self._user_id

    @active_prop
    def use_cache(self):
        if self._use_cache:
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
        api.change_cache_usage(self._id, new_use_cache)

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
        return self._finance_information

    def payment_details(self) -> PaymentDetails:
        return PaymentDetails(
            recipient="Studentenrat TUD - AG DSN",
            bank="Ostsächsische Sparkasse Dresden",
            iban="DE61 8505 0300 3120 2195 40",
            bic="OSDD DE 81 XXX",
            purpose="{id}, {name}, {address}".format(
                id=self._user_id,
                name=self._realname,
                address=self._address,
            ),
        )


def to_kib(v):
    return (v // 1024) if v is not None else 0


def evaluate_status(status):
    message = None
    style = None
    if status['violation']:
        message, style = gettext('Verstoß gegen Netzordnung'), 'danger'
    elif not status['account_balanced']:
        message, style = gettext('Nicht bezahlt'), 'warning'
    elif status['traffic_exceeded']:
        message, style = gettext('Trafficlimit überschritten'), 'danger'
    elif not status['member']:
        message, style = gettext('Kein Mitglied'), 'muted'

    if status['member'] and not status['network_access']:
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
