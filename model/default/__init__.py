#!/usr/bin/env python
# -*- coding: utf-8 -*-

# noinspection PyMethodMayBeStatic

from model.constants import FULL_FEATURE_SET, DISPLAY_FEATURE_SET


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

    def __eq__(self, other):
        return self.uid == other.uid

    def get_id(self):
        """Required by flask-login"""
        return self.uid

    def _get_ip(self):
        """Get the IP (usually from self.uid)"""
        raise NotImplementedError

    @property
    def ip(self):
        if self._ip is None:
            self._get_ip()
        return self._ip

    @staticmethod
    def get(username):
        """Used by the user_loader. Shall return a User instance."""
        raise NotImplementedError

    def re_authenticate(self, password):
        self.authenticate(self.uid, password)

    @staticmethod
    def authenticate(username, password):
        """Shall return a User instance or raise PasswordInvalid"""
        raise NotImplementedError

    # Below this line: Actual feature functions
    # TODO complete set of used / needed functions (for all divisions)

    _supported_features = set()

    @classmethod
    def supported(cls):
        return cls._supported_features

    @classmethod
    def unsupported(cls, display=False):
        return (DISPLAY_FEATURE_SET if display
                else FULL_FEATURE_SET) - cls._supported_features

    def change_password(self, old, new):
        raise NotImplementedError

    def change_mac_address(self, old, new):
        raise NotImplementedError

    def change_mail(self, password, new_mail):
        raise NotImplementedError

    def get_information(self):
        # TODO what should be returned here?i
        raise NotImplementedError

    def get_traffic_data(self):
        raise NotImplementedError

    def get_current_credit(self):
        raise NotImplementedError

    def has_user_db(self):
        raise NotImplementedError

    def user_db_create(self, password):
        raise NotImplementedError

    def user_db_drop(self):
        raise NotImplementedError

    def user_db_password_change(self, password):
        raise NotImplementedError

