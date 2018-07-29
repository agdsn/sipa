from collections import namedtuple

from flask import request
from flask_login import current_user
from sqlalchemy.exc import OperationalError

from sipa.backends.extension import backends

TransactionTuple = namedtuple('Transaction', ['datum', 'value'])

PaymentDetails = namedtuple('PaymentDetails', 'recipient bank iban bic purpose')


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
