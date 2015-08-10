#!/usr/bin/env python
# -*- coding: utf-8 -*-

# noinspection PyMethodMayBeStatic
from functools import wraps

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


def feature_required(needed_feature, given_features):
    """

    :param func: The wrapped function
    :param needed_feature: The feature needed
    :param given_features: The set of enabled features
    :return:
    """
    def feature_decorator(func):
        @wraps(func)
        def decorated_view(*args, **kwargs):
            if needed_feature in given_features:
                return func(*args, **kwargs)
            else:
                raise NotImplementedError(
                    "Function '{}' requires feature '{}'"
                        .format(func.__name__, needed_feature)
                )
        return decorated_view
    return feature_decorator

def LdapHelper():
    class _LdapHelper(object):
        # todo add generic LDAP features based on /wu
        # todo find features / parameters to depend on

        @staticmethod
        def authenticate(uid, password):
            raise NotImplementedError

        @staticmethod
        def get(uid):
            raise NotImplementedError


    return _LdapHelper
