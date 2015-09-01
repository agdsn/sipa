# -*- coding: utf-8 -*-
import datetime

from flask.ext.login import AnonymousUserMixin
from flask.globals import current_app

from model.constants import FULL_FEATURE_SET, info_property, ACTIONS, \
    STATUS_COLORS, WEEKDAYS
from model.default import BaseUser
from sipa.utils.exceptions import PasswordInvalid, UserNotFound

import requests

# noinspection PyMethodMayBeStatic
class User(BaseUser):
    """User object will be created from LDAP credentials,
    only stored in session.

    the terms 'uid' and 'username' refer to the same thing.
    """

    def __init__(self, uid, id, name=None, mail=None, ip=None):
        super(User, self).__init__(uid)
        self.id = id
        self.name = name
        self.group = "static group"
        self.mail = mail
        self._ip = ip

    def _get_ip(self):
        # TODO: check whether / how this function is used.
        self._ip = "127.0.0.1"

    def __repr__(self):
        return "User<{},{}.{}>".format(self.uid, self.name, self.group)

    def __str__(self):
        return "User {} ({}), {}".format(self.name, self.uid, self.group)

    _supported_features = FULL_FEATURE_SET - {'userdb', 'mac_change', 'mail_change', 'password_change'}

    @staticmethod
    def get(username, **kwargs):
        """Static method for flask-login user_loader,
        used before _every_ request.
        """
        userData = User.do_api_call('find?login=' + str(username))

        if userData is None:
            raise UserNotFound

        uid = userData["login"] or username
        name = userData["name"] or username
        mail = username + "@wh17.tu-dresden.de"

        return User(uid, userData["id"], name, mail, "127.0.0.1")

    @staticmethod
    def authenticate(username, password):
        auth = User.do_api_call('auth', 'post', {'login': username, 'pass': password})

        if auth == 'NoAccount':
            raise UserNotFound

        if auth:
            return User.get(username)
        else:
            raise PasswordInvalid

    @staticmethod
    def from_ip(ip):
        userData = User.do_api_call('find?ip=' + ip)

        if userData is not None:
            return User(userData["login"], userData["name"], 'passive')
        else:
            return AnonymousUserMixin()

    def get_information(self):
        userData = User.do_api_call(str(self.id))

        return {
            'id': info_property(userData["id"]),
            'uid': info_property(userData["login"]),
            'address': info_property(userData["address"]),
            'mail': info_property(userData["mail"]),
            'status': info_property(userData["status"], STATUS_COLORS.GOOD),
            'ip': info_property(", ".join([h["ip"] for h in userData["hosts"] if h["ip"] != None]), STATUS_COLORS.INFO),
            'mac': info_property(", ".join([h["mac"] for h in userData["hosts"] if h["mac"] != None])),
            'hostname': info_property(", ".join([h["hostname"] for h in userData["hosts"] if h["hostname"] != None])),
            'hostalias': info_property(", ".join([h["alias"] for h in userData["hosts"] if h["alias"] != None]))
        }

    def get_traffic_data(self):
        trafficData = User.do_api_call(str(self.id) + '/traffic')

        if (trafficData):
            hostOneTraffic = trafficData[0]["traffic"]
            traffic = {'history': [], 'credit': 0}

            # loop through expected days ([-6..0])
            for d in range(-6, 1):
                date = datetime.date.today() + datetime.timedelta(d)
                day = date.strftime('%w')
                # pick the to `date` corresponding data
                d = next((x for x in hostOneTraffic if x['date'] == date.strftime("%Y-%m-%d")), None)
                if d:
                    (input, output, credit) = (
                        round(d[param] / 1048576.0, 2)
                        for param in ['in', 'out', 'credit']
                    )
                    traffic['history'].append(
                        (WEEKDAYS[day], input, output, credit))
                else:
                    traffic['history'].append(
                        (WEEKDAYS[day], 0.0, 0.0, 0.0))

            traffic['credit'] = (lambda x: x['credit']/1048576)(hostOneTraffic[-1])

            return traffic
        else:
            return {'credit': 0,
                'history': [(WEEKDAYS[str(day)], 0, 0, 0)
                            for day in range(7)]}

    def get_current_credit(self):
        creditData = User.do_api_call(str(self.id) + '/credit')
        return creditData[0]["credit"]/1048576 if creditData else 0

    def change_password(self, old, new):
        raise NotImplementedError("Function change_password not implemented")

    def change_mac_address(self, old, new):
        raise NotImplementedError("Function change_mac_address not implemented")

    def change_mail(self, password, new_mail):
        raise NotImplementedError("Function change_mail not implemented")

    @staticmethod
    def do_api_call(request, method = 'get', postdata = None):
        """Request the NVTool-Api for informations
        """
        requestUri = current_app.config['GEROK_ENDPOINT'] + request
        authHeaderStr = 'Token token=' + current_app.config['GEROK_API_TOKEN']

        if (method == 'get'):
            response = requests.get(requestUri, verify=False, headers={'Authorization': authHeaderStr})
        else:
            response = requests.post(requestUri, data = postdata, verify=False, headers={'Authorization': authHeaderStr})

        return response.json()
