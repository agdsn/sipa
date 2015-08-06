#!/usr/bin/env python
# -*- coding: utf-8 -*-

# noinspection PyMethodMayBeStatic
class AuthenticatedUserMixin:
    """The user object which claims to be authenticated
    when “asked” by flask-login.
    """
    def is_authenticated(self):
        """Required by flask-login"""
        return True

    def is_active(self):
        """Required by flask-login"""
        return True

    def is_anonymous(self):
        """Required by flask-login"""
        return False


class BaseUser(object, AuthenticatedUserMixin):
    """The user object containing a minimal amount of functions in order to work
    properly (flask special functions, used methods by sipa)
    """

    def __init__(self, uid):
        """
        Note that init itself is not called directly, but by the static methods.
        :param uid:A unique unicode identifier for the User
        :return:
        """
        self.uid = uid

    def get_id(self):
        """Required by flask-login"""
        return self.uid

    @staticmethod
    def get(username):
        """Used by the user_loader. Shall return a User instance."""
        raise NotImplementedError

    @staticmethod
    def authenticate(username, password):
        """Shall return a User instance or raise PasswordInvalid"""
        raise NotImplementedError

    # Below this line: Actual feature functions
    # TODO complete set of used / needed functions (for all divisions)

    def change_password(self, old, new):
        raise NotImplementedError

    def change_mac_address(self, old, new):
        raise NotImplementedError

    def get_information(self):
        # TODO what should be returned here?i
        raise NotImplementedError

    def get_traffic_data(self):
        raise NotImplementedError
