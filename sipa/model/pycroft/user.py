from __future__ import annotations
import logging
from datetime import date
from decimal import Decimal

from pydantic import ValidationError
from schwifty import IBAN

from sipa.model.user import BaseUser
from sipa.model.finance import BaseFinanceInformation
from sipa.model.fancy_property import (
    ActiveProperty,
    UnsupportedProperty,
    Capabilities,
    connection_dependent,
)
from sipa.model.misc import PaymentDetails
from sipa.model.exceptions import UserNotFound, PasswordInvalid, \
    MacAlreadyExists, NetworkAccessAlreadyActive, TerminationNotPossible, UnknownError, \
    ContinuationNotPossible, SubnetFull, UserNotContactableError, TokenNotFound, LoginNotAllowed
from .api import PycroftApi
from .exc import PycroftBackendError
from .schema import UserData, UserStatus
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
            self.user_data: UserData = UserData.model_validate(user_data)
            self._userdb: UserDB = UserDB(self)
        except ValidationError as e:
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

        user = cls.get(result['id'])

        if not user.has_property('sipa_login'):
            raise LoginNotAllowed

        return user

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

    @property
    def realname(self) -> ActiveProperty[str, str]:
        return ActiveProperty[str, str](name="realname", value=self.user_data.name)

    @property
    def birthdate(self) -> ActiveProperty[date, date]:
        return ActiveProperty[date, date](
            name="birthdate", value=self.user_data.birthdate
        )

    @property
    def login(self) -> ActiveProperty[str, str]:
        return ActiveProperty[str, str](name="login", value=self.user_data.login)

    @property
    @connection_dependent
    def ips(self) -> ActiveProperty[str, str]:
        ips = sorted(ip for i in self.user_data.interfaces for ip in i.ips)
        return ActiveProperty[str, str](name="ips", value=", ".join(ips))

    @property
    @connection_dependent
    def mac(self) -> ActiveProperty[str, str]:
        macs = ", ".join(i.mac for i in self.user_data.interfaces)
        return ActiveProperty[str, str](
            name="mac",
            value=macs,
            capabilities=Capabilities.edit_if(len(self.user_data.interfaces) <= 1),
        )

    def change_mac_address(self, new_mac, host_name, password):
        assert len(self.user_data.interfaces) == 1

        status, result = api.change_mac(
            self.user_data.id,
            password,
            self.user_data.interfaces[0].id,
            new_mac,
            host_name,
        )

        if status == 401:
            raise PasswordInvalid
        elif status == 400:
            raise MacAlreadyExists

    @property
    @connection_dependent
    def network_access_active(self) -> ActiveProperty[bool, bool]:
        can_edit = (
            self.user_data.room is not None
            and self.has_property("network_access")
            and not self.user_data.interfaces
        )
        return ActiveProperty[bool, bool](
            name="network_access_active",
            value=bool(self.user_data.interfaces),
            capabilities=Capabilities.edit_if(can_edit),
        )

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

    def estimate_balance(self, end_date) -> str:
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

    @property
    def mail(self) -> ActiveProperty[str, str]:
        return ActiveProperty[str, str](
            name="mail",
            value=self.user_data.mail,
            capabilities=Capabilities.edit_if(self.has_property("mail")),
        )

    def change_mail(self, password: str, new_mail: str, mail_forwarded: bool):
        status, result = api.change_mail(
            self.user_data.id,
            password,
            new_mail,
            mail_forwarded,
        )
        if status == 401:
            raise PasswordInvalid
        elif status == 404:
            raise UserNotFound
        self.user_data.mail_forwarded = mail_forwarded
        self.user_data.mail = new_mail

    @property
    def mail_forwarded(self) -> ActiveProperty[bool, str]:
        value = self.user_data.mail_forwarded
        return ActiveProperty[bool, str](
            name="mail_forwarded",
            raw_value=value,
            value=gettext("Aktiviert") if value else gettext("Nicht aktiviert"),
            capabilities=Capabilities.edit_if(self.has_property("mail")),
        )

    @property
    def mail_confirmed(self) -> ActiveProperty[str, str]:
        confirmed = self.user_data.mail_confirmed
        editable = self.has_property('mail') and self.user_data.mail and not confirmed
        return ActiveProperty(
            name="mail_confirmed",
            value=gettext("Bestätigt") if confirmed else gettext("Nicht bestätigt"),
            style="success" if confirmed else "danger",
            capabilities=Capabilities.edit_if(editable),
        )

    def resend_confirm_mail(self) -> bool:
        return api.resend_confirm_email(self.user_data.id)

    @property
    def address(self) -> ActiveProperty[str | None, str]:
        return ActiveProperty[str | None, str](
            name="address",
            value=self.user_data.room,
        )

    @property
    def status(self) -> ActiveProperty[str, str]:
        value, style = self.evaluate_status(self.user_data.status)
        return ActiveProperty[str, str](name="status", value=value, style=style)

    @property
    def id(self) -> ActiveProperty[str, str]:
        return ActiveProperty[str, str](name="id", value=self.user_data.user_id)


    @property
    def userdb_status(self) -> ActiveProperty[str, str]:
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
    def userdb(self) -> UserDB:
        return self._userdb

    @property
    def has_connection(self) -> bool:
        return True

    @property
    def finance_information(self) -> FinanceInformation:
        return FinanceInformation(
            balance=self.user_data.finance_balance,
            transactions=((parse_date(t.valid_on), t.amount, t.description) for t in
                          self.user_data.finance_history),
            last_update=self.user_data.last_finance_update
        )

    def payment_details(self) -> PaymentDetails:
        return PaymentDetails(
            recipient=current_app.config["PAYMENT_BENEFICIARY"],
            iban=IBAN(current_app.config["PAYMENT_IBAN"], validate_bban=True),
            purpose=f"{self.user_data.user_id}, {self.user_data.name}, {self.user_data.room}",
        )

    def has_property(self, property: str) -> bool:
        return property in self.user_data.properties

    @property
    def membership_end_date(self) -> ActiveProperty[date | None, date | None]:
        """Implicitly used in :py:meth:`evaluate_status`"""
        return ActiveProperty[date | None, date | None](
            name="membership_end_date",
            value=self.user_data.membership_end_date,
            capabilities=Capabilities.edit_if(self.is_member),
        )

    @property
    def is_member(self) -> bool:
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

    @property
    def wifi_password(self) -> ActiveProperty[str | None, str | None]:
        return ActiveProperty(
            name="wifi_password",
            value=self.user_data.wifi_password,
            style="password" if self.user_data.wifi_password is not None else None,
            description_url="../pages/service/wlan",
            capabilities=Capabilities(edit=True, delete=False),
        )

    def reset_wifi_password(self):
        status, result = api.reset_wifi_password(self.user_data.id)

        if status != 200:
            raise UnknownError

        return result

    @classmethod
    def request_password_reset(cls, user_ident, email):
        status, result = api.request_password_reset(user_ident, email.lower())

        if status == 404:
            raise UserNotFound
        elif status == 412:
            raise UserNotContactableError
        elif status != 200:
            raise UnknownError

        return result

    @classmethod
    def password_reset(cls, token, new_password):
        status, result = api.reset_password(token, new_password)

        if status == 403:
            raise TokenNotFound
        elif status != 200:
            raise UnknownError

        return result

    def get_request_repayment(self):
        status, result = api.get_request_repayment(self.user_data.id)

        if status != 200:
            raise UnknownError

        return result


    def post_request_repayment(self, beneficiary: str, iban: IBAN, amount: Decimal):
        status, result = api.post_request_repayment(self.user_data.id, beneficiary, iban, amount)

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
