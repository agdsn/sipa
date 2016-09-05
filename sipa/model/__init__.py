# -*- coding: utf-8 -*-
import logging
import operator
from collections import namedtuple
from ipaddress import IPv4Address, AddressValueError

from flask import request, session, current_app
from flask_login import current_user, AnonymousUserMixin
from sqlalchemy.exc import OperationalError
from werkzeug.local import LocalProxy

from . import sample, wu, gerok, hss, pycroft
from .sqlalchemy import db
from sipa.utils.exceptions import InvalidConfiguration


logger = logging.getLogger(__name__)


#: The implemented datasources available by default
AVAILABLE_DATASOURCES = [
    pycroft.datasource,  # on top, because PYCROFT stands above it all™
    sample.datasource,
    wu.datasource,
    gerok.datasource,
    hss.datasource,
]


def evaluates_uniquely(objects, func):
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
    :rtype: bool
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

    Originating from the needs of the [AG DSN](github.com/agdsn), the
    user should not select the backend, but the location where he
    lives.  Thus, he selects a :py:class:`Dormitory`, which has not
    only a name, but also a `display_name` and ip subnets.  The latter
    are needed to semi-authenticate a user based on his ip.

    **Usage:**

    >>> app = Flask('appname')
    >>> backends = Backends()
    >>> app.config['BACKENDS'] = ['name1', 'name2']
    >>> backends.init_app(app)
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
    def __init__(self, available_datasources=None):
        if available_datasources is None:
            available_datasources = AVAILABLE_DATASOURCES

        #: A list of datasources that can be activated. Defaults to
        #: :py:data:`AVAILABLE_DATASOURCES`
        self.available_datasources = available_datasources

        #: The datasources dict
        self._datasources = {}
        #: The dormitory dict
        self._dormitories = {}
        #: The premature_dormitories dict
        self._premature_dormitories = {}

    def init_app(self, app):
        """Register self to app and initialize datasources

        The datasources will be registered according to the app's
        config.

        :param app: The flask app object to register against
        """
        app.extensions['backends'] = self
        self.app = app

        backends = app.config.get('BACKENDS')
        if not backends:
            logger.warning('No backends configured')
            return

        for backend_name in backends:
            self._register_backend(backend_name)

    def _register_backend(self, name):
        """Register a datasource by name.

        First, find the name in the available datasources' names, warn
        on inconsistencies.  If found, add the `name: datasource` pair
        to the private dict.

        :param datasource: the datasource to register
        :raises: `ValueError` if a backend with this name is already
            registered
        """
        if name in self._datasources:
            raise InvalidConfiguration('Datasource {} already registered'
                                       .format(name))

        if not evaluates_uniquely(AVAILABLE_DATASOURCES,
                                  func=operator.attrgetter('name')):
            raise ValueError("Implememented datasources have non-unique names")

        for dsrc in self.available_datasources:
            if dsrc.name == name:
                new_datasource = dsrc
                break
        else:
            raise InvalidConfiguration("{} is not an available datasource"
                                       .format(name))

        self._datasources[name] = new_datasource

        # check for name collisions in the updated dormitories
        new_dormitories = new_datasource.dormitories
        if any(dorm.name in self._dormitories.keys()
               for dorm in new_dormitories):
            raise ValueError("Some dormitories of datasource Dormitory "
                             "have a name already registered")
        for dormitory in new_datasource.dormitories:
            self._register_dormitory(dormitory)

    def _register_dormitory(self, dormitory):
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

    @staticmethod
    def backends_preinit(app):
        app.config['SQLALCHEMY_BINDS'] = {}
        db.init_app(app)

    def init_backends(self):
        """Initialize the activated backends

        This is the method that does the actual initialization.  It
        calls each :py:class:`DataSource`s `init_context` function.

        In there, things like setting up a pg session or registering
        an ldap object to the app might be done.
        """
        self.backends_preinit(self.app)

        for datasource in self.datasources:
            if datasource.init_context:
                datasource.init_context(self.app)

    # CENTRAL PROPERTIES

    @property
    def datasources(self):
        """A list of the currently registered datasources"""
        return list(self._datasources.values())

    @property
    def dormitories(self):
        """A list of the currently registered dormitories"""
        return list(self._dormitories.values())

    @property
    def premature_dormitories(self):
        """A list of the currently registered premature dormitories"""
        return list(self._premature_dormitories.values())

    @property
    def all_dormitories(self):
        """A list of the currently registered dormitories including
        premature dormitories.
        """
        return self.dormitories + list(self._premature_dormitories.values())

    # CONVENIENCE PROPERTIES

    @property
    def dormitories_short(self):
        """Return a list of dormitories as tuples instead of objects

        :return: a list of ``(name, display_name)`` tuples
        :rtype: list of :py:data:`_dorm_summary` namedtuples
        """
        return sorted([
            _dorm_summary(name=dormitory.name,
                          display_name=dormitory.display_name)
            for dormitory in self.dormitories + self.premature_dormitories
        ])

    @property
    def supported_dormitories_short(self):
        """Return a list of supported dormitories as tuples instead of
        objects

        :return: a list of ``(name, display_name)`` tuples
        :rtype: list of :py:data:`_dorm_summary` namedtuples
        """
        return sorted([
            _dorm_summary(name=dormitory.name,
                          display_name=dormitory.display_name)
            for dormitory in self.dormitories
        ], key=operator.itemgetter(1))

    # LOOKUP METHODS

    def get_dormitory(self, name):
        """Lookup the dormitory with name ``name``.

        :param str name: The dormitory's ``name``

        :return: The dormitory object
        :rtype: :py:class:`~sipa.model.datasource.Dormitory`
        """
        for dormitory in self.all_dormitories:
            if dormitory.name == name:
                return dormitory

    def get_datasource(self, name):
        """Lookup the datasource with name ``name``.

        :param str name: The datasource's ``name``

        :return: The datasource object
        :rtype: :py:class:`~sipa.model.datasource.Datasource`
        """
        for datasource in self.datasources:
            if datasource.name == name:
                return datasource

    def dormitory_from_ip(self, ip):
        """Return the dormitory whose subnets contain ``ip``

        :param str ip: The ip

        :return: The dormitory containing ``ip``
        :rtype: :py:class:`~sipa.model.datasource.Dormitory`
        """
        try:
            address = IPv4Address(str(ip))
        except AddressValueError:
            pass
        else:
            for dormitory in self.dormitories:
                if address in dormitory.subnets:
                    return dormitory

    def preferred_dormitory_name(self):
        """Return the name of the preferred dormitory based on the
        request's ip

        :return: name of the dormitory
        :rtype: str
        """
        dormitory = self.dormitory_from_ip(request.remote_addr)
        if dormitory:
            return dormitory.name

    def user_from_ip(self, ip):
        """Return the User that corresponds to ``ip`` according to the
        datasource.

        :param str ip: The ip

        :return: The corresponding User in the sense of the
                 datasource.
        :rtype: The corresponding datasources ``user_class``.
        """
        dormitory = self.dormitory_from_ip(ip)
        if not dormitory:
            return AnonymousUserMixin()

        datasource = dormitory.datasource
        if datasource is None:
            return AnonymousUserMixin()

        return datasource.user_class.from_ip(ip)

    # PROXIES

    def current_dormitory(self):
        """Read the current dormitory from the session

        :rtype: :py:class:`~sipa.model.datasource.Dormitory`
        """
        return self.get_dormitory(session['dormitory'])

    def current_datasource(self):
        """Read the current datasource from the session

        :rtype: :py:class:`~sipa.model.datasource.Datasource`
        """
        dormitory = self.current_dormitory()
        if dormitory:
            return dormitory.datasource


backends = LocalProxy(lambda: current_app.extensions['backends'])


#: A namedtuple to improve readability of some return values
_dorm_summary = namedtuple('_dorm_summary', ['name', 'display_name'])


def query_gauge_data():
    credit = {'data': None, 'error': False, 'foreign_user': False}
    try:
        if current_user.is_authenticated and current_user.has_connection:
            user = current_user
        else:
            user = backends.user_from_ip(request.remote_addr)
        credit['data'] = user.credit
    except OperationalError:
        credit['error'] = True
    except AttributeError:
        credit['foreign_user'] = True
    return credit
