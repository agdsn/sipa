# -*- coding: utf-8 -*-
from random import random

from flask.ext.login import AnonymousUserMixin

from model.constants import WEEKDAYS
from model.default import BaseUser
from model.property import active_prop, unsupported_prop

from sipa.utils import argstr
from sipa.utils.exceptions import PasswordInvalid, UserNotFound

import configparser


PATH = "/tmp/sipa_sample.conf"


def init_context(app):
    config = configparser.ConfigParser()
    config['test'] = {
        'name': 'Test User',
        'id': '1337-0',
        'uid': 'test',
        'password': 'test',
        'address': "Keller, Wundtstr. 5",
        'mail': 'test@agdsn.de',
        'mac': 'aa:bb:cc:dd:ee:ff',
        'ip': '141.30.228.39',
        'hostname': 'My_Server',
        'hostalias': 'leethax0r',
    }

    with open(PATH, 'w') as conf_file:
        config.write(conf_file)


# noinspection PyMethodMayBeStatic
class User(BaseUser):
    datasource = 'sample'

    def __init__(self, uid):
        super(User, self).__init__(uid)
        self.config = self._get_config()
        self.name = self.config[uid]['name']
        self.old_mail = self.config[uid]['mail']
        self._ip = "127.0.0.1"

    def __repr__(self):
        return "{}.{}({})".format(__name__, type(self).__name__, argstr(
            uid=self.uid,
            name=self.name,
            mail=self.mail,
            ip=self._ip,
        ))

    can_change_password = True

    login_list = {
        'test': ('test', 'Test Nutzer', 'test@agdsn.de'),
    }

    @classmethod
    def get(cls, username, **kwargs):
        """Static method for flask-login user_loader,
        used before _every_ request.
        """
        config = cls._get_config()
        if config.has_section(username):
            return cls(username)
        else:
            return AnonymousUserMixin()

    @classmethod
    def authenticate(cls, username, password):
        config = cls._get_config()

        if config.has_section(username):
            if config.get(username, 'password') == password:
                return cls.get(username)
            else:
                raise PasswordInvalid
        else:
            raise UserNotFound

    @classmethod
    def from_ip(cls, ip):
        return cls.get('test')

    def change_password(self, old, new):
        self.config[self.uid]['password'] = new
        self._write_config()

    @property
    def traffic_history(self):
        def rand():
            return random() * 1024
        return [{
            'day': WEEKDAYS[day],
            'input': rand(),
            'output': rand()*0.1,
            'throughput': rand(),
            'credit': random() * 1024 * 63,
        } for day in range(7)]

    @property
    def credit(self):
        return random() * 1024 * 63

    @active_prop
    def realname(self):
        return self.name

    @active_prop
    def login(self):
        return self.uid

    @active_prop
    def mac(self):
        return self.config.get('test', 'mac')

    @mac.setter
    def mac(self, value):
        self.config.set('test', 'mac', value)
        self._write_config()

    @active_prop
    def mail(self):
        return self.config.get('test', 'mail')

    @mail.setter
    def mail(self, value):
        self.config.set(self.uid, 'mail', value)
        self._write_config()

    @mail.deleter
    def mail(self):
        self.config.set(self.uid, 'mail', "")
        self._write_config()

    @active_prop
    def address(self):
        return self.config.get('test', 'address')

    @active_prop
    def ips(self):
        return self.config.get('test', 'ip')

    @active_prop
    def status(self):
        return "OK"

    @active_prop
    def id(self):
        return self.config.get('test', 'id')

    @active_prop
    def hostname(self):
        return self.config.get('test', 'hostname')

    @active_prop
    def hostalias(self):
        return self.config.get('test', 'hostalias')

    @unsupported_prop
    def userdb_status(self):
        pass

    userdb = None
