from flask_login import AnonymousUserMixin

from sipa.model.fancy_property import unsupported_prop, active_prop
from ..user import BaseUser


class User(BaseUser):
    @classmethod
    def get(cls, username):
        return cls(uid=username)

    @classmethod
    def from_ip(cls, ip):
        return AnonymousUserMixin()

    @classmethod
    def authenticate(cls, username, password):
        return AnonymousUserMixin()

    can_change_password = False

    def change_password(self, old, new):
        raise NotImplementedError

    @property
    def traffic_history(self):
        return []

    @property
    def credit(self):
        return 0

    @active_prop
    def realname(self):
        return "Pycroft"

    @active_prop
    def login(self):
        return "root"

    @active_prop
    def mac(self):
        return "00:bb:ee:ff:cc:dd"

    @active_prop
    def address(self):
        return "Wundtstraße"

    @active_prop
    def status(self):
        return "Zukunftsfähig"

    @property
    def userdb_status(self):
        raise NotImplementedError

    @property
    def userdb(self):
        raise NotImplementedError

    @property
    def has_connection(self):
        raise NotImplementedError

    @property
    def last_finance_update(self):
        raise NotImplementedError

    @unsupported_prop
    def mail(self):
        raise NotImplementedError

    @unsupported_prop
    def id(self):
        raise NotImplementedError

    @unsupported_prop
    def hostname(self):
        return

    @unsupported_prop
    def hostalias(self):
        return

    @unsupported_prop
    def finance_balance(self):
        raise NotImplementedError
