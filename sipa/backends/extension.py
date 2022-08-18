from __future__ import annotations

import operator
from collections.abc import Callable
from ipaddress import IPv4Address, AddressValueError
from typing import NamedTuple, cast

from flask import request, session, current_app, Flask
from flask_login import AnonymousUserMixin
from werkzeug.local import LocalProxy

from .datasource import DataSource, Dormitory
from .exceptions import InvalidConfiguration
from .logging import logger
from .types import UserLike


def evaluates_uniquely(objects, func) -> bool:
    """Return true if the return value of ``func`` is unique among
    ``objects``.

    This can be used to check whether some attribute `obj.attr` is
    unique among a set of such objects, and can thus be used as a key.

    **Usage:**

    >>> from operator import itemgetter
    >>> objs = [{'name': "foo"}, {'name': "bar"}]
    >>> evaluates_uniquely(objs, func=itemgetter('name'))
    True

    >>> from operator import itemgetter
    >>> objs = [{'name': "foo"}, {'name': "foo"}]
    >>> evaluates_uniquely(objs, func=itemgetter('name'))
    False

    :param objects: the object on which to apply func to
    :param func: the function to be evaluated, given each object as a
        parameter.  Must return something hashable.

    :return: whether the uniqueness holds
    """
    values = [func(obj) for obj in objects]
    return len(values) == len(set(values))


