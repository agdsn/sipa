from flask_login import AnonymousUserMixin

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

    @property
    def realname(self):
        return "Pycroft"

    @property
    def login(self):
        return "root"

    @property
    def mac(self):
        return "00:bb:ee:ff:cc:dd"

    @property
    def mail(self):
        return "pycroft@agd.sn"

    @property
    def address(self):
        return "Wundtstraße"

    @property
    def status(self):
        return "Zukunftsfähig"

    @property
    def id(self):
        return 0

    @property
    def hostname(self):
        return

    @property
    def hostalias(self):
        return

    @property
    def userdb_status(self):
        return

    @property
    def userdb(self):
        return

    @property
    def has_connection(self):
        return

    @property
    def finance_balance(self):
        return 0

    @property
    def last_finance_update(self):
        return
