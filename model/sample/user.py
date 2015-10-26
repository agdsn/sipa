# -*- coding: utf-8 -*-
from random import random

from flask.ext.login import AnonymousUserMixin

from model.constants import WEEKDAYS
from model.default import BaseUser
from model.property import active_prop, unsupported_prop

from sipa.utils.exceptions import PasswordInvalid, UserNotFound

import configparser


PATH = "/tmp/sipa_sample.conf"


def init_context(app):
    config = configparser.RawConfigParser()
    config.add_section('test')
    config.set('test', 'name', 'Test User')
    config.set('test', 'id', '1337-0')
    config.set('test', 'uid', 'test')
    config.set('test', 'password', 'test')
    config.set('test', 'address', "Keller, Wundtstr. 5")
    config.set('test', 'mail', 'test@agdsn.de')
    config.set('test', 'mac', 'aa:bb:cc:dd:ee:ff')
    config.set('test', 'ip', '141.30.228.39')
    config.set('test', 'hostname', 'My_Server')
    config.set('test', 'hostalias', 'leethax0r')

    with open(PATH, 'w', encoding='utf-8') as conf_file:
        config.write(conf_file)


# noinspection PyMethodMayBeStatic
class User(BaseUser):
    datasource = 'sample'

    def __init__(self, uid, name=None, mail=None, ip=None):
        super(User, self).__init__(uid)
        self.config = self._get_config()
        self.name = self.config.get(uid, 'name')
        self.group = "static group"
        self.old_mail = self.config.get(uid, 'mail')
        self._ip = ip if ip else "127.0.0.1"

    def __repr__(self):
        return "{}.{}({})".format(__name__, type(self).__name__, argstr(
            uid=self.uid,
            name=self.name,
            mail=self.mail,

        ))


    @staticmethod
    def _get_config():
        config = configparser.RawConfigParser()
        config.read(PATH)
        return config

    def _write_config(self):
        with open(PATH, 'wb') as conf_file:
            self.config.write(conf_file)
        self.config = User._get_config()

    def __repr__(self):
        return "User<{},{}.{}>".format(self.uid, self.name, self.group)

    def __str__(self):
        return "User {} ({}), {}".format(self.name, self.uid, self.group)

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
        self.config.set('test', 'password', new)
        self._write_config()

    def get_traffic_data(self):
        def rand():
            return round(random() * 1024, 2)
        return {'credit': 0,
                'history': [(WEEKDAYS[day], rand(), rand()*0.1, rand())
                            for day in range(7)]}

    def get_current_credit(self):
        return round(random() * 1024 * 63, 2)

    @active_prop
    def login(self):
        return self.uid

    @active_prop
    def mac(self):
        return self.config.get('test', 'mac')

    @mac.setter
    def mac(self, value):
        self.config.set(self.uid, 'mac', value)
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
