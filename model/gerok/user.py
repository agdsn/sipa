# -*- coding: utf-8 -*-
import datetime

from flask.ext.login import AnonymousUserMixin
from flask.globals import current_app

from werkzeug.local import LocalProxy

from model.constants import WEEKDAYS
from model.default import BaseUser
from model.property import active_prop, unsupported_prop

from sipa.utils.exceptions import PasswordInvalid, UserNotFound
from sipa.utils import argstr

import requests


endpoint = LocalProxy(lambda: current_app.extensions['gerok_api']['endpoint'])
token = LocalProxy(lambda: current_app.extensions['gerok_api']['token'])


# noinspection PyMethodMayBeStatic
class User(BaseUser):
    """User object will be created from LDAP credentials,
    only stored in session.

    the terms 'uid' and 'username' refer to the same thing.
    """

    datasource = 'gerok'

    def __init__(self, uid, id, name=None, mail=None):
        super(User, self).__init__(uid)
        self._id = id
        self.name = name
        self.group = "static group"
        self.mail = mail
        self.cache_information()

    def __repr__(self):
        return "{}.{}({})".format(__name__, type(self).__name__, argstr(
            uid=self.uid,
            id=self._id,
            name=self.name,
            mail=self.mail,
        ))

    def __str__(self):
        return "User {} ({}), {}".format(self.name, self.uid, self.group)

    can_change_password = False

    @classmethod
    def get(cls, username, **kwargs):
        """Static method for flask-login user_loader,
        used before _every_ request.
        """
        userData = do_api_call('find?login=' + str(username))

        if userData is None:
            raise UserNotFound

        uid = userData['login'] or username
        name = userData['name'] or username
        # TODO: Somehow access the entry in the datasource constructor
        mail = username + "@wh17.tu-dresden.de"

        return cls(uid, userData['id'], name, mail)

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
        userData = do_api_call('find?ip=' + ip)

        if userData is not None:
            return cls(userData['login'], userData['name'], 'passive')
        else:
            return AnonymousUserMixin()

    def cache_information(self):
        user_data = do_api_call(str(self.id))

        self._id = user_data['id']
        self._login = user_data['login']
        self._address = user_data['address']
        self._mail = user_data['mail']
        self._status = user_data['status']

        hosts = user_data['hosts']
        self._ips = {h['ip'] for h in hosts} - {None}
        self._macs = {h['mac'] for h in hosts} - {None}
        self._hostnames = {h['hostname'] for h in hosts} - {None}
        self._hostaliases = {h['alias'] for h in hosts} - {None}

    def change_password(self):
        raise NotImplementedError

    @property
    def traffic_history(self):
        trafficData = do_api_call("{}/traffic".format(self.id))

        if (trafficData):
            hostOneTraffic = trafficData[0]['traffic']
            traffic = {'history': [], 'credit': 0}

            # loop through expected days ([-6..0])
            for d in range(-6, 1):
                date = datetime.date.today() + datetime.timedelta(d)
                day = date.strftime('%w')
                # pick the to `date` corresponding data
                d = next((
                    x for x in hostOneTraffic
                    if x['date'] == date.strftime("%Y-%m-%d")
                ), None)
                if d:
                    (input, output, credit) = (
                        round(d[param] / 1048576.0, 2)
                        for param in ['in', 'out', 'credit']
                    )
                    traffic['history'].append(
                        (WEEKDAYS[int(day)], input, output, credit))
                else:
                    traffic['history'].append(
                        (WEEKDAYS[int(day)], 0.0, 0.0, 0.0))

            traffic['credit'] = (lambda x: x['credit']/1048576)(
                hostOneTraffic[-1])

            return traffic
        else:
            return {'credit': 0,
                    'history': [(WEEKDAYS[int(day)], 0, 0, 0)
                                for day in range(7)]}

    @property
    def credit(self):
        creditData = do_api_call(str(self.id) + '/credit')
        return creditData[0]['credit']/1048576 if creditData else 0

    @active_prop
    def id(self):
        return self._id

    @active_prop
    def login(self):
        return self._login

    @active_prop
    def status(self):
        return self._status

    @active_prop
    def address(self):
        return self._address

    @active_prop
    def ips(self):
        return ", ".join(self._ips)

    @active_prop
    def mac(self):
        return ", ".join(self._macs)

    @active_prop
    def mail(self):
        return self._mail

    @active_prop
    def hostname(self):
        return ", ".join(self._hostnames)

    @active_prop
    def hostalias(self):
        return ", ".join(self._hostaliases)

    @unsupported_prop
    def userdb_status(self):
        pass

    userdb = None


def do_api_call(request, method='get', postdata=None):
    """Request the NVTool-Api for informations
    """
    requestUri = endpoint + request
    authHeaderStr = 'Token token=' + token

    if (method == 'get'):
        response = requests.get(requestUri, verify=False,
                                headers={'Authorization': authHeaderStr})
    else:
        response = requests.post(requestUri, data=postdata, verify=False,
                                 headers={'Authorization': authHeaderStr})

    if response.status_code != 200:
        raise ValueError("Gerok API returned status != 200 OK")

    try:
        return response.json()
    except ValueError:
        return response.text
