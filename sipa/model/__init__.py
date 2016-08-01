# -*- coding: utf-8 -*-
import operator
from collections import namedtuple
from ipaddress import IPv4Address, AddressValueError

from flask import request, session
from flask_login import current_user, AnonymousUserMixin
from sqlalchemy.exc import OperationalError

from . import sample, wu, gerok, hss
from .sqlalchemy import db


registered_datasources = [
    sample.datasource,
    wu.datasource,
    gerok.datasource,
    hss.datasource,
]

registered_dormitories = (
    sample.dormitories + wu.dormitories + gerok.dormitories + hss.dormitories
)

premature_dormitories = []


class Backends:
    def init_app(self, app):
        """Register self to app and initialize datasources

        The datasource initialization is done via their `init_context`
        method.
        """
        app.extensions['backends'] = self
        self.app = app

    def init_backends(self):
        self.app.config['SQLALCHEMY_BINDS'] = {}
        db.init_app(self.app)

        for datasource in self.datasources:
            if datasource.init_context:
                datasource.init_context(self.app)

    _datasources = [
        sample.datasource,
        wu.datasource,
        gerok.datasource,
        hss.datasource,
    ]

    _dormitories = (
        sample.dormitories + wu.dormitories + gerok.dormitories + hss.dormitories
    )

    _premature_dormitories = []

    @property
    def datasources(self):
        return self._datasources

    @property
    def dormitories(self):
        return self._dormitories

    @property
    def premature_dormitories(self):
        return self._premature_dormitories

    @property
    def all_dormitories(self):
        return self._dormitories + self._premature_dormitories

    # Here begin the higher-level lookup functions

    @property
    def dormitories_short(self):
        return sorted([
            _dorm_summary(name=dormitory.name,
                          display_name=dormitory.display_name)
            for dormitory in self._dormitories + self._premature_dormitories
        ])

    @property
    def supported_dormitories(self):
        return self.supported_dormitories

    @property
    def supported_dormitories_short(self):
        return sorted([
            _dorm_summary(name=dormitory.name,
                          display_name=dormitory.display_name)
            for dormitory in self._dormitories
        ], key=operator.itemgetter(1))

    def get_dormitory(self, name):
        for dormitory in self.all_dormitories:
            if dormitory.name == name:
                return dormitory

    def get_datasource(self, name):
        for datasource in self.datasources:
            if datasource.name == name:
                return datasource

    def dormitory_from_ip(self, ip):
        """Return the dormitory whose subnets contain `ip`"""
        try:
            address = IPv4Address(str(ip))
        except AddressValueError:
            pass
        else:
            for dormitory in self.dormitories:
                if address in dormitory.subnets:
                    return dormitory

    def preferred_dormitory_name(self):
        """Return the name of the request's ip's dormitory"""
        dormitory = self.dormitory_from_ip(request.remote_addr)
        if dormitory:
            return dormitory.name

    def user_from_ip(self, ip):
        """Return the User that corresponds to `ip` according to the datasource.

        :return: The corresponding User in the sense of the datasource.
        :rtype: The corresponding datasources `user_class`.
        """
        dormitory = self.dormitory_from_ip(ip)
        if not dormitory:
            return AnonymousUserMixin()

        datasource = dormitory.datasource
        if datasource is None:
            return AnonymousUserMixin()

        return datasource.user_class.from_ip(ip)

    def current_dormitory(self):
        """Read the current dormitory from the session"""
        return self.get_dormitory(session['dormitory'])

    def current_datasource(self):
        """Read the current datasource from the session"""
        dormitory = self.current_dormitory()
        if dormitory:
            return dormitory.datasource


backends = Backends()


_dorm_summary = namedtuple('_dorm_summary', ['name', 'display_name'])


def init_context(app):
    """Call each datasources `init_context` method."""
    app.config['SQLALCHEMY_BINDS'] = {}
    db.init_app(app)
    for datasource in app.extensions['datasources']:
        if datasource.init_context:
            datasource.init_context(app)


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
