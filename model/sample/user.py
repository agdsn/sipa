# -*- coding: utf-8 -*-
from random import random

from flask.ext.login import AnonymousUserMixin

from model.constants import FULL_FEATURE_SET, info_property, ACTIONS, \
    STATUS_COLORS, WEEKDAYS
from model.default import BaseUser
from sipa.utils.exceptions import PasswordInvalid, UserNotFound

import ConfigParser
import os


PATH = "/tmp/sipa_sample.conf"


def init_context(app):
    config = ConfigParser.RawConfigParser()
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

    with open(PATH, 'wb') as conf_file:
        config.write(conf_file)


# noinspection PyMethodMayBeStatic
class User(BaseUser):
    """User object will be created from LDAP credentials,
    only stored in session.

    the terms 'uid' and 'username' refer to the same thing.
    """

    def __init__(self, uid, name=None, mail=None, ip=None):
        super(User, self).__init__(uid)
        self.config = self._get_config()
        self.name = self.config.get(uid, 'name')
        self.group = "static group"
        self.mail = self.config.get(uid, 'mail')
        self._ip = ip

    def _get_ip(self):
        # TODO: check whether / how this function is used.
        self._ip = "127.0.0.1"

    @staticmethod
    def _get_config():
        config = ConfigParser.RawConfigParser()
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

    login_list = {
        'test': ('test', 'Test Nutzer', 'test@agdsn.de'),
    }

    @staticmethod
    def get(username, **kwargs):
        """Static method for flask-login user_loader,
        used before _every_ request.
        """
        config = User._get_config()
        if config.has_section(username):
            return User(username)
        else:
            return AnonymousUserMixin()

    @staticmethod
    def authenticate(username, password):
        config = User._get_config()

        if config.has_section(username):
            if config.get(username, 'password') == password:
                return User.get(username)
            else:
                raise PasswordInvalid
        else:
            raise UserNotFound

    @staticmethod
    def from_ip(ip):
        return AnonymousUserMixin()

    def change_password(self, old, new):
        self.config.set('test', 'password', new)
        self._write_config()

    _supported_features = FULL_FEATURE_SET - {'userdb'}

    def get_information(self):
        mail = self.config.get('test', 'mail')
        if mail:
            mail_actions = {ACTIONS.EDIT, ACTIONS.DELETE}
        else:
            mail_actions = {ACTIONS.EDIT}

        return {
            'id': info_property(self.config.get('test', 'id')),
            'uid': info_property(self.config.get('test', 'uid')),
            'address': info_property(self.config.get('test', 'address')),
            'mail': info_property(self.config.get('test', 'mail'),
                                  actions=mail_actions),
            'status': info_property("OK", STATUS_COLORS.GOOD),
            'ip': info_property(self.config.get('test', 'ip'),
                                STATUS_COLORS.INFO),
            'mac': info_property(self.config.get('test', 'mac'),
                                 actions={ACTIONS.EDIT}),
            'hostname': info_property(self.config.get('test', 'hostname')),
            'hostalias': info_property(self.config.get('test', 'hostalias'))
        }

    def get_traffic_data(self):
        def rand():
            return round(random() * 1024, 2)
        return {'credit': 0,
                'history': [(WEEKDAYS[str(day)], rand(), rand(), rand())
                            for day in range(7)]}

    def get_current_credit(self):
        return round(random() * 1024 * 63, 2)

    def change_mac_address(self, old, new):
        self.config.set(self.uid, 'mac', new)
        self._write_config()

    def change_mail(self, password, new_mail):
        self.config.set(self.uid, 'mail', new_mail)
        self._write_config()
