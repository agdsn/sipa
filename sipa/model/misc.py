from collections import namedtuple

from flask import request
from flask_login import current_user

from sipa.backends import backends

TransactionTuple = namedtuple('Transaction', ['datum', 'value'])

PaymentDetails = namedtuple('PaymentDetails', 'recipient bank iban bic purpose')


def has_connection(user):
    return user.is_authenticated and user.has_connection


def should_display_traffic_data():
    return has_connection(current_user) or has_connection(
        backends.user_from_ip(request.remote_addr))
