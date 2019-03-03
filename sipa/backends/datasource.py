from __future__ import annotations
from ipaddress import IPv4Network, IPv4Address
from typing import Callable, Dict, List, Type

from flask import Flask

from sipa.utils import argstr, compare_all_attributes, xor_hashes
from .logging import logger
from .types import UserLike


InitContextCallable = Callable[[Flask], None]


class DataSource:
    """A class providing a certain Backend.

    This class provides information about the backend you defined, for
    instance the user class.
    """
    def __init__(self, name: str, user_class: Type[UserLike], mail_server: str,
                 webmailer_url: str = None,
                 support_mail: str = None,
                 init_context: InitContextCallable = None) -> None:
        super().__init__()

        #: Holds the name of this datasource.  Must be unique among
        #: what you register onto your `Backends` object.
        self.name = name

        class _user_class(user_class):  # type: ignore
            datasource = self
        #: the user_class used in the sense of ``flask_login``.
        self.user_class: Type[UserLike] = _user_class

        #: The mail server to be appended to a user's login in order
        #: to construct the mail address.
        self.mail_server = mail_server
        self.webmailer_url = webmailer_url
        self.support_mail = (support_mail if support_mail
                             else "support@{}".format(mail_server))
        self._init_context = init_context
        self._dormitories: Dict[str, Dormitory] = {}

    def __eq__(self, other):
        return compare_all_attributes(self, other, ['name'])

    def __repr__(self):
        return "<{cls} {name!r}>".format(
            cls=type(self).__name__,
            name=self.name,
        )

    def __hash__(self):
        return xor_hashes(self.name, self.user_class, self.support_mail, self.mail_server)

    def register_dormitory(self, dormitory: Dormitory):
        name = dormitory.name
        if name in self._dormitories:
            raise ValueError("Dormitory {} already registered", name)
        self._dormitories[name] = dormitory

    @property
    def dormitories(self) -> List[Dormitory]:
        """A list of all registered dormitories."""
        return list(self._dormitories.values())

    def init_context(self, app: Flask):
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
        config = app.config.get('BACKENDS_CONFIG', {}).get(self.name, {}).copy()

        try:
            self.support_mail = config.pop('support_mail')
        except KeyError:
            pass

        for key in config.keys():
            logger.warning("Ignoring unknown key '%s'", key,
                           extra={'data': {'config': config}})

        if self._init_context:
            return self._init_context(app)


class SubnetCollection:
    """A simple class for combining multiple IPv4Networks.

    Provides __contains__ functionality for IPv4Addresses.
    """

    def __init__(self, subnets: List[IPv4Network]) -> None:
        if isinstance(subnets, list):
            for subnet in subnets:
                if not isinstance(subnet, IPv4Network):
                    raise TypeError("List of IPv4Network objects expected "
                                    "in SubnetCollection.__init__")
        else:
            raise TypeError("List expected in SubnetCollection.__init__")

        self.subnets = subnets

    def __repr__(self):
        return "{}.{}({})".format(__name__, type(self).__name__, argstr(
            subnets=self.subnets,
        ))

    # hint should be replaced with typing info from stub
    def __contains__(self, address: IPv4Address):
        for subnet in self.subnets:
            if address in subnet:
                return True
        return False

    def __eq__(self, other):
        return compare_all_attributes(self, other, ['subnets'])

    def __hash__(self):
        return xor_hashes(*self.subnets)


class Dormitory:
    """A dormitory as selectable on the login page."""

    def __init__(self, name: str, display_name: str, datasource: DataSource,
                 subnets=None) -> None:
        self.name = name
        self.display_name = display_name
        self.datasource = datasource
        # TODO rework dormitory registration (make it safe)
        # Add a `Backends` binding to `Datasource` and check global dorm
        # existence when calling `register_dormitory`
        datasource.register_dormitory(self)
        self.subnets = SubnetCollection(subnets if subnets else [])

    def __repr__(self):
        return "{}.{}({})".format(__name__, type(self).__name__, argstr(
            name=self.name,
            display_name=self.display_name,
            datasource=self.datasource,
            subnets=self.subnets.subnets,
        ))

    def __eq__(self, other):
        return compare_all_attributes(self, other, ['name', 'datasource'])

    def __hash__(self):
        return xor_hashes(self.name, self.display_name, self.datasource, self.subnets)
