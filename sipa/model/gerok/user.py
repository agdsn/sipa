# -*- coding: utf-8 -*-
import logging
from datetime import date, timedelta
from functools import partial

import requests
from flask_login import AnonymousUserMixin
from flask.globals import current_app
from werkzeug.local import LocalProxy

from sipa.model.user import BaseUser
from sipa.model.fancy_property import active_prop, connection_dependent, \
    unsupported_prop
from sipa.utils import argstr
from sipa.utils.exceptions import PasswordInvalid, UserNotFound

logger = logging.getLogger(__name__)


endpoint = LocalProxy(lambda: current_app.extensions['gerok_api']['endpoint'])
token = LocalProxy(lambda: current_app.extensions['gerok_api']['token'])


# noinspection PyMethodMayBeStatic
class User(BaseUser):
    """User object will be created from LDAP credentials,
    only stored in session.

    the terms 'uid' and 'username' refer to the same thing.
    """

    def __init__(self, user_data):
        super().__init__(uid=user_data['login'])
        self.cache_information(user_data)
        self._user_data = user_data  # keep it for the repr

    def __repr__(self):
        return "{}.{}({})".format(__name__, type(self).__name__, argstr(
            user_data=self._user_data,
        ))

    can_change_password = False

    @classmethod
    def get(cls, username, **kwargs):
        """Static method for flask-login user_loader,
        used before _every_ request.
        """
        userData = do_api_call('find?login=' + str(username))

        if not userData:
            raise UserNotFound

        return cls(user_data=userData)

    @classmethod
    def authenticate(cls, username, password):
        auth = do_api_call('auth', 'post', {'login': username,
                                            'pass': password})

        if auth == 'NoAccount':
            raise UserNotFound

        if auth:
            return cls.get(username)
        else:
            raise PasswordInvalid

    @classmethod
    def from_ip(cls, ip):
        try:
            userData = do_api_call('find?ip=' + ip)
        except ConnectionError:
            return AnonymousUserMixin()

        if not userData:
            return AnonymousUserMixin()

        return cls(user_data=userData)

    def cache_information(self, user_data=None):
        if user_data is None:
            # If neither an _id nor user_data is provided, this is a
            # bug.
            assert hasattr(self, '_id')
            # pylint: disable=access-member-before-definition
            user_data = do_api_call(str(self._id))

        self._id = user_data.get('id', '')
        self._login = user_data.get('login', '')
        self._address = user_data.get('address', '')
        self._mail = user_data.get('mail', '')
        self._status = user_data.get('status', '')
        self._realname = user_data.get('name', '')

        hosts = user_data.get('hosts', [])
        self._ips = {h['ip'] for h in hosts} - {None}
        self._macs = {h['mac'] for h in hosts} - {None}
        self._hostnames = {h['hostname'] for h in hosts} - {None}
        self._hostaliases = {h['alias'] for h in hosts} - {None}

    def change_password(self):
        raise NotImplementedError

    @property
    def traffic_history(self):
        trafficData = do_api_call("{}/traffic".format(self._id))

        if trafficData:
            hostOneTraffic = trafficData[0]['traffic']
            traffic_history = []

            # loop through expected days ([-6..0])
            for d in range(-6, 1):
                date = date_from_delta(d)
                day = date.weekday()
                # pick the to `date` corresponding data
                host = next((
                    x for x in hostOneTraffic
                    if x['date'] == date.strftime("%Y-%m-%d")
                ), None)
                if host:
                    (input, output, credit) = (
                        round(host[param] / 1024, 2)
                        for param in ['in', 'out', 'credit']
                    )

                    traffic_history.append({
                        'day': day,
                        'input': input,
                        'output': output,
                        'throughput': input+output,
                        'credit': credit,
                    })
                else:
                    traffic_history.append({
                        'day': day,
                        'input': 0.0,
                        'output': 0.0,
                        'throughput': 0.0,
                        'credit': 0.0,
                    })

            return traffic_history
        else:
            return [{
                'day': day,
                'input': 0.0,
                'output': 0.0,
                'throughput': 0.0,
                'credit': 0.0,
            } for day in range(7)]

    @property
    def credit(self):
        creditData = do_api_call(str(self._id) + '/credit')
        return creditData[0]['credit'] / 1024 if creditData else 0

    max_credit = 63 * 1024 * 1024
    daily_credit = 3 * 1024 * 1024

    @active_prop
    def id(self):
        return self._id

    @active_prop
    def realname(self):
        return self._realname

    @active_prop
    def login(self):
        return self._login

    @active_prop
    def status(self):
        return self._status

    has_connection = True

    @active_prop
    def address(self):
        return self._address

    @active_prop
    @connection_dependent
    def ips(self):
        return ", ".join(self._ips)

    @active_prop
    @connection_dependent
    def mac(self):
        return ", ".join(self._macs)

    @active_prop
    def mail(self):
        if self._mail:
            return self._mail
        # TODO: Get mail suffix from `DataSource`
        return "{}@wh17.tu-dresden.de".format(self._login)

    @active_prop
    @connection_dependent
    def hostname(self):
        return ", ".join(self._hostnames)

    @active_prop
    @connection_dependent
    def hostalias(self):
        return ", ".join(self._hostaliases)

    @unsupported_prop
    def userdb_status(self):
        pass

    userdb = None

    @unsupported_prop
    def finance_balance(self):
        raise NotImplementedError


def do_api_call(request, method='get', postdata=None):
    """Request the NVTool-Api for informations
    """

    if method == 'get':
        request_function = requests.get
    elif method == 'post':
        request_function = partial(requests.post, data=postdata)
    else:
        raise ValueError("`method` must be one of ['get', 'post']!")

    try:
        response = request_function(
            endpoint + request,
            verify=False,
            headers={'Authorization': 'Token token={}'.format(token)},
        )
    except ConnectionError as e:
        logger.error("Caught a ConnectionError when accessing Gerok API",
                     extra={'data': {'endpoint': endpoint + request}})
        raise ConnectionError("Gerok API unreachable") from e

    if response.status_code not in [200, 400, 403, 404]:
        logger.warning("Gerok API returned HTTP status %s", response.status_code,
                       extra={'data': {'status_code': response.status_code}})

    try:
        return response.json()
    except ValueError:
        return response.text


def date_from_delta(delta):
    """Return a `datetime.date` which differs delta days from today"""
    return date.today() + timedelta(delta)


def date_str_from_delta(delta):
    """Return a date-string which differs delta days from today"""
    return date_from_delta(delta).strftime("%Y-%m-%d")
