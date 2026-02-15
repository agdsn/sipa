from __future__ import annotations
from dataclasses import dataclass
import typing as t
from collections import namedtuple

from flask import request
from flask_login import current_user

from sipa.backends import backends
from sipa.backends.types import UserLike

if t.TYPE_CHECKING:
    from .user import BaseUser
else:

    class BaseUser: ...


TransactionTuple = namedtuple("Transaction", ["datum", "value"])


@dataclass(frozen=True)
class PaymentDetails:
    recipient: str
    bank: str
    iban: str
    bic: str

    def with_purpose(self, purpose: str):
        return UserPaymentDetails(
            recipient=self.recipient,
            bank=self.bank,
            iban=self.iban,
            bic=self.bic,
            purpose=purpose,
        )


@dataclass(frozen=True)
class UserPaymentDetails(PaymentDetails):
    purpose: str


def has_connection(user: UserLike) -> bool:
    try:
        has_connection = user.has_connection
    except AttributeError:
        return False
    return user.is_authenticated and has_connection


def should_display_traffic_data() -> bool:
    if has_connection(t.cast(BaseUser, current_user)):
        return True
    if not (ip := request.remote_addr):
        return False
    return (u := backends.user_from_ip(ip)) is not None and has_connection(u)