class Backends:
    """The `Backends` flask extension

    This extension lets you initialize some of the available
    datasources and provides some central methods to look things up,
    like for example the user object from some ip.

    `Backends` builds upon the following concept:

    A user is enabled to log in using different backends, called
    *datasources*.  A :py:class:`DataSource` provides information such
    as its name, the email suffix, the user class, the initialization
    method, and so on.

    Originating from the needs of the `AG DSN <https://github.com/agdsn>`_, the
    user should not select the backend, but the location where he
    lives.  Thus, he selects a :py:class:`Dormitory`, which has not
    only a name, but also a `display_name` and ip subnets.  The latter
    are needed to semi-authenticate a user based on his ip.

    **Usage:**

    >>> app = Flask('appname')
    >>> datasource = DataSource(name='name1', user_class=object,
    >>>                         mail_server='srv')
    >>> backends = Backends()
    >>> backends.register(datasource)
    >>> backends.init_app(app)
    >>> app.config['BACKENDS'] = ['name1']
    >>> # further initialization…
    >>> backends.init_backends()  # call each backend's init method
    >>> app.run()

    This class provides methods concerning:

    * *initialization* of the extension and backends
    * *lists* of the currently (un)supported dormitories and
       datasources
    * *lookup properties* to access the datasources/dormitories/users
      given certain information (ip, name, …)
    * *proxy methods* to access the current datasource/dormitory
      (similiar to current_user)

    """
    def __init__(self):
        #: Which datasources are available
        self.available_datasources: dict[str, DataSource] = {}
        #: The datasources dict
        self._datasources: dict[str, DataSource] = {}
        #: The dormitory dict
        self._dormitories: dict[str, Dormitory] = {}
        self.app: Flask = None
        self._pre_backends_init_hook: Callable[[Flask], None] = lambda app: None

    def init_app(self, app: Flask):
        """Register self to app and initialize datasources

        The datasources will be registered according to the app's
        config.

        :param app: The flask app object to register against
        """
        app.extensions['backends'] = self
        self.app = app

        backends_to_enable = app.config.get('BACKENDS')
        if not backends_to_enable:
            logger.warning('No backends configured')
            return

        for backend_name in backends_to_enable:
            self._activate_datasource(backend_name)

    def register(self, datasource: DataSource):
        # TODO: annotate the return type as Backend → Backend

        if datasource.name in self.available_datasources:
            raise InvalidConfiguration(f"Datasource name {datasource.name}"
                                       f" is used multiple times")
        self.available_datasources[datasource.name] = datasource

    def _activate_datasource(self, name: str):
        """Activate a datasource by name.

        First, find the name in the available datasources' names, warn
        on inconsistencies.  If found, add the `name: datasource` pair
        to the private dict.

        :raises InvalidConfiguration: if the name does not correspond to a
            registered datasource
        """
        if name in self._datasources:
            logger.warning(f"Datasource {name} already activated")
            return

        try:
            new_datasource = self.available_datasources[name]
        except KeyError:
            raise InvalidConfiguration(f"{name} is not an available datasource")

        self._datasources[name] = new_datasource

        # check for name collisions in the updated dormitories
        new_dormitories = new_datasource.dormitories
        if any(dorm.name in self._dormitories.keys()
               for dorm in new_dormitories):
            raise ValueError("Some dormitories of datasource Dormitory "
                             "have a name already registered")
        for dormitory in new_datasource.dormitories:
            self._register_dormitory(dormitory)

    def _register_dormitory(self, dormitory: Dormitory):
        """Register a dormitory by putting it to the dict

        :param dormitory: The dormitory to register
        :raises: `ValueError` if a dormitory with this name is already
            registered.
        """
        name = dormitory.name
        if name in self._dormitories:
            raise ValueError("Dormitory with name {} already exists"
                             .format(name))
        self._dormitories[name] = dormitory

    @property
    def pre_init_hook(self) -> Callable[[Callable], Callable]:  # Decorators are fun :-)
        def decorator(f):
            self._pre_backends_init_hook = f
        return decorator

    def init_backends(self):
        """Initialize the activated backends

        This is the method that does the actual initialization.  It
        calls each :py:class:`DataSource`s `init_context` function.

        In there, things like setting up a pg session or registering
        backend specific flask extensions to the app might be done.
        """
        self._pre_backends_init_hook(self.app)

        for datasource in self.datasources:
            if datasource.init_context:
                datasource.init_context(self.app)

    # CENTRAL PROPERTIES

    @property
    def datasources(self) -> list[DataSource]:
        """A list of the currently registered datasources"""
        return list(self._datasources.values())

    @property
    def dormitories(self) -> list[Dormitory]:
        """A list of the currently registered dormitories"""
        return list(self._dormitories.values())

    # The logic is removed, but the interface is still used
    premature_dormitories: list[Dormitory] = []

    @property
    def all_dormitories(self) -> list[Dormitory]:
        """A list of the currently registered dormitories including
        premature dormitories.
        """
        return self.dormitories + self.premature_dormitories

    # CONVENIENCE PROPERTIES

    @property
    def dormitories_short(self) -> list[_dorm_summary]:
        """Return a list of dormitories as tuples instead of objects"""
        return sorted(
            _dorm_summary(name=dormitory.name,
                          display_name=dormitory.display_name)
            for dormitory in self.dormitories + self.premature_dormitories
        )

    @property
    def supported_dormitories_short(self) -> list[_dorm_summary]:
        """Return a list of supported dormitories as tuples instead of
        objects
        """
        return sorted((
            _dorm_summary(name=dormitory.name,
                          display_name=dormitory.display_name)
            for dormitory in self.dormitories
        ), key=operator.itemgetter(1))

    # LOOKUP METHODS

    def get_dormitory(self, name: str) -> Dormitory | None:
        """Lookup the dormitory with name ``name``.

        :param name: The dormitory's ``name``

        :return: The dormitory object
        """
        for dormitory in self.all_dormitories:
            if dormitory.name == name:
                return dormitory
        return None

    def get_first_dormitory(self) -> Dormitory | None:
        """Quick fix function to remove dorm selector on login.

        :return: The dormitory object
        """
        for dormitory in self.all_dormitories:
            return dormitory

        return None


    def get_datasource(self, name: str) -> DataSource | None:
        """Lookup the datasource with name ``name``.

        :param name: The datasource's ``name``

        :return: The datasource object
        """
        for datasource in self.datasources:
            if datasource.name == name:
                return datasource
        return None

    def dormitory_from_ip(self, ip: str) -> Dormitory | None:
        """Return the dormitory whose subnets contain ``ip``

        :param ip: The ip

        :return: The dormitory containing ``ip``
        """
        try:
            address = IPv4Address(str(ip))
        except AddressValueError:
            pass
        else:
            for dormitory in self.dormitories:
                if address in dormitory.subnets:
                    return dormitory
        return None

    def preferred_dormitory_name(self) -> str | None:
        """Return the name of the preferred dormitory based on the
        request's ip

        :return: name of the dormitory
        """
        dormitory = self.dormitory_from_ip(request.remote_addr)
        if dormitory:
            return dormitory.name
        return None

    def user_from_ip(self, ip: str) -> UserLike | None:
        """Return the User that corresponds to ``ip`` according to the
        datasource.

        :param ip: The ip

        :return: The corresponding User in the sense of the
                 datasource.
        """
        dormitory = self.dormitory_from_ip(ip)
        if not dormitory:
            return AnonymousUserMixin()

        datasource = dormitory.datasource
        if datasource is None:
            return AnonymousUserMixin()

        return datasource.user_class.from_ip(ip)

    # PROXIES

    def current_dormitory(self) -> Dormitory | None:
        """Read the current dormitory from the session"""
        return self.get_dormitory(session['dormitory'])

    def current_datasource(self) -> DataSource | None:
        """Read the current datasource from the session"""
        dormitory = self.current_dormitory()
        if dormitory:
            return dormitory.datasource
        return None


#: A namedtuple to improve readability of some return values
class _dorm_summary(NamedTuple):
    name: str
    display_name: str
backends: Backends = cast(Backends,
                          LocalProxy(lambda: current_app.extensions['backends']))
