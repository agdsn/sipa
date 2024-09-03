from collections import namedtuple

from flask import request
from flask_login import current_user

from sipa.backends import backends

import typing as t
from schwifty import IBAN

TransactionTuple = namedtuple('Transaction', ['datum', 'value'])

class PaymentDetails(t.NamedTuple):
    recipient: str
    iban: IBAN
    purpose: str


def has_connection(user):
    return user.is_authenticated and user.has_connection


def should_display_traffic_data():
    return has_connection(current_user) or has_connection(
        backends.user_from_ip(request.remote_addr))
