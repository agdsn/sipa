import typing as t
from datetime import datetime, date
from random import random

from flask import current_app
from flask_login import AnonymousUserMixin
from werkzeug.local import LocalProxy

from sipa.model.exceptions import PasswordInvalid, UserNotFound
from sipa.model.fancy_property import (
    ActiveProperty,
    Capabilities,
    UnsupportedProperty,
)
from sipa.model.finance import BaseFinanceInformation
from sipa.model.misc import PaymentDetails
from sipa.model.mspk_client import MPSKClientEntry
from sipa.model.user import BaseUser
from sipa.utils import argstr


class SampleUserData(t.TypedDict):
    name: str
    id: str
    uid: str
    password: str
    address: str
    mail: str
    mail_forwarded: bool
    mail_confirmed: bool
    mac: str
    ip: str
    status: str
    membership_end_date: str | None
    is_member: bool
    mpsk_clients: list[MPSKClientEntry] | None

def init_app(app):
    app.extensions['sample_users'] = {
        'test': {
            'name': 'Test User',
            'id': '1337-0',
            'uid': 'test',
            'password': 'test',
            'address': "Keller, Wundtstr. 5",
            'mail': 'test@agdsn.de',
            'mail_forwarded': True,
            'mail_confirmed': True,
            'mac': 'aa:bb:cc:dd:ee:ff',
            'ip': '141.30.228.39',
            'mpsk_clients': [MPSKClientEntry(name="Hallo", id=0, mac="11:11:11:11:11")],
            'status': "OK",
            'membership_end_date': None,
            'is_member': True,
        }
    }


config = LocalProxy(lambda: current_app.extensions['sample_users'])


class SampleFinanceInformation(BaseFinanceInformation):
    has_to_pay = True

    @property
    def raw_balance(self):
        """Some random balance"""
        return random() * 10 - 5

    @property
    def history(self):
        return [
            (datetime(2016, 4, 1), 21, "Desc 1"),
            (datetime(2016, 4, 30), -3.5, "Desc 2"),
            (datetime(2023, 12, 23), -3.5, "Desc 3"),
        ]

    @property
    def last_update(self):
        return max(l[0] for l in self.history)

