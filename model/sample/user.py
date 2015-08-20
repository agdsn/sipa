# -*- coding: utf-8 -*-
from random import random

from flask.ext.login import AnonymousUserMixin

from model.constants import FULL_FEATURE_SET, info_property, ACTIONS, \
    STATUS_COLORS, WEEKDAYS
from model.default import BaseUser
from sipa.utils.exceptions import PasswordInvalid, UserNotFound


def init_context(app):
    pass


# noinspection PyMethodMayBeStatic
class User(BaseUser):
    """User object will be created from LDAP credentials,
    only stored in session.

    the terms 'uid' and 'username' refer to the same thing.
    """

    def __init__(self, uid, name, mail, ip=None):
        super(User, self).__init__(uid)
        self.name = name
        self.group = "static group"
        self.mail = mail
        self._ip = ip

    def _get_ip(self):
        self._ip = "127.0.0.1"

    def __repr__(self):
        return "User<{},{}.{}>".format(self.uid, self.name, self.group)

    def __str__(self):
        return "User {} ({}), {}".format(self.name, self.uid, self.group)

    login_list = {
        'test': ('test', 'Test Nutzer', 'test@agdsn.de'),
    }


    @staticmethod
    def get(username, **kwargs):
        """Static method for flask-login user_loader,
        used before _every_ request.
        """
        if username in User.login_list:
            return User(username, *(User.login_list[username][1:3]), **kwargs)
        else:
            return AnonymousUserMixin()

    @staticmethod
    def authenticate(username, password):

        if username in User.login_list:
            if User.login_list[username][0] == password:
                return User.get(username)
            else:
                raise PasswordInvalid
        else:
            raise UserNotFound

    @staticmethod
    def from_ip(ip):
        return AnonymousUserMixin()

    def change_password(self, old, new):
        raise NotImplementedError("Function change_password not implemented")

    _supported_features = FULL_FEATURE_SET - {
        'userdb', 'mac_change', 'mail_change', 'password_change'
    }

    def get_information(self):
        return {
            'id': info_property("1337-0"),
            'uid': info_property("test"),
            'address': info_property(u"Serverraum, Wundtstraße 5"),
            'mail': info_property(self.mail),
            'status': info_property("OK", STATUS_COLORS.GOOD),
            'ip': info_property("127.0.0.1", STATUS_COLORS.INFO),
            'mac': info_property("aa:bb:cc:dd:ee:ff"),
            'hostname': info_property("Serverkiste", actions={ACTIONS.EDIT}),
            'hostalias': info_property("leethaxor")
        }

    def get_traffic_data(self):
        def rand():
            return round(random() * 1024, 2)
        return {'credit': 0,
                'history': [(WEEKDAYS[str(day)], rand(), rand(), rand())
                            for day in range(7)]}

    def get_current_credit(self):
        return round(random() * 1024 * 63, 2)

    def change_mac_address(self):
        raise NotImplementedError("Function change_mac_address not implemented")
