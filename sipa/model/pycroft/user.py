# -*- coding: utf-8 -*-
import logging

from sipa.model.user import BaseUser
from sipa.model.finance import BaseFinanceInformation
from sipa.model.fancy_property import active_prop, connection_dependent, \
    unsupported_prop
from sipa.model.misc import PaymentDetails
from sipa.model.exceptions import UserNotFound, PasswordInvalid
from .api import PycroftApi

from flask_login import AnonymousUserMixin
from flask.globals import current_app
from flask_babel import gettext
from werkzeug.local import LocalProxy
from werkzeug.http import parse_date

logger = logging.getLogger(__name__)

endpoint = LocalProxy(lambda: current_app.extensions['pycroft_api']['endpoint'])
token = LocalProxy(lambda: current_app.extensions['pycroft_api']['api_key'])


def api():
    return PycroftApi(endpoint, token)


class User(BaseUser):
    def __init__(self, user_data):
        super().__init__(uid=str(user_data['id']))
        self.cache_user_data(user_data)

    @classmethod
    def get(cls, username):
        status, user_data = api().get_user(username)

        if status != 200:
            raise UserNotFound

        return cls(user_data)

    @classmethod
    def from_ip(cls, ip):
        status, user_data = api().get_user_from_ip(ip)

        if status != 200:
            return AnonymousUserMixin()

        return cls(user_data)

    def re_authenticate(self, password):
        self.authenticate(self._login, password)

    @classmethod
    def authenticate(cls, username, password):
        status, result = api().authenticate(username, password)

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
        self._interfaces = user_data['interfaces']
        self._finance_information = FinanceInformation(
            balance=user_data['finance_balance'],
            transactions=((parse_date(t['valid_on']), t['amount']) for t in
                          user_data['finance_history']),
            last_update=parse_date(user_data['last_finance_update'])
        )

    can_change_password = True

    def change_password(self, old, new):
        status, result = api().change_password(self._id, old, new)

        if status != 200:
            raise PasswordInvalid

    @property
    def traffic_history(self):
        # TODO: Implement
        from random import random

        def rand():
            return random() * 7 * 1024 ** 2

        return [{
            'day': day,
            **(lambda i, o: {
                'input': i,
                'output': o,
                'throughput': i + o,
            })(rand(), rand() * 0.04),
            'credit': random() * 1024 ** 2 * 210,
        } for day in range(7)]

    @property
    def credit(self):
        return self._credit

    max_credit = 105 * 1024 * 1024
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
        return ", ".join(i['mac'] for i in self._interfaces)

    # TODO: Implement changing of MAC

    @active_prop
    def mail(self):
        return self._mail

    @mail.setter
    def mail(self, new_mail):
        result, status = api().change_mail(self._id, self._tmp_password, new_mail)

        if status == 401:
            raise PasswordInvalid
        elif status == 404:
            raise UserNotFound

    @mail.deleter
    def mail(self):
        result, status = api().change_mail(self._id, self._tmp_password, new_mail=None)
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
        api().change_cache_usage(self._id, new_use_cache)

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
