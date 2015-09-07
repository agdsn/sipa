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


class BaseUser(AuthenticatedUserMixin):
    """The user object containing a minimal amount of functions in order to work
    properly (flask special functions, used methods by sipa)
    """

    def __init__(self, uid):
        """Initialize the User object.

        Note that init itself is not called directly, but mainly by the
        static methods.

        This method should be called by any subclass.  Therefore,
        prepend `super(User, self).__init__(uid)`.  After this, other
        variables like `mail`, `group` or `name` can be initialized
        similiarly.

        :param uid:A unique unicode identifier for the User
        """
        self.uid = uid

    def __eq__(self, other):
        return self.uid == other.uid

    def get_id(self):
        """Required by flask-login"""
        return self.uid

    def _get_ip(self):
        """Get the IP (usually from self.uid)

        This method sets self._ip accordingly.

        It is used to provide the `ip` property as implemented below.
        """
        raise NotImplementedError

    @property
    def ip(self):
        if self._ip is None:
            self._get_ip()
        return self._ip

    @staticmethod
    def get(username):
        """Used by user_loader. Return a User instance."""
        raise NotImplementedError

    @staticmethod
    def from_ip(ip):
        """Return a user based on an ip.

        If there is no user associated with this ip, return AnonymousUserMixin.
        """
        raise NotImplementedError

    def re_authenticate(self, password):
        self.authenticate(self.uid, password)

    @staticmethod
    def authenticate(username, password):
        """Return a User instance or raise PasswordInvalid"""
        raise NotImplementedError

    _supported_features = set()

    @classmethod
    def supported(cls):
        return cls._supported_features

    @classmethod
    def unsupported(cls, display=False):
        return (DISPLAY_FEATURE_SET if display
                else FULL_FEATURE_SET) - cls._supported_features

    def change_password(self, old, new):
        """Change the user's password from old to new.

        Although the password has been checked using
        re_authenticate(), some data sources like those which have to
        perform an LDAP bind need it anyways.
        """
        raise NotImplementedError

    def change_mac_address(self, old, new):
        """Change the user's mac address.

        No reauthentication necessary, this is done in usersuite.
        """
        # TODO: Refactor if old address is necessary
        # TODO: implement possibility for multiple devices
        raise NotImplementedError

    def change_mail(self, password, new_mail):
        """Change the user's mail address.

        Although reauthentication has already happened, some modules
        neeed the password to execute the LDAP-bind.
        """
        raise NotImplementedError

    def get_information(self):
        """Return a set of properties.

        Although the properties are actually dicts, use the methods
        from the constants module (like info_property) to generate
        them.  The properties returned should match what is given in
        FULL_FEATURE_SET of the constants module to ensure
        datasource-wide similiarity.  This means, if a certain feature
        does not appear in said set, it should be added and, if
        possible, implemented in the other datasource modules as well.

        A simple example yielding 'value' everywhere would look like
        this:

        return {
            'id': info_property('value'),
            'uid': info_property('value'),
            'address': info_property('value'),
            'mail': info_property('value',
                                  actions={ACTIONS.DELETE}),
            'status': info_property("OK", STATUS_COLORS.GOOD),
            'ip': info_property('value',
                                STATUS_COLORS.INFO),
            'mac': info_property('value',
                                 actions={ACTIONS.EDIT}),
            'hostname': info_property('value'),
            'hostalias': info_property('value')
        }

        NOTE: remember to set _supported_features accordingly.
        Else, fields might get marked `Unsupported`!
        """
        raise NotImplementedError

    def get_traffic_data(self):
        """Return the current credit and the traffic history as a dict.

        The history should cover one week.

        The dict syntax is as follows:

        return {'credit': 0,
                'history': [(WEEKDAYS[str(day)], <in>, <out>, <credit>)
                            for day in range(7)]}

        """
        raise NotImplementedError

    def get_current_credit(self):
        """Return the current credit in MiB"""
        raise NotImplementedError

    def has_user_db(self):
        """Return whether the user activated his userdb"""
        raise NotImplementedError

    def user_db_create(self, password):
        """Create a userdb for the user

        :param password: The password for the userdb
        """
        raise NotImplementedError

    def user_db_drop(self):
        """Delete the userdb completely"""
        raise NotImplementedError

    def user_db_password_change(self, password):
        """Change the password of the userdb"""
        raise NotImplementedError
