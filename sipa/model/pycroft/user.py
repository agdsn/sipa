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

    @unsupported_prop
    def realname(self):
        return "Pycroft"

    @unsupported_prop
    def login(self):
        return "root"

    @unsupported_prop
    def mac(self):
        return "00:bb:ee:ff:cc:dd"

    @unsupported_prop
    def mail(self):
        return "pycroft@agd.sn"

    @unsupported_prop
    def address(self):
        return "Wundtstraße"

    @unsupported_prop
    def status(self):
        return "Zukunftsfähig"

    @unsupported_prop
    def id(self):
        return 0

    @unsupported_prop
    def hostname(self):
        return

    @unsupported_prop
    def hostalias(self):
        return

    @unsupported_prop
    def userdb_status(self):
        return

    @unsupported_prop
    def userdb(self):
        return

    @unsupported_prop
    def has_connection(self):
        return

    @unsupported_prop
    def finance_balance(self):
        return 0

    @unsupported_prop
    def last_finance_update(self):
        return
