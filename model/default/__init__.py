#!/usr/bin/env python
# -*- coding: utf-8 -*-

# noinspection PyMethodMayBeStatic
from collections import namedtuple
from model.property import active_prop


# noinspection PyMethodMayBeStatic
class AuthenticatedUserMixin:
    """The user object which claims to be authenticated
    when “asked” by flask-login.
    """
    is_authenticated = True
    is_active = True
    is_anonymous = False


# TODO: update Baseuser after migration
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

    @classmethod
    def get(cls, username):
        """Used by user_loader. Return a User instance."""
        raise NotImplementedError

    @classmethod
    def from_ip(cls, ip):
        """Return a user based on an ip.

        If there is no user associated with this ip, return AnonymousUserMixin.
        """
        raise NotImplementedError

    def re_authenticate(self, password):
        self.authenticate(self.uid, password)

    @classmethod
    def authenticate(cls, username, password):
        """Return a User instance or raise PasswordInvalid"""
        raise NotImplementedError

    def change_password(self, old, new):
        """Change the user's password from old to new.

        Although the password has been checked using
        re_authenticate(), some data sources like those which have to
        perform an LDAP bind need it anyways.
        """
        raise NotImplementedError

    # TODO: check whether this is needed, *should* be obsolete
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

    # TODO: somehow structure that user_db

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

    def rows(self, description_dict):
        # TODO: move to useful direction
        Row = namedtuple('Row', ['description', 'property'])

        for key, val in description_dict.items():
            yield Row(description=val, property=self.__getattribute__(key))

    @active_prop
    def ips(self):
        raise NotImplementedError

    @active_prop
    def login(self):
        return self.uid

    @active_prop
    def mac(self):
        raise NotImplementedError

    @active_prop
    def mail(self):
        raise NotImplementedError

    @active_prop
    def user_id(self):
        raise NotImplementedError

    @active_prop
    def address(self):
        raise NotImplementedError

    @active_prop
    def status(self):
        return "OK"

    @active_prop
    def id(self):
        raise NotImplementedError

    @active_prop
    def hostname(self):
        raise NotImplementedError

    @active_prop
    def hostalias(self):
        raise NotImplementedError

    @property
    def userdb(self):
        return None
