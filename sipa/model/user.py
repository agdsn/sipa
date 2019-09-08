from __future__ import annotations
# -*- coding: utf-8 -*-

# noinspection PyMethodMayBeStatic
from abc import ABCMeta, abstractmethod
from collections import namedtuple
from contextlib import contextmanager
from typing import TypeVar, Type, List, Dict, Optional

from sipa.model.fancy_property import active_prop, UnsupportedProperty, PropertyBase
from sipa.model.finance import BaseFinanceInformation
from sipa.model.misc import PaymentDetails


# noinspection PyMethodMayBeStatic
class AuthenticatedUserMixin:
    """A mixin object defining a User class to be authenticated and
    active.

    Simliar to flask-login's
    :py:class:`~flask_login.AnonymousUserMixin`, this class defines a
    user which is active, authenticated, and not anonymous.
    """
    is_authenticated = True
    is_active = True
    is_anonymous = False


Row = namedtuple('Row', ['description', 'property'])

# for annotating the classmethods
T = TypeVar('T', bound='BaseUser')


class BaseUser(AuthenticatedUserMixin, metaclass=ABCMeta):
    """Abstract base class defining what a user must have in order to
    work properly with sipa.

    Note that initialization shouldn't be done via :meth:`__init__`
    directly, but usign one of the classmethods :meth:`get`,
    :meth:`authenticate` or :meth:`from_ip`!

    Apart from being an ABC, this class provides some logic already.

    This includes setting :data:`uid` in :meth:`__init__`, defining
    equality, and some others.

    This class adheres to the protocol imposed by
    :class:`Flask-Login <flask_login:flask_login.UserMixin>`

    Abstract methods / properties are prepended with ``[Abstract]``.
    """

    def __init__(self, uid):
        #: A unique unicode identifier for the User, needed for
        #: :meth:`get_id`
        self.uid = uid

    def __eq__(self, other):
        return self.uid == other.uid and self.datasource == other.datasource

    datasource = None

    def get_id(self):
        """This method is Required by flask-login."""
        return self.uid

    @classmethod
    @abstractmethod
    def get(cls: Type[T], username: str) -> T:
        """Fetch a user given his username.

        :param username: the username
        :return: the user object
        """
        pass

    @classmethod
    @abstractmethod
    def from_ip(cls: Type[T], ip: str) -> T:
        """Return a user based on an ip.

        If there is no user associated with this ip, return
        :py:class:`~flask_login.AnonymousUserMixin`.

        :param ip: the ip
        :return: the user object
        """
        pass

    def re_authenticate(self, password):
        self.authenticate(self.uid, password)

    @contextmanager
    def tmp_authentication(self, password):
        """Check and temporarily store the given password.

        Returns a context manager.  The password is stored in
        `self._tmp_password`.

        This is quite an ugly hack, only existing because some datasources
        need the user password to change certain user properties such as mail
        address and MAC address. The need for the password breaks
        compatability with the usual `instance.property = value`.

        I could not think of a better way to get around this.
        """
        self.re_authenticate(password)
        self._tmp_password = password
        yield
        del self._tmp_password

    @classmethod
    @abstractmethod
    def authenticate(cls, username, password):
        """Return a User instance or raise PasswordInvalid"""
        pass

    @property
    @abstractmethod
    def can_change_password(self) -> bool:
        """Whether password change is possible/permitted."""
        pass

    @abstractmethod
    def change_password(self, old, new):
        """Change the user's password from old to new.

        Although the password has been checked using
        :meth:`re_authenticate()`, some data sources like those which have to
        perform an LDAP bind need it anyways.
        """
        pass

    @property
    @abstractmethod
    def traffic_history(self) -> List[Dict]:
        """Return the current traffic history as a dict.

        The history should cover one week. The assumed unit is KiB.

        The list syntax is as follows::

            [{
                'day': day.weekday(),
                'input': in,
                'output': out,
                'throughput': in + out,
            }, …]

        The traffic values shall be in KiB, as usual.

        :return: The history of the used traffic
        """
        pass

    def generate_rows(self, description_dict: Dict):
        for key, val in description_dict.items():
            yield Row(description=val, property=getattr(self, key))

    @active_prop
    @abstractmethod
    def realname(self) -> PropertyBase:
        """**[Abstract]** The real-life name"""
        pass

    @active_prop
    @abstractmethod
    def login(self) -> PropertyBase:
        """**[Abstract]** The login"""
        pass

    @active_prop
    @abstractmethod
    def mac(self) -> PropertyBase:
        """**[Abstract]** The MAC Address"""
        pass

    @active_prop
    @abstractmethod
    def mail(self) -> PropertyBase:
        """**[Abstract]** The mail address.

        This can either be the forward or the internal adress
        (``"{login}@{server}"``)
        """
        pass

    @active_prop
    @abstractmethod
    def address(self) -> PropertyBase:
        """**[Abstract]** Where the user lives"""
        pass

    @active_prop
    @abstractmethod
    def status(self) -> PropertyBase:
        """**[Abstract]** The current membership status in the sense of
        the AG DSN constitution.

        This mostly means active, ex-active or passive.
        """
        pass

    @active_prop
    @abstractmethod
    def id(self) -> PropertyBase:
        """**[Abstract]** The “user-id”.

        Some Backends provide a secondary id besides the login.
        """
        pass

    @active_prop
    @abstractmethod
    def use_cache(self) -> PropertyBase:
        """**[Abstract]** Flag indicating cache usage."""
        pass

    @active_prop
    @abstractmethod
    def hostname(self) -> PropertyBase:
        """**[Abstract]** The hostname.

        This usually is an alias consisting of the last digits of the
        mac/ip.
        """
        pass

    @active_prop
    @abstractmethod
    def hostalias(self) -> PropertyBase:
        """**[Abstract]** The hostalias.

        An optionally configurable alias for the device.
        """
        pass

    @property
    @abstractmethod
    def userdb_status(self) -> PropertyBase:
        """The status of the user's db, if available."""
        pass

    @property
    @abstractmethod
    def userdb(self) -> BaseUserDB:
        """**[Abstract]** The :class:`BaseUserDB` object, if available.

        If :data:`userdb_status` is non-empty, it is assumed to exist.
        """
        pass

    @property
    @abstractmethod
    def has_connection(self) -> PropertyBase:
        """**[Abstract]** Whether the user has a connection"""
        pass

    @property
    @abstractmethod
    def finance_information(self) -> Optional[BaseFinanceInformation]:
        """**[Abstract]** Finance information about the User.

        If not supported, set to None.
        """
        pass

    @property
    def finance_balance(self) -> PropertyBase:
        """The :class:`fancy property <sipa.model.fancy_property.PropertyBase>`
        representing the finance balance"""
        info = self.finance_information
        if not info:
            return UnsupportedProperty('finance_balance')
        return info.balance

    @abstractmethod
    def payment_details(self) -> PaymentDetails:
        """**[Abstract]** Payment details for the User."""
        pass

    def has_property(self, property):
        """Method to check if a user has a property"""
        return False

    @property
    @abstractmethod
    def is_member(self):
        pass


class BaseUserDB(metaclass=ABCMeta):
    """An abstract base class defining an interface for a user's
    database

    Some backends provide a database for each user.  This interface
    defines methods that must be made available when enabling support
    for this in the corresponding user_class.
    """
    def __init__(self, user: BaseUser):
        """Set the `BaseUser` object `user`"""
        #: A backreference to the :class:`User` object
        self.user = user

    @property
    @abstractmethod
    def has_db(self) -> Optional[bool]:
        """**[Abstract]** Whether the database is enabled

        Returns None, if the user database is unreachable.
        """
        pass

    @abstractmethod
    def create(self, password: str):
        """**[Abstract]** Create the database"""
        pass

    @abstractmethod
    def drop(self):
        """**[Abstract]** Drop the database"""
        pass

    @abstractmethod
    def change_password(self, password: str):
        """**[Abstract]** Change the password of the database"""
        pass
