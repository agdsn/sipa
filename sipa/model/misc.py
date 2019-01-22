from collections import namedtuple

from flask import request
from flask_login import current_user

from sipa.backends import backends

TransactionTuple = namedtuple('Transaction', ['datum', 'value'])

PaymentDetails = namedtuple('PaymentDetails', 'recipient bank iban bic purpose')


def should_display_traffic_data():
    return ((current_user.is_authenticated and current_user.has_connection)
            or backends.user_from_ip(request.remote_addr) is not None)
