#!/usr/bin/env python
# -*- coding: utf-8 -*-

class BaseUser(object):
    """The user object containing a minimal amount of functions in order to work
    properly (flask special functions, used methods by sipa)
    """

    def __init__(self, uid):
        self.uid = uid


    def is_authenticated(self):
        """Required by flask-login"""
        return True


    def is_active(self):
        """Required by flask-login"""
        return True


    def is_anonymous(self):
        """Required by flask-login"""
        return False


    def get_id(self):
        """Required by flask-login"""
        raise NotImplementedError


    @staticmethod
    def get(username):
        """used by the user_loader"""
        raise NotImplementedError


    @staticmethod
    def authenticate(username, password):
        """Returns an instance or raises PasswordInvalid"""
        raise NotImplementedError


    def change_password(self, old, new):
        raise NotImplementedError


    def get_information(self):
        raise NotImplementedError


    def get_traffic_data(self):
        raise NotImplementedError
