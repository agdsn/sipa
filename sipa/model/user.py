# -*- coding: utf-8 -*-

# noinspection PyMethodMayBeStatic
from abc import ABCMeta, abstractmethod
from collections import namedtuple

from sipa.model.fancy_property import active_prop, UnsupportedProperty


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


class BaseUser(AuthenticatedUserMixin, metaclass=ABCMeta):
    """Abstract base class defining what a user must have in order to
    work properly with sipa.

    Note that initialization shouldn't be done via :meth:`__init__`
    directly, but usign one of the classmethods :meth:`get`,
    :meth:`authenticate` or :meth:`from_ip`!

    Apart from being an ABC, this class provides some logic already.

    This includes setting :data:`uid` in :meth:`__init__`, defining
    equality, and some others.

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
        """This method is Required by flask-login.

        See the `flask_login manual
        <https://flask-login.readthedocs.io/en/latest/#your-user-class>`
        """
        return self.uid

    @classmethod
    @abstractmethod
    def get(cls, username):
        """Fetch a user given his username.

        :param str username: the username
        :return: the user object
        :rtype: this class
        """
        pass

    @classmethod
    @abstractmethod
    def from_ip(cls, ip):
        """Return a user based on an ip.

        If there is no user associated with this ip, return AnonymousUserMixin.
        :param str ip: the ip
        :return: the user object
        :rtype: this class
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
        """Whether password change is possible/permitted.

        :rtype: bool
        """
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
    def traffic_history(self):
        """Return the current credit and the traffic history as a dict.

        The history should cover one week. The assumed unit is KiB.

        The list syntax is as follows::

            [{
                'day': day.weekday(),
                'input': in,
                'output': out,
                'throughput': in + out,
                'credit': credit,
            }, …]

        The traffic values shall be in KiB, as usual.

        :return: The history of the used traffic
        :rtype: list of dicts
        """
        pass

    @property
    @abstractmethod
    def credit(self):
        """**[Abstract]** The current credit in KiB

        :rtype: int/float
        """
        pass

    def generate_rows(self, description_dict):
        for key, val in description_dict.items():
            yield Row(description=val, property=getattr(self, key))

    @active_prop
    @abstractmethod
    def realname(self):
        """**[Abstract]** The real-life name

        :rtype: :py:class:`~sipa.model.fancy_property.PropertyBase`
        """
        pass

    @active_prop
    @abstractmethod
    def login(self):
        """**[Abstract]** The login

        :rtype: :py:class:`~sipa.model.fancy_property.PropertyBase`
        """
        pass

    @active_prop
    @abstractmethod
    def mac(self):
        """**[Abstract]** The MAC Address

        :rtype: :py:class:`~sipa.model.fancy_property.PropertyBase`
        """
        pass

    @active_prop
    @abstractmethod
    def mail(self):
        """**[Abstract]** The mail address.

        This can either be the forward or the internal adress
        (``"{login}@{server}"``)

        :rtype: :py:class:`~sipa.model.fancy_property.PropertyBase`
        """
        pass

    @active_prop
    @abstractmethod
    def address(self):
        """**[Abstract]** Where the user lives

        :rtype: :py:class:`~sipa.model.fancy_property.PropertyBase`
        """
        pass

    @active_prop
    @abstractmethod
    def status(self):
        """**[Abstract]** The current membership status in the sense of
        the AG DSN constitution.

        This mostly means active, ex-active or passive.

        :rtype: :py:class:`~sipa.model.fancy_property.PropertyBase`
        """
        pass

    @active_prop
    @abstractmethod
    def id(self):
        """**[Abstract]** The “user-id”.

        Some Backends provide a secondary id besides the login.

        :rtype: :py:class:`~sipa.model.fancy_property.PropertyBase`
        """
        pass

    @active_prop
    @abstractmethod
    def use_cache(self):
        """**[Abstract]** Flag indicating cache usage.

        :rtype: :py:class:`~sipa.model.fancy_property.PropertyBase`
        """
        pass

    @active_prop
    @abstractmethod
    def hostname(self):
        """**[Abstract]** The hostname.

        This usually is an alias consisting of the last digits of the
        mac/ip.

        :rtype: :py:class:`~sipa.model.fancy_property.PropertyBase`
        """
        pass

    @active_prop
    @abstractmethod
    def hostalias(self):
        """**[Abstract]** The hostalias.

        An optionally configurable alias for the device.

        :rtype: :py:class:`~sipa.model.fancy_property.PropertyBase`
        """
        pass

    @property
    @abstractmethod
    def userdb_status(self):
        """The status of the user's db, if available.

        :rtype: :py:class:`~sipa.model.fancy_property.PropertyBase`
        """
        pass

    @property
    @abstractmethod
    def userdb(self):
        """**[Abstract]** The `BaseUserDB` object, if available.

        If :data:`userdb_status` is non-empty, it is assumed to exist.

        :rtype: :class:`BaseUserDB`
        """
        pass

    @property
    @abstractmethod
    def has_connection(self):
        """**[Abstract]** Whether the user has a connection

        :rtype: :py:class:`~sipa.model.fancy_property.PropertyBase`
        """
        pass

    @property
    @abstractmethod
    def finance_information(self):
        """**[Abstract]** Finance information about the User.

        If not supported, set to None.
        """
        pass

    @property
    def finance_balance(self):
        """The ``FancyProperty`` representing the finance balance"""
        info = self.finance_information
        if not info:
            return UnsupportedProperty('finance_balance')
        return info.balance

    @abstractmethod
    def payment_details(self):
        """**[Abstract]** Payment details for the User.

        :return A dict with beneficiary, IBAN, purpose etc.
        :rtype: dict
        """
        pass


class BaseUserDB(metaclass=ABCMeta):
    """An abstract base class defining an interface for a user's
    database

    Some backends provide a database for each user.  This interface
    defines methods that must be made available when enabling support
    for this in the corresponding user_class.
    """
    def __init__(self, user):
        """Set the `BaseUser` object `user`"""
        #: A backreference to the :class:`User` object
        self.user = user

    @property
    @abstractmethod
    def has_db(self):
        """**[Abstract]** Wheter the database is enabled

        :rtype: bool
        """
        pass

    @abstractmethod
    def create(self, password):
        """**[Abstract]** Create the database

        :param str password: The password of the database
        """
        pass

    @abstractmethod
    def drop(self):
        """**[Abstract]** Drop the database"""
        pass

    @abstractmethod
    def change_password(self, password):
        """**[Abstract]** Change the password of the database

        :param str password: the new password of the database
        """
        pass
