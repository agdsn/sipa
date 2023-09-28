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
    hostname: str
    hostalias: str
    membership_end_date: str | None
    is_member: bool


def init_context(app):
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
            'status': "OK",
            'hostname': 'My_Server',
            'hostalias': 'leethax0r',
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
            (datetime(2016, 5, 30), -3.5, "Desc 3"),
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
        config[self.uid]['password'] = new

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
            value=config[self.uid]["mac"],
            capabilities=Capabilities(edit=True, delete=False),
        )

    @mac.setter
    def mac(self, value):
        config[self.uid]['mac'] = value

    @property
    def mail(self):
        return ActiveProperty[str, str](
            name="mail",
            value=config[self.uid]["mail"],
            capabilities=Capabilities(edit=True, delete=False),
        )

    @property
    def mail_forwarded(self):
        return ActiveProperty[bool, bool](
            name="mail_forwarded", value=config[self.uid]["mail_forwarded"]
        )

    @property
    def mail_confirmed(self):
        return ActiveProperty[bool, bool](
            name="mail_confirmed", value=config[self.uid]["mail_confirmed"]
        )

    def resend_confirm_mail(self) -> bool:
        """ Resend the confirmation mail."""
        pass

    @mail.setter
    def mail(self, value: str) -> None:
        config[self.uid]['mail'] = value

    @property
    def network_access_active(self):
        return ActiveProperty[bool, bool](
            name="network_access_active",
            value=True,
            capabilities=Capabilities(edit=True, delete=False),
        )

    @network_access_active.setter
    def network_access_active(self, value):
        pass

    @property
    def address(self):
        return ActiveProperty[str, str](
            name="address", value=config[self.uid]["address"]
        )

    @property
    def ips(self):
        return ActiveProperty[str, str](name="ips", value=config[self.uid]["ip"])

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
    def hostname(self):
        return ActiveProperty[str, str](name="hostname", value=self.config["hostname"])

    @property
    def hostalias(self):
        return ActiveProperty[str, str](
            name="hostalias", value=self.config["hostalias"]
        )

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
