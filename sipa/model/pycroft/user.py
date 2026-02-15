from __future__ import annotations

import logging
import typing as t
from datetime import date

from pydantic import ValidationError

from sipa.model.user import TableRow
from sipa.model.finance import BaseFinanceInformation
from sipa.model.fancy_property import (
    ActiveProperty,
    UnsupportedProperty,
    PropertyBase,
    Capabilities,
    connection_dependent,
)
from sipa.model.misc import UserPaymentDetails, PaymentDetails
from sipa.model.exceptions import UserNotFound, PasswordInvalid, \
    MacAlreadyExists, NetworkAccessAlreadyActive, TerminationNotPossible, UnknownError, \
    ContinuationNotPossible, SubnetFull, UserNotContactableError, TokenNotFound, LoginNotAllowed, \
    MaximumNumberMPSKClients, NoWiFiPasswordGenerated
from .api import PycroftApi
from .exc import PycroftBackendError
from .schema import UserData, UserStatus
from .userdb import UserDB

from flask_login import AnonymousUserMixin
from flask_babel import gettext
from werkzeug.http import parse_date

from ..mspk_client import MPSKClientEntry

logger = logging.getLogger(__name__)


# TODO drop the sample user make this the only type
# TODO find remaining usages of `BaseUser`
@t.final
class User:
    # TODO remove, this is legacy from flask_login
    is_authenticated = True
    is_active = True
    is_anonymous = False

    uid: int
    user_data: UserData
    api: PycroftApi
    _payment_details: PaymentDetails

    def __init__(
        self,
        user_data: dict,
        api: PycroftApi | None = None,
        payment_details: PaymentDetails | None = None,
    ):
        try:
            self.user_data: UserData = UserData.model_validate(user_data)
            self.login: str = self.user_data.login
            self._userdb: UserDB = UserDB(self.login)
        except ValidationError as e:
            raise PycroftBackendError("Error when parsing user lookup response") from e

        self.uid: str = self.user_data.id

        from flask.globals import current_app
        self.api = api or t.cast(
            PycroftApi,
            current_app.extensions['pycroft_api']
        )
        self._payment_details = payment_details or PaymentDetails(
            recipient=current_app.config["PAYMENT_DETAILS"]["RECIPIENT"],
            bank=current_app.config["PAYMENT_DETAILS"]["BANK"],
            iban=current_app.config["PAYMENT_DETAILS"]["IBAN"],
            bic=current_app.config["PAYMENT_DETAILS"]["BIC"],
        )

    def __eq__(self, other):
        return self.uid == other.uid and self.datasource == other.datasource

    # TODO deprecate / replace by proper api call
    @classmethod
    def get(cls, username: str):
        raise NotImplementedError("You need to migrate to fetch_by_name() instead")

    @classmethod
    def from_ip(cls, ip):
        raise NotImplementedError("You need to migrate to fetch_by_ip() instead")

    def re_authenticate(self, password):
        self.authenticate(self.api, self.user_data.login, password)

    @staticmethod
    def authenticate(api: PycroftApi, username: str, password: str) -> User:
        status, result = api.authenticate(username, password)

        if status != 200:
            raise PasswordInvalid

        user = fetch_by_name(api, result['id'])

        if not user.has_property('sipa_login'):
            raise LoginNotAllowed

        return user

    can_change_password = True

    def change_password(self, old, new):
        status, _ = self.api.change_password(self.user_data.id, old, new)

        if status != 200:
            raise PasswordInvalid

    # TODO just pass through `list[TrafficHistoryEntry]` and move presentation
    # to the blueprint
    @property
    def traffic_history(self):
        return [{
            'day': (d.weekday() if (d := parse_date(entry.timestamp)) else None),
            'input': to_kib(entry.ingress),
            'output': to_kib(entry.egress),
            'throughput': to_kib(entry.ingress) + to_kib(entry.egress),
        } for entry in self.user_data.traffic_history]

    def generate_rows(
        self, description_dict: dict[str, tuple[str, str] | tuple[str]]
    ) -> t.Iterator[TableRow]:
        for key, val in description_dict.items():
            d = self.__text_to_dict(val)
            yield TableRow(
                property=getattr(self, key), description=d["description"], subtext=d.get("subtext")
            )

    @staticmethod
    def __text_to_dict(val: str | t.Sequence[str]) -> dict:
        match val:
            case [d, s]:
                return {"description": d, "subtext": s}
            case [d]:
                return {"description": d}
            case _:
                return {"description": "Error"}

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

        status, _ = self.api.change_mac(
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
        status, _ = self.api.activate_network_access(self.user_data.id, password, mac,
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
        status, _ = self.api.terminate_membership(self.user_data.id, end_date)

        if status == 400:
            raise TerminationNotPossible
        elif status != 200:
            raise UnknownError

    def estimate_balance(self, end_date):
        status, result = self.api.estimate_balance_at_end_of_membership(self.user_data.id, end_date)

        if status == 200:
            return result['estimated_balance']
        else:
            raise UnknownError

    def continue_membership(self):
        status, _ = self.api.continue_membership(self.user_data.id)

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
        status, _ = self.api.change_mail(
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
    def mail_forwarded(self) -> ActiveProperty[str, bool]:
        value = self.user_data.mail_forwarded
        return ActiveProperty[str, bool](
            name="mail_forwarded",
            raw_value=value,
            value=gettext("Aktiviert") if value else gettext("Nicht aktiviert"),
            capabilities=Capabilities.edit_if(self.has_property("mail")),
        )

    @property
    def mail_confirmed(self) -> ActiveProperty[str, str]:
        confirmed = self.user_data.mail_confirmed
        editable = self.has_property('mail') and self.user_data.mail and not confirmed
        return ActiveProperty[str, str](
            name="mail_confirmed",
            value=gettext("Bestätigt") if confirmed else gettext("Nicht bestätigt"),
            style="success" if confirmed else "danger",
            capabilities=Capabilities.edit_if(editable),
        )

    def resend_confirm_mail(self) -> bool:
        return self.api.resend_confirm_email(self.user_data.id)

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
    def userdb_status(self) -> PropertyBase[str, str]:
        status = self.userdb.has_db

        capabilities = Capabilities(edit=True, delete=True)

        if not self.has_property("userdb"):
            return UnsupportedProperty[str, str]("userdb_status")

        if status is None:
            return ActiveProperty[str, str](name="userdb_status",
                                  value=gettext("Datenbank nicht erreichbar"),
                                  style='danger',
                                  empty=True)

        if status:
            return ActiveProperty[str, str](name="userdb_status",
                                  value=gettext("Aktiviert"),
                                  style='success',
                                  capabilities=capabilities)

        return ActiveProperty[str, str](name="userdb_status",
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

    @property
    def finance_balance(self) -> PropertyBase[str, float | None]:
        """The :class:`fancy property <sipa.model.fancy_property.PropertyBase>`
        representing the finance balance"""
        info = self.finance_information
        if not info:
            return UnsupportedProperty("finance_balance")
        return info.balance

    def payment_details(self) -> UserPaymentDetails:
        return self._payment_details.with_purpose(
            f"{self.user_data.user_id}, {self.user_data.name}, {self.user_data.room}",
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
    def mpsk_clients(self) -> ActiveProperty[list[MPSKClientEntry], list[MPSKClientEntry]]:
        return ActiveProperty(
            name="mpsk_clients",
            value=self.user_data.mpsk_clients,
            capabilities=Capabilities(edit=True, displayable=False),
        )

    def change_mpsk_clients(self, mac, name, mpsk_id, password: str):
        status, _ = self.api.change_mpsk(
            user_id=self.user_data.id,
            mac=mac,
            name=name,
            mpsk_id=mpsk_id,
            password=password,
        )

        if status == 400:
            raise ValueError(f"mac: {mac} not found for user")
        elif status == 409:
            raise MacAlreadyExists
        elif status == 422:
            raise ValueError

    def add_mpsk_client(self, name, mac, password):
        status, response = self.api.add_mpsk(
            self.user_data.id,
            password,
            mac,
            name)
        if status == 400:
            raise MaximumNumberMPSKClients
        elif status == 409:
            raise MacAlreadyExists
        elif status == 422:
            raise ValueError
        elif status == 412:
            raise NoWiFiPasswordGenerated

        if 'name' in response.keys() and 'mac' in response.keys() and 'id' in response.keys():
            return MPSKClientEntry(name=response.get('name'), mac=response.get('mac'), id=response.get('id'))
        else:
            raise ValueError(f"Invalid response from {response}")

    def delete_mpsk_client(self, mpsk_id, password):
        status, _ = self.api.delete_mpsk(
            self.user_data.id,
            password,
            mpsk_id,
        )
        if status == 400 or status == 401:
            raise ValueError(f'Mpsk client not found for user: {mpsk_id}')

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
            if len(self.user_data.interfaces) > 0:
                message += ', {}'.format(gettext('Netzzugang gesperrt'))
            else:
                message += ', {}'.format(gettext('Kabelgebundener Zugang nicht aktiviert'))

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
            capabilities=Capabilities(edit=True, copyable=True),
        )

    def reset_wifi_password(self):
        status, result = self.api.reset_wifi_password(self.user_data.id)

        if status != 200:
            raise UnknownError

        return result


def fetch_by_name(api: PycroftApi, username: str) -> User:
    status, user_data = api.get_user(username)

    if status != 200:
        raise UserNotFound

    # TODO can we reasonably ensure that `user` is a `LiteralString`?
    #  It is not user-provided, but pycroft-provided.
    #  so in _some sense_ it is internally controlled, but in another it is not.
    #  Perhaps a conscious cast at this one point should be fine.
    return User(user_data)


def fetch_by_ip(api: PycroftApi, ip) -> User | AnonymousUserMixin:
    status, user_data = api.get_user_from_ip(ip)

    if status != 200:
        return AnonymousUserMixin()

    return User(user_data)


def request_password_reset(api: PycroftApi, user_ident: str, email: str) -> dict:
    status, result = api.request_password_reset(user_ident, email.lower())

    if status == 404:
        raise UserNotFound
    elif status == 412:
        raise UserNotContactableError
    elif status != 200:
        raise UnknownError

    return result


def password_reset(api: PycroftApi, token: str, new_password: str) -> dict:
    status, result = api.reset_password(token, new_password)

    if status == 403:
        raise TokenNotFound
    elif status != 200:
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

