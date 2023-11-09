from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass, field
from ipaddress import IPv4Network, IPv4Address, AddressValueError

from flask import Flask

from sipa.utils import compare_all_attributes, xor_hashes
from .logging import logger
from .types import UserLike

InitContextCallable = Callable[[Flask], None]


class DataSource:
    """A class providing a certain Backend.

    This class provides information about the backend you defined, for
    instance the user class.
    """

    def __init__(
        self,
        name: str,
        user_class: type[UserLike],
        dormitories: list[Dormitory],
        mail_server: str,
        webmailer_url: str = None,
        support_mail: str = None,
        init_app: InitContextCallable = None,
    ) -> None:
        super().__init__()

        #: Holds the name of this datasource.  Must be unique among
        #: what you register onto your `Backends` object.
        self.name = name

        class _user_class(user_class):  # type: ignore
            datasource = self
        #: the user_class used in the sense of ``flask_login``.
        self.user_class: type[UserLike] = _user_class

        self._dormitories = {d.name: d for d in dormitories}
        #: The mail server to be appended to a user's login in order
        #: to construct the mail address.
        self.mail_server = mail_server
        self.webmailer_url = webmailer_url
        self.support_mail = (support_mail if support_mail
                             else f"support@{mail_server}")
        self._init_app = init_app

    def __eq__(self, other):
        return compare_all_attributes(self, other, ['name'])

    def __repr__(self):
        return f"<{type(self).__name__} {self.name!r}>"

    def __hash__(self):
        return xor_hashes(self.name, self.user_class, self.support_mail, self.mail_server)

    @property
    def dormitories(self) -> list[Dormitory]:
        """A list of all registered dormitories."""
        return list(self._dormitories.values())

    def get_dormitory(self, name) -> Dormitory | None:
        """Get the dormitory with the given name."""
        return self._dormitories.get(name)

    def dormitory_from_ip(self, ip: str) -> Dormitory | None:
        """Return the dormitory whose subnets contain ``ip``

        :param ip: The ip

        :return: The dormitory containing ``ip``
        """
        try:
            address = IPv4Address(str(ip))
        except AddressValueError:
            return None
        return next((d for d in self.dormitories if address in d.subnets), None)

    def init_app(self, app: Flask):
        """Initialize this backend

            - Apply the custom configuration of
              :py:obj:`app.config['BACKENDS_CONFIG'][self.name]`

            - Call :py:meth:`_init_context(app)` as given in the
              config

        The custom config supports the following keys:

            - ``support_mail``: Set ``self.support_mail``

        If an unknown key is given, a warning will be logged.

        :param Flask app: the app to initialize against
        """
        # copy the dict so we can freely ``pop`` things
        # TODO deprecate `BACKENDS_CONFIG`
        config = app.config.get('BACKENDS_CONFIG', {}).get(self.name, {}).copy()

        try:
            self.support_mail = config.pop('support_mail')
        except KeyError:
            pass

        for key in config.keys():
            logger.warning("Ignoring unknown key '%s'", key,
                           extra={'data': {'config': config}})

        if self._init_app:
            return self._init_app(app)


@dataclass(frozen=True)
class SubnetCollection:
    """A simple class for combining multiple IPv4Networks.

    Provides __contains__ functionality for IPv4Addresses.
    """

    subnets: list[IPv4Network] = field(default_factory=list)

    # hint should be replaced with typing info from stub
    def __contains__(self, address: IPv4Address):
        for subnet in self.subnets:
            if address in subnet:
                return True
        return False


# used for two things:
# 1. determining whether the source IP belongs to a pycroft user
# 2. suggesting a default dormitory name based on an IP
@dataclass(frozen=True)
class Dormitory:
    """A dormitory as selectable on the login page."""

    name: str
    display_name: str
    subnets: SubnetCollection = SubnetCollection()

