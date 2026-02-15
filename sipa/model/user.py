from __future__ import annotations

import typing as t
# noinspection PyMethodMayBeStatic
from abc import ABCMeta, abstractmethod
from datetime import date
from typing import TypeVar

from sipa.model.fancy_property import UnsupportedProperty, PropertyBase
from sipa.model.finance import BaseFinanceInformation
from sipa.model.misc import UserPaymentDetails
from .mspk_client import MPSKClientEntry


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
