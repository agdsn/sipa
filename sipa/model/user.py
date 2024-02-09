from __future__ import annotations

import typing as t
# noinspection PyMethodMayBeStatic
from abc import ABCMeta, abstractmethod
from datetime import date
from typing import TypeVar

from sipa.model.fancy_property import UnsupportedProperty, PropertyBase
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


class TableRow(t.NamedTuple):
    """Represents a Row in on the user pages Table"""

    property: str
    description: str
    subtext: str | None = None


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

    def __init__(self, uid: str):
        #: A unique unicode identifier for the User, needed for
        #: :meth:`get_id`
        self.uid: str = uid

    def __eq__(self, other):
        return self.uid == other.uid and self.datasource == other.datasource

    datasource = None

    def get_id(self) -> str:
        """This method is Required by flask-login."""
        return self.uid

    @classmethod
    @abstractmethod
    def get(cls: type[T], username: str) -> T:
        """Fetch a user given his username.

        :param username: the username
        :return: the user object
        """
        pass

    @classmethod
    @abstractmethod
    def from_ip(cls: type[T], ip: str) -> T:
        """Return a user based on an ip.

        If there is no user associated with this ip, return
        :py:class:`~flask_login.AnonymousUserMixin`.

        :param ip: the ip
        :return: the user object
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
    def can_change_password(self) -> bool:
        """Whether password change is possible/permitted."""
        pass

    @abstractmethod
    def change_password(self, old, new):
        """Change the user's password from old to new."""
        pass

    @property
    @abstractmethod
    def traffic_history(self) -> list[dict]:
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

    def generate_rows(self, description_dict: dict) -> t.Iterator[TableRow]:
        for key, val in description_dict.items():
            yield TableRow(property=getattr(self, key), **self.__text_to_dict(val))

    def __text_to_dict(self, val: str|list[str]) -> dict:
        match val:
            case [d, s]:
                return {"description": d, "subtext": s}
            case [d]:
                return {"description": d}
            case _:
                return {"description": "Error"}

    @property
    @abstractmethod
    def realname(self) -> PropertyBase[str, str]:
        """The real-life name"""
        pass

    @property
    @abstractmethod
    def login(self) -> PropertyBase[str, str]:
        """The login"""
        pass

    @property
    @abstractmethod
    def mac(self) -> PropertyBase[str, str]:
        """The MAC Address"""
        pass

    @property
    @abstractmethod
    def mail(self) -> PropertyBase[str, str]:
        """The mail address.

        (``"{login}@{server}"``)
        """
        pass

    @abstractmethod
    def change_mail(
        self, password: str, new_mail: str, mail_forwarded: bool
    ) -> None: ...

    @property
    @abstractmethod
    def birthdate(self) -> PropertyBase[date, date]:
        """Date of birth"""
        pass

    @property
    @abstractmethod
    def mail_forwarded(self) -> PropertyBase[bool, bool]:
        """Whether mail forwarding is enabled."""
        pass

    @property
    @abstractmethod
    def mail_confirmed(self) -> PropertyBase[bool, bool]:
        """Whether mail is confirmed."""
        pass

    @abstractmethod
    def resend_confirm_mail(self) -> bool:
        """Resend the confirmation mail."""
        pass

    @property
    @abstractmethod
    def address(self) -> PropertyBase[str, str]:
        """Where the user lives"""
        pass

    @property
    @abstractmethod
    def status(self) -> PropertyBase[str, str]:
        """The current membership status in the sense of
        the AG DSN constitution.

        This mostly means active, ex-active or passive.
        """
        pass

    @property
    @abstractmethod
    def id(self) -> PropertyBase[str, str]:
        """The “user-id”.

        Some Backends provide a secondary id besides the login.
        """
        pass

    @property
    @abstractmethod
    def userdb_status(self) -> PropertyBase[str, str]:
        """The status of the user's db, if available."""
        pass

    @property
    @abstractmethod
    def userdb(self) -> BaseUserDB:
        """The :class:`BaseUserDB` object, if available.

        If :data:`userdb_status` is non-empty, it is assumed to exist.
        """
        pass

    @property
    @abstractmethod
    def has_connection(self) -> PropertyBase[bool, bool]:
        """Whether the user has a connection"""
        pass

    @property
    @abstractmethod
    def finance_information(self) -> BaseFinanceInformation | None:
        """Finance information about the User.

        If not supported, set to None.
        """
        pass

    @property
    def finance_balance(self) -> PropertyBase[str, float | None]:
        """The :class:`fancy property <sipa.model.fancy_property.PropertyBase>`
        representing the finance balance"""
        info = self.finance_information
        if not info:
            return UnsupportedProperty('finance_balance')
        return info.balance

    @abstractmethod
    def payment_details(self) -> PaymentDetails:
        """Payment details for the User."""
        pass

    def has_property(self, property):
        """Method to check if a user has a property"""
        return False

    @property
    def membership_end_date(self) -> PropertyBase[date | None, date | None]:
        """Date when the membership ends"""
        return UnsupportedProperty("membership_end_date")

    @property
    def network_access_active(self) -> PropertyBase[bool, bool] | UnsupportedProperty:
        """Whether or not the network access is active"""
        return UnsupportedProperty("network_access_active")

    def activate_network_access(self, password, mac, birthdate, host_name):
        """Method to activate network access"""
        raise NotImplementedError

    def terminate_membership(self, end_date):
        """Method to terminate membership"""
        raise NotImplementedError

    def continue_membership(self):
        """Calculate balance at a given end_date"""
        raise NotImplementedError

    def estimate_balance(self, end_date):
        """Calculate balance at a given end_date"""
        raise NotImplementedError

    @property
    @abstractmethod
    def is_member(self) -> bool:
        pass

    @property
    def wifi_password(self) -> PropertyBase[str, str | None]:
        return UnsupportedProperty("wifi_password")

    @classmethod
    def request_password_reset(cls, user_ident, email):
        raise NotImplementedError

    @classmethod
    def password_reset(cls, token, new_password):
        raise NotImplementedError


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
    def has_db(self) -> bool | None:
        """Whether the database is enabled

        Returns None, if the user database is unreachable.
        """
        pass

    @abstractmethod
    def create(self, password: str):
        """Create the database"""
        pass

    @abstractmethod
    def drop(self):
        """Drop the database"""
        pass

    @abstractmethod
    def change_password(self, password: str):
        """Change the password of the database"""
        pass
