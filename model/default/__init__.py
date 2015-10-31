# -*- coding: utf-8 -*-

# noinspection PyMethodMayBeStatic
from abc import ABCMeta, abstractmethod
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

Row = namedtuple('Row', ['description', 'property'])


class BaseUser(AuthenticatedUserMixin, metaclass=ABCMeta):
    """The user object containing a minimal amount of functions in order to work
    properly (flask special functions, used methods by sipa)
    """

    def __init__(self, uid):
        """Initialize the User object.

        Note that init itself is not called directly, but mainly by the
        static methods.

        This method should be called by any subclass.  Therefore,
        prepend `super().__init__(uid)`.  After this, other
        variables like `mail`, `group` or `name` can be initialized
        similiarly.

        :param uid:A unique unicode identifier for the User
        """
        self.uid = uid

    def __eq__(self, other):
        return self.uid == other.uid and self.datasource == other.datasource

    @property
    @abstractmethod
    def datasource(self):
        pass

    def get_id(self):
        """Required by flask-login"""
        return self.uid

    @classmethod
    @abstractmethod
    def get(cls, username):
        """Used by user_loader. Return a User instance."""
        pass

    @classmethod
    @abstractmethod
    def from_ip(cls, ip):
        """Return a user based on an ip.

        If there is no user associated with this ip, return AnonymousUserMixin.
        """
        pass

    def re_authenticate(self, password):
        self.authenticate(self.uid, password)

    @classmethod
    @abstractmethod
    def authenticate(cls, username, password):
        """Return a User instance or raise PasswordInvalid"""
        pass

    @property
    @abstractmethod
    def can_change_password(self):
        pass

    @abstractmethod
    def change_password(self, old, new):
        """Change the user's password from old to new.

        Although the password has been checked using
        re_authenticate(), some data sources like those which have to
        perform an LDAP bind need it anyways.
        """
        pass

    @property
    @abstractmethod
    def traffic_history(self):
        """Return the current credit and the traffic history as a dict.

        The history should cover one week.

        The dict syntax is as follows:

        return {'credit': 0,
                'history': [(day, <in>, <out>, <credit>)
                            for day in range(7)]}

        """
        pass

    @property
    @abstractmethod
    def credit(self):
        """Return the current credit in MiB"""
        pass

    def generate_rows(self, description_dict):
        for key, val in description_dict.items():
            yield Row(description=val, property=self.__getattribute__(key))

    @active_prop
    def ips(self):
        pass

    @active_prop
    @abstractmethod
    def realname(self):
        pass

    @active_prop
    @abstractmethod
    def login(self):
        pass

    @active_prop
    @abstractmethod
    def mac(self):
        pass

    @active_prop
    @abstractmethod
    def mail(self):
        pass

    @active_prop
    @abstractmethod
    def user_id(self):
        pass

    @active_prop
    @abstractmethod
    def address(self):
        pass

    @active_prop
    @abstractmethod
    def status(self):
        pass

    @active_prop
    @abstractmethod
    def id(self):
        pass

    @active_prop
    @abstractmethod
    def hostname(self):
        pass

    @active_prop
    @abstractmethod
    def hostalias(self):
        pass

    @property
    @abstractmethod
    def userdb_status(self):
        pass

    @property
    @abstractmethod
    def userdb(self):
        """The actual `BaseUserDB` object"""
        pass


class BaseUserDB(metaclass=ABCMeta):
    def __init__(self, user):
        """Set the `BaseUser` object `user`"""
        self.user = user

    @property
    @abstractmethod
    def has_db(self):
        pass

    @abstractmethod
    def create(self, password):
        pass

    @abstractmethod
    def drop(self):
        pass

    @abstractmethod
    def change_password(self, password):
        pass
