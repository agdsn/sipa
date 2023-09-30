from __future__ import annotations

from typing import NamedTuple, cast

from flask import request, current_app, Flask
from flask_login import AnonymousUserMixin
from werkzeug.local import LocalProxy

from .datasource import DataSource, Dormitory
from .exceptions import InvalidConfiguration
from .logging import logger
from .types import UserLike


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
    >>> app.config['BACKEND'] = 'name1'
    >>> backends = Backends(available_datasources=[datasource])
    >>> backends.init_app(app)
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

    def __init__(self, available_datasources: list[DataSource]):
        #: Which datasources are available
        self.available_datasources = {d.name: d for d in available_datasources}
        self.app: Flask = None
        self.datasource: DataSource = None

    def init_app(self, app: Flask):
        """Register self to app and initialize datasources

        The datasources will be registered according to the app's
        config.

        :param app: The flask app object to register against
        """
        if "backends" in app.extensions:
            logger.warning("Backends extension already initialized. Skipping.")
            return
        app.extensions['backends'] = self
        self.app = app

        if "BACKENDS" in app.config:
            logger.warning(
                "BACKENDS is deprecated. Use BACKEND instead. "
                "Multiple backends at the same time is unsupported."
            )
        backend_name = app.config["BACKEND"]
        try:
            new_datasource = self.available_datasources[backend_name]
        except KeyError:
            raise InvalidConfiguration(
                f"{backend_name} is not an available datasource"
            ) from None
        self.datasource = new_datasource
        if self.datasource.init_app:
            self.datasource.init_app(self.app)

    # CENTRAL PROPERTIES

    @property
    def dormitories(self) -> list[Dormitory]:
        """A list of the currently registered dormitories"""
        return self.datasource.dormitories

    # CONVENIENCE PROPERTIES

    @property
    def dormitories_short(self) -> list[_dorm_summary]:
        """Return a list of dormitories as tuples instead of objects"""
        return sorted(
            _dorm_summary(name=dormitory.name,
                          display_name=dormitory.display_name)
            for dormitory in self.dormitories
        )

    # LOOKUP METHODS

    def get_dormitory(self, name: str) -> Dormitory | None:
        """Lookup the dormitory with name ``name``."""
        return self.datasource.get_dormitory(name)

    def dormitory_from_ip(self, ip: str) -> Dormitory | None:
        """Return the dormitory whose subnets contain ``ip``"""
        return self.datasource.dormitory_from_ip(ip)

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
        # initial check: IP in known ranges?
        if not self.dormitory_from_ip(ip):
            return AnonymousUserMixin()

        return self.datasource.user_class.from_ip(ip)


#: A namedtuple to improve readability of some return values
class _dorm_summary(NamedTuple):
    name: str
    display_name: str
backends: Backends = cast(Backends,
                          LocalProxy(lambda: current_app.extensions['backends']))
