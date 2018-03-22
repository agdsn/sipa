# -*- coding: utf-8 -*-
from flask import Flask, url_for
from flask_login import current_user, login_user
from flask_testing import TestCase

from sipa.login_manager import SipaLoginManager


class AuthenticatedUser:
    def __init__(self, uid):
        self.uid = uid

    def get_id(self):
        return self.uid
    is_authenticated = True
    is_active = True
    is_anonymous = False


class SipaLoginManagerTest(TestCase):
    def create_app(self):
        app = Flask('test')
        app.testing = True
        app.config['SECRET_KEY'] = "foobar"*9
        login_manager = SipaLoginManager(app)

        @app.route('/login')
        def login():
            user = AuthenticatedUser(uid="test_user")
            login_user(user)
            return "OK"

        @app.route('/restricted')
        def restricted():
            return current_user.uid if current_user.is_authenticated else ""

        @login_manager.user_loader
        def load_user(uid):
            return AuthenticatedUser(uid=uid)

        self.mgr = login_manager
        return app

    def login(self):
        response = self.client.get(url_for('login'))
        self.assertEqual(response.data.decode('utf-8'), "OK")


class SipaLoginManagerAuthenticationTest(SipaLoginManagerTest):
    def test_authentication_works(self):
        self.login()
        response = self.client.get(url_for('restricted'))
        self.assertEqual(response.data.decode('utf-8'), "test_user")