# noinspection PyMethodMayBeStatic
class User(BaseUser):
    def __init__(self, uid):
        super().__init__(uid)
        self.config: SampleUserData = config[uid]
        self._realname = self.config["name"]
        self.old_mail = self.config["mail"]
        self._ip = "127.0.0.1"

    def __repr__(self):
        return "{}.{}({})".format(__name__, type(self).__name__, argstr(
            uid=self.uid,
            realname=self._realname,
            mail=self.mail,
            ip=self._ip,
        ))

    can_change_password = True

    login_list = {
        'test': ('test', 'Test Nutzer', 'test@agdsn.de'),
    }

    @classmethod
    def get(cls, username):
        """Static method for flask-login user_loader,
        used before _every_ request.
        """
        if username in config:
            return cls(username)
        else:
            return AnonymousUserMixin()

    @classmethod
    def authenticate(cls, username, password):
        if username in config:
            if config[username]['password'] == password:
                return cls.get(username)
            else:
                raise PasswordInvalid
        else:
            raise UserNotFound

    @classmethod
    def from_ip(cls, ip):
        return cls.get('test')

    def change_password(self, old, new):
        self.config["password"] = new

    @property
    def traffic_history(self):
        def rand():
            return random() * 7 * 1024**2
        return [{
            'day': day,
            **(lambda i, o: {
                'input': i,
                'output': o,
                'throughput': i + o,
            })(rand(), rand()*0.04),
        } for day in range(7)]

    @property
    def realname(self):
        return ActiveProperty[str, str](name="realname", value=self._realname)

    @property
    def login(self):
        return ActiveProperty[str, str](name="login", value=self.uid)

    @property
    def mac(self):
        return ActiveProperty[str, str](
            name="mac",
            value=self.config["mac"],
            capabilities=Capabilities(edit=True, delete=False, displayable=True),
        )

    @mac.setter
    def mac(self, value):
        self.config["mac"] = value

    @property
    def mpsk_clients(self) -> ActiveProperty[str | None, list | None]:
        return ActiveProperty(name="mpsk_clients", value=self.config["mpsk_clients"], capabilities=Capabilities(edit=True, delete=False, displayable=False))

    @mpsk_clients.setter
    def mpsk_clients(self, value):
        self.config["mpsk_clients"] = value

    def change_mpsk_clients(self, mac, name, mpsk_id, password: str):
        if mpsk_id in range(len(self.config["mpsk_clients"])):
            self.config["mpsk_clients"][mpsk_id].name = name
            self.config["mpsk_clients"][mpsk_id].mac = mac
        else:
            raise ValueError(f"mac: {mac} not found for user")

    def add_mpsk_client(self, name, mac, password):
        dev = MPSKClientEntry(mac=mac, name=name, id=len(self.config["mpsk_clients"]))
        return dev

    def delete_mpsk_client(self, mpsk_id: int, password):

        if mpsk_id <= len(self.config["mpsk_clients"]):
            self.config["mpsk_clients"].pop(mpsk_id)
        else:
            raise ValueError(f"Id: {mpsk_id} not found for user")

    @property
    def mail(self):
        return ActiveProperty[str, str](
            name="mail",
            value=self.config["mail"],
            capabilities=Capabilities(edit=True, delete=False, displayable=True),
        )

    def change_mail(self, password: str, new_mail: str, mail_forwarded: bool):
        self.config["mail"] = new_mail

    @property
    def mail_forwarded(self):
        return ActiveProperty[bool, bool](
            name="mail_forwarded", value=self.config["mail_forwarded"]
        )

    @property
    def mail_confirmed(self):
        return ActiveProperty[bool, bool](
            name="mail_confirmed", value=self.config["mail_confirmed"]
        )

    def resend_confirm_mail(self) -> bool:
        """ Resend the confirmation mail."""
        pass

    @mail.setter
    def mail(self, value: str) -> None:
        self.config["mail"] = value

    @property
    def network_access_active(self):
        return ActiveProperty[bool, bool](
            name="network_access_active",
            value=True,
            capabilities=Capabilities(edit=True, delete=False, displayable=True),
        )

    @property
    def address(self):
        return ActiveProperty[str, str](name="address", value=self.config["address"])

    @property
    def ips(self):
        return ActiveProperty[str, str](name="ips", value=self.config["ip"])

    @property
    def status(self):
        status_str = self.config["status"]
        value = (
            status_str
            if not self.membership_end_date
            else f"{status_str} (ends at {self.membership_end_date.value})"
        )
        return ActiveProperty[str, str](name="status", value=value)

    has_connection = True

    @property
    def id(self):
        return ActiveProperty[str, str](name="id", value=self.config["id"])

    @property
    def userdb_status(self):
        return UnsupportedProperty("userdb_status")

    @property
    def birthdate(self):
        return UnsupportedProperty("birthdate")

    def payment_details(self) -> PaymentDetails:
        return PaymentDetails(
            recipient="Donald Duck",
            bank="Geldspeicher GbR",
            iban="EH12432543209523",
            bic="ENTHAUS123",
            purpose=self.id.value,
        )

    @property
    def membership_end_date(self):
        print(self.config)
        return ActiveProperty[date | None, date | None](
            name="membership_end_date",
            value=self.config["membership_end_date"],
            capabilities=Capabilities.edit_if(self.is_member),
        )

    @property
    def is_member(self) -> bool:
        return self.config["is_member"]

    def estimate_balance(self, end_date):
        return random() * 10 - 5

    def terminate_membership(self, end_date):
        self.config["membership_end_date"] = end_date
        print(self.config)

    def continue_membership(self):
        self.config["membership_end_date"] = None

    @property
    def wifi_password(self):
        return ActiveProperty[str, str](name="wifi_password", value="password")

    @classmethod
    def request_password_reset(cls, user_ident, email):
        raise NotImplementedError

    @classmethod
    def password_reset(cls, token, new_password):
        raise NotImplementedError

    userdb = None

    finance_information = SampleFinanceInformation()
