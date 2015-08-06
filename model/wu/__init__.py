#!/usr/bin/env python
# -*- coding: utf-8 -*-

from random import random
import datetime

from flask import request

from flask.ext.babel import gettext

from flask.ext.login import current_user

from sqlalchemy.exc import OperationalError

from model.default import BaseUser
from model.wu.database_utils import sql_query
from model.wu.ldap_utils import search_in_group, LdapConnector, get_dn

from sipa import logger, app
from sipa.utils import timestamp_from_timetag, timetag_from_timestamp
from sipa.utils.exceptions import PasswordInvalid, UserNotFound, DBQueryEmpty


# TODO split into `SQLUser` and `LDAPUser` or similar
# TODO split into AuthenticatedUserMixin and FlaskLoginUserMixin
class User(BaseUser):
    """User object will be created from LDAP credentials,
    only stored in session.

    the terms 'uid' and 'username' refer to the same thing.
    """

    def __init__(self, uid, name, mail):
        super(BaseUser, self).__init__()
        self.uid = uid
        self.name = name
        self.group = self.define_group()
        self.mail = mail


    def __repr__(self):
        # todo use here or in `__str__` real-world strings as "Alice Brown"
        return "User<%s,%s,%s>" % (self.uid, self.name, self.group)


    def get_id(self):
        return self.uid


    def define_group(self):
        """Define a user group from the LDAP group
        """
        # todo check: does this work? has it _ever_ worked?
        if search_in_group(self.uid, 'Aktiv'):
            return 'active'
        elif search_in_group(self.uid, 'Exaktiv'):
            return 'exactive'
        return 'passive'


    @staticmethod
    def get(username):
        """Static method for flask-login user_loader,
        used before _every_ request.
        """
        user = LdapConnector.fetch_user(username)
        return User(user['uid'], user['name'], user['mail'])


    def re_authenticate(self, password):
        self.authenticate(self.uid, password)


    @staticmethod
    def authenticate(username, password):
        """This method checks the user and password combination against LDAP

        Returns the User object if successful.
        """
        try:
            with LdapConnector(username, password):
                return User.get(username)
        except PasswordInvalid:
            logger.info('Failed login attempt (Wrong %s)', 'password',
                        extra={'data': {'username': username}})
            raise
        except UserNotFound:
            logger.info('Failed login attempt (Wrong %s)', 'username',
                        extra={'data': {'username': username}})
            raise

    def change_password(self, old, new):
        """Change a user's password from old to new
        """
        try:
            with LdapConnector(self.uid, old) as l:
                l.passwd_s(get_dn(l),
                           old.encode('iso8859-1'),
                           new.encode('iso8859-1'))
        except PasswordInvalid:
            logger.info('Wrong password provided when attempting '
                        'change of password')
            raise
        else:
            logger.info('Password successfully changed')


    @staticmethod
    def from_ip(ip):
        result = sql_query("SELECT nutzer_id FROM computer WHERE c_ip = %s",
                            (ip,)).fetchone()
        if result is None:
            return None

        return User.get(result['nutzer_id'])

    def get_information(self):
        """Executes select query for the username and returns a prepared dict.

        * Dormitory IDs in Mysql are from 1-11, so we map to 0-10 with "x-1".

        Returns "-1" if a query result was empty (None), else
        returns the prepared dict.
        """
        # user = sql_query(
        #     "SELECT nutzer_id, wheim_id, etage, zimmernr, status "
        #     "FROM nutzer "
        #     "WHERE unix_account = %s",
        #     (self.uid,)
        # ).fetchone()
        #
        # if not user:
        #     raise DBQueryEmpty
        #
        # computer = sql_query(
        #     "SELECT c_etheraddr, c_ip, c_hname, c_alias "
        #     "FROM computer "
        #     "WHERE nutzer_id = %s",
        #     (user['nutzer_id'])
        # ).fetchone()
        #
        # if not computer:
        #     raise DBQueryEmpty

        # todo fix helios && implement
        #
        # user_dict = {
        #     'id': user['nutzer_id'],
        #     'address': u"{0} / {1} {2}".format(
        #         app.config['DORMITORIES'][user['wheim_id'] - 1],
        #         user['etage'],
        #         user['zimmernr']
        #     ),
        #     'status': status_string_from_id(user['status']),
        #     'status_is_good': user['status'] == 1,
        #     'ip': computer['c_ip'],
        #     'mac': computer['c_etheraddr'].upper(),
        #     'hostname': computer['c_hname'],
        #     'hostalias': computer['c_alias'],
        #     'heliosdb': has_mysql_db
        # }

        user_dict = {
            'id': 1337,
            'checksum': 0,
            'address': '<insert description here>',
            'status': 'OK',
            'status_is_good': True,
            'ip': '127.0.0.1',
            'mac': 'aa:bb:cc:dd:ee:ff',
            'hostname': 'whdd231wh49xv',
            'hostalias': 'leethaxor',
            'heliosdb': False
        }

        return user_dict


    def get_traffic_data(self):
        # todo implement
        def rand():
            return round(random(), 2)
        return {
            'credit': 0,
            # todo app is used in /model. this is bad.
            # These are Weekdays, not anything app-related.
            'history': [("HOMO",  # app.config['WEEKDAYS'][str(day)],
                         rand(), rand(), rand())
                        for day in range(7)]
        }

    # todo copy below function backup to above
    # def _query_trafficdata(ip=None, user_id=None):
    #     """Query traffic input/output for IP
    #
    #     :param ip: a valid ip
    #     :param user_id: an id of a mysql user tuple
    #     :return: a dict containing the traffic data in the form of
    #     {'history': [('weekday', in, out, credit), …], 'credit': credit}
    #     """
    #     if user_id is None:
    #         if ip is None:
    #             raise AttributeError('Either ip or user_id must be specified!')
    #         user_id = user_id_from_ip(ip)
    #     else:
    #         # ip gotten from db is preferred to the ip possibly given as parameter
    #         ip = ip_from_user_id(user_id)
    #
    #     trafficdata = sql_query(
    #         "SELECT t.timetag - %(today)s AS day, input, output, amount "
    #         "FROM traffic.tuext AS t "
    #         "LEFT OUTER JOIN credit AS c ON t.timetag = c.timetag "
    #         "WHERE ip = %(ip)s AND c.user_id = %(uid)s "
    #         "AND t.timetag BETWEEN %(weekago)s AND %(today)s "
    #         "ORDER BY 'day' DESC ",
    #         {'today': timetag_from_timestamp(),
    #          'weekago': timetag_from_timestamp() - 6,
    #          'ip': ip,
    #          'uid': user_id}
    #     ).fetchall()
    #
    #     if not trafficdata:
    #         raise DBQueryEmpty('No trafficdata retrieved for user {}@{}'
    #                            .format(user_id, ip))
    #
    #     traffic = {'history': [], 'credit': 0}
    #     returned_days = [int(i['day']) for i in trafficdata]
    #
    #     # loop through expected days ([-6..0])
    #     for d in range(-6, 1):
    #         day = datetime.date.fromtimestamp(
    #             timestamp_from_timetag(timetag_from_timestamp() + d)
    #         ).strftime('%w')
    #         if d in returned_days:
    #             # pick the to `d` corresponding item of the mysql-result
    #             i = next((x for x in trafficdata if x['day'] == d), None)
    #
    #             (input, output, credit) = (
    #                 round(i[param] / 1024.0, 2)
    #                 for param in ['input', 'output', 'amount']
    #             )
    #             traffic['history'].append(
    #                 (app.config['WEEKDAYS'][day], input, output, credit))
    #         else:
    #             traffic['history'].append(
    #                 (app.config['WEEKDAYS'][day], 0.0, 0.0, 0.0))
    #
    #     traffic['credit'] = (lambda x: x[3] - x[1] - x[2])(traffic['history'][-1])
    #
    #     return traffic


    def get_current_credit(self):
        # todo implement
        return round(random(), 2)


def query_gauge_data():
    credit = {}
    try:
        if current_user.is_authenticated():
            credit['data'] = current_user.get_current_credit()
        else:
            from model import User
            credit['data'] = User.from_ip(request.remote_addr).get_current_credit()
            # query_current_credit(ip=request.remote_addr)
    except OperationalError:
        credit['error'] = gettext(u'Fehler bei der Abfrage der Daten')
    else:
        if not credit['data']:
            credit['error'] = gettext(u'Diese IP gehört nicht '
                                      u'zu unserem Netzwerk')
    return credit