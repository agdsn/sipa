# -*- coding: utf-8 -*-
import os

from flask import request
from flask.ext.babel import gettext
from flask.ext.login import current_user
from sqlalchemy.exc import OperationalError

model_name = os.getenv('SIPA_MODEL', 'sample')

module = __import__('{}.{}.user'.format(__name__, model_name),
                    fromlist='{}.{}'.format(__name__, model_name))

init_context = module.init_context
User = module.User


def query_gauge_data():
    credit = {}
    try:
        if current_user.is_authenticated():
            credit['data'] = current_user.get_current_credit()
        else:
            from model import User
            user = User.from_ip(request.remote_addr)
            if isinstance(user, User):
                credit['data'] = user.get_current_credit()
    except OperationalError:
        credit['error'] = gettext(u'Fehler bei der Abfrage der Daten')
    else:
        if 'data' not in credit:
            credit['error'] = gettext(u'Diese IP gehört nicht '
                                      u'zu unserem Netzwerk')
    return credit
