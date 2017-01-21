# -*- coding: utf-8 -*-
from datetime import datetime
from random import random

from flask import current_app
from flask_login import AnonymousUserMixin
from werkzeug import LocalProxy

from sipa.model.user import BaseUser
from sipa.model.fancy_property import active_prop, unsupported_prop
from sipa.model.finance import BaseFinanceInformation
from sipa.utils import argstr
from sipa.utils.exceptions import PasswordInvalid, UserNotFound


def init_context(app):
    app.extensions['sample_users'] = {
        'test': {
            'name': 'Test User',
            'id': '1337-0',
            'uid': 'test',
            'password': 'test',
            'address': "Keller, Wundtstr. 5",
            'mail': 'test@agdsn.de',
            'mac': 'aa:bb:cc:dd:ee:ff',
            'ip': '141.30.228.39',
            'status': "OK",
            'hostname': 'My_Server',
            'hostalias': 'leethax0r',
        }
    }

config = LocalProxy(lambda: current_app.extensions['sample_users'])


class SampleFinanceInformation(BaseFinanceInformation):
    has_to_pay = True

    @property
    def _balance(self):
        """Some random balance"""
        return random() * 10 - 5

    @property
    def history(self):
        return [
            (datetime(2016, 4, 1), 21),
            (datetime(2016, 4, 30), -3.5),
            (datetime(2016, 5, 30), -3.5),
        ]

    @property
    def last_update(self):
        return max(l[0] for l in self.history)


# noinspection PyMethodMayBeStatic
class User(BaseUser):
    def __init__(self, uid):
        super().__init__(uid)
        self.config = config
        self._realname = config[uid]['name']
        self.old_mail = config[uid]['mail']
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
            'credit': random() * 1024**2 * 63,
        } for day in range(7)]

    @property
    def credit(self):
        return random() * 1024**2 * 63

    max_credit = 63 * 1024 * 1024
    daily_credit = 3 * 1024 * 1024

    @active_prop
    def realname(self):
        return self._realname

    @active_prop
    def login(self):
        return self.uid

    @active_prop
    def mac(self):
        return config[self.uid]['mac']

    @mac.setter
    def mac(self, value):
        config[self.uid]['mac'] = value

    @active_prop
    def mail(self):
        return config[self.uid]['mail']

    @mail.setter
    def mail(self, value):
        config[self.uid]['mail'] = value

    @mail.deleter
    def mail(self):
        self.config[self.uid]['mail'] = ""

    @active_prop
    def address(self):
        return self.config[self.uid]['address']

    @active_prop
    def ips(self):
        return self.config[self.uid]['ip']

    @active_prop
    def status(self):
        return self.config[self.uid]['status']

    has_connection = True

    @active_prop
    def id(self):
        return self.config[self.uid]['id']

    @active_prop
    def hostname(self):
        return self.config[self.uid]['hostname']

    @active_prop
    def hostalias(self):
        return self.config[self.uid]['hostalias']

    @unsupported_prop
    def userdb_status(self):
        pass

    userdb = None

    finance_information = SampleFinanceInformation()
